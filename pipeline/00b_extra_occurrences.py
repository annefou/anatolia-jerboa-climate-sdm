"""Occurrences from outside GBIF, merged with the GBIF set of 00_occurrences.py.

  * iNaturalist (API v1): observations of Scarturus williamsi (taxon 1431637) not already in GBIF, quality
    grade "needs_id" only ("casual" = captive, no date or no evidence, excluded), positional accuracy <= 10 km.
  * Literature / collection tables: every CSV in <ROOT>/occ/sources/ with columns
        source, locality, lon, lat, uncertainty_m, year, voucher
    (one row per specimen or locality; coordinates as published or georeferenced from the locality text,
    uncertainty as published or from the georeference). Records without coordinates are counted, not used.
Same filters as 00_occurrences.py (study extent, Afghanistan excluded, uncertainty <= 10 km), except that points
digitised from published maps are accepted up to 15 km (their reading uncertainty); one record per
HEALPix cell (GBIF kept first, then literature, then iNaturalist).

Usage: python pipeline/00b_extra_occurrences.py <ROOT>
Writes <ROOT>/occ/occurrences_merged.parquet (not committed) and results/occurrences_merged_summary.json.
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

ROOT = sys.argv[1]
INAT_TAXON = 1431637


def inat() -> pd.DataFrame:
    rows, page = [], 1
    while True:
        r = requests.get("https://api.inaturalist.org/v1/observations",
                         params={"taxon_id": INAT_TAXON, "quality_grade": "needs_id", "per_page": 200, "page": page},
                         timeout=120)
        r.raise_for_status()
        res = r.json()["results"]
        for o in res:
            if not o.get("geojson"):
                continue
            lon, lat = o["geojson"]["coordinates"]
            rows.append({"source": "iNaturalist needs_id", "record_id": f"inat:{o['id']}", "lon": lon, "lat": lat,
                         "uncertainty_m": o.get("positional_accuracy"), "year": (o.get("observed_on_details") or {}).get("year"),
                         "countryCode": None, "license": o.get("license_code")})
        if len(res) < 200:
            return pd.DataFrame(rows)
        page += 1


def literature() -> tuple[pd.DataFrame, dict]:
    frames, counts = [], {}
    for f in sorted(glob.glob(f"{ROOT}/occ/sources/*.csv")):
        d = pd.read_csv(f)
        counts[os.path.basename(f)] = {"rows": len(d), "with_coordinates": int(d[["lon", "lat"]].notna().all(1).sum())}
        d = d[d[["lon", "lat"]].notna().all(1)].copy()
        d["record_id"] = d["source"].astype(str) + ":" + d.get("voucher", pd.Series(range(len(d)), index=d.index)).astype(str)
        d["countryCode"] = None
        d["license"] = "see source"
        frames.append(d[["source", "record_id", "lon", "lat", "uncertainty_m", "year", "countryCode", "license"]])
    return (pd.concat(frames) if frames else pd.DataFrame()), counts


def main() -> None:
    g = pd.read_parquet(f"{ROOT}/occ/occurrences.parquet")
    g = g.assign(source="GBIF", record_id="gbif:" + g.gbifID.astype(str))[
        ["source", "record_id", "lon", "lat", "uncertainty_m", "year", "countryCode", "license"]]
    lit, lit_counts = literature()
    ina = inat()
    allr = pd.concat([g, lit, ina], ignore_index=True)
    x0, y0, x1, y1 = common.EXTENT
    allr = allr[(allr.lon > x0) & (allr.lon < x1) & (allr.lat > y0) & (allr.lat < y1)]
    allr = allr[allr.countryCode.fillna("") != "AF"]
    lim = np.where(allr.source.str.contains("digitised"), 15000, 10000)
    allr = allr[allr.uncertainty_m.isna() | (allr.uncertainty_m <= lim)]
    allr["cell"] = common.lonlat_to_cell(allr.lon.values, allr.lat.values)
    order = {"GBIF": 0, "iNaturalist needs_id": 2}
    allr["rank"] = allr.source.map(lambda s: order.get(s, 1))
    one = allr.sort_values(["rank", "year"], ascending=[True, False]).drop_duplicates("cell")
    one.drop(columns="rank").to_parquet(f"{ROOT}/occ/occurrences_merged.parquet", index=False)
    summary = {"retrieved_utc": pd.Timestamp.now("UTC").isoformat(timespec="seconds"),
               "inaturalist_needs_id_records": len(ina), "literature_files": lit_counts,
               "cells_by_source": one.source.value_counts().to_dict(), "cells_total": len(one),
               "gbif_only_cells": int((one.source == "GBIF").sum())}
    json.dump(summary, open("results/occurrences_merged_summary.json", "w"), indent=1, default=str)
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
