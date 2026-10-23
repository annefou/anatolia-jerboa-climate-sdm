"""WorldClim 2.1 bioclimatic variables on HEALPix cells (depth 10, healpix-geo, WGS84, NESTED).

Inputs (read over HTTP, only the study window; nothing redistributed):
  * baseline 1970-2000, wc2.1_2.5m_bio.zip (Fick & Hijmans 2017);
  * CMIP6 downscaled with WorldClim's change-factor method, wc2.1_2.5m_bioc_<GCM>_<SSP>_<period>.tif:
    MIROC6 under all four SSPs and four periods (the paper's design), and every other GCM WorldClim offers for
    SSP3-7.0 2021-2040 (ensemble spread, not in the paper).
The paper used 30 arc-second files; this replication uses 2.5 arc-minute (~4.6 km) files, which are finer
than the ~6.4 km HEALPix cells the model runs on. Resampling: healpix-resample BilinearResampler in conservative
mode (common.BilinearToCells); cells less than half covered by land in the baseline (exact area overlap) are
set to missing, as WorldClim has no values over sea.
Variables: the eight retained in the paper (Table 2): bio2, bio3, bio4, bio8, bio9, bio14, bio15, bio19.

Usage: python pipeline/01_worldclim_healpix.py <ROOT>     (ROOT = work)
Writes <ROOT>/clim/cells.parquet (cell ids, centres) and <ROOT>/clim/worldclim_<name>.parquet.
"""
import os
import sys
import time

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ROOT = sys.argv[1]
OUT = f"{ROOT}/clim"
BIO = [2, 3, 4, 8, 9, 14, 15, 19]
RES = 1 / 24                     # 2.5 arc-minutes
BASE = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_bio.zip"
FUT = "https://geodata.ucdavis.edu/cmip6/2.5m/{g}/{s}/wc2.1_2.5m_bioc_{g}_{s}_{p}.tif"
SSPS = ["ssp126", "ssp245", "ssp370", "ssp585"]
PERIODS = ["2021-2040", "2041-2060", "2061-2080", "2081-2100"]
GCMS = ["ACCESS-CM2", "BCC-CSM2-MR", "CMCC-ESM2", "EC-Earth3-Veg", "FIO-ESM-2-0", "GISS-E2-1-G",
        "HadGEM3-GC31-LL", "INM-CM5-0", "IPSL-CM6A-LR", "MIROC6", "MPI-ESM1-2-HR", "MRI-ESM2-0", "UKESM1-0-LL"]
ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="5", GDAL_HTTP_RETRY_DELAY="20",
           CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif,.zip")

# study window on the global 2.5' grid (x0 = -180, ytop = 90), padded by one pixel
x0, y0, x1, y1 = common.EXTENT
C0, C1 = int(np.floor((x0 + 180) / RES)) - 1, int(np.ceil((x1 + 180) / RES)) + 1
R0, R1 = int(np.floor((90 - y1) / RES)) - 1, int(np.ceil((90 - y0) / RES)) + 1
WIN = Window(C0, R0, C1 - C0, R1 - R0)


def read_window(path: str, band: int) -> np.ndarray:
    for i in range(5):
        try:
            with rasterio.Env(**ENV), rasterio.open(path) as r:
                assert abs(r.transform.a - RES) < 1e-9 and abs(r.transform.c + 180) < 1e-9 and abs(r.transform.f - 90) < 1e-9
                a = r.read(band, window=WIN, masked=True).astype("float64")
                return a.filled(np.nan)
        except rasterio.errors.RasterioIOError:
            if i == 4:
                raise
            time.sleep(30 * (i + 1))


def to_cells(arrays: dict, op, land) -> pd.DataFrame:
    out = {}
    for k, a in arrays.items():
        out[k] = op(a.ravel())
        out[k][~land] = np.nan               # cell mostly over sea: no WorldClim value
    return pd.DataFrame(out)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    ids, clon, clat, polys = common.extent_cells()
    xw, yt = -180 + C0 * RES, 90 - R0 * RES
    ci, pi, w = common.grid_weights(polys, xw, yt, RES, WIN.width, WIN.height)
    n = len(ids)
    # land share per cell from the baseline's valid pixels (exact overlap), then the resampler
    probe = read_window(f"/vsizip//vsicurl/{BASE}/wc2.1_2.5m_bio_1.tif", 1)
    _, land_frac = common.conservative_mean(ci, pi, w, probe.ravel(), n)
    land = land_frac >= 0.5
    pd.DataFrame({"cell": ids, "lon": clon, "lat": clat, "land_frac": land_frac}).to_parquet(f"{OUT}/cells.parquet", index=False)
    lon = -180 + (C0 + np.arange(WIN.width) + 0.5) * RES
    lat = 90 - (R0 + np.arange(WIN.height) + 0.5) * RES
    LON, LAT = np.meshgrid(lon, lat)
    op = common.BilinearToCells(LON.ravel(), LAT.ravel(), np.cos(np.radians(LAT.ravel())), ids)
    print(f"{n} cells at depth {common.DEPTH} ({common.cell_area_km2():.1f} km2 each)", flush=True)

    jobs = [("baseline_1970-2000", [f"/vsizip//vsicurl/{BASE}/wc2.1_2.5m_bio_{b}.tif" for b in BIO], [1] * len(BIO))]
    for s in SSPS:
        for p in PERIODS:
            jobs.append((f"MIROC6_{s}_{p}", [f"/vsicurl/{FUT.format(g='MIROC6', s=s, p=p)}"] * len(BIO), BIO))
    for g in GCMS:
        if g != "MIROC6":
            jobs.append((f"{g}_ssp370_2021-2040", [f"/vsicurl/{FUT.format(g=g, s='ssp370', p='2021-2040')}"] * len(BIO), BIO))
    for name, paths, bands in jobs:
        f = f"{OUT}/worldclim_{name}.parquet"
        if os.path.exists(f):
            continue
        t = time.time()
        try:
            arr = {f"bio{b}": read_window(pth, bd) for b, pth, bd in zip(BIO, paths, bands)}
        except rasterio.errors.RasterioIOError as e:
            print(f"skip {name}: {e}", flush=True)
            continue
        df = to_cells(arr, op, land)
        df.insert(0, "cell", ids)
        df.to_parquet(f, index=False)
        print(f"{name}: {time.time() - t:.0f} s, valid cells {df.bio9.notna().sum()}", flush=True)


if __name__ == "__main__":
    main()
