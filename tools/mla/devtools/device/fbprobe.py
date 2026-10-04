#!/usr/bin/env python3
# Runs ON THE RECEIVER (read-only).  Samples the DISPLAYED framebuffer page (enigma2 57b7a51 renders in
# cmImmediate mode directly into it; HDMI scans it out) inside one EventView description box, ~every 1 ms,
# and measures how long the box is partially cleared during the RunningText repaints.
# usage: fbprobe.py <x0> <x1> <y0> <y1> <seconds> [label]
import mmap, os, sys, time
x0, x1, y0, y1, secs = (int(a) for a in sys.argv[1:6])
label = sys.argv[6] if len(sys.argv) > 6 else "box"
W, STRIDE = 1920, 7680
fd = os.open("/dev/fb0", os.O_RDONLY)
mm = mmap.mmap(fd, STRIDE * 2160, mmap.MAP_SHARED, mmap.PROT_READ)
pan = open("/sys/class/graphics/fb0/pan").read().strip()
yoff = int(pan.split(",")[1])
TBL = bytes((1 if b >= 0xC0 else 0) for b in range(256))
rows = list(range(y0, y1, 4))
top = rows[:len(rows) // 3]
def count(rs):
    n = 0
    for y in rs:
        o = (y + yoff) * STRIDE
        n += mm[o + x0 * 4:o + x1 * 4:4].translate(TBL).count(1)
    return n
def sample():
    return count(top)
t_end = time.monotonic() + secs
ts, vs = [], []
while time.monotonic() < t_end:
    ts.append(time.monotonic()); vs.append(sample())
srt = sorted(vs); med = srt[len(srt) // 2]
low = [v < 0.5 * med for v in vs]
dips, cur, start = [], False, 0
for i, l in enumerate(low):
    if l and not cur: cur, start = True, ts[i]
    if not l and cur: cur = False; dips.append((ts[i] - start) * 1000)
dt = (ts[-1] - ts[0]) / max(1, len(ts) - 1) * 1000
pct = lambda q: srt[min(len(srt) - 1, int(q * len(srt)))]
print("%s top-third percentiles p0/p1/p5/p50 = %d/%d/%d/%d" % (label, srt[0], pct(0.01), pct(0.05), med))
print("%s pan=%s samples=%d interval=%.2fms median_textpx=%d low_fraction=%.4f dips=%d dip_ms(avg/max)=%.1f/%.1f" % (
    label, pan, len(vs), dt, med, sum(low) / len(low), len(dips), (sum(dips) / len(dips)) if dips else 0, max(dips) if dips else 0))
