#!/usr/bin/env python3
# Detects the "blank band" defect: inside the EventView description boxes (95..575 / 950..1530, y 245..506,
# narrow variant) find text rows; flag frames where the first text row starts > 1 line (29 px) below the box
# top while text continues below (i.e. empty band above visible text that is not the swim's natural end).
import sys, glob, os
from PIL import Image
def rows(im, x0, x1, y0, y1):
    g = im.convert("L").crop((x0, y0, x1, y1)); w, h = g.size; px = g.load()
    return [y for y in range(h) if sum(1 for x in range(0, w, 2) if px[x, y] > 170) > 3]
bad = 0; n = 0
for f in sorted(glob.glob(sys.argv[1] + "/*.png")):
    im = Image.open(f); n += 1
    for name, (x0, x1) in (("left", (95, 575)), ("right", (950, 1530))):
        r = rows(im, x0, x1, 245, 506)
        if not r: continue
        top, bottom = r[0], r[-1]
        if top > 40 and bottom > 200:
            bad += 1; print("BAND? %s %s first-text-row=%d last=%d" % (os.path.basename(f), name, top, bottom))
print("frames=%d suspicious=%d" % (n, bad))
