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
    # references: settled frame (last before the cursor moves) per cursor position
    refs = []  # (cursor_y, now_crop, next_crop)
    prev = None
    fs = frames(slow)
    for i, (t, p) in enumerate(fs):
        im = Image.open(p).convert("RGB")
        c = cursor(im, b["list"])
        if c is None:
            continue
        if prev is not None and abs(c - prev[0]) > 8:
            refs.append((prev[0],) + prev[1])
        prev = (c, crops(im, b))
    if prev:
        refs.append((prev[0],) + prev[1])
    # one reference per row (keep the last settled one)
    by_y = {}
    for y, n, x in refs:
        key = int(round(y / 10.0))
        by_y[key] = (y, n, x)
    refs = sorted(by_y.values())
    print("references: %d rows at y=%s" % (len(refs), [r[0] for r in refs]))
    for i, (y, n, x) in enumerate(refs):
        others = [diff(n, r[1]) for j, r in enumerate(refs) if j != i]
        print("  row y=%d: min distance to another row's now-poster %.1f" % (y, min(others) if others else -1))

    def row_of(c):
        return min(range(len(refs)), key=lambda i: abs(refs[i][0] - c)) if c is not None else None

    stale = trans = ok = unknown = 0
    since = None; cur = None; t0 = None; events = []
    for t, p in frames(fast):
        t0 = t0 or t
        im = Image.open(p).convert("RGB")
        r = row_of(cursor(im, b["list"]))
        if r is None:
            unknown += 1
            continue
        if r != cur:
            cur, since = r, t
        n, x = crops(im, b)
        dn = [diff(n, ref[1]) for ref in refs]
        dx = [diff(x, ref[2]) for ref in refs]
        own = dn[r] + dx[r]
        best = min(range(len(refs)), key=lambda i: dn[i] + dx[i])
        wrong = best != r and (dn[best] + dx[best]) + 6.0 < own
        held = (t - since) / 1e9
        if wrong and held >= HOLD:
            stale += 1
            events.append("%.2fs cursor row %d (held %.2fs) shows row %d posters (own %.1f, other %.1f)" % ((t - t0) / 1e9, r, held, best, own, dn[best] + dx[best]))
        elif wrong:
            trans += 1
        else:
            ok += 1
    for e in events[:20]:
        print("  STALE " + e)
    print("POSTER_SUMMARY frames_ok=%d transition(<%.1fs after a move)=%d stale=%d no_cursor=%d" % (ok, HOLD, trans, stale, unknown))


if __name__ == "__main__":
    main()
