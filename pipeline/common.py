"""Shared grid helpers: HEALPix cells over the study area (healpix-geo, WGS84 ellipsoid, NESTED) and
conservative (area-weighted) aggregation of lat/lon rasters onto them.

No science choices here, only grid bookkeeping. No point-spread / Gaussian kernel is used anywhere.
"""
from __future__ import annotations

import numpy as np
import shapely
import healpix_geo.nested as hn

DEPTH = 10                       # ~6.4 km cells (41 km2 each on the WGS84 ellipsoid)
ELLIPSOID = "WGS84"
# Study extent of Helvaci & Colak 2025 (section 2.1): 25-73 E, 27-42 N
EXTENT = (25.0, 27.0, 73.0, 42.0)
WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563


def authalic_radius(a: float = WGS84_A, f: float = WGS84_F) -> float:
    """Radius of the sphere with the same surface area as the ellipsoid (healpix-geo's equal-area basis)."""
    e2 = f * (2 - f)
    e = np.sqrt(e2)
    q_p = 1 + (1 - e2) / (2 * e) * np.log((1 + e) / (1 - e))
    return float(a * np.sqrt(q_p / 2))


def cell_area_km2(depth: int = DEPTH) -> float:
    return float(4 * np.pi * authalic_radius() ** 2 / (12 * 4 ** depth)) / 1e6


def extent_cells(extent=EXTENT, depth: int = DEPTH, step: int = 4):
    """Cells whose whole polygon lies inside the lon/lat extent.

    Returns sorted ids (uint64), cell-centre lon/lat and the cell polygons as (N, 4*step, 2) lon/lat vertices.
    """
    x0, y0, x1, y1 = extent
    ring = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    ids, _, _ = hn.polygon_coverage(ring, depth, ellipsoid=ELLIPSOID, flat=True)
    ids = np.unique(np.asarray(ids, np.uint64))
    vlon, vlat = hn.vertices(ids, depth, ellipsoid=ELLIPSOID, step=step)
    inside = (vlon > x0).all(1) & (vlon < x1).all(1) & (vlat > y0).all(1) & (vlat < y1).all(1)
    ids, vlon, vlat = ids[inside], vlon[inside], vlat[inside]
    clon, clat = hn.healpix_to_lonlat(ids, depth, ellipsoid=ELLIPSOID)
    return ids, np.asarray(clon), np.asarray(clat), np.stack([vlon, vlat], -1)


def grid_weights(polys: np.ndarray, x0: float, ytop: float, res: float, W: int, H: int):
    """Exact area-overlap weights between cell polygons (N, k, 2) and a north-up lon/lat grid.

    Column c spans [x0 + c*res, x0 + (c+1)*res], row r spans [ytop - (r+1)*res, ytop - r*res].
    Returns (cell_index, pixel_flat_index, w) with w = area(cell & pixel) / area(cell), summing to 1 per cell.
    Areas are computed in lon/lat; over one ~6 km cell cos(latitude) changes by < 0.1 %, so these area
    fractions equal ellipsoidal area fractions to that precision.
    """
    N = len(polys)
    xmin, xmax = polys[..., 0].min(1), polys[..., 0].max(1)
    ymin, ymax = polys[..., 1].min(1), polys[..., 1].max(1)
    c0 = np.floor((xmin - x0) / res).astype(np.int64)
    c1 = np.floor((xmax - x0) / res).astype(np.int64)
    r0 = np.floor((ytop - ymax) / res).astype(np.int64)
    r1 = np.floor((ytop - ymin) / res).astype(np.int64)
    assert c0.min() >= 0 and r0.min() >= 0 and c1.max() < W and r1.max() < H, "cells outside the grid"
    nc, nr = c1 - c0 + 1, r1 - r0 + 1
    geoms = shapely.polygons(polys)
    area = shapely.area(geoms)
    out_i, out_p, out_w = [], [], []
    for dr in range(int(nr.max())):
        for dc in range(int(nc.max())):
            k = np.flatnonzero((dr < nr) & (dc < nc))
            rr, cc = r0[k] + dr, c0[k] + dc
            boxes = shapely.box(x0 + cc * res, ytop - (rr + 1) * res, x0 + (cc + 1) * res, ytop - rr * res)
            a = shapely.area(shapely.intersection(geoms[k], boxes)) / area[k]
            keep = a > 0
            out_i.append(k[keep]); out_p.append((rr * W + cc)[keep]); out_w.append(a[keep])
    ci, pi, w = np.concatenate(out_i), np.concatenate(out_p), np.concatenate(out_w)
    tot = np.bincount(ci, w, minlength=N)
    assert np.allclose(tot, 1, atol=1e-6), f"weights do not sum to 1 (min {tot.min()}, max {tot.max()})"
    return ci, pi, w


def conservative_mean(ci, pi, w, values_flat, ncells):
    """Area-weighted mean of the valid native pixels inside each cell. Returns (mean, valid_area_fraction)."""
    v = values_flat[pi].astype(np.float64)
    ok = np.isfinite(v)
    ww = np.where(ok, w, 0.0)
    num = np.bincount(ci, ww * np.where(ok, v, 0.0), minlength=ncells)
    den = np.bincount(ci, ww, minlength=ncells)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(den > 0, num / den, np.nan)
    return mean, den


def sphere_to_wgs84_weights(polys: np.ndarray, src_depth: int, clon=None, clat=None):
    """Exact area-overlap weights from a spherical HEALPix grid (Climate DT as delivered) onto WGS84 cells.

    The Climate DT grid is HEALPix on the sphere: its cell polygons, taken as geodetic lon/lat, are offset from
    the WGS84 (authalic) cells with the same index by ~0.1 deg of latitude here, so ids are never matched.
    Candidates: the spherical cell containing each target cell's centre and its ring-1 neighbours (source and
    target cells have the same size, so the ring covers the whole target polygon). The weight is
    area(target & source) / area(target), computed in lon/lat (see grid_weights for precision).
    Returns (cell_index, source_cell_id, w).
    """
    N = len(polys)
    if clon is None:
        clon, clat = polys[..., 0].mean(1), polys[..., 1].mean(1)
    c = np.asarray(hn.lonlat_to_healpix(np.asarray(clon, float), np.asarray(clat, float), np.uint8(src_depth),
                                        ellipsoid="sphere"), np.uint64)
    nb = np.asarray(hn.kth_neighbourhood(c, src_depth, 1), np.uint64)
    tgt = np.repeat(np.arange(N), nb.shape[1])
    src = nb.ravel()
    ok = src < np.uint64(12 * 4 ** src_depth)
    ti, si = tgt[ok], src[ok]
    us, inv = np.unique(si, return_inverse=True)
    vlon, vlat = hn.vertices(us, src_depth, ellipsoid="sphere", step=4)
    spoly = shapely.polygons(np.stack([vlon, vlat], -1))
    tpoly = shapely.polygons(polys)
    w = shapely.area(shapely.intersection(tpoly[ti], spoly[inv])) / shapely.area(tpoly)[ti]
    keep = w > 0
    ti, si, w = ti[keep], si[keep], w[keep]
    tot = np.bincount(ti, w, minlength=N)
    assert tot.min() > 0.9999 and tot.max() < 1.0001, f"sphere->WGS84 weights do not sum to 1 ({tot.min()}, {tot.max()})"
    return ti, si, w / tot[ti]


def lonlat_to_cell(lon, lat, depth: int = DEPTH):
    return np.asarray(hn.lonlat_to_healpix(np.asarray(lon, float), np.asarray(lat, float),
                                           np.uint8(depth), ellipsoid=ELLIPSOID), np.uint64)


class BilinearToCells:
    """healpix-resample BilinearResampler in conservative mode, from source samples onto the study cells.

    Source samples are pixel or cell centres in geodetic lon/lat (a lon/lat grid, or Climate DT's spherical
    HEALPix centres), `area` their footprint (cos(lat) for a lon/lat grid, 1 for equal-area cells). Target:
    healpix-geo WGS84 cells at DEPTH. The conservative mode returns sum(value * area) per cell, so an intensive
    field's mean is resample(value) / resample(valid ones). Chosen after pipeline/90_compare_resamplers.py:
    mean |difference| from the exact area overlap < 0.1 (degC or mm), regional means preserved, all cells filled.
    """

    def __init__(self, lon, lat, area, cell_ids):
        from healpix_resample import BilinearResampler
        self.op = BilinearResampler(lon_deg=np.asarray(lon, float), lat_deg=np.asarray(lat, float), level=DEPTH,
                                    nest=True, ellipsoid=ELLIPSOID, verbose=False, area=np.asarray(area, float))
        self.cell_ids = np.asarray(cell_ids, np.uint64)

    def __call__(self, values) -> np.ndarray:
        v = np.asarray(values, float)
        num = self.op.resample(v, conservative=True)
        den = self.op.resample(np.where(np.isfinite(v), 1.0, np.nan), conservative=True)
        cid = np.asarray(num.cell_ids, np.uint64)
        with np.errstate(invalid="ignore", divide="ignore"):
            m = np.asarray(num.cell_data, float) / np.asarray(den.cell_data, float)
        out = np.full(len(self.cell_ids), np.nan)
        pos = np.searchsorted(self.cell_ids, cid)
        pos = np.clip(pos, 0, len(self.cell_ids) - 1)
        hit = self.cell_ids[pos] == cid
        out[pos[hit]] = m[hit]
        return out
