# Charts of the LifeWatch ERIC country file for Türkiye

Each chart in the country file is a small JSX module (Claude Docs widget) that draws an SVG from inline rows.
The rows are copies of the committed results files below, written by the scripts listed; the same rows also give the PNG.

| Chart code | Section | Rows | Written by | PNG |
| --- | --- | --- | --- | --- |
| [jerboa-loss-vs-null.jsx](jerboa-loss-vs-null.jsx) | 3.1 | `results/doc_figure_loss_vs_null.json` | `pipeline/99_doc_figures.py` | `figures/doc_loss_vs_null.png` |
| [jerboa-worldclim-vs-climatedt.jsx](jerboa-worldclim-vs-climatedt.jsx) | 3.1 | `results/doc_figure_climatedt.json` | `pipeline/99_doc_figures.py` | `figures/doc_worldclim_vs_climatedt.png` |
| [engagement-diagram.jsx](engagement-diagram.jsx) | 4 | `(no data: a drawn diagram)` | `-` | `-` |
| (image) | 3.1 | `inputs/literature/helvaci2025_fig1A_digitised.csv` | `pipeline/digitise/fig1_points.py` | `figures/helvaci2025_fig1A_digitised_overlay.png` |
