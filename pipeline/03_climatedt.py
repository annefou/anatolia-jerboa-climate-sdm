"""Monthly 2 m temperature and precipitation from the DestinE Climate DT generation 2 on the study cells,
read with healpix-connector v0.2.0 (doi:10.5281/zenodo.23603498), ``sources.climatedt_monthly``.

The connector requests the monthly stream ("clmn", resolution "high" = HEALPix depth 10 on the sphere)
by numeric parameter id (avg_2t 228004, avg_tprate 235055), checks every returned message, and resamples
sphere -> WGS84 with healpix-resample bilinear in conservative mode (``resampling.BilinearConservative``);
hist 1990-2014 then SSP3-7.0. Ids are never matched between the sphere and the ellipsoid.
Years written before the switch to the connector (same method, own script) were compared with the
connector for 2015 (IFS-FESOM): identical to the last digit (difference 0.0 on 1.9 million cell-months).
Access: DestinE upgraded access, credential read by polytope-client from ~/.polytopeapirc (never copied here).
Licence: DestinE Terms and Conditions; raw extracts are not redistributed (work/ is git-ignored), only derived
statistics are published: "This data is created based on data of the European Union, using the Destination
Earth Platform, but has been modified."

Usage: python pipeline/03_climatedt.py <ROOT> <MODEL> [<Y0> <Y1>]
Writes <ROOT>/dt/<MODEL>/<year>.npz with t2m (degC) and pr (mm per month), arrays (12, ncells) in the order
of <ROOT>/clim/cells.parquet, float32, plus <year>.request.json.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from healpix_connector.sources.climatedt_monthly import MonthlyStreamSampler

ROOT, MODEL = sys.argv[1], sys.argv[2]
Y0, Y1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1991, 2040)
OUT = f"{ROOT}/dt/{MODEL}"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    cells = pd.read_parquet(f"{ROOT}/clim/cells.parquet").cell.values.astype(np.uint64)
    order = np.argsort(cells)
    inv = np.empty_like(order)
    inv[order] = np.arange(len(order))               # connector cells are sorted; back to the table's order
    sampler = MonthlyStreamSampler(cells, ["avg_2t", "avg_tprate"], model=MODEL, resolution="high",
                                   local_dir=f"{OUT}/grib")
    for year in range(Y0, Y1 + 1):
        fn = f"{OUT}/{year}.npz"
        if os.path.exists(fn):
            continue
        t0 = time.time()
        try:
            y = sampler.year(year)
        except RuntimeError as e:
            print("FAIL", MODEL, year, str(e)[:300], flush=True)
            continue
        np.savez_compressed(fn, t2m=y.values["avg_2t"][:, inv].astype(np.float32),
                            pr=y.values["avg_tprate"][:, inv].astype(np.float32))
        json.dump({"connector": "healpix-connector 0.2.0", "method": y.method, "depth": y.depth,
                   "requests": y.requests, "seconds": round(time.time() - t0)},
                  open(fn.replace(".npz", ".request.json"), "w"))
        print("OK", MODEL, year, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
