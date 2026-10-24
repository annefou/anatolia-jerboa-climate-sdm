# 04 — FORRT Replication Study

Method read from `pipeline/00_occurrences.py`, `pipeline/00b_extra_occurrences.py`, `pipeline/02_sdm.py`, `pipeline/06_null_control.py` and `pipeline/digitise/` (2026-10-24).

## Field-by-field draft

<!-- field: study -->
### Short URI suffix for study ID (text input, required)

```
scarturus-williamsi-habitat-loss-replication-study
```

<!-- field: label -->
### Label/name of replication study (text input, required)

```
Replication of the projected habitat loss of Williams' jerboa with public occurrences on HEALPix cells and a null control
```

<!-- field: type -->
### Choose the study type (dropdown, required)

Same model design, climate products and threshold (reproduction); occurrence data rebuilt from other sources, a different grid and software (replication).

- [ ] Replication Study - replication with different methodology or conditions
- [x] Reproduction/Replication Study - study that is both, reproduction and replication
- [ ] Reproduction Study - direct reproduction: same methodology, same tools

<!-- field: claim -->
### Choose FORRT claim (search/select, required)

```
«URI of step 03 (FORRT Claim), filled by the chain wizard»
```

<!-- field: scope -->
### Describe what part of the claim is reproduced/replicated. (textarea, required)

```
The claim that 63.69-98.41% of the currently suitable habitat of Scarturus williamsi is lost by 2081-2100 across SSP1-2.6, SSP2-4.5, SSP3-7.0 and SSP5-8.5 with MIROC6. In scope: the size of the end-of-century loss per scenario with the paper's model design and threshold, its dependence on emissions, whether it exceeds the loss produced by model noise alone, and how it depends on the occurrence data and the threshold. Out of scope: the phylogeography and genetic results, the variable importance and response curves, and land-use change.
```

<!-- field: methodology -->
### Describe how the claim is reproduced/replicated. (textarea, required)

```
Model as in the paper: Random Forest on eight bioclimatic variables (bio2, bio3, bio4, bio8, bio9, bio14, bio15, bio19), 1000 random background cells over 25-73 E and 27-42 N, 10 replicates with a random 70/30 split, ensemble weighted by TSS, suitability threshold 0.3, loss as the share of currently suitable habitat that is unsuitable in the future. Climate: WorldClim 2.1 baseline and MIROC6 CMIP6 layers for the four scenarios and periods. Unit: HEALPix cells of 40.5 km2 (depth 10, WGS84 ellipsoid, nested). Occurrences, since the paper's are not public: three sets, GBIF only (19 cells); GBIF plus iNaturalist plus 53 localities read from the paper's Figure 1A (73 cells); and 23 localities named in GenBank records of an independent study (43 cells). Null control: the ensemble is refitted five times with new seeds on the same data and baseline; the loss between fits is method noise. Sensitivity: data-tuned threshold (max TSS) and 10000 background cells.
```

<!-- field: deviation -->
### Describe any deviations from original methodology. (textarea, optional)

```
The paper's validated occurrence coordinates are not published, so occurrences come from GBIF, iNaturalist, map readings of Figure 1A (about 15 km uncertainty) and geocoded GenBank localities. Cells of 40.5 km2 replace 1 km pixels and WorldClim is used at 2.5 arc-minutes instead of 30 arc-seconds. scikit-learn Random Forest replaces the R sdm package. The null control, the threshold and background sensitivity, and additional climate inputs (eleven CMIP6 models for 2021-2040, ERA5 with Climate DT projections) are not in the paper.
```

<!-- field: keyword -->
### Search keywords (Wikidata) (search/select, optional)

Checked with `wikidata_lookup` (2026-10-24).

- Williams's jerboa (Q111744929)
- species distribution modelling (Q117051118)
- climate change (Q125928)

<!-- field: discipline -->
### Search discipline (Wikidata) (search/select, optional)

- ecology (Q7150)

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 04.
