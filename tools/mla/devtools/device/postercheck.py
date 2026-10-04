#!/usr/bin/env python3
"""Stale-poster check for a Channel Selection recording (receiver grab loop, 1280x720 JPEG, name = ns timestamp).

usage: postercheck.py <slow_dir> <fast_dir> [--design posterlist]

slow_dir: the cursor stops >= 3 s on every row -> the settled frame before each move is the reference of that row
          (cursor y -> now/next poster crops).
fast_dir: fast navigation over the same rows.  Every frame: cursor row (highlight bar) and the now/next poster crops
          are matched against all row references.  A frame is STALE when its poster matches the reference of a
          DIFFERENT row (better than the own row's reference by a clear margin) although the cursor has already been
          on its row for >= HOLD seconds.  Frames inside HOLD after a move are counted separately as 'transition'.
"""
import os, sys
from PIL import Image, ImageChops, ImageStat

BOXES = {"posterlist": {"list": (300, 560, 70, 560), "now": (691, 180, 835, 404), "next": (689, 450, 783, 598),
	"row0": 90, "row_h": 40}}  # 1280x720: list rows are 40 px (60 px at 1920); row k centre = 90 + 40 k
BAR = (48, 50, 63)
HOLD = 0.5


def frames(d):
    return sorted((int(x[:-4]), os.path.join(d, x)) for x in os.listdir(d) if x.endswith(".jpg"))


def cursor(im, box):
    lx0, lx1, ly0, ly1 = box
    rows = []
    for y in range(ly0, ly1, 2):
        px = sorted(im.getpixel((x, y)) for x in range(lx0, lx1, 6))
        m = px[len(px) // 2]
        rows.append(all(abs(m[i] - BAR[i]) <= 14 for i in range(3)))
    best, run, start, bs = 0, 0, 0, None
    for i, r in enumerate(rows + [False]):
        if r:
            if not run:
                start = i
            run += 1
        else:
            if run > best:
                best, bs = run, start
            run = 0
    return None if best < 4 else ly0 + 2 * (bs + best // 2)


def diff(a, b):
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]


def crops(im, b):
    g = im.convert("L")
    return g.crop(b["now"]), g.crop(b["next"])


def main():
    slow, fast = sys.argv[1], sys.argv[2]
    b = BOXES["posterlist"]

    def row(im):
        c = cursor(im, b["list"])
        if c is None:
            return None
        k = int(round((c - b["row0"]) / float(b["row_h"])))
        return k if abs(b["row0"] + k * b["row_h"] - c) <= b["row_h"] // 2 else None

    # references: in the slow pass the cursor rests >= 3 s on every row; the last frame on a row is its reference
    last = {}
    for t, p in frames(slow):
        im = Image.open(p).convert("RGB")
        k = row(im)
        if k is not None:
            last[k] = crops(im, b)
    rows = sorted(last)
    print("reference rows: %s" % rows)
    distinct = [k for k in rows if all(diff(last[k][0], last[j][0]) + diff(last[k][1], last[j][1]) > 12 for j in rows if j != k)]
    print("rows with distinct posters (others share the neutral frame): %s" % distinct)

    stale = trans = ok = unknown = other_row = 0
    since = None; cur = None; t0 = None; events = []; longest = 0.0; tstart = None
    for t, p in frames(fast):
        t0 = t0 or t
        im = Image.open(p).convert("RGB")
        r = row(im)
        if r is None or r not in last:
            unknown += 1
            continue
        if r != cur:
            cur, since = r, t
        n, x = crops(im, b)
        d = {k: diff(n, last[k][0]) + diff(x, last[k][1]) for k in rows}
        best = min(d, key=d.get)
        wrong = best != r and best in distinct and d[best] + 6.0 < d[r]
        held = (t - since) / 1e9
        if wrong:
            longest = max(longest, held)
        if wrong and held >= HOLD:
            stale += 1
            events.append("%.2fs cursor row %d (held %.2fs) shows row %d posters (own %.1f, other %.1f)" % ((t - t0) / 1e9, r, held, best, d[r], d[best]))
        elif wrong:
            trans += 1
        else:
            ok += 1
    for e in events[:20]:
        print("  STALE " + e)
    print("POSTER_SUMMARY rows=%d distinct=%d frames_ok=%d transition(<%.1fs after a move)=%d stale=%d no_cursor=%d longest_previous_poster=%.2fs" % (len(rows), len(distinct), ok, HOLD, trans, stale, unknown, longest))


if __name__ == "__main__":
    main()
