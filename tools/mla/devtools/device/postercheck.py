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

    # Second method, independent of the slow pass (posters may finish downloading between passes):
    # split the fast recording into segments with a constant cursor row; a frame >= HOLD into a segment is STALE
    # when its posters equal the FINAL posters of the PREVIOUS segment (another channel) but not its own final ones.
    segs = []
    for t, p in frames(fast):
        im = Image.open(p).convert("RGB")
        r = row(im)
        if r is None:
            continue
        if not segs or segs[-1][0] != r:
            segs.append([r, []])
        segs[-1][1].append((t, crops(im, b)))
    t0 = segs[0][1][0][0] if segs else 0
    stale = trans = ok = 0
    events = []
    for i in range(1, len(segs)):
        r, fr = segs[i]
        own = fr[-1][1]
        prev = segs[i - 1][1][-1][1]
        if diff(own[0], prev[0]) + diff(own[1], prev[1]) < 12:
            ok += len(fr)  # both channels show the same posters (e.g. the neutral frame): nothing to tell apart
            continue
        for t, c in fr:
            held = (t - fr[0][0]) / 1e9
            dp = diff(c[0], prev[0]) + diff(c[1], prev[1])
            do = diff(c[0], own[0]) + diff(c[1], own[1])
            if dp < 8 and do > 20:
                if held >= HOLD:
                    stale += 1
                    events.append("%.2fs row %d held %.2fs still shows row %d posters" % ((t - t0) / 1e9, r, held, segs[i - 1][0]))
                else:
                    trans += 1
            else:
                ok += 1
    for e in events[:20]:
        print("  STALE " + e)
    print("POSTER_SUMMARY segments=%d frames_ok=%d previous_channel_posters_within_%.1fs=%d stale=%d" % (len(segs), ok, HOLD, trans, stale))


if __name__ == "__main__":
    main()
