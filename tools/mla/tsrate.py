#!/usr/bin/env python3
"""T6 ground truth independent of the receiver's demux readers: per-PID bitrate of the live
service measured from the OpenWebif TS stream (port 8001), counted per second.

usage: tsrate.py <service ref> <vpid> <apid> [seconds=10] [host=192.168.1.250]
prints: video kbit/s min/avg/max per 1-s window and audio avg (TS payload incl. headers)
"""
import sys
import time
import urllib.request


def main(ref, vpid, apid, secs=10, host="192.168.1.250"):
	vpid, apid, secs = int(vpid), int(apid), int(secs)
	r = urllib.request.urlopen("http://%s:8001/%s" % (host, ref), timeout=15)
	buf, per = b"", []
	t_end = time.time() + secs + 2
	t0, cnt = None, {vpid: 0, apid: 0}
	while time.time() < t_end:
		buf += r.read(188 * 512)
		i = buf.find(b"\x47")
		buf = buf[i:] if i > 0 else buf
		n = len(buf) // 188
		for k in range(n):
			p = buf[k * 188:(k + 1) * 188]
			if p[0] != 0x47:
				continue
			pid = ((p[1] & 0x1F) << 8) | p[2]
			if pid in cnt:
				cnt[pid] += 188
		buf = buf[n * 188:]
		now = time.time()
		if t0 is None:
			t0 = now
			cnt = {vpid: 0, apid: 0}
		elif now - t0 >= 1.0:
			per.append((cnt[vpid] * 8 / 1000 / (now - t0), cnt[apid] * 8 / 1000 / (now - t0)))
			t0, cnt = now, {vpid: 0, apid: 0}
	per = per[1:]  # first window includes stream start-up
	v = [x for x, _ in per]
	a = [y for _, y in per]
	print("video kbit/s min %d avg %d max %d | audio avg %d | windows %d" % (min(v), sum(v) / len(v), max(v), sum(a) / len(a), len(per)))


if __name__ == "__main__":
	main(*sys.argv[1:])
