"""ERA5-Land monthly climate 1991-2020 on the study cells (healpix-geo WGS84, depth 10): the observation-based
baseline for the Climate DT configuration.

Sources (Copernicus Climate Data Store, CC-BY; account read by cdsapi from ~/.cdsapirc, never copied here):
  * derived-era5-land-daily-statistics: 2 m temperature daily maximum and daily minimum (UTC day, from hourly
    data), one request per year and statistic -> monthly means of daily max / min (WorldClim's tmax / tmin);
  * reanalysis-era5-land-monthly-means: total precipitation (m per day, monthly mean) -> mm per month.
Grid: 0.1 deg regular lon/lat points; resampled with healpix-resample (common.BilinearToCells, conservative
mode, area = cos(latitude)). Sea points are missing in ERA5-Land and stay missing.

Usage: python pipeline/04_era5land.py <ROOT> [<Y0> <Y1>]
Writes <ROOT>/era5l/<year>.npz with tmax, tmin (degC) and pr (mm per month), arrays (12, ncells), float32.
Raw downloads are deleted after processing.
"""
import calendar
import os
import sys
import time
import zipfile

import numpy as np
import pandas as pd
import xarray as xr
import cdsapi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ROOT = sys.argv[1]
Y0, Y1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1991, 2020)
OUT = f"{ROOT}/era5l"
x0, y0, x1, y1 = common.EXTENT
AREA = [y1, x0, y0, x1]          # N, W, S, E


def retrieve(c, dataset, req, target):
    for attempt in range(6):
        try:
            c.retrieve(dataset, req, target)
            return
        except Exception as e:
            print("retry", dataset, req.get("year"), attempt, type(e).__name__, str(e)[:200], flush=True)
            time.sleep(120 * (attempt + 1))
    raise RuntimeError(f"CDS request failed: {dataset} {req.get('year')}")


def open_nc(path):
    if zipfile.is_zipfile(path):
        d = path + "_x"
        zipfile.ZipFile(path).extractall(d)
        path = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".nc")][0]
    return xr.open_dataset(path)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    cells = pd.read_parquet(f"{ROOT}/clim/cells.parquet")
    ids = cells.cell.values.astype(np.uint64)
    c = cdsapi.Client(quiet=True)
    op = None
    # precipitation, all years in one request
    pr_file = f"{OUT}/tp_monthly_{Y0}_{Y1}.nc"
    if not os.path.exists(pr_file):
        retrieve(c, "reanalysis-era5-land-monthly-means",
                 {"product_type": ["monthly_averaged_reanalysis"], "variable": ["total_precipitation"],
                  "year": [str(y) for y in range(Y0, Y1 + 1)], "month": [f"{m:02d}" for m in range(1, 13)],
                  "time": ["00:00"], "area": AREA, "data_format": "netcdf", "download_format": "unarchived"}, pr_file)
    tp = open_nc(pr_file)
    tvar = "valid_time" if "valid_time" in tp.dims else "time"
    for year in range(Y0, Y1 + 1):
        fn = f"{OUT}/{year}.npz"
        if os.path.exists(fn):
            continue
        t0 = time.time()
        raw = {}
        for stat in ("daily_maximum", "daily_minimum"):
            f = f"{OUT}/t2m_{stat}_{year}.nc"
            if not os.path.exists(f):
                retrieve(c, "derived-era5-land-daily-statistics",
                         {"variable": ["2m_temperature"], "year": str(year), "month": [f"{m:02d}" for m in range(1, 13)],
                          "day": [f"{d:02d}" for d in range(1, 32)], "daily_statistic": stat,
                          "time_zone": "utc+00:00", "frequency": "1_hourly", "area": AREA}, f)
            raw[stat] = f
        tx = open_nc(raw["daily_maximum"]).t2m
        tn = open_nc(raw["daily_minimum"]).t2m
        dt = "valid_time" if "valid_time" in tx.dims else "time"
        tx_m = tx.groupby(f"{dt}.month").mean().values - 273.15
        tn_m = tn.groupby(f"{dt}.month").mean().values - 273.15
        p = tp.tp.sel({tvar: tp[tvar].dt.year == year})
        days = np.array([calendar.monthrange(year, m)[1] for m in range(1, 13)])
        pr_m = p.values * 1000 * days[:, None, None]                         # m/day -> mm per month
        assert tx_m.shape[0] == 12 and pr_m.shape[0] == 12
        if op is None:
            lat, lon = tx.latitude.values, tx.longitude.values
            LON, LAT = np.meshgrid(lon, lat)
            op = common.BilinearToCells(LON.ravel(), LAT.ravel(), np.cos(np.radians(LAT.ravel())), ids)
            assert np.allclose(p.latitude.values, lat) and np.allclose(p.longitude.values, lon)
        out = {k: np.stack([op(a[m].ravel()) for m in range(12)]).astype(np.float32)
               for k, a in (("tmax", tx_m), ("tmin", tn_m), ("pr", pr_m))}
        np.savez_compressed(fn, **out)
        for f in raw.values():
            os.remove(f)
        print("OK ERA5-Land", year, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
