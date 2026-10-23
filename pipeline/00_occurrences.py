"""GBIF occurrences of Williams' jerboa within the study extent of Helvaci & Colak 2025, read with
healpix-connector (LifeWatch ERIC / GRID4EARTH, v0.2.0, doi:10.5281/zenodo.23603498).

Taxonomy, stated: Catalogue of Life eXtended Release (GBIF's default), checklistKey 7ddf754f-...
In COL XR the name "Scarturus williamsi" matches *Scarturus williamsi* (Hamidi, Darvish & Matin, 2016),
the concept attached to the Iranian Kopet-Dag population, while Thomas's 1897 species is
*Allactaga (Paralactaga) williamsi* Thomas, 1897. GBIF records labelled Scarturus williamsi from
Turkiye and the Caucasus are attached to the 2016 concept by name matching, so both keys are read:
BSW8 (Thomas 1897) and VNB82 (records filed under the 2016 name); the key of each record is kept.
Filters, following section 2.1 of the paper: inside 25-73 E, 27-42 N; Afghanistan excluded
(S. caprimulga, Lebedev et al.); presences only (occurrenceStatus); no fossils; no GBIF geospatial
issue flags; coordinate uncertainty <= 10 km when stated; one record per HEALPix cell (depth 10).
Each record's footprint (the cells its uncertainty disc covers) is kept from the connector.
The literature records the paper added are not in GBIF (see 00b_extra_occurrences.py).

Usage: python pipeline/00_occurrences.py <ROOT>      (ROOT = work)
Writes <ROOT>/occ/occurrences.parquet (not committed: individual records stay under their GBIF licences)
and results/occurrences_summary.json (counts per filter, key, country, basis of record, licence, dataset).
"""
import json
import os
import sys

import pandas as pd
from healpix_connector import __version__ as connector_version
from healpix_connector.connectors import gbif
from healpix_connector.region import Region

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ROOT = sys.argv[1]
OUT = f"{ROOT}/occ"
KEYS = {"BSW8": "Allactaga (Paralactaga) williamsi Thomas, 1897",
        "VNB82": "Scarturus williamsi (Hamidi, Darvish & M. Matin, 2016), name used for GBIF records labelled Scarturus williamsi"}
BAD = ("ZERO_COORDINATE", "COORDINATE_INVALID", "COORDINATE_OUT_OF_RANGE", "COUNTRY_COORDINATE_MISMATCH",
       "PRESUMED_SWAPPED_COORDINATE", "PRESUMED_NEGATED_LONGITUDE", "PRESUMED_NEGATED_LATITUDE")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    os.makedirs("results", exist_ok=True)
    region = Region.from_bbox(*common.EXTENT)
    recs, prov = [], {}
    for key in KEYS:
        r = gbif.search(region, taxon_key=key, checklist_key=gbif.COL_XR)
        prov[key] = r.provenance
        recs += gbif.to_cells(r.records, common.DEPTH, footprints=True)
    df = pd.DataFrame(recs).drop_duplicates("gbifID")
    steps = {"in_extent_both_keys": len(df)}
    df = df[df.countryCode.fillna("") != "AF"]
    steps["afghanistan_excluded"] = len(df)
    df = df[df.occurrenceStatus.fillna("PRESENT") == "PRESENT"]
    steps["presences_only"] = len(df)
    df = df[df.basisOfRecord != "FOSSIL_SPECIMEN"]
    df = df[~df.issues.apply(lambda i: any(b in (i or []) for b in BAD))]
    steps["no_geospatial_issue"] = len(df)
    df = df[df.coordinateUncertaintyInMeters.isna() | (df.coordinateUncertaintyInMeters <= 10000)]
    steps["uncertainty_le_10km"] = len(df)
    df["n_footprint_cells"] = df.footprint_cells.apply(len)
    one = df.sort_values("year", ascending=False).drop_duplicates("cell")
    steps["one_per_cell"] = len(one)
    one = one.rename(columns={"decimalLongitude": "lon", "decimalLatitude": "lat",
                              "coordinateUncertaintyInMeters": "uncertainty_m", "license": "license"})
    one.to_parquet(f"{OUT}/occurrences.parquet", index=False)
    summary = {"connector": f"healpix-connector {connector_version}", "taxonomy": "Catalogue of Life XR",
               "checklist_key": gbif.COL_XR, "taxon_keys": KEYS, "filter_steps": steps,
               "healpix_depth": common.DEPTH,
               "kept_by_taxon_key": one.taxon_key.value_counts().to_dict(),
               "kept_by_country": one.countryCode.value_counts().to_dict(),
               "kept_by_basis": one.basisOfRecord.value_counts().to_dict(),
               "kept_by_licence": one.license.value_counts().to_dict(),
               "kept_by_dataset": one.datasetKey.value_counts().to_dict(),
               "uncertainty_stated": int(one.footprint_known.sum()),
               "footprint_cells_median": float(one.n_footprint_cells.median()),
               "provenance": prov}
    json.dump(summary, open("results/occurrences_summary.json", "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in summary.items() if k != "provenance"}, indent=1, default=str))


if __name__ == "__main__":
    main()
