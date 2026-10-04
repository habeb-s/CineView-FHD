#!/usr/bin/env python3
# Line-jump recording check: after every move, the settled frame must equal the previous settled frame
# shifted by a whole number of lines (+-29 / +-58 px, up or down) on the overlapping rows.
# A wrong repaint (stale or doubled text) leaves differing pixels in every candidate shift -> "BAD".
# 2026-10-05: a move that lands exactly on the FIRST settled frame (the text's first line, start of the recording)
# is a restart-to-top (CineViewMLALineText at the end of a long text) -> "restart ok"; still pixel-exact.
# usage: jumpcheck.py <rec.bin> [pitch]
import struct, sys
import numpy as np
src = sys.argv[1]; P = int(sys.argv[2]) if len(sys.argv) > 2 else 29
d = open(src, "rb").read(); w, h, n = struct.unpack("<III", d[6:18]); ts = struct.unpack("<%dd" % n, d[18:18 + 8 * n]); off = 18 + 8 * n
fr = [np.frombuffer(d[off + i * w * h * 3: off + (i + 1) * w * h * 3], dtype=np.uint8).reshape(h, w, 3).astype(np.int16) for i in range(n)]
bright = [(f.max(axis=2) >= 0xC0) for f in fr]
segs, s = [], 0
for i in range(1, n + 1):
    if i == n or np.abs(fr[i] - fr[i - 1]).max() > 40:
        if i - s >= 2: segs.append((s, i - 1))
        s = i
bad = restarts = 0
TOP = bright[segs[0][1]] if segs else None
for (a0, a1), (b0, b1) in zip(segs, segs[1:]):
    A, B = bright[a1], bright[b0]
    res = {}
    for sh in (P, -P, 2 * P, -2 * P, 3 * P, -3 * P, 4 * P, -4 * P):  # several steps can fall into one recording gap
        res[sh] = int((A[sh:] != B[:h - sh]).sum()) if sh > 0 else int((A[:h + sh] != B[-sh:]).sum())
    best = min(res, key=res.get)
    ok = res[best] <= 300
    note = ""
    if not ok and TOP is not None and int((B != TOP).sum()) <= 300:
        ok, note = True, " restart-to-top"
        restarts += 1
    bad += not ok
    rows = np.where(((A[best:] != B[:h - best]) if best > 0 else (A[:h + best] != B[-best:])).sum(axis=1) > 25)[0]
    print("move %3d->%3d t=%5.1fs shift=%+d residual=%5d %s%s%s" % (a1, b0, ts[b0] - ts[0], best, res[best], "ok" if ok else "BAD", note, "" if ok else " rows %d-%d" % (rows.min(), rows.max()) if len(rows) else ""))
print("SUMMARY moves=%d bad=%d restarts=%d" % (len(segs) - 1, bad, restarts))
