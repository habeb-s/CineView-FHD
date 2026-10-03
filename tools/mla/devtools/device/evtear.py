#!/usr/bin/env python3
# Per frame: text-line starts inside both EventView description boxes (Classic narrow variant, y 245..506).
# Prints the first visible line and the line pitch pattern so a persistent shift (real defect) can be told
# apart from a random top-blank tear (framebuffer read racing a redraw).
import sys, glob, os
from PIL import Image
def starts(im, x0, x1, y0=245, y1=506):
    g = im.convert("L").crop((x0, y0, x1, y1)); w, h = g.size; px = g.load(); on = False; out = []
    for y in range(h):
        n = sum(1 for x in range(0, w, 2) if px[x, y] > 170)
        if n > 3 and not on: out.append(y); on = True
        elif n <= 1 and on: on = False
    return out
band = 0
for f in sorted(glob.glob(sys.argv[1] + "/*.png")):
    im = Image.open(f); row = []
    for name, (x0, x1) in (("L", (95, 575)), ("R", (950, 1530))):
        s = starts(im, x0, x1)
        flag = bool(s) and s[0] > 40 and s[-1] > 200
        band += flag
        row.append("%s first=%s n=%d%s" % (name, s[0] if s else "-", len(s), " BAND" if flag else ""))
    print(os.path.basename(f), " | ".join(row))
print("band boxes:", band)
