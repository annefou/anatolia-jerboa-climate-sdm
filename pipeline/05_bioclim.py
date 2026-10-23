"""Bioclimatic variables for the reanalysis / Climate DT configuration, on the study cells.

Baseline: ERA5-Land (04_era5land.py) or ERA5 (04b_era5.py) 1991-2020, monthly climatology of tmax, tmin (mean of daily max / min) and precipitation.
Future: change-factor method, the same as WorldClim's CMIP6 layers, with the Climate DT as the source of change:
  delta_T(m)  = Climate DT avg_2t, 2021-2040 minus 1991-2020 (hist 1991-2014 + SSP3-7.0 2015-2020), per month
  tmax' = tmax + delta_T, tmin' = tmin + delta_T   (the monthly stream has no max/min: diurnal range unchanged)
  pr'   = pr * (DT pr future / DT pr baseline), or pr + difference where the DT baseline is < 1 mm per month;
          the ratio is capped at 5.
Definitions follow WorldClim / dismo::biovars: tavg = (tmax + tmin) / 2; bio2 = mean(tmax - tmin);
bio3 = 100 bio2 / bio7; bio4 = 100 sd(tavg); bio7 = max(tmax) - min(tmin); bio8 / bio9 = mean tavg of the
wettest / driest quarter; bio14 = min pr; bio15 = 100 sd(pr) / (1 + mean(pr)); bio19 = pr of the coldest quarter.
Checks written to results/bioclim_checks.json:
  * how much bio2 changes by 2021-2040 (SSP3-7.0) in the 11 WorldClim CMIP6 models with SSP3-7.0 (tests the
    unchanged-diurnal-range assumption);
  * Climate DT 1991-2020 bias against the baseline reanalysis (mean temperature, precipitation), per model.

Usage: python pipeline/05_bioclim.py <ROOT> <BASELINE> <MODEL> [<MODEL> ...]   BASELINE = era5land | era5
Writes <ROOT>/clim/<BASELINE>_baseline_1991-2020.parquet, <ROOT>/clim/<BASELINE>_ClimateDT-<MODEL>_ssp370_2021-2040.parquet
and results/bioclim_checks_<BASELINE>.json.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT, BASE, MODELS = sys.argv[1], sys.argv[2], sys.argv[3:]
FOLDER = {"era5land": "era5l", "era5": "era5"}[BASE]
VARS = ["bio2", "bio3", "bio4", "bio8", "bio9", "bio14", "bio15", "bio19"]


def bioclim(tmax, tmin, pr) -> pd.DataFrame:
    """tmax, tmin, pr: (12, n). Returns the eight variables used in the paper."""
    tavg = (tmax + tmin) / 2
    idx = np.array([[(m + k) % 12 for k in range(3)] for m in range(12)])          # 12 circular quarters
    q_pr = pr[idx].sum(1)                                                           # (12, n)
    q_t = tavg[idx].mean(1)
    pick = lambda q, i: np.take_along_axis(q, i[None, :], 0)[0]
    bio7 = tmax.max(0) - tmin.min(0)
    bio2 = (tmax - tmin).mean(0)
    return pd.DataFrame({
        "bio2": bio2, "bio3": 100 * bio2 / bio7, "bio4": 100 * tavg.std(0, ddof=1),
        "bio8": pick(q_t, q_pr.argmax(0)), "bio9": pick(q_t, q_pr.argmin(0)),
        "bio14": pr.min(0), "bio15": 100 * pr.std(0, ddof=1) / (1 + pr.mean(0)),
        "bio19": pick(q_pr, q_t.argmin(0))})


def clim(folder, keys, y0, y1):
    files = [f"{folder}/{y}.npz" for y in range(y0, y1 + 1)]
    missing = [f for f in files if not os.path.exists(f)]
    assert not missing, f"missing {len(missing)} years in {folder}, e.g. {missing[:3]}"
    acc = {k: 0.0 for k in keys}
    for f in files:
        d = np.load(f)
        for k in keys:
            acc[k] = acc[k] + d[k].astype(np.float64)
    return {k: v / len(files) for k, v in acc.items()}


def main() -> None:
    cells = pd.read_parquet(f"{ROOT}/clim/cells.parquet")
    land = cells.land_frac.values >= 0.5
    e5 = clim(f"{ROOT}/{FOLDER}", ["tmax", "tmin", "pr"], 1991, 2020)
    base = bioclim(e5["tmax"], e5["tmin"], e5["pr"])
    base[~land] = np.nan
    base.insert(0, "cell", cells.cell.values)
    base.to_parquet(f"{ROOT}/clim/{BASE}_baseline_1991-2020.parquet", index=False)
    checks = {"baseline": BASE, "dt_bias_vs_baseline_1991_2020": {}, "dt_change_2021_2040": {}}
    e5_t = (e5["tmax"] + e5["tmin"]) / 2
    for model in MODELS:
        b = clim(f"{ROOT}/dt/{model}", ["t2m", "pr"], 1991, 2020)
        f = clim(f"{ROOT}/dt/{model}", ["t2m", "pr"], 2021, 2040)
        dT = f["t2m"] - b["t2m"]
        ratio = np.where(b["pr"] >= 1, np.minimum(f["pr"] / np.maximum(b["pr"], 1e-9), 5), np.nan)
        pr_f = np.where(np.isfinite(ratio), e5["pr"] * ratio, np.maximum(e5["pr"] + f["pr"] - b["pr"], 0))
        fut = bioclim(e5["tmax"] + dT, e5["tmin"] + dT, pr_f)
        fut[~land] = np.nan
        fut.insert(0, "cell", cells.cell.values)
        fut.to_parquet(f"{ROOT}/clim/{BASE}_ClimateDT-{model}_ssp370_2021-2040.parquet", index=False)
        m = land[None, :] & np.isfinite(e5_t)
        checks["dt_bias_vs_baseline_1991_2020"][model] = {
            "t_mean_bias_degC": round(float(np.nanmean((b["t2m"] - e5_t)[m])), 2),
            "t_mae_degC": round(float(np.nanmean(np.abs(b["t2m"] - e5_t)[m])), 2),
            "pr_annual_ratio": round(float(np.nansum(b["pr"][m]) / np.nansum(e5["pr"][m])), 3)}
        checks["dt_change_2021_2040"][model] = {
            "dT_annual_mean_degC": round(float(np.nanmean(dT[:, land])), 2),
            "dT_summer_JJA_degC": round(float(np.nanmean(dT[5:8][:, land])), 2),
            "pr_annual_change_pct": round(float(100 * (np.nansum(f["pr"][:, land]) / np.nansum(b["pr"][:, land]) - 1)), 1)}
    # diurnal range: does bio2 change in CMIP6 (WorldClim change-factor layers)?
    wb = pd.read_parquet(f"{ROOT}/clim/worldclim_baseline_1970-2000.parquet")
    d2 = {}
    for fpath in sorted(glob.glob(f"{ROOT}/clim/worldclim_*_ssp370_2021-2040.parquet")):
        g = os.path.basename(fpath).split("_")[1]
        diff = (pd.read_parquet(fpath).bio2 - wb.bio2)[land].dropna()
        d2[g] = {"mean": round(float(diff.mean()), 3), "p05": round(float(diff.quantile(0.05)), 3),
                 "p95": round(float(diff.quantile(0.95)), 3)}
    checks["cmip6_bio2_change_2021_2040_ssp370_degC"] = d2
    checks["baseline_bio2_mean_degC"] = round(float(base.bio2[land].mean()), 2)
    os.makedirs("results", exist_ok=True)
    json.dump(checks, open(f"results/bioclim_checks_{BASE}.json", "w"), indent=1)
    print(json.dumps(checks, indent=1))


if __name__ == "__main__":
    main()
