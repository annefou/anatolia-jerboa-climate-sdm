"""Rows of the figures shown in the LifeWatch ERIC country file for Turkiye, from the committed results.

Figure "projected loss against the null control" (2021-2040, SSP3-7.0, 11 CMIP6 models; null = 5 refits
with no climate change), for both occurrence sets and both thresholds.
Reads results/loss_worldclim*.csv and results/null_control_worldclim*.json; writes results/doc_figure_loss_vs_null.json.
Also writes figures/doc_loss_vs_null.png and figures/doc_worldclim_vs_climatedt.png (the second figure is described below).
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

# Figure "WorldClim against the Climate Digital Twin" (73 cells, 2021-2040, SSP3-7.0): each configuration with its
# own null control. Reads results/loss_era5_occurrences_merged.csv, null_control_era5_occurrences_merged.json and
# bioclim_checks_era5.json; writes results/doc_figure_climatedt.json.
CONF = {"worldclim": "WorldClim + 11 CMIP6", "era5": "ERA5 + Climate DT IFS-FESOM"}
rows2 = []
for conf, clab in CONF.items():
    tag = f"{conf}_occurrences_merged"
    loss = pd.read_csv(f"results/loss_{tag}.csv")
    null = json.load(open(f"results/null_control_{tag}.json"))
    for thr, tlab in THR.items():
        n = null[thr]
        rows2.append({"thr": tlab, "conf": clab, "kind": "null", "series": "No climate change (null control, 5 refits)", "mid": n["null_loss_pct_mean"],
                      "lo": n["null_loss_pct_range"][0], "hi": n["null_loss_pct_range"][1]})
        g = loss[(loss.design == "paper_design") & (loss.threshold == thr) & loss.climate.str.contains("ssp370_2021-2040")]
        rows2.append({"thr": tlab, "conf": clab, "kind": "proj", "series": "2021-2040, SSP3-7.0 projection", "n_models": int(len(g)),
                      "mid": round(float(g.loss_pct.median()), 1), "lo": float(g.loss_pct.min()), "hi": float(g.loss_pct.max())})
json.dump(rows2, open("results/doc_figure_climatedt.json", "w"), indent=1)
print(json.dumps(rows2, indent=1))

# The same two figures as PNG, drawn from the rows above (the country file draws them live from the same rows).
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE, GREY = "#2f6fd6", "#b8b8b0"


def dot_range(rows, group_key, title, subtitle, out):
    panels = list(dict.fromkeys(r["thr"] for r in rows))
    groups = list(dict.fromkeys(r[group_key] for r in rows))
    fig, axs = plt.subplots(1, len(panels), figsize=(11, 4.6), sharey=True)
    for ax, p in zip(axs, panels):
        for gi, g in enumerate(groups):
            for r in (r for r in rows if r["thr"] == p and r[group_key] == g):
                x = gi + (-0.15 if r["kind"] == "null" else 0.15)
                c = GREY if r["kind"] == "null" else BLUE
                ax.vlines(x, r["lo"], r["hi"], color=c, lw=3)
                ax.plot(x, r["mid"], "o", color=c, ms=9)
                n = r.get("n_models", 1)
                ax.annotate(f"{int(r['mid'] + 0.5)}%" + (f" ({n} models)" if r["kind"] == "proj" and n > 1 else ""),
                            (x, r["mid"]), xytext=(8, -4), textcoords="offset points", fontsize=9)
        ax.set_xticks(range(len(groups)), groups, fontsize=9)
        ax.set_xlim(-0.6, len(groups) - 0.4)
        ax.set_ylim(0, 100)
        ax.set_title(p, fontsize=10, fontweight="bold")
        ax.grid(axis="y", color="0.9")
        ax.spines[["top", "right"]].set_visible(False)
    axs[0].set_ylabel("Share of today's suitable habitat lost (%)")
    axs[0].plot([], [], "o", color=GREY, label="No climate change (null control, 5 refits)")
    axs[0].plot([], [], "o", color=BLUE, label="2021-2040, SSP3-7.0 projection")
    fig.legend(loc="upper left", bbox_to_anchor=(0.01, 0.9), ncol=2, frameon=False, fontsize=9)
    fig.suptitle(title, x=0.01, ha="left", fontweight="bold")
    fig.text(0.01, 0.905, subtitle, fontsize=9, color="0.35")
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    fig.savefig(out, dpi=160)
    plt.close(fig)


dot_range(rows, "occ", "With the authors' localities, projected loss clears the noise",
          "Williams' jerboa, WorldClim 2.1 + 11 CMIP6 models; dot = median (null: mean), line = range",
          "figures/doc_loss_vs_null.png")
dot_range(rows2, "conf", "The Climate Digital Twin gives the same answer as WorldClim",
          "Williams' jerboa, 73 cells; each climate source against its own null control",
          "figures/doc_worldclim_vs_climatedt.png")
