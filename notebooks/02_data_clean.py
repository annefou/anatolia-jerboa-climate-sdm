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
# # 02 — Climate layers on the HEALPix grid
#
# WorldClim and ERA5 are resampled onto WGS84 HEALPix cells with healpix-resample (bilinear, conservative mode) or,
# for ERA5 (0.25°, wider than a cell), healpix-connector `sources.gridded.sample_cells_from_grid`.
# `pipeline/90_compare_resamplers.py` compares them with an exact area overlap.
#
# The Climate DT monthly stream has no maximum or minimum temperature; the future diurnal range is kept from the
# reanalysis baseline. `pipeline/05_bioclim.py` measures how much it changes in CMIP6.

# %%
import json
from pathlib import Path

R = Path("../results")
print(json.dumps(json.loads((R / "resampler_comparison.json").read_text()), indent=1)[:3000])

# %%
print(json.dumps(json.loads((R / "bioclim_checks_era5.json").read_text()), indent=1)[:3000])
