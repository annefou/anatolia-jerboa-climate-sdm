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
# # 01 — Data
#
# **DRAFT, not reviewed.** LifeWatch ERIC feasibility test, our reading of the published work (Helvacı and Çolak 2025,
# *Biology* 14:1184, [doi:10.3390/biology14091184](https://doi.org/10.3390/biology14091184)), open to correction by
# the authors.
#
# The pipeline is in `pipeline/` and `Snakefile` (see *How to reproduce* in the README). It is **not** rerun when this
# book is built: it downloads WorldClim and CMIP6 layers and reads ERA5 and Climate DT (DestinE upgraded access).
# These pages read the summary results committed in `results/`, the digitised localities in `inputs/` and the
# figures in `figures/`.
#
# | Input | Source | Licence | Pipeline step |
# |---|---|---|---|
# | GBIF occurrences, *Scarturus williamsi* (Catalogue of Life XR keys BSW8 and VNB82) | GBIF via healpix-connector v0.2.0 ([doi:10.5281/zenodo.23603498](https://doi.org/10.5281/zenodo.23603498)) | per record (mostly CC BY, CC BY-NC) | `pipeline/00_occurrences.py` |
# | 53 localities read from Figure 1A of the paper (~15 km uncertainty) | Helvacı and Çolak 2025 | CC BY 4.0 | `pipeline/digitise/`, `inputs/literature/` |
# | 23 GenBank localities (check without map digitising) | Olgun Karacan et al. 2024, [doi:10.1155/jzs/8123686](https://doi.org/10.1155/jzs/8123686), geocoded with Nominatim | – | `pipeline/digitise/genbank_localities.py`, `inputs/literature_genbank/` |
# | WorldClim 2.1 (2.5′) and CMIP6 change factors | WorldClim | CC BY 4.0 | `pipeline/01_worldclim_healpix.py` |
# | ERA5 1991–2020 | Planetary Computer Zarr | Copernicus, CC BY | `pipeline/04b_era5.py` |
# | Climate DT generation 2, IFS-FESOM and IFS-NEMO | DestinE upgraded access | DestinE terms: derived statistics only | `pipeline/03_climatedt.py` |
#
# Grid: HEALPix depth 10 (40.5 km² cells; healpix-geo, WGS84 ellipsoid, NESTED).

# %%
import json
from pathlib import Path

import pandas as pd

R = Path("../results")
g = json.loads((R / "occurrences_summary.json").read_text())
print("GBIF via", g["connector"], "|", g["taxonomy"], "| taxon keys:", g["taxon_keys"])
print(pd.Series(g["filter_steps"], name="GBIF records kept at each step").to_string())
for name in ["occurrences_merged_summary", "occurrences_genbank_summary"]:
    s = json.loads((R / f"{name}.json").read_text())
    print(name, "| cells:", s.get("cells_total"), "| by source:", s.get("cells_by_source"))

# %%
lit = pd.read_csv("../inputs/literature/helvaci2025_fig1A_digitised.csv")
print(len(lit), "localities digitised from Figure 1A")
lit.head()
