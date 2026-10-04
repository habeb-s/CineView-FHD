#!/usr/bin/env python3
# Runs ON THE RECEIVER (read-only).  Records a rectangle of the DISPLAYED framebuffer page (enigma2 57b7a51
# cmImmediate: what HDMI scans out) at a fixed rate and writes raw RGB frames + timestamps to a file.
# usage: fbrec.py <x> <y> <w> <h> <fps> <seconds> <outfile>
# outfile format: b"FBREC1" + w,h,n (3x uint32) + n doubles (t, seconds) + n*w*h*3 bytes RGB
import mmap, os, struct, sys, time
x, y, w, h, fps, secs = (float(a) if i == 4 else int(a) for i, a in enumerate(sys.argv[1:7]))
out = sys.argv[7]
STRIDE = 7680
fd = os.open("/dev/fb0", os.O_RDONLY)
mm = mmap.mmap(fd, STRIDE * 2160, mmap.MAP_SHARED, mmap.PROT_READ)
yoff = int(open("/sys/class/graphics/fb0/pan").read().strip().split(",")[1])
frames, ts = [], []
period = 1.0 / fps
t0 = time.monotonic()
nxt = t0
while time.monotonic() - t0 < secs:
    now = time.monotonic()
    if now < nxt:
        time.sleep(nxt - now)
    t = time.monotonic()
    buf = bytearray()
    for r in range(y, y + h):
        o = (r + yoff) * STRIDE + x * 4
        buf += mm[o:o + w * 4]
    frames.append(bytes(buf)); ts.append(t - t0)
    nxt += period
with open(out, "wb") as f:
    f.write(b"FBREC1" + struct.pack("<III", w, h, len(frames)))
    f.write(struct.pack("<%dd" % len(ts), *ts))
    for b in frames:  # BGRA -> RGB
        rgb = bytearray(w * h * 3)
        rgb[0::3] = b[2::4]; rgb[1::3] = b[1::4]; rgb[2::3] = b[0::4]
        f.write(rgb)
print("fbrec %s: %d frames in %.1f s (%.1f fps)" % (out, len(frames), ts[-1], len(frames) / max(ts[-1], 0.001)))
