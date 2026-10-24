# 06 — CiTO Citation

**Description:** *"Declare citations between papers or other works, using Citation Typing Ontology"*

## Field-by-field draft

<!-- field: work -->
### Identifier for the citing creative work (text input, required)

```
«URI of step 05 (FORRT Replication Outcome), filled by the chain wizard»
```

### List citations (repeatable group, required ≥1)

#### Citation 1 — back to the original paper

##### Citation Type (dropdown)

Outcome is "partially supported", so `qualifies` (from `vocabulary("cito_relation")`, live).

```
qualifies
```

##### DOI or other URL of the cited work (text input)

```
https://doi.org/10.3390/biology14091184
```

#### Additional citations (optional)

All DOIs resolved on 2026-10-24; relations from `vocabulary("cito_relation")`. The paper is also cited for its Figure 1A localities (CC BY 4.0); Olgun Karacan et al. 2024 for the GenBank localities; WorldClim 2 for the climate data; healpix-connector for reading GBIF and gridded climate onto the cells.

- Type: uses data from → URL: https://doi.org/10.3390/biology14091184
- Type: uses data from → URL: https://doi.org/10.1155/jzs/8123686
- Type: cites as data source → URL: https://doi.org/10.1002/joc.5086
- Type: uses method in → URL: https://doi.org/10.5281/zenodo.23603498

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 06.
