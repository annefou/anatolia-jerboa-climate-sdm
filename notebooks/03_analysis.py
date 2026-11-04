# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 03 — Claim tested
#
# Williams' jerboa loses 40–48 % of its suitable habitat by 2021–2040 and 64–98 % by 2081–2100 (MIROC6, four SSPs;
# Random Forest, eight bioclimatic variables, threshold 0.3).
#
# Model as in the paper (Random Forest, 1,000 background cells, 10 replicates 70/30, TSS-weighted ensemble), plus a
# **null control** (`pipeline/06_null_control.py`): the "loss" the model shows with no climate change at all, from 5
# refits. A projected loss means something only when it clears the null.

# %%
import json
from pathlib import Path

import pandas as pd

R = Path("../results")
rows = []
for f, label in [("sdm_worldclim", "19 GBIF cells"), ("sdm_worldclim_occurrences_merged", "73 cells (GBIF + iNat + Fig 1A)"),
                 ("sdm_worldclim_occurrences_genbank", "43 cells (GBIF + GenBank)"),
                 ("sdm_era5_occurrences_merged", "73 cells, ERA5 baseline")]:
    d = json.loads((R / f"{f}.json").read_text())
    m = d["paper_design"]["metrics_mean"]
    rows.append({"occurrences": label, "presence cells": d["n_presence_cells"], "AUC": m["auc"], "TSS": m["tss"],
                 "max-TSS threshold": d["paper_design"]["threshold_maxtss"]})
pd.DataFrame(rows)

# %% [markdown]
# ## Null control against projected loss, near term (2021–2040, SSP3-7.0)

# %%
pd.DataFrame(json.loads((R / "doc_figure_loss_vs_null.json").read_text()))

# %% [markdown]
# ## Loss by model and scenario, 73 cells, paper design

# %%
loss = pd.read_csv(R / "loss_worldclim_occurrences_merged.csv")
loss[loss.design == "paper_design"].pivot(index="climate", columns="threshold", values="loss_pct")

# %% [markdown]
# ## WorldClim against ERA5 + Climate DT changes

# %%
pd.DataFrame(json.loads((R / "doc_figure_climatedt.json").read_text()))

# %% [markdown]
# With public GBIF data alone the projected loss cannot be told from model noise; with the authors' own localities a
# climate signal clears it. The magnitude depends strongly on the threshold; the direction and the dependence on
# emissions are the robust findings.
