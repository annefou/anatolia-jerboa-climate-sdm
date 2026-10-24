# 09 — Geographical coverage (optional)

One pooled coverage: the paper models a single study region.

## Shared field

<!-- field: paper -->
### Cited DOI (text input, required — same for every location)

```
10.3390/biology14091184
```

---

## Per-location block

### Location A

<!-- field: quoteType -->
**Quote type** (radio: whole | ends, required)

```
whole
```

<!-- field: quotation -->
**Quoted Text** (textarea, required) — verified with `verify_quote` on `paper/helvaci-2025.pdf`: page 4, characters 1377–1489, match "normalized".

```
The study region spans 25–73◦ E longitude and 27–42◦ N latitude, encompassing all confirmed records (Figure 1A).
```

<!-- field: quotation-end -->
**Quoted Text End** (textarea, optional — only if quote type = ends). Leave blank for `whole`.

```

```

<!-- field: location -->
**Short ID for location** (text input, required)

```
anatolia-iran-azerbaijan
```

<!-- field: location-label -->
**Area name** (text input, required) — add each place in the form's location search: Anatolia, Iran, Azerbaijan.

```
Anatolia, Iran and Azerbaijan
```

<!-- field: geometry -->
**Short ID for geometry** (text input, optional)

```
coverage
```

<!-- field: wkt -->
**Geometry as Well-known Text (WKT)** — left to the form's geocoder. The quoted box is 25–73° E, 27–42° N.

```

```

<!-- field: comment -->
**Comment** (textarea, required)

```
The quoted sentence gives the bounding box of the study region, which covers the confirmed records of Scarturus williamsi in Anatolia, Iran and Azerbaijan; Afghanistan is excluded in the methods.
```

## Publication note

Each location block is a **standalone** nanopub, not one of the six FORRT chain steps.
Publish it via the platform's **"Document geographical coverage"** template. After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` under a "Geographical coverage" row.
