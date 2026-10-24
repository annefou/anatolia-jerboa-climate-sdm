# 05 — FORRT Replication Outcome

Numbers read from `results/loss_worldclim*.csv`, `results/null_control_worldclim*.json`, `results/sdm_worldclim*.json` and `results/occurrences_merged_summary.json` (2026-10-24).

## Field-by-field draft

<!-- field: outcome -->
### Short URI suffix for outcome ID (text input, required)

```
scarturus-williamsi-habitat-loss-outcome
```

<!-- field: label -->
### Plain-text label for the outcome (text input, required)

```
Severe end-of-century habitat loss reproduced with the authors' localities, not with public GBIF data alone; size depends on the threshold
```

<!-- field: study -->
### Choose study (search/select, required)

```
«URI of step 04 (FORRT Replication Study), filled by the chain wizard»
```

<!-- field: repo -->
### Repository URL (text input, required)

The Zenodo version DOI of the release the results come from; substituted by the release workflow.

```
https://doi.org/{{ZENODO_VERSION_DOI}}
```

<!-- field: date -->
### Choose completion date (text input, required)

```
2026-10-23
```

<!-- field: validationStatus -->
### Choose validation status (dropdown, required)

From `vocabulary("validation_status")`: the direction and the severity hold with the authors' localities and with an independent set, but not with public GBIF data alone, and the size depends strongly on the threshold.

- [ ] contradicted
- [ ] inconclusive
- [ ] not tested
- [x] partially supported
- [ ] validated

<!-- field: confidenceLevel -->
### Choose confidence level (dropdown, required)

From `vocabulary("confidence_level")`: the paper's occurrence data could not be used; localities read from a map carry about 15 km uncertainty.

- [ ] high - Strong evidence, mostly agrees with original
- [ ] low - Limited evidence, significant disagreement
- [x] moderate - Adequate evidence, partial agreement
- [ ] very high - Extensive evidence, high agreement with original
- [ ] very low - Minimal evidence, major disagreement

<!-- field: conclusion -->
### Describe the overall conclusion about the original claim (textarea, required)

```
With the paper's design, threshold 0.3 and the 73 cells that include localities read from the paper's map, MIROC6 losses for 2081-2100 are 83.6, 92.3, 95.1 and 95.8% from SSP1-2.6 to SSP5-8.5, against the paper's 63.69-98.41%, and well above the 25% apparent loss that refitting the model with no climate change produces. An independent set of GenBank localities gives 81.8-98.0% against a 36% null. With public GBIF records alone (19 cells) the losses, 45.6-56.4%, cannot be told apart from the 51.5% null and show no rise with emissions. With a data-tuned threshold the losses fall to 27-41%. The severe, emission-dependent loss is supported, but only with the authors' localities, and its size depends on the threshold.
```

<!-- field: evidence -->
### Describe the evidence that supports your conclusion (textarea, required)

```
Occurrence sets (HEALPix cells of 40.5 km2): GBIF 19; GBIF + iNaturalist + 53 Figure 1A localities 73; GenBank localities 43. Cross-validated AUC / TSS: 0.80 / 0.60 (19), 0.90 / 0.72 (73), 0.90 / 0.73 (43); paper 0.84 / 0.64. Loss 2081-2100, MIROC6, threshold 0.3, SSP1-2.6 / 2-4.5 / 3-7.0 / 5-8.5: 73 cells 83.6 / 92.3 / 95.1 / 95.8%; 43 cells 81.8 / 90.6 / 96.2 / 98.0%; 19 cells 56.4 / 53.9 / 45.6 / 47.3%; paper 63.69 / 90.27 / 98.41 / 93.14%. Null control, five refits, mean (range): 25.3% (15.5-34.4), 36.1% (16.2-51.5), 51.5% (26.2-73.8). Max-TSS threshold, 73 cells: loss 27.2-40.7%, null 14.8% (4.6-27.4). SSP3-7.0 2021-2040, eleven CMIP6 models, 73 cells: 62.4-85.7% (paper, MIROC6: 39.76%). Files: results/loss_worldclim_occurrences_merged.csv, results/null_control_worldclim_occurrences_merged.json.
```

<!-- field: limitations -->
### Describe what limits the conclusions of the study (textarea, optional)

```
The paper's validated coordinates are not public; map readings of Figure 1A carry about 15 km uncertainty and GenBank localities 5-15 km. Cells of 6.4 km against the paper's 1 km grid. One climate model for the end of the century, as in the paper. A fixed threshold of 0.3 drives the size of the loss: with 10000 background cells almost no cell exceeds it. Climate only; conversion of steppe to cropland is not modelled.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 05.
