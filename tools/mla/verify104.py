#!/usr/bin/env python3
"""verify104.py <1.0.3 dir> <1.0.4 dir>: every 1.0.4 package = its 1.0.3 package with only composer.py and
version.json changed in data, only Version/Source changed in control, composer.py = mla/engine/composer.py."""
import io, os, re, sys, tarfile
A, B = sys.argv[1:3]
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mla", "engine", "composer.py"), "rb").read()


def ar(p):
	d = open(p, "rb").read(); i, o = 8, {}
	while i < len(d):
		n = d[i:i+16].decode().strip().rstrip("/"); s = int(d[i+48:i+58]); i += 60; o[n] = d[i:i+s]; i += s + s % 2
	return o


def files(blob):
	t = tarfile.open(fileobj=io.BytesIO(blob)); return {m.name: (t.extractfile(m).read() if m.isfile() else (m.type, m.linkname, m.mode)) for m in t.getmembers()}


ok = True
for f in sorted(x for x in os.listdir(A) if x.endswith(".ipk")):
	g = f.replace("_1.0.3", "_1.0.4")
	pa, pb = ar(os.path.join(A, f)), ar(os.path.join(B, g))
	da, db = files(pa["data.tar.gz"]), files(pb["data.tar.gz"])
	changed = sorted(n for n in set(da) | set(db) if da.get(n) != db.get(n))
	ca, cb = files(pa["control.tar.gz"]), files(pb["control.tar.gz"])
	cchanged = sorted(n for n in set(ca) | set(cb) if ca.get(n) != cb.get(n))
	ctl_diff = [l for l in cb["./control"].decode().splitlines() if l not in ca["./control"].decode().splitlines()]
	good = (changed == ["./usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/version.json", "./usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py"]
		and db["./usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py"] == SRC and cchanged == ["./control"]
		and all(re.match(r"^(Version|Source): .*1\.0\.4", l) for l in ctl_diff) and pa["debian-binary"] == pb["debian-binary"])
	ok &= good
	print("%s %s  changed=%d ctl=%s" % ("PASS" if good else "FAIL", g, len(changed), ctl_diff))
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
