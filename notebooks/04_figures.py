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
# # 04 — Figures
#
# Written by `pipeline/99_doc_figures.py` and `pipeline/digitise/` and committed in `figures/`.
#
# ## Projected loss against the null control
# ![Loss vs null](../figures/doc_loss_vs_null.png)
#
# ## WorldClim + CMIP6 against ERA5 + Climate DT
# ![WorldClim vs Climate DT](../figures/doc_worldclim_vs_climatedt.png)
#
# ## Localities digitised from Figure 1A, overlay check
# ![Digitised overlay](../figures/helvaci2025_fig1A_digitised_overlay.png)

# %% [markdown]
# ## Limits
# - The paper's own coordinates are not public; map readings carry about 15 km uncertainty. Cells of 6.4 km against
#   the paper's 1 km grid.
# - Climate only: land use (steppe turned to cropland) is not in the model.
# - The Climate DT monthly stream has no maximum or minimum temperature (see 02).
