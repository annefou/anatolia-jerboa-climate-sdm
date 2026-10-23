"""Digitised occurrence localities of Helvaci & Colak 2025, Figure 1A (map of the localities used for
modelling: circles = genetic + modelling data, squares = modelling data only).

Input: the figure as distributed by Europe PMC (PMC12467805, biology-14-01184-g001.jpg, 742 x 414 px; CC BY 4.0).
Method: symbol centres read by eye on a 4x nearest-neighbour enlargement of panel A (coordinates below, in
4x pixels), then converted with the map's calibration (equirectangular): latitude ticks 42/40/38/36/34/32 N at
y = 15.5/48/80.5/112.5/145.3/177.8 px of the original (16.2 px per degree), longitude labels 30/40/50 E centred
at x = 99/232/362 px (13.15 px per degree). Checks: centre of Cyprus (33.2 E, 35.1 N) and the Lebanese
locality (Aarsal, 36.41 E, 34.18 N) fall within ~3 px. One original pixel is ~0.075 deg; with the reading error
every point gets an uncertainty of 15 km. Touching symbols are read as separate points; symbols hidden under
others cannot be recovered. An automatic detection was tried first and missed or merged points (35 and 9
points found on two settings), so it was replaced by this reading.
The overlay written by this script must be checked by eye after any change.

Usage: python pipeline/digitise/fetch_figure.py work/fig
       python pipeline/digitise/fig1_points.py work/fig/biology-14-01184-g001.jpg \
              inputs/literature/helvaci2025_fig1A_digitised.csv figures/helvaci2025_fig1A_digitised_overlay.png
"""
import sys

from PIL import Image, ImageDraw

FIG, OUT, OVL = sys.argv[1:4]
X0, PX_LON = 99.0, 13.15          # x of 30 E, px per degree (original pixels)
Y42, PX_LAT = 15.5, 16.2          # y of 42 N, px per degree
# (x4, y4, region as coloured in the figure, symbol)
POINTS = [
    (337, 250, "Aegean", "circle"), (351, 263, "Aegean", "circle"), (390, 327, "Aegean", "circle"),
    (428, 262, "Aegean", "circle"), (419, 229, "Central", "circle"), (428, 208, "Central", "circle"),
    (439, 205, "Central", "circle"), (458, 220, "Central", "circle"), (486, 222, "Central", "circle"),
    (507, 178, "Central", "circle"), (553, 201, "Central", "circle"), (566, 215, "Central", "circle"),
    (578, 215, "Central", "square"), (599, 180, "Central", "square"), (597, 209, "Central", "square"),
    (590, 222, "Central", "square"), (566, 246, "Central", "circle"), (572, 281, "Central", "circle"),
    (622, 243, "Central", "circle"), (645, 250, "Central", "circle"), (665, 255, "Central", "circle"),
    (645, 271, "Central", "circle"), (625, 288, "Central", "circle"), (708, 262, "Central", "circle"),
    (711, 210, "Central", "circle"), (728, 236, "Central", "circle"), (696, 150, "BlackSea", "circle"),
    (616, 123, "BlackSea", "square"), (493, 333, "Central", "circle"), (540, 322, "Central", "circle"),
    (548, 315, "Central", "circle"), (552, 345, "Central", "circle"), (571, 362, "Central", "circle"),
    (645, 328, "Central", "circle"), (793, 281, "Eastern", "circle"), (880, 274, "Eastern", "circle"),
    (941, 201, "Eastern", "circle"), (1036, 184, "Eastern", "circle"), (1100, 274, "Eastern", "circle"),
    (1125, 162, "Eastern", "square"), (1143, 200, "Eastern", "circle"), (1156, 196, "Eastern", "circle"),
    (1286, 288, "Azerbaijan", "circle"), (1349, 300, "Iran", "circle"), (1183, 347, "Azerbaijan", "circle"),
    (1356, 390, "Iran", "circle"), (1365, 405, "Iran", "circle"), (1378, 418, "Iran", "circle"),
    (1362, 524, "Iran", "circle"), (1388, 522, "Iran", "circle"), (1253, 600, "Iran", "circle"),
    (1465, 697, "Iran", "circle"), (740, 566, "Lebanon", "square"),
]


def main():
    with open(OUT, "w") as f:
        f.write("source,locality,lon,lat,uncertainty_m,year,voucher\n")
        for j, (x4, y4, region, sym) in enumerate(POINTS):
            lon = 30 + (x4 / 4 - X0) / PX_LON
            lat = 42 - (y4 / 4 - Y42) / PX_LAT
            f.write(f"Helvaci&Colak2025_Fig1A_digitised,{region}_{sym}_{j:02d},{lon:.3f},{lat:.3f},15000,,pt{j:02d}\n")
    im = Image.open(FIG).convert("RGB").crop((0, 0, 378, 196)).resize((1512, 784), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for j, (x4, y4, _, _) in enumerate(POINTS):
        d.ellipse((x4 - 4, y4 - 4, x4 + 4, y4 + 4), fill=(255, 0, 255))
        d.text((x4 + 8, y4 - 16), str(j), fill=(0, 0, 0))
    im.save(OVL)
    print(len(POINTS), "points")


if __name__ == "__main__":
    main()
