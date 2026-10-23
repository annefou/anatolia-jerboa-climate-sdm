"""ERA5 monthly climate 1991-2020 on the study cells (healpix-geo WGS84, depth 10): a second observation-based
baseline for the Climate DT configuration, used while the ERA5-Land daily statistics wait in the CDS queue.

Source: ERA5 hourly single levels, Zarr copy on Microsoft Planetary Computer (collection era5-pds, one store per
variable and month; anonymous SAS token from the Planetary Computer token service; ERA5 licence: Copernicus, CC-BY):
  * air_temperature_at_2_metres_1hour_Maximum / _Minimum -> daily (UTC) max / min -> monthly means
    (WorldClim's tmax / tmin);
  * precipitation_amount_1hour_Accumulation (m) -> monthly total in mm.
Only the chunks covering the study extent are read (about 20 MB per variable and month).
Grid: 0.25 deg regular lon/lat, taken as WGS84 geodetic coordinates (no sphere-to-ellipsoid step, unlike the
Climate DT HEALPix grid). The ERA5 box (~25 km) is wider than the 6.4 km cell, so each WGS84 cell takes the value
of the box containing its centre (healpix-connector sources.gridded.sample_cells_from_grid); the value describes
the box, not the cell. Not used: healpix-resample's BilinearResampler (it spreads each source point over its
nearest cells, so with a source coarser than the target only 23 % of the cells get a value, tested 2026-10-23)
and healpix-convert's ERA5 converter (PSF, depth 7). An exact area overlap (common.grid_weights) gives the same
values except on box edges (sensitivity kept in work/era5_overlap). Sea cells are masked later (05_bioclim.py).

Usage: python pipeline/04b_era5.py <ROOT> [<Y0> <Y1>]
Writes <ROOT>/era5/<year>.npz with tmax, tmin (degC) and pr (mm per month), arrays (12, ncells), float32.
Nothing raw is kept on disk.
"""
import os
import sys
import time

import numpy as np
import pandas as pd
import requests
import xarray as xr
from healpix_connector.sources.gridded import sample_cells_from_grid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ROOT = sys.argv[1]
Y0, Y1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1991, 2020)
OUT = f"{ROOT}/era5"
ACCOUNT, CONTAINER = "cpdataeuwest", "era5"
TOKEN_URL = f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{ACCOUNT}/{CONTAINER}"
VARS = {"tmax": "air_temperature_at_2_metres_1hour_Maximum", "tmin": "air_temperature_at_2_metres_1hour_Minimum",
        "pr": "precipitation_amount_1hour_Accumulation"}
x0, y0, x1, y1 = common.EXTENT
PAD = 0.5                        # degrees around the extent


def sas_token() -> str:
    r = requests.get(TOKEN_URL, timeout=60)
    r.raise_for_status()
    return r.json()["token"]


def open_month(var: str, year: int, month: int, token: str) -> xr.DataArray:
    ds = xr.open_zarr(f"abfs://{CONTAINER}/ERA5/{year}/{month:02d}/{var}.zarr", consolidated=True,
                      storage_options={"account_name": ACCOUNT, "credential": token})
    da = ds[var]
    return da.sel(lat=slice(y1 + PAD, y0 - PAD), lon=slice(x0 - PAD, x1 + PAD))


def monthly(year: int, month: int, token: str) -> dict:
    out = {}
    for key, var in VARS.items():
        for attempt in range(5):
            try:
                da = open_month(var, year, month, token).load()
                break
            except Exception as e:
                print("retry", var, year, month, attempt, type(e).__name__, str(e)[:200], flush=True)
                time.sleep(30 * (attempt + 1))
                token = sas_token()
        else:
            raise RuntimeError(f"failed: {var} {year}-{month:02d}")
        t = da.dims[0]
        if key == "pr":
            out[key] = da.sum(t).values * 1000.0                                   # m -> mm per month
        else:
            day = da[t].dt.floor("D")
            agg = da.groupby(day).max() if key == "tmax" else da.groupby(day).min()
            out[key] = agg.mean(agg.dims[0]).values - 273.15
        out["_grid"] = (da.lon.values, da.lat.values)
    return out


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    cells = pd.read_parquet(f"{ROOT}/clim/cells.parquet")
    ids = cells.cell.values.astype(np.uint64)
    op, grid = None, None
    for year in range(Y0, Y1 + 1):
        fn = f"{OUT}/{year}.npz"
        if os.path.exists(fn):
            continue
        t0, token = time.time(), sas_token()
        acc = {k: [] for k in VARS}
        for month in range(1, 13):
            m = monthly(year, month, token)
            if op is None:
                lon, lat = m["_grid"]
                res = float(lon[1] - lon[0])
                assert np.allclose(np.diff(lon), res) and np.allclose(np.diff(lat), -res)
                op = lambda a, lon=lon, lat=lat, res=res: sample_cells_from_grid(a, lon, lat, ids, common.DEPTH, res).value
                grid = (lon, lat)
            assert np.allclose(m["_grid"][0], grid[0]) and np.allclose(m["_grid"][1], grid[1])
            for k in VARS:
                acc[k].append(op(m[k]))
        np.savez_compressed(fn, **{k: np.stack(v).astype(np.float32) for k, v in acc.items()})
        print("OK ERA5", year, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
