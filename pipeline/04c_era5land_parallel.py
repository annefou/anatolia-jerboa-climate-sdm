"""ERA5-Land daily maximum and minimum temperature, requested in parallel (same product, area and processing as
04_era5land.py, which sends one request at a time and needed about 9.5 hours per year in the CDS queue).

Each (year, statistic) request runs in its own thread; the CDS queues them per user and runs several at once.
When both statistics of a year are in, the year is processed exactly as in 04_era5land.py (monthly means of the
daily maximum and minimum, precipitation from the monthly-means file, HEALPix cells with common.BilinearToCells)
and written to <ROOT>/era5l/<year>.npz. Years already written are skipped, so it can run beside 04_era5land.py
and be restarted at any time. Raw downloads go to <ROOT>/era5l/parallel/ and are deleted once a year is written.

Usage: python pipeline/04c_era5land_parallel.py <ROOT> [<WORKERS>]

Not part of the results: kept for future work on daily indices (README, "Future exploration").
"""
import calendar
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ROOT = sys.argv[1]
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 8
sys.argv = [sys.argv[0], ROOT]                       # 04_era5land reads its arguments at import
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("era5land", os.path.join(os.path.dirname(__file__), "04_era5land.py"))
e5l = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e5l)

OUT = e5l.OUT
RAW = f"{OUT}/parallel"
LOCK = threading.Lock()


def fetch(year, stat):
    import cdsapi
    f = f"{RAW}/t2m_{stat}_{year}.nc"
    if not os.path.exists(f):
        tmp = f + ".part"
        e5l.retrieve(cdsapi.Client(quiet=True), "derived-era5-land-daily-statistics",
                     {"variable": ["2m_temperature"], "year": str(year), "month": [f"{m:02d}" for m in range(1, 13)],
                      "day": [f"{d:02d}" for d in range(1, 32)], "daily_statistic": stat,
                      "time_zone": "utc+00:00", "frequency": "1_hourly", "area": e5l.AREA}, tmp)
        os.replace(tmp, f)
    return year, stat, f


def process(year, files, tp, tvar, op_box):
    tx = e5l.open_nc(files["daily_maximum"]).t2m
    tn = e5l.open_nc(files["daily_minimum"]).t2m
    dt = "valid_time" if "valid_time" in tx.dims else "time"
    tx_m = tx.groupby(f"{dt}.month").mean().values - 273.15
    tn_m = tn.groupby(f"{dt}.month").mean().values - 273.15
    p = tp.tp.sel({tvar: tp[tvar].dt.year == year})
    days = np.array([calendar.monthrange(year, m)[1] for m in range(1, 13)])
    pr_m = p.values * 1000 * days[:, None, None]
    assert tx_m.shape[0] == 12 and pr_m.shape[0] == 12
    with LOCK:
        if op_box[0] is None:
            lat, lon = tx.latitude.values, tx.longitude.values
            LON, LAT = np.meshgrid(lon, lat)
            ids = pd.read_parquet(f"{ROOT}/clim/cells.parquet").cell.values.astype(np.uint64)
            op_box[0] = common.BilinearToCells(LON.ravel(), LAT.ravel(), np.cos(np.radians(LAT.ravel())), ids)
        op = op_box[0]
        out = {k: np.stack([op(a[m].ravel()) for m in range(12)]).astype(np.float32)
               for k, a in (("tmax", tx_m), ("tmin", tn_m), ("pr", pr_m))}
    np.savez_compressed(f"{OUT}/{year}.npz", **out)
    for f in files.values():
        os.remove(f)


def main():
    import cdsapi
    os.makedirs(RAW, exist_ok=True)
    pr_file = f"{OUT}/tp_monthly_{e5l.Y0}_{e5l.Y1}.nc"
    if not os.path.exists(pr_file):                  # the same precipitation request as 04_era5land.py
        e5l.retrieve(cdsapi.Client(quiet=True), "reanalysis-era5-land-monthly-means",
                     {"product_type": ["monthly_averaged_reanalysis"], "variable": ["total_precipitation"],
                      "year": [str(y) for y in range(e5l.Y0, e5l.Y1 + 1)], "month": [f"{m:02d}" for m in range(1, 13)],
                      "time": ["00:00"], "area": e5l.AREA, "data_format": "netcdf", "download_format": "unarchived"},
                     pr_file)
    tp = e5l.open_nc(pr_file)
    tvar = "valid_time" if "valid_time" in tp.dims else "time"
    todo = [y for y in range(e5l.Y0, e5l.Y1 + 1) if not os.path.exists(f"{OUT}/{y}.npz")]
    got, op_box = {}, [None]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(fetch, y, s) for y in todo for s in ("daily_maximum", "daily_minimum")]
        for fu in as_completed(futs):
            year, stat, f = fu.result()
            got.setdefault(year, {})[stat] = f
            print("got", year, stat, f"{(time.time() - t0) / 3600:.1f} h", flush=True)
            if len(got[year]) == 2 and not os.path.exists(f"{OUT}/{year}.npz"):
                process(year, got[year], tp, tvar, op_box)
                print("OK ERA5-Land", year, flush=True)


if __name__ == "__main__":
    main()
