"""Rows of the figures shown in the LifeWatch ERIC country file for Turkiye, from the committed results.

Figure "projected loss against the null control" (2021-2040, SSP3-7.0, 12 CMIP6 models; null = 5 refits
with no climate change), for both occurrence sets and both thresholds.
Reads results/loss_worldclim*.csv and results/null_control_worldclim*.json; writes results/doc_figure_loss_vs_null.json.
"""
import json

import pandas as pd

OCC = {"occurrences": "19 GBIF cells", "occurrences_merged": "73 cells"}
THR = {"thr0.3": "Fixed threshold 0.3", "thr_maxtss": "Data-tuned threshold (max TSS)"}
rows = []
for occ, olab in OCC.items():
    tag = "worldclim" if occ == "occurrences" else f"worldclim_{occ}"
    loss = pd.read_csv(f"results/loss_{tag}.csv")
    null = json.load(open(f"results/null_control_{tag}.json"))
    for thr, tlab in THR.items():
        n = null[thr]
        rows.append({"thr": tlab, "occ": olab, "kind": "null", "series": "No climate change (null control, 5 refits)",
                     "mid": n["null_loss_pct_mean"], "lo": n["null_loss_pct_range"][0], "hi": n["null_loss_pct_range"][1]})
        g = loss[(loss.design == "paper_design") & (loss.threshold == thr) & loss.climate.str.contains("ssp370_2021-2040")]
        rows.append({"thr": tlab, "occ": olab, "kind": "proj", "series": f"2021-2040, SSP3-7.0 ({len(g)} CMIP6 models)",
                     "mid": round(float(g.loss_pct.median()), 1), "lo": float(g.loss_pct.min()), "hi": float(g.loss_pct.max())})
json.dump(rows, open("results/doc_figure_loss_vs_null.json", "w"), indent=1)
print(json.dumps(rows, indent=1))
