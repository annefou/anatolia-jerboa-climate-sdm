"""Localities of the Scarturus williamsi specimens sequenced by Olgun Karacan et al. 2024 (J. Zool. Syst. Evol. Res.,
doi:10.1155/jzs/8123686), from their GenBank records (cytochrome b, MG255325-MG255411 and PQ064096-PQ064104, as
listed in the paper), geocoded with OpenStreetMap Nominatim.

The paper's own coordinates are in its Table S1 (not retrieved). GenBank gives "Turkey: <village or district>,
<province>" per specimen voucher. Names joining two places ("A/B": a sequence shared by specimens from both) and
province-only names (Elazig, Konya) are left out. Each name is geocoded once (Nominatim, 1 request per second,
country tr); the uncertainty follows the kind of place found: village, hamlet, town or suburb 5 km; district or
other administrative area 15 km. The geocoded table must be checked by eye after any change (printed at the end).

Usage: python pipeline/digitise/genbank_localities.py inputs/literature_genbank/olgunkaracan2024_genbank_localities.csv
"""
import collections
import re
import sys
import time

import requests

OUT = sys.argv[1]
IDS = [f"MG{n}" for n in range(255325, 255412)] + [f"PQ{n:06d}" for n in range(64096, 64105)]
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = {"User-Agent": "LifeWatch-ERIC anatolia-jerboa-climate-sdm (research; contact via LifeWatch ERIC)"}
# Checked by eye (2026-10-23): names the geocoder resolves wrongly, and a misspelling in GenBank.
QUERY = {"Akdag, Yozgat": "Akdağmadeni, Yozgat",     # the district; the plain query returned Çayıralan
         "Aralik, Igdir": "Aralık, Iğdır"}            # the plain query returned the Iğdır plain
ALIAS = {"Goksekisik, Eskisehir": "Gokcekisik, Eskisehir"}
# Not found and left out: "Buyuksala, Kutahya".
FINE = {"village", "hamlet", "town", "suburb", "neighbourhood", "quarter", "isolated_dwelling", "locality"}


def genbank():
    r = requests.get(EFETCH, params={"db": "nuccore", "id": ",".join(IDS), "rettype": "gb", "retmode": "text"},
                     timeout=120)
    r.raise_for_status()
    loc = collections.defaultdict(list)
    for rec in r.text.split("\n//"):
        acc = re.search(r"^ACCESSION\s+(\S+)", rec, re.M)
        org = re.search(r'/organism="([^"]+)"', rec)
        geo = re.search(r'/geo_loc_name="([^"]+)"', rec, re.S)
        vou = re.search(r'/specimen_voucher="([^"]+)"', rec)
        if not (acc and org and geo) or org.group(1) != "Scarturus williamsi":
            continue
        name = " ".join(geo.group(1).split()).replace("Turkey: ", "")
        if "/" in name or "," not in name:
            continue
        name = ALIAS.get(name, name)
        loc[name].append(f"{acc.group(1)}:{vou.group(1) if vou else ''}")
    return loc


def geocode(name):
    r = requests.get(NOMINATIM, params={"q": QUERY.get(name, name), "countrycodes": "tr", "format": "jsonv2",
                                         "limit": 1, "addressdetails": 1}, headers=UA, timeout=60)
    r.raise_for_status()
    time.sleep(1.1)
    if not r.json():
        return None
    h = r.json()[0]
    return float(h["lon"]), float(h["lat"]), h.get("addresstype") or h.get("type"), h.get("display_name", "")


def main():
    loc = genbank()
    rows = []
    for name, vouchers in sorted(loc.items()):
        g = geocode(name)
        if g is None:
            print("NOT FOUND", name)
            continue
        lon, lat, kind, disp = g
        unc = 5000 if kind in FINE else 15000
        rows.append((name, lon, lat, unc, kind, disp, vouchers))
    with open(OUT, "w") as f:
        f.write("source,locality,lon,lat,uncertainty_m,year,voucher\n")
        for name, lon, lat, unc, kind, disp, vouchers in rows:
            f.write(f"OlgunKaracan2024_GenBank,\"{name}\",{lon:.4f},{lat:.4f},{unc},,\"{' '.join(vouchers)}\"\n")
    for name, lon, lat, unc, kind, disp, vouchers in rows:
        print(f"{name:28s} {lon:8.3f} {lat:7.3f} {unc:6d} {kind:14s} n={len(vouchers):2d}  {disp[:70]}")
    print(len(rows), "localities")


if __name__ == "__main__":
    main()
