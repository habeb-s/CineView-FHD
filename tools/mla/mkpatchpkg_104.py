#!/usr/bin/env python3
"""CineView MLA 1.0.4 = each published 1.0.3 package with ONE file replaced:
  usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py  <- mla/engine/composer.py (plain source, same for every image)
Fix: optional plugin features (OAWeather weather widgets) are left out of a generation when the plugin is not
installed, instead of failing validation; the guardian's pre-start recover rebuilds the active generation when the
installed plugins change.  version.json and control Version/Source updated; maintainer scripts, layout packs,
compiled modules and every other file byte for byte unchanged.
usage: mkpatchpkg_104.py <1.0.3 ipk> <out dir>"""
import hashlib, io, json, os, re, sys, tarfile, time

IPK, OUT = sys.argv[1:3]
MI = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
COMPOSER = os.path.join(MI, "mla", "engine", "composer.py")
TARGET = "./usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py"


def ar(p):
	d = open(p, "rb").read(); i, o = 8, {}
	while i < len(d):
		n = d[i:i+16].decode().strip().rstrip("/"); s = int(d[i+48:i+58]); i += 60; o[n] = d[i:i+s]; i += s + s % 2
	return o


parts = ar(IPK)
ctl = tarfile.open(fileobj=io.BytesIO(parts["control.tar.gz"])); cf = {m.name: ctl.extractfile(m).read() for m in ctl.getmembers() if m.isfile()}
dat = tarfile.open(fileobj=io.BytesIO(parts["data.tar.gz"])); members = [(m, dat.extractfile(m).read() if m.isfile() else None) for m in dat.getmembers()]
info = json.loads([b for m, b in members if m.name.endswith("CineViewMLA/version.json")][0])
old = re.search(rb"^Version: (.*)$", cf["./control"], re.M).group(1).decode()
assert old.startswith("1.0.3"), old
new = "1.0.4" + old[len("1.0.3"):]
src = open(COMPOSER, "rb").read()
info.update(version=new, date=time.strftime("%Y-%m-%d"), fix="optional weather (OAWeather): the design applies without the plugin; widgets return when it is installed")
hit = 0
buf = io.BytesIO(); tf = tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT)
for m, b in members:
	if m.name == TARGET:
		b = src; hit += 1
	elif m.name.endswith("CineViewMLA/version.json"):
		b = json.dumps(info, indent=1).encode()
	if b is not None:
		m.size = len(b); tf.addfile(m, io.BytesIO(b))
	else:
		tf.addfile(m)
tf.close()
assert hit == 1, "composer.py not found in the package"
cf["./control"] = cf["./control"].replace(("Version: " + old).encode(), ("Version: " + new).encode()).replace(("Source: CineView MLA " + old).encode(), ("Source: CineView MLA " + new).encode())
cb = io.BytesIO(); ct = tarfile.open(fileobj=cb, mode="w:gz", format=tarfile.GNU_FORMAT)
for m in ctl.getmembers():
	if m.isfile():
		b = cf[m.name]; m.size = len(b); ct.addfile(m, io.BytesIO(b))
	else:
		ct.addfile(m)
ct.close()
os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "enigma2-plugin-skins-cineview-fhd-mla_%s_all.ipk" % new)
with open(path, "wb") as f:
	f.write(b"!<arch>\n")
	for n, b in (("debian-binary", parts["debian-binary"]), ("control.tar.gz", cb.getvalue()), ("data.tar.gz", buf.getvalue())):
		f.write(("%-16s%-12d%-6d%-6d%-8s%-10d`\n" % (n, int(time.time()), 0, 0, "100644", len(b))).encode()); f.write(b)
		if len(b) % 2: f.write(b"\n")
print("%s  %s" % (os.path.basename(path), hashlib.sha256(open(path, "rb").read()).hexdigest()))
