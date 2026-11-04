# anatolia-jerboa-climate-sdm

[![CI](https://github.com/annefou/anatolia-jerboa-climate-sdm/actions/workflows/ci.yml/badge.svg)](https://github.com/annefou/anatolia-jerboa-climate-sdm/actions/workflows/ci.yml)
[![Jupyter Book](https://github.com/annefou/anatolia-jerboa-climate-sdm/actions/workflows/jupyter-book.yml/badge.svg)](https://annefou.github.io/anatolia-jerboa-climate-sdm/)
[![Docker](https://github.com/annefou/anatolia-jerboa-climate-sdm/actions/workflows/docker.yml/badge.svg)](https://github.com/annefou/anatolia-jerboa-climate-sdm/pkgs/container/anatolia-jerboa-climate-sdm)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23942469.svg)](https://doi.org/10.5281/zenodo.23942469)
[![FAIR4RS](https://img.shields.io/badge/FAIR4RS-conformant-brightgreen)](docs/fair4rs-checklist.md)
[![FORRT](https://img.shields.io/badge/FORRT-replication-blue)](https://forrt.org/)
[![Science Live](https://img.shields.io/badge/Science%20Live-nanopub%20chain-purple)](nanopubs/PUBLISHED.md)
[![RO-Crate](https://img.shields.io/badge/RO--Crate-1.2-orange)](ro-crate-metadata.json)
[![Software Heritage](https://archive.softwareheritage.org/badge/origin/https://github.com/annefou/anatolia-jerboa-climate-sdm/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/annefou/anatolia-jerboa-climate-sdm)

> **Phylogeography of Scarturus williamsi and Climate Change Impacts: Genetic Diversity and Projected Habitat Loss in Anatolia** — replication study.
> Reference paper: [10.3390/biology14091184](https://doi.org/10.3390/biology14091184)

**DRAFT, not reviewed.** LifeWatch ERIC feasibility test prepared for the meeting with HUBIOM (Hacettepe University) on 30 October 2026. Our reading of the published work, open to correction by the authors.

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

- Occurrences: GBIF read with [healpix-connector](https://github.com/annefou/healpix-connector) v0.2.0 ([doi:10.5281/zenodo.23603498](https://doi.org/10.5281/zenodo.23603498)), Catalogue of Life XR taxonomy stated (keys BSW8, *Allactaga (Paralactaga) williamsi* Thomas 1897, and VNB82, the 2016 concept to which records labelled *Scarturus williamsi* are attached by name matching), each record's uncertainty footprint kept; iNaturalist "needs ID"; 53 localities digitised from Figure 1A of the paper (CC BY 4.0) with an overlay check, about 15 km uncertainty: `inputs/literature/helvaci2025_fig1A_digitised.csv`, `figures/helvaci2025_fig1A_digitised_overlay.png`, reproduced by `pipeline/digitise/fetch_figure.py` then `fig1_points.py`.
- Check without map digitising: 23 *S. williamsi* localities named in the GenBank records of Olgun Karacan et al. 2024 (doi:10.1155/jzs/8123686; their Table S1 gives provinces only), geocoded with OpenStreetMap Nominatim (5 km for a village or town, 15 km for a district): `inputs/literature_genbank/olgunkaracan2024_genbank_localities.csv` by `pipeline/digitise/genbank_localities.py`; set `occurrences_genbank` (43 cells), run with `00b_extra_occurrences.py work occurrences_genbank <file>`, `02_sdm.py`, `06_null_control.py`.
- Climate: WorldClim 2.1 (2.5') and CMIP6 change-factor layers; ERA5 1991-2020 (`pipeline/04b_era5.py`, Planetary Computer Zarr) with Climate DT generation 2 changes (IFS-FESOM and IFS-NEMO), read with healpix-connector `sources.climatedt_monthly`.
- ERA5 (0.25 deg, wider than a cell) goes onto the WGS84 cells with healpix-connector `sources.gridded.sample_cells_from_grid` (value of the box containing the cell centre); an exact area overlap differs by 0.1 degC on average (2001).
- Grid: HEALPix depth 10 (40.5 km2 cells; healpix-geo, WGS84 ellipsoid, NESTED); resampling with healpix-resample, bilinear in conservative mode (`pipeline/90_compare_resamplers.py`: within 0.1 of an exact area overlap; Climate DT sphere -> WGS84 by matching ids would be off by 0.80 degC on average).
- Model: as in the paper (Random Forest, 1,000 background cells, 10 replicates 70/30, TSS-weighted ensemble), plus a null control (`pipeline/06_null_control.py`) and sensitivity to the threshold and to 10,000 background cells.

### Limits

- The paper's own coordinates are not public; map readings carry about 15 km uncertainty. Cells of 6.4 km against the paper's 1 km grid.
- Climate only: land use (steppe turned to cropland) is not in the model.
- The Climate DT monthly stream has no maximum or minimum temperature; future diurnal range is kept from the reanalysis baseline (`pipeline/05_bioclim.py` measures how much it changes in CMIP6).

### Future exploration: daily data for extremes (not part of the results)

The model uses monthly climatologies (WorldClim 1970-2000; ERA5 1991-2020 with Climate DT changes). Monthly means
hide what happens on single days: frost days, hot days, dry spells, the length of the warm season. A model built on
such indices would need daily data, for example ERA5-Land daily maximum and minimum temperature (0.1 deg,
Copernicus Climate Data Store) for the baseline and the Climate DT's daily or hourly output for the future, on the
same HEALPix cells. Whether these indices improve the model has not been tested.

ERA5-Land was first planned as a second monthly baseline. It was not completed (the CDS queue took about 9.5 hours
per year) and was not needed: WorldClim and ERA5 already give the same answer against the null control. The two
scripts are kept as a starting point for the daily work: `pipeline/04_era5land.py` (one request at a time) and
`pipeline/04c_era5land_parallel.py` (parallel requests) download the daily maximum and minimum, but today they
reduce them to monthly means; a daily-index version would count days instead. To run them
(`pixi run snakemake --cores 1 era5land`) you need a free Copernicus Climate Data Store account: accept the licences
of `derived-era5-land-daily-statistics` and `reanalysis-era5-land-monthly-means` on their dataset pages, and put
your personal access token in `~/.cdsapirc` (`url: https://cds.climate.copernicus.eu/api`, `key: <token>`), or in
`CDSAPI_URL` and `CDSAPI_KEY`.

### Data

GBIF records under their own licences (mostly CC BY and CC BY-NC); WorldClim (CC BY 4.0); DestinE Climate DT (DestinE Terms: derived statistics only); ERA5 (Copernicus, CC BY). Only code, plots and summary statistics are in this repository.

---

## Install and run

You can read the results without installing anything: the summary tables are in `results/`, the figures in
`figures/`, and the [Jupyter Book](https://annefou.github.io/anatolia-jerboa-climate-sdm/) shows both. Rerunning the analysis needs the
steps below.

### Install

1. Install pixi (<https://pixi.sh>): `curl -fsSL https://pixi.sh/install.sh | bash`.
2. Get the code and the pinned environment:

   ```bash
   git clone https://github.com/annefou/anatolia-jerboa-climate-sdm.git
   cd anatolia-jerboa-climate-sdm
   pixi install
   ```

   Linux (x86-64), macOS (Apple silicon) and Windows: the pixi lock file covers all three. Pixi installs everything from `pixi.toml` and `pixi.lock` into `.pixi/`; `pixi run <task>` runs a
   task in that environment without activating it.

### Accounts each step needs

| What you run | Data | Account needed |
| --- | --- | --- |
| `pixi run snakemake --cores 1` (the paper's design) | GBIF and iNaturalist occurrences, the paper's Figure 1A (Europe PMC), WorldClim 2.1 and CMIP6 | **none**: all public and anonymous |
| `pixi run snakemake --cores 1 climatedt` | ERA5 1991-2020 (Microsoft Planetary Computer) | none (anonymous token, fetched by the script) |
| | Climate DT generation 2, IFS-FESOM and IFS-NEMO | **DestinE upgraded access** |
| `pipeline/digitise/genbank_localities.py` (optional re-check) | GenBank records, OpenStreetMap Nominatim | none; the geocoded result is committed in `inputs/literature_genbank/` |

Accounts are read from your home directory or the environment, never from the repository, and nothing in `work/`
(the downloads) is committed. Set up only the ones for the steps you run.

### Destination Earth: Climate DT (DestinE upgraded access)

1. Create an account on the DestinE Platform, <https://platform.destine.eu/>, and request **upgraded access**, which
   includes the Climate Change Adaptation Digital Twin. Eligibility and terms are set by the platform (at the time of
   writing: users in EU Member States and in countries associated with the Digital Europe Programme; check the current
   terms of use before you apply). Upgraded access is not automatic: allow time for the request to be reviewed.
2. Get the Polytope key (an offline token) with ECMWF's script; it asks for your DestinE user name and password and
   writes `{"user_key": "<offline token>"}` to `~/.polytopeapirc`:

   ```bash
   curl -sO https://raw.githubusercontent.com/destination-earth-digital-twins/polytope-examples/main/desp-authentication.py
   pixi run python desp-authentication.py
   ```

   `polytope-client` also reads `POLYTOPE_USER_KEY` from the environment. A *DestinE Data Lake* (DEDL) API key is a
   different credential and is refused by Polytope (HTTP 401).
3. Authentication is not authorisation: a valid key can still be refused the data if upgraded access has not been
   granted yet; the first request tells you.
4. Terms: raw Climate DT data may not be redistributed. The pipeline keeps downloads in `work/` (not in git) and
   commits only derived statistics; keep it that way in any fork.

### Run

```bash
pixi run snakemake --cores 1             # GBIF, iNaturalist, digitised and GenBank localities, WorldClim + CMIP6: no account
pixi run snakemake --cores 1 climatedt   # ERA5 (anonymous) + Climate DT: DestinE upgraded access
```

Single steps: `pixi run occurrences`, `pixi run climate`, `pixi run sdm`, `pixi run python pipeline/06_null_control.py work`.

Every step is a script in `pipeline/` with its usage in its docstring; `Snakefile` gives the order, inputs and
outputs. `pixi run snakemake --cores 1 --dry-run` lists what would run without downloading anything.
The charts of the LifeWatch country file are in `docs/country_file/` (chart code and the rows they plot).

### With Docker

The image holds the environment and the code, never an account. Put the accounts the steps need in a file that
stays on your machine (for example `~/credentials.env`, outside the repository) and pass it at run time, from the
cloned repository (so that `work/` and `results/` are kept on your disk):

```
CDSAPI_URL=https://cds.climate.copernicus.eu/api
CDSAPI_KEY=<CDS personal access token>
COPERNICUSMARINE_SERVICE_USERNAME=<Copernicus Marine user name>
COPERNICUSMARINE_SERVICE_PASSWORD=<Copernicus Marine password>
POLYTOPE_USER_KEY=<DestinE offline token>
```

```bash
docker run --rm --env-file ~/credentials.env -v "$PWD/work:/app/work" -v "$PWD/results:/app/results" \
    ghcr.io/annefou/anatolia-jerboa-climate-sdm:latest pixi run snakemake --cores 1 climatedt
```

Leave out the lines a step does not need. The image is published on GitHub's container registry with each release.

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

- This software: [`CITATION.cff`](CITATION.cff) → DOI [10.5281/zenodo.23942469](https://doi.org/10.5281/zenodo.23942469)
- The original paper: [10.3390/biology14091184](https://doi.org/10.3390/biology14091184)

## Acknowledgements

This repository was built from [`sciencelivehub/forrt-replication-template`](https://github.com/sciencelivehub/forrt-replication-template), part of the [Science Live platform](https://platform.sciencelive4all.org). The template is licensed MIT and contributions (especially new domain flavours under [`docs/domain-flavours/`](docs/domain-flavours/)) are welcome.
