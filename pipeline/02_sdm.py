"""Species distribution model and habitat-loss projections, following section 2.3 of Helvaci & Colak 2025.

As in the paper: Random Forest, eight bioclimatic predictors (bio2, 3, 4, 8, 9, 14, 15, 19), 1000 random
background points over the study extent, 10 replicates with a random 70/30 split, ensemble weighted by TSS,
AUC / TSS / COR on the held-out 30 %, fixed suitability threshold 0.3, habitat loss = share of currently
suitable habitat that is not suitable in the future.
Different from the paper (all stated in results): occurrences are GBIF only (19 cells, the literature records
are not public); the unit is a HEALPix cell (depth 10, 40.5 km2, equal area), so background points are
uniform in area and areas are cell counts x 40.5 km2; 2.5' WorldClim instead of 30''.
Sensitivity (not in the paper): threshold = mean max-TSS threshold of the replicates; 10 000 background cells.

Usage: python pipeline/02_sdm.py <ROOT> [<CONFIG> [<OCC>]]   CONFIG = worldclim (default) | era5land,
       OCC = occurrences (GBIF, default) | occurrences_merged (GBIF + iNaturalist + digitised literature)
Reads <ROOT>/occ/occurrences.parquet and <ROOT>/clim/<config>_*.parquet. Writes results/sdm_<config>.json,
results/loss_<config>.csv and <ROOT>/sdm/<config>_suitability.parquet (per-cell suitability, not committed).
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ROOT = sys.argv[1]
CONFIG = sys.argv[2] if len(sys.argv) > 2 else "worldclim"
OCC = sys.argv[3] if len(sys.argv) > 3 else "occurrences"          # or occurrences_merged (00b)
TAG = CONFIG if OCC == "occurrences" else f"{CONFIG}_{OCC}"
BASELINE = {"worldclim": "baseline_1970-2000", "era5land": "baseline_1991-2020"}[CONFIG]
VARS = ["bio2", "bio3", "bio4", "bio8", "bio9", "bio14", "bio15", "bio19"]
NREP, NBG, THR, SEED = 10, 1000, 0.3, 20251001


def fit_ensemble(X, y, rng):
    """10 replicates, 70/30 split of presences and background. Returns models, weights (TSS) and metrics."""
    models, rows = [], []
    pres, bg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    for r in range(NREP):
        tp = rng.permutation(pres); tb = rng.permutation(bg)
        n_p, n_b = int(round(0.7 * len(tp))), int(round(0.7 * len(tb)))
        tr = np.r_[tp[:n_p], tb[:n_b]]; te = np.r_[tp[n_p:], tb[n_b:]]
        m = RandomForestClassifier(n_estimators=500, random_state=int(rng.integers(1 << 31)), n_jobs=-1)
        m.fit(X[tr], y[tr])
        p = m.predict_proba(X[te])[:, 1]
        fpr, tpr, thr = roc_curve(y[te], p)
        j = np.argmax(tpr - fpr)
        rows.append({"replicate": r, "auc": roc_auc_score(y[te], p), "tss": tpr[j] - fpr[j],
                     "thr_maxtss": float(min(thr[j], 1.0)), "cor": float(np.corrcoef(y[te], p)[0, 1]),
                     "n_test_presence": int(len(tp) - n_p)})
        models.append(m)
    met = pd.DataFrame(rows)
    w = met.tss.clip(lower=0).values
    return models, w / w.sum(), met


def predict(models, w, X):
    return np.sum([wi * m.predict_proba(X)[:, 1] for m, wi in zip(models, w)], axis=0)


def main() -> None:
    os.makedirs(f"{ROOT}/sdm", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    cells = pd.read_parquet(f"{ROOT}/clim/cells.parquet")
    base = pd.read_parquet(f"{ROOT}/clim/{CONFIG}_{BASELINE}.parquet")
    valid = base[VARS].notna().all(1).values
    occ = pd.read_parquet(f"{ROOT}/occ/{OCC}.parquet")
    pos = pd.Series(np.arange(len(cells)), index=cells.cell.values)
    pc = pos.reindex(occ.cell.values).dropna().astype(int).values
    pc = np.unique(pc[valid[pc]])
    futures = sorted(f for f in glob.glob(f"{ROOT}/clim/{CONFIG}_*.parquet") if BASELINE not in f)
    out, loss_rows = {"config": CONFIG, "occurrences": OCC, "n_presence_cells": int(len(pc)), "cell_area_km2": common.cell_area_km2(),
                      "variables": VARS}, []
    suit = {"cell": cells.cell.values}
    for label, nbg in (("paper_design", NBG), ("sensitivity_bg10000", 10000)):
        rng = np.random.default_rng(SEED)
        cand = np.setdiff1d(np.flatnonzero(valid), pc)
        bg = rng.choice(cand, nbg, replace=False)
        idx = np.r_[pc, bg]
        X, y = base[VARS].values[idx], np.r_[np.ones(len(pc)), np.zeros(len(bg))].astype(int)
        models, w, met = fit_ensemble(X, y, rng)
        cur = np.full(len(cells), np.nan); cur[valid] = predict(models, w, base[VARS].values[valid])
        thr_tss = float(np.average(met.thr_maxtss, weights=w))
        out[label] = {"n_background": nbg, "metrics_mean": met[["auc", "tss", "cor"]].mean().round(3).to_dict(),
                      "metrics_sd": met[["auc", "tss", "cor"]].std().round(3).to_dict(),
                      "threshold_maxtss": round(thr_tss, 3)}
        if label == "paper_design":
            suit["baseline"] = cur
        for thr_name, thr in (("thr0.3", THR), ("thr_maxtss", thr_tss)):
            now = cur >= thr
            out[label][f"suitable_km2_baseline_{thr_name}"] = round(float(now.sum() * common.cell_area_km2()))
            for f in futures:
                name = os.path.basename(f)[len(CONFIG) + 1:-8]
                fut_df = pd.read_parquet(f)
                ok = valid & fut_df[VARS].notna().all(1).values
                fut = np.full(len(cells), np.nan); fut[ok] = predict(models, w, fut_df[VARS].values[ok])
                if label == "paper_design" and thr_name == "thr0.3":
                    suit[name] = fut
                later = fut >= thr
                lost = (now & ~later).sum(); gained = (~now & later & ok).sum()
                loss_rows.append({"design": label, "threshold": thr_name, "climate": name,
                                  "suitable_now_cells": int(now.sum()), "lost_cells": int(lost), "gained_cells": int(gained),
                                  "loss_pct": round(100 * lost / max(now.sum(), 1), 1),
                                  "net_change_pct": round(100 * (gained - lost) / max(now.sum(), 1), 1)})
    pd.DataFrame(suit).to_parquet(f"{ROOT}/sdm/{TAG}_suitability.parquet", index=False)
    loss = pd.DataFrame(loss_rows)
    loss.to_csv(f"results/loss_{TAG}.csv", index=False)
    json.dump(out, open(f"results/sdm_{TAG}.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
    print(loss[(loss.design == "paper_design")].to_string(index=False))


if __name__ == "__main__":
    main()
