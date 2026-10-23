"""Download Figure 1 of Helvaci & Colak 2025 (Biology 14:1184, CC BY 4.0) from Europe PMC.

The supplementary archive of PMC12467805 contains the article's figures; Figure 1 is
biology-14-01184-g001.jpg (742 x 414 px). It is the input of pipeline/digitise/fig1_points.py.

Usage: python pipeline/digitise/fetch_figure.py <OUT_DIR>
"""
import io
import os
import sys
import time
import urllib.request
import zipfile

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12467805/supplementaryFiles"
NAME = "biology-14-01184-g001.jpg"


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for attempt in range(5):
        try:
            data = urllib.request.urlopen(URL, timeout=900).read()
            z = zipfile.ZipFile(io.BytesIO(data))
            break
        except (zipfile.BadZipFile, OSError):        # the archive sometimes arrives truncated
            time.sleep(30 * (attempt + 1))
    else:
        raise SystemExit("could not download the Europe PMC supplementary archive")
    open(os.path.join(out, NAME), "wb").write(z.read(NAME))
    print(os.path.join(out, NAME))


if __name__ == "__main__":
    main()
