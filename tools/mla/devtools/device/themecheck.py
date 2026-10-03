#!/usr/bin/env python3
# For every theme sweep screenshot (OSD layer only), measure how much of the drawn UI still carries the
# NAVY hue (h 200-230 deg, s > .35, l .04-.40) and the theme's own hue.  Navy is the reference.
import sys, os, glob, colorsys
from PIL import Image
HUE = {"navy": 213, "purple": 271, "burgundy": 341, "green": 155, "graphite": 213, "black": None}
base = sys.argv[1]
themes = [t for t in ("navy", "black", "graphite", "burgundy", "green", "purple") if os.path.isdir(os.path.join(base, t))]
screens = sorted({os.path.basename(f)[:-8] for f in glob.glob(os.path.join(base, "navy", "*_osd.png"))})
def stats(p):
    im = Image.open(p).convert("RGBA"); im.thumbnail((480, 270)); nav = own = tot = 0
    for r, g, b, a in im.getdata():
        if a < 200: continue
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s < 0.35 or not (0.04 < l < 0.40): tot += 1; continue
        tot += 1; hd = h * 360
        if 200 <= hd <= 230: nav += 1
    return (100.0 * nav / tot) if tot else 0.0, tot
print("%-16s" % "screen" + "".join("%10s" % t for t in themes))
flag = []
for s in screens:
    row = []
    for t in themes:
        p = os.path.join(base, t, s + "_osd.png")
        if not os.path.exists(p): row.append("   -"); continue
        v, tot = stats(p); row.append("%9.2f%%" % v)
        if t not in ("navy", "graphite") and v > 1.0: flag.append((t, s, round(v, 2)))
    print("%-16s" % s + "".join("%10s" % x for x in row))
print("navy-hue residue > 1%% in non-navy themes: %s" % (flag or "none"))
