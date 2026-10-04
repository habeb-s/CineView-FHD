#!/usr/bin/env python3
# Analyse an fbrec.py recording on ai-agent: animated GIF (real timing) + motion metrics.
# usage: fbana.py <rec file> <out.gif> [label]
import struct, sys
from PIL import Image
import numpy as np
src, gif = sys.argv[1], sys.argv[2]
label = sys.argv[3] if len(sys.argv) > 3 else src
d = open(src, "rb").read()
assert d[:6] == b"FBREC1"
w, h, n = struct.unpack("<III", d[6:18])
ts = struct.unpack("<%dd" % n, d[18:18 + 8 * n])
off = 18 + 8 * n
fr = [np.frombuffer(d[off + i * w * h * 3: off + (i + 1) * w * h * 3], dtype=np.uint8).reshape(h, w, 3) for i in range(n)]
# text profile per row (bright pixels = text)
prof = [((f.max(axis=2) >= 0xC0).sum(axis=1)).astype(float) for f in fr]
shifts, changes, blanks = [], [], 0
med_top = np.median([p[: h // 3].sum() for p in prof])
for i in range(1, n):
    a, b = prof[i - 1], prof[i]
    if np.abs(a - b).sum() < 0.002 * w * h:
        continue
    best, bs = None, 0
    for s in range(-40, 41):  # +s: text moved up by s px (b[y] == a[y+s]); -s: moved down
        e = (np.abs(a[s:] - b[: h - s]).sum() / (h - s)) if s >= 0 else (np.abs(a[: h + s] - b[-s:]).sum() / (h + s))
        if best is None or e < best:
            best, bs = e, s
    changes.append(ts[i]); shifts.append(bs)
for p in prof:
    if p[: h // 3].sum() < 0.5 * med_top:
        blanks += 1
iv = np.diff(changes) if len(changes) > 1 else np.array([0.0])
mv = [abs(s) for s in shifts if s != 0]
hist = {"1-5": sum(1 for s in mv if s <= 5), "6-20": sum(1 for s in mv if 5 < s <= 20), "21-40": sum(1 for s in mv if s > 20)}
dur = ts[-1] - ts[0]
print("%s: %d frames %.1f fps | content changes %d (%.2f/s) | interval median %.2f s | shift per change median %s px, max %s px | net movement %d px = %.1f px/s | frames with blank top third %d" % (
    label, n, n / max(dur, 1e-3), len(changes), len(changes) / max(dur, 1e-3), float(np.median(iv)),
    int(np.median(mv)) if mv else 0, max(mv) if mv else 0, sum(mv), sum(mv) / max(dur, 1e-3), blanks) + " | shift histogram " + str(hist))
ims = [Image.fromarray(f) for f in fr]
durs = [int(round((ts[i + 1] - ts[i]) * 1000)) for i in range(n - 1)] + [100]
ims[0].save(gif, save_all=True, append_images=ims[1:], duration=durs, loop=0, optimize=False)
