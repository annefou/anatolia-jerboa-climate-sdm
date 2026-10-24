# Paper summary

> Working scratchpad for the paper-analysis phase; it feeds the Quote / AIDA / Claim drafts and is not itself a nanopub.

**Reference paper:** Phylogeography of Scarturus williamsi and Climate Change Impacts: Genetic Diversity and Projected Habitat Loss in Anatolia

**DOI:** 10.3390/biology14091184

**Authors:** Zeycan Helvacı (Aksaray University), Ercüment Çolak (Ankara University)

**Year:** 2025 (*Biology* 14, 1184; CC BY 4.0)

## Headline claim

> Climate projections reveal severe vulnerability with habitat losses of 63.69–98.41% by 2081–2100 across emission scenarios.

Verified with `verify_quote` against `paper/helvaci-2025.pdf` (page 1, abstract; SHA-256 b89b5815…6c3cee).

## Methodology summary

- **Data sources:** occurrence records from the literature, GBIF and IUCN, validated by hand (coordinates not published; shown in Figure 1A); WorldClim 2.1 at 30″; MIROC6 CMIP6 downscaled projections, SSP1-2.6, 2-4.5, 3-7.0, 5-8.5, four 20-year periods.
- **Model:** Random Forest (R `sdm` 1.2-55), eight bioclimatic variables (bio2, 3, 4, 8, 9, 14, 15, 19), 1,000 random background points, 10 replicates 70/30, TSS-weighted ensemble; suitability threshold 0.3; habitat loss = share of currently suitable habitat unsuitable in the future.
- **Study region:** 25–73° E, 27–42° N (Anatolia, Iran, Azerbaijan; Afghanistan excluded).
- **Headline numbers (Table 3):** loss 2081–2100 of 63.69 (SSP1-2.6), 90.27 (SSP2-4.5), 98.41 (SSP3-7.0), 93.14 % (SSP5-8.5); 2021–2040 of 39.76–48.24 %. Model AUC 0.84, TSS 0.64.

## Replication design choice

- [ ] **Reproduction Study**
- [ ] **Replication Study**
- [x] **Reproduction/Replication Study**

Same model design, climate products and threshold (reproduction); different occurrence data (the paper's are not public: GBIF plus localities read from Figure 1A, and an independent check with GenBank localities), HEALPix cells of 40.5 km² instead of 1 km pixels, Python instead of R, and a null control the paper does not have (replication).

## Notes for downstream drafts

- The paper writes "Turkey"; our own text writes "Türkiye". Quotes stay verbatim.
- 73 cells (53 digitised + 19 GBIF + 1 iNaturalist): 2081–2100 losses 83.6–95.8 %; null 25 % (15–34). GBIF alone (19 cells): 45.6–56.4 %, null 51.5 % (26–74). GenBank check (43 cells): 81.8–98.0 %, null 36.1 % (16–52). Max-TSS threshold: 27–41 % against null 15 % (5–27).
- Outcome: partially supported, moderate confidence. Ask the authors before opening the repo (digitised localities).
- Paper PDF is local only (`paper/*.pdf` git-ignored), downloaded from mdpi-res.com on 2026-10-24.
