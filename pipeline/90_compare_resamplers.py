"""Which resampler for which variable? Exact area overlap (pipeline/common.py) against healpix-resample's
ConservativeResampler and BilinearResampler (plain and conservative=True), on the same inputs and target cells
(depth 10, healpix-geo WGS84, NESTED):

  1. WorldClim 2.1 baseline bio9 (temperature, degC) and bio14 (precipitation, mm), 2.5' lon/lat grid;
  2. Climate DT avg_2t, January 2030, IFS-FESOM SSP3-7.0, native spherical HEALPix nside 1024 (one probe
     field, internal), placed at its spherical cell centres taken as geodetic lon/lat.

Reported per method: share of target cells that get a value, and against the exact overlap: mean difference,
mean absolute difference, 99th percentile of |difference|, and the area-weighted regional mean.
Usage: python pipeline/90_compare_resamplers.py <ROOT> [<DT_GRIB>]
Writes results/resampler_comparison.json.
"""
import json
import os
import sys

import numpy as np
import rasterio
from rasterio.windows import Window
import healpix_geo.nested as hn
from healpix_resample import BilinearResampler, ConservativeResampler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ROOT = sys.argv[1]
DT = sys.argv[2] if len(sys.argv) > 2 else f"{ROOT}/dt_probe/clmn_high_avg_2t.grib"
RES = 1 / 24
BASE = "/vsizip//vsicurl/https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_bio.zip/wc2.1_2.5m_bio_{b}.tif"
ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.zip")


def hr(cls, lon, lat, val, area, conservative):
    op = cls(lon_deg=lon, lat_deg=lat, level=common.DEPTH, nest=True, ellipsoid="WGS84", verbose=False,
             **({"area": area} if area is not None else {}))
    if cls is ConservativeResampler or conservative:
        # conservative modes return sum(val * area) per cell; the mean of an intensive field is that sum
        # divided by the same operator applied to ones
        kw = {"conservative": True} if cls is BilinearResampler else {}
        num, den = op.resample(val, **kw), op.resample(np.ones_like(val), **kw)
        return np.asarray(num.cell_ids, np.uint64), np.asarray(num.cell_data, float) / np.asarray(den.cell_data, float)
    r = op.resample(val)
    return np.asarray(r.cell_ids, np.uint64), np.asarray(r.cell_data, float)


def compare(name, ids, exact, methods):
    pos = {int(c): i for i, c in enumerate(ids)}
    out = {"n_target_cells": int(np.isfinite(exact).sum())}
    ref_ok = np.isfinite(exact)
    for m, (cid, val) in methods.items():
        v = np.full(len(ids), np.nan)
        k = np.array([pos.get(int(c), -1) for c in cid])
        v[k[k >= 0]] = val[k >= 0]
        both = ref_ok & np.isfinite(v)
        d = v[both] - exact[both]
        out[m] = {"cells_with_value_pct": round(100 * both.sum() / ref_ok.sum(), 2),
                  "mean_diff": round(float(d.mean()), 4), "mae": round(float(np.abs(d).mean()), 4),
                  "p99_abs_diff": round(float(np.quantile(np.abs(d), 0.99)), 4),
                  "regional_mean": round(float(v[both].mean()), 4), "regional_mean_exact": round(float(exact[both].mean()), 4)}
    print(name, json.dumps(out, indent=1), flush=True)
    return out


def main():
    ids, clon, clat, polys = common.extent_cells()
    res = {"depth": common.DEPTH, "target": "healpix-geo WGS84 nested", "inputs": {}}
    # 1. WorldClim, lon/lat grid
    x0, y0, x1, y1 = common.EXTENT
    C0, C1 = int(np.floor((x0 + 180) / RES)) - 1, int(np.ceil((x1 + 180) / RES)) + 1
    R0, R1 = int(np.floor((90 - y1) / RES)) - 1, int(np.ceil((90 - y0) / RES)) + 1
    win = Window(C0, R0, C1 - C0, R1 - R0)
    ci, pi, w = common.grid_weights(polys, -180 + C0 * RES, 90 - R0 * RES, RES, win.width, win.height)
    lon = -180 + (C0 + np.arange(win.width) + 0.5) * RES
    lat = 90 - (R0 + np.arange(win.height) + 0.5) * RES
    LON, LAT = np.meshgrid(lon, lat)
    for b in (9, 14):
        with rasterio.Env(**ENV), rasterio.open(BASE.format(b=b)) as r:
            a = r.read(1, window=win, masked=True).astype(float).filled(np.nan)
        exact, _ = common.conservative_mean(ci, pi, w, a.ravel(), len(ids))
        ok = np.isfinite(a.ravel())
        lo, la, v = LON.ravel()[ok], LAT.ravel()[ok], a.ravel()[ok]
        area = np.cos(np.radians(la))
        methods = {"hr_conservative": hr(ConservativeResampler, lo, la, v, area, False),
                   "hr_bilinear": hr(BilinearResampler, lo, la, v, None, False),
                   "hr_bilinear_conservative": hr(BilinearResampler, lo, la, v, area, True)}
        res["inputs"][f"worldclim_bio{b}"] = compare(f"worldclim bio{b}", ids, exact, methods)
    # 2. Climate DT, spherical HEALPix nside 1024
    if os.path.exists(DT):
        import eccodes
        with open(DT, "rb") as f:
            h = eccodes.codes_grib_new_from_file(f)
            assert eccodes.codes_get(h, "gridType") == "healpix" and eccodes.codes_get(h, "orderingConvention") == "nested"
            vals = eccodes.codes_get_values(h) - 273.15
            nside = eccodes.codes_get(h, "Nside")
        sd = int(np.log2(nside))
        ti, si, ww = common.sphere_to_wgs84_weights(polys, sd)
        exact = np.bincount(ti, ww * vals[si.astype(np.int64)], minlength=len(ids))
        # source samples: spherical cells covering the extent (plus margin), at their centres
        ring = np.array([[x0 - 1, y0 - 1], [x1 + 1, y0 - 1], [x1 + 1, y1 + 1], [x0 - 1, y1 + 1]])
        src, _, _ = hn.polygon_coverage(ring, sd, ellipsoid="sphere", flat=True)
        src = np.asarray(src, np.uint64)
        slon, slat = hn.healpix_to_lonlat(src, sd, ellipsoid="sphere")
        v = vals[src.astype(np.int64)]
        methods = {"hr_conservative": hr(ConservativeResampler, slon, slat, v, None, False),
                   "hr_bilinear": hr(BilinearResampler, slon, slat, v, None, False),
                   "hr_bilinear_conservative": hr(BilinearResampler, slon, slat, v, None, True),
                   "same_index_no_regrid": (ids, vals[ids.astype(np.int64)])}
        res["inputs"]["climatedt_avg_2t_2030_01"] = compare("climate dt avg_2t", ids, exact, methods)
    os.makedirs("results", exist_ok=True)
    json.dump(res, open("results/resampler_comparison.json", "w"), indent=1)


if __name__ == "__main__":
    main()
