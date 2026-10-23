"""Null control for the habitat-loss metric: how much "loss" appears with no climate change at all?

The ensemble of pipeline/02_sdm.py (paper design: Random Forest, 1000 background points, 10 replicates
70/30, TSS-weighted, threshold 0.3) is fitted again with different random seeds (new background draw, new
splits, new trees) on the same occurrences and the same baseline climate. "Loss" between two such fits is pure
method noise. Compared with the losses projected for MIROC6 (results/loss_<config>.csv).

Usage: python pipeline/06_null_control.py <ROOT> [<CONFIG> [<OCC>]]
Writes results/null_control_<config>.json.
"""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sdm", os.path.join(HERE, "02_sdm.py"))
ROOT = sys.argv[1]
CONFIG = sys.argv[2] if len(sys.argv) > 2 else "worldclim"
OCC = sys.argv[3] if len(sys.argv) > 3 else "occurrences"
sys.argv = [sys.argv[0], ROOT, CONFIG, OCC]
sdm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdm)
NSEED = 5


def main():
    cells = pd.read_parquet(f"{ROOT}/clim/cells.parquet")
    base = pd.read_parquet(f"{ROOT}/clim/{CONFIG}_{sdm.BASELINE}.parquet")
    valid = base[sdm.VARS].notna().all(1).values
    occ = pd.read_parquet(f"{ROOT}/occ/{OCC}.parquet")
    pos = pd.Series(np.arange(len(cells)), index=cells.cell.values)
    pc = pos.reindex(occ.cell.values).dropna().astype(int).values
    pc = np.unique(pc[valid[pc]])
    maps = []
    for s in range(NSEED):
        rng = np.random.default_rng(1000 + s)
        bg = rng.choice(np.setdiff1d(np.flatnonzero(valid), pc), sdm.NBG, replace=False)
        idx = np.r_[pc, bg]
        X, y = base[sdm.VARS].values[idx], np.r_[np.ones(len(pc)), np.zeros(len(bg))].astype(int)
        models, w, met = sdm.fit_ensemble(X, y, rng)
        p = np.full(len(cells), np.nan); p[valid] = sdm.predict(models, w, base[sdm.VARS].values[valid])
        thr_tss = float(np.average(met.thr_maxtss, weights=w))
        maps.append({"thr0.3": p >= sdm.THR, "thr_maxtss": p >= thr_tss})
    out = {"config": CONFIG, "occurrences": OCC, "n_seeds": NSEED}
    for thr in ("thr0.3", "thr_maxtss"):
        rows = []
        for i in range(NSEED):
            for j in range(NSEED):
                if i != j:
                    a, b = maps[i][thr], maps[j][thr]
                    rows.append({"loss_pct": 100 * (a & ~b).sum() / max(a.sum(), 1)})
        r = pd.DataFrame(rows)
        out[thr] = {"suitable_cells_per_fit": [int(m[thr].sum()) for m in maps],
                    "null_loss_pct_mean": round(float(r.loss_pct.mean()), 1),
                    "null_loss_pct_range": [round(float(r.loss_pct.min()), 1), round(float(r.loss_pct.max()), 1)]}
    json.dump(out, open(f"results/null_control_{sdm.TAG}.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
