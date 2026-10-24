# 01 — Quote-with-comment (paper-rooted chains)

**Form heading:** *"Annotate a paper quotation — Annotating a paper quotation with personal interpretation"*

## Field-by-field draft

<!-- field: paper -->
### Cited DOI (text input, required)

Resolved with `resolve_doi` (2026-10-24): Helvacı & Çolak 2025, *Biology* 14, 1184.

```
10.3390/biology14091184
```

### Quote mode (radio button)

- [x] **Quote whole text (less than 500 characters)**
- [ ] Quote start/end *(use this if the quote exceeds 500 chars)*

<!-- field: quotation -->
### The exact quotation from the paper (max. 500 characters) (textarea, required)

Verified with `verify_quote` on `paper/helvaci-2025.pdf`: page 1 (abstract), characters 2890–3013, match "normalized" (en dashes and line breaks only).

```
Climate projections reveal severe vulnerability with habitat losses of 63.69–98.41% by 2081–2100 across emission scenarios.
```

Character count: 123 / 500.

<!-- field: quotation-end -->
### End of quotation (optional - use when quoting beginning and end of a longer passage, max. 500 characters) (textarea, optional)

*(skip — single short quote)*

```

```

<!-- field: comment -->
### Our interpretation and explanation of why this quotation is relevant (max. 800 characters) (textarea, required)

```
This is the paper's headline conservation result: a Random Forest model of the climate niche of Williams' jerboa, an endemic steppe rodent, projects that most of its currently suitable habitat becomes unsuitable by 2081-2100 under every emission scenario. The replication tests whether the size of this loss holds with the paper's design when the occurrence data have to be rebuilt from public sources, and whether it exceeds the apparent loss that refitting the same model with no climate change already produces.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 01.
