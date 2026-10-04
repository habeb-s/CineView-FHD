#!/usr/bin/env python3
# Info-panel latency after each cursor move in a Channel Selection recording (receiver grab loop, 1280x720 JPEG,
# file name = capture time in ns).  Cursor = y of the highlight bar in the list (median colour of a row strip);
# panel = change of the panel header crop (picon + channel name).  Boxes (1280x720) per design via argv:
#   lagcheck.py <dir> <list_x0,x1,y0,y1> <header_x0,y0,x1,y1> <bar_rgb r,g,b>
import os, sys
from PIL import Image, ImageChops, ImageStat
d = sys.argv[1]
lx0, lx1, ly0, ly1 = map(int, sys.argv[2].split(","))
hb = tuple(map(int, sys.argv[3].split(",")))
bar = tuple(map(int, sys.argv[4].split(",")))
fs = sorted((int(x[:-4]), x) for x in os.listdir(d) if x.endswith(".jpg"))
t0 = fs[0][0]
def cursor(im):
    rows = []
    for y in range(ly0, ly1, 2):
        px = sorted(im.getpixel((x, y)) for x in range(lx0, lx1, 6))
        m = px[len(px) // 2]
        rows.append(all(abs(m[i] - bar[i]) <= 12 for i in range(3)))
    best, run, start, bs = 0, 0, 0, None
    for i, r in enumerate(rows + [False]):
        if r:
            if not run: start = i
            run += 1
        else:
            if run > best: best, bs = run, start
            run = 0
    return None if best < 4 else ly0 + 2 * (bs + best // 2)
events = []; prevc = None; prevh = None; lastmove = None; lags = []; pending = None
for t, n in fs:
    im = Image.open(os.path.join(d, n)).convert("RGB")
    c = cursor(im); h = im.crop(hb).convert("L")
    hchg = prevh is not None and ImageStat.Stat(ImageChops.difference(h, prevh)).mean[0] > 2.0
    if c is not None and prevc is not None and abs(c - prevc) > 8:
        if pending is not None:
            print("  move @%.2fs: superseded by next move before the panel changed" % ((pending - t0) / 1e9))
        pending = t
        if hchg:
            lags.append(0.0); print("move @%.2fs cursor y %d->%d, panel same frame" % ((t - t0) / 1e9, prevc, c)); pending = None
        else:
            print("move @%.2fs cursor y %d->%d" % ((t - t0) / 1e9, prevc, c))
    elif hchg and pending is not None:
        lags.append((t - pending) / 1e9); print("   panel @%.2fs lag %.2fs" % ((t - t0) / 1e9, lags[-1])); pending = None
    if c is not None: prevc = c
    prevh = h
span = (fs[-1][0] - t0) / 1e9
print("frames=%d span=%.1fs fps=%.1f frame_step=%.2fs" % (len(fs), span, len(fs) / span, span / len(fs)))
if lags:
    s = sorted(lags)
    print("LAG_SUMMARY measured_moves=%d median=%.2fs p90=%.2fs max=%.2fs" % (len(s), s[len(s) // 2], s[int(len(s) * 0.9) - 1 if len(s) > 1 else 0], s[-1]))
