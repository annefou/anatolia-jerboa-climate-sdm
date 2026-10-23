# anatolia-jerboa-climate-sdm

[![CI](https://github.com/annefou/anatolia-jerboa-climate-sdm/actions/workflows/ci.yml/badge.svg)](https://github.com/annefou/anatolia-jerboa-climate-sdm/actions/workflows/ci.yml)
[![Jupyter Book](https://github.com/annefou/anatolia-jerboa-climate-sdm/actions/workflows/jupyter-book.yml/badge.svg)](https://annefou.github.io/anatolia-jerboa-climate-sdm/)
[![Docker](https://github.com/annefou/anatolia-jerboa-climate-sdm/actions/workflows/docker.yml/badge.svg)](https://github.com/annefou/anatolia-jerboa-climate-sdm/pkgs/container/anatolia-jerboa-climate-sdm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/{{ZENODO_DOI}}.svg)]({{ZENODO_DOI}})
[![FAIR4RS](https://img.shields.io/badge/FAIR4RS-conformant-brightgreen)](docs/fair4rs-checklist.md)
[![FORRT](https://img.shields.io/badge/FORRT-replication-blue)](https://forrt.org/)
[![Science Live](https://img.shields.io/badge/Science%20Live-nanopub%20chain-purple)](nanopubs/PUBLISHED.md)
[![RO-Crate](https://img.shields.io/badge/RO--Crate-1.2-orange)](ro-crate-metadata.json)
[![Software Heritage](https://archive.softwareheritage.org/badge/origin/https://github.com/annefou/anatolia-jerboa-climate-sdm/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/annefou/anatolia-jerboa-climate-sdm)

> **Phylogeography of Scarturus williamsi and Climate Change Impacts: Genetic Diversity and Projected Habitat Loss in Anatolia** — replication study.
> Reference paper: [10.3390/biology14091184](https://doi.org/10.3390/biology14091184)

**DRAFT, not reviewed.** LifeWatch ERIC feasibility test prepared for the meeting with HUBIOM (Hacettepe University) on 30 October 2026. Our reading of the published work, open to correction by the authors. Private until the authors have seen it.

### Claim tested (Helvacı and Çolak 2025, *Biology* 14:1184)

Williams' jerboa loses 40-48 % of its suitable habitat by 2021-2040 and 64-98 % by 2081-2100 (MIROC6, four SSPs; Random Forest, eight bioclimatic variables, threshold 0.3).

### Results (23 October 2026; WorldClim + CMIP6, the paper's design)

| | 19 GBIF cells | 73 cells (GBIF + iNaturalist + 53 localities read from the paper's Figure 1A) |
| --- | --- | --- |
| Cross-validated AUC / TSS | 0.80 / 0.60 | 0.90 / 0.72 |
| Null control: "loss" with no climate change (5 refits), threshold 0.3 | 51 % (26-74 %) | 25 % (15-34 %) |
| Loss 2021-2040, SSP3-7.0, 11 CMIP6 models (WorldClim has no SSP3-7.0 for FIO-ESM-2-0 and HadGEM3-GC31-LL), threshold 0.3 | 42-61 % | 62-86 % (median 76 %) |
| Loss 2081-2100, MIROC6, SSP1-2.6 -> SSP5-8.5 | 56 -> 47 % (no trend) | 84 -> 96 % (rises with emissions) |
| Same, data-tuned threshold (max TSS): null / near-term loss | 18 % / 15-21 % | 15 % (5-27 %) / 17-30 % |

With public GBIF data alone the projected loss cannot be told from model noise; with the authors' own localities a climate signal clears it. The magnitude depends strongly on the threshold; the direction and the dependence on emissions are the robust findings. Tables: `results/`.

### Method

- Occurrences: GBIF read with [healpix-connector](https://github.com/annefou/healpix-connector) v0.2.0 ([doi:10.5281/zenodo.23603498](https://doi.org/10.5281/zenodo.23603498)), Catalogue of Life XR taxonomy stated (keys BSW8, *Allactaga (Paralactaga) williamsi* Thomas 1897, and VNB82, the 2016 concept to which records labelled *Scarturus williamsi* are attached by name matching), each record's uncertainty footprint kept; iNaturalist "needs ID"; 53 localities digitised from Figure 1A of the paper (CC BY 4.0) with an overlay check, about 15 km uncertainty: `inputs/literature/helvaci2025_fig1A_digitised.csv`, `figures/helvaci2025_fig1A_digitised_overlay.png`, reproduced by `pipeline/digitise/fetch_figure.py` then `fig1_points.py` (kept in this private repository until the authors agree).
- Climate: WorldClim 2.1 (2.5') and CMIP6 change-factor layers; ERA5 1991-2020 (`pipeline/04b_era5.py`, Planetary Computer Zarr) with Climate DT generation 2 changes (IFS-FESOM done, IFS-NEMO in progress), read with healpix-connector `sources.climatedt_monthly`; ERA5-Land (`pipeline/04_era5land.py`) as a second baseline when the CDS queue allows.
- ERA5 (0.25 deg, wider than a cell) goes onto the WGS84 cells with healpix-connector `sources.gridded.sample_cells_from_grid` (value of the box containing the cell centre); an exact area overlap differs by 0.1 degC on average (2001).
- Grid: HEALPix depth 10 (40.5 km2 cells; healpix-geo, WGS84 ellipsoid, NESTED); resampling with healpix-resample, bilinear in conservative mode (`pipeline/90_compare_resamplers.py`: within 0.1 of an exact area overlap; Climate DT sphere -> WGS84 by matching ids would be off by 0.80 degC on average).
- Model: as in the paper (Random Forest, 1,000 background cells, 10 replicates 70/30, TSS-weighted ensemble), plus a null control (`pipeline/06_null_control.py`) and sensitivity to the threshold and to 10,000 background cells.

### Limits

- The paper's own coordinates are not public; map readings carry about 15 km uncertainty. Cells of 6.4 km against the paper's 1 km grid.
- Climate only: land use (steppe turned to cropland) is not in the model.
- The Climate DT monthly stream has no maximum or minimum temperature; future diurnal range is kept from the reanalysis baseline (`pipeline/05_bioclim.py` measures how much it changes in CMIP6).

### Data

GBIF records under their own licences (mostly CC BY and CC BY-NC); WorldClim (CC BY 4.0); DestinE Climate DT (DestinE Terms: derived statistics only); ERA5 and ERA5-Land (Copernicus, CC BY). Only code, plots and summary statistics are in this repository.

---

## Quick start

```bash
git clone https://github.com/annefou/anatolia-jerboa-climate-sdm.git
cd anatolia-jerboa-climate-sdm
pixi install
pixi run occurrences          # GBIF via healpix-connector
pixi run climate              # WorldClim and CMIP6 on HEALPix
pixi run sdm                  # model, losses, threshold and background sensitivity
pixi run python pipeline/06_null_control.py work
```

(Pixi resolves `pixi.toml` against the per-platform `pixi.lock`, installs the env under `.pixi/`, and provides `pixi run` for any task without needing an `activate` step.)

Or with Docker:

```bash
docker run --rm ghcr.io/annefou/anatolia-jerboa-climate-sdm:latest
```

The Jupyter Book version is at <https://annefou.github.io/anatolia-jerboa-climate-sdm/>.

## Built from a template

This repository was created from [`sciencelivehub/forrt-replication-template`](https://github.com/sciencelivehub/forrt-replication-template). The template ships an operating manual for AI assistants ([`CLAUDE.md`](CLAUDE.md), [`AGENTS.md`](AGENTS.md)), domain conventions ([`DOMAIN.md`](DOMAIN.md)), and reference docs (`docs/`) so that an AI working only inside this repository can guide a researcher from "paper PDF + GitHub repo" to "published FORRT chain + Zenodo DOI" with no other context.

If you are reading this in a fresh fork, run [`/init-template`](.claude/skills/init-template/SKILL.md) inside Claude Code to substitute the placeholder tokens with your details. (For other AI tools, see [`docs/ai-portability.md`](docs/ai-portability.md).)

After `/init-template`, do these one-time setup steps to enable the full CI/CD path:

- **Enable GitHub Pages** at *Settings → Pages → Source: GitHub Actions*. Until enabled, the Jupyter Book build runs but the deploy step is skipped (CI stays green).
- All three workflows share one **readiness guard** (`.github/actions/check-ready`). Before `/init-template` runs, the `.template-uninitialised` sentinel makes them skip with an informative `::notice::` (badges stay green); `/init-template` deletes the sentinel, which activates them. They also skip while `notebooks/*.py` are still scaffolds (Phase 2). **Once you've published a nanopub chain** (real URIs in `nanopubs/PUBLISHED.md`), a skip is treated as a bug and **fails the run loudly** — so a finished replication can't sit on silently-green-but-empty CI.

## Repository structure

```
.
├── CLAUDE.md / AGENTS.md       # operating manual for AI assistants
├── DOMAIN.md                   # domain flavour (current: biodiversity + earth observation)
├── USER_PREFERENCES.md         # per-user style (edit on first clone)
├── README.md                   # this file
├── LICENSE                     # MIT
├── CITATION.cff                # how to cite
├── codemeta.json               # software metadata (CodeMeta-2.0)
├── ro-crate-metadata.json      # research object packaging (RO-Crate 1.2)
├── pixi.toml + pixi.lock       # pinned dependencies (single source of truth; lockfile is per-platform)
├── Dockerfile                  # container build
├── Snakefile                   # pipeline orchestration
├── myst.yml + index.md         # Jupyter Book scaffold
├── paper/                      # the source paper PDF
├── data/                       # downloaded artefacts (gitignored)
├── notebooks/                  # jupytext .py pipeline (01–04)
├── nanopubs/                   # FORRT chain drafts + published-URI registry
├── docs/                       # reference material
├── figures/                    # curated figures used in the Jupyter Book
├── .github/workflows/          # CI, Jupyter Book, Docker
└── .claude/                    # Claude Code agents, skills, sandbox config
```

## What you get

This template bakes in conventions that took multiple replications to discover. By using it, you inherit:

- **FAIR4RS conformance** — see [`docs/fair4rs-checklist.md`](docs/fair4rs-checklist.md) for the principle-by-principle mapping.
- **Self-contained data downloads** — the first notebook fetches everything; no manual data prep.
- **`pixi.toml` + `pixi.lock` as single source of truth** — local dev, Docker, and CI all install the same per-platform-pinned env.
- **`prefix-dev/setup-pixi`-based CI** — caches the env, runs the pipeline with `pixi run`, executes notebooks via a glob, fails fast on a stale lockfile.
- **Jupyter Book deployment** — auto-deploys to GitHub Pages with `BASE_URL` set correctly. (Don't put `base_url` in `myst.yml` — MyST silently ignores it.)
- **Docker + GHCR + Zenodo image archival** — `release` trigger pushes to GHCR and (optionally) archives to Zenodo for long-term preservation.
- **RO-Crate packaging** — the entire repo is a navigable Research Object via `ro-crate-metadata.json` (Process Run Crate + Workflow RO-Crate profiles).
- **Six-step FORRT chain workspace** — `nanopubs/drafts/` has a field-by-field skeleton for each step. `nanopubs/PUBLISHED.md` is the URI registry.
- **Layered AI guidance** — `CLAUDE.md` (universal) + `DOMAIN.md` (swappable per field) + `USER_PREFERENCES.md` (per-user). See [`docs/ai-portability.md`](docs/ai-portability.md) for non-Claude AI tools.
- **Sandbox by default** — `.claude/settings.json` denies file ops outside the repo, so a fresh AI session can't accidentally read `~/.ssh/` or write to `/etc/`.

## The six FORRT chain steps

A complete FORRT chain has six steps published on [platform.sciencelive4all.org](https://platform.sciencelive4all.org):

```
Quote-with-comment  →  AIDA  →  FORRT Claim  →  Replication Study  →  Replication Outcome  →  CiTO Citation
```

(For question-rooted chains with no upstream paper, replace step 1 with PICO or PCC. See [`docs/chain-decision-tree.md`](docs/chain-decision-tree.md).)

Drafts live in [`nanopubs/drafts/`](nanopubs/drafts/) field-by-field. Published URIs go into [`nanopubs/PUBLISHED.md`](nanopubs/PUBLISHED.md).

Optional further layers:

- **Research Software nanopub** — for reusable upstream tools (not demo repos). See [`docs/forrt-form-fields.md`](docs/forrt-form-fields.md) § Research Software.
- **Research Synthesis nanopub** — when this chain is part of a multi-chain story. See [`docs/forrt-form-fields.md`](docs/forrt-form-fields.md) § Research Synthesis.

## After publishing

When the chain is live and the FAIR4RS checklist is green, drafting an announcement post is the next step. See [`docs/announcement-template.md`](docs/announcement-template.md) for the structural template (vision-piece-first; the worked replication is the payoff, not the lead).

For lower-level nanopub work — retraction, superseding, batch publishing — see [`docs/programmatic-nanopubs.md`](docs/programmatic-nanopubs.md).

## Citation

If you use this work, please cite both:

- This software: [`CITATION.cff`](CITATION.cff) → DOI [{{ZENODO_DOI}}]({{ZENODO_DOI}})
- The original paper: [10.3390/biology14091184](https://doi.org/10.3390/biology14091184)

## Acknowledgements

This repository was built from [`sciencelivehub/forrt-replication-template`](https://github.com/sciencelivehub/forrt-replication-template), part of the [Science Live platform](https://platform.sciencelive4all.org). The template is licensed MIT and contributions (especially new domain flavours under [`docs/domain-flavours/`](docs/domain-flavours/)) are welcome.
