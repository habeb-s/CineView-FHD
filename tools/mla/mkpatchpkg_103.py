#!/usr/bin/env python3
"""CineView MLA 1.0.3 = each published 1.0.2 package with TWO modules replaced, compiled with the package's own
Python (UNCHECKED_HASH, sourceless like every other module):
  Components/CineViewMLAPosterMatch     <- mla/components/_lib/CineViewMLAPosterMatch.py
  Components/Renderer/CineViewMLAPosterX <- the renderer build.py writes (golden + tools/mla/patches/posterx_identity.py),
                                            identical for every image; pass it as <renderer.py>
version.json and control Version/Source updated; maintainer scripts and every other file byte for byte unchanged.
usage: mkpatchpkg_103.py <1.0.2 ipk> <renderer.py> <out dir>"""
import hashlib, io, json, os, re, subprocess, sys, tarfile, tempfile, time

IPK, RENDERER, OUT = sys.argv[1:4]
MI = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = os.path.expanduser("~/cineview-mla")
MODULES = {
	"usr/lib/enigma2/python/Components/CineViewMLAPosterMatch.py": os.path.join(MI, "mla", "components", "_lib", "CineViewMLAPosterMatch.py"),
	"usr/lib/enigma2/python/Components/Renderer/CineViewMLAPosterX.py": RENDERER,
}
EXE = {"3.12": "/usr/bin/python3.12", "3.13": R + "/py313/python/bin/python3.13", "3.14": R + "/py314/python/bin/python3.14"}


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
assert old.startswith("1.0.2"), old
new = "1.0.3" + old[len("1.0.2"):]
py = info["python"]
pycs = {}
with tempfile.TemporaryDirectory() as td:
	for rel, src in MODULES.items():
		out = td + "/m.pyc"
		subprocess.run([EXE[py], "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], dfile='/'+sys.argv[3], doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)", src, out, rel], check=True)
		pycs["./" + rel + "c"] = open(out, "rb").read()
info.update(version=new, date=time.strftime("%Y-%m-%d"), fix="posters: original title from the EPG description (localised EPG titles)")
hit = set()
buf = io.BytesIO(); tf = tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT)
for m, b in members:
	if m.name in pycs:
		b = pycs[m.name]; hit.add(m.name)
	elif m.name.endswith("CineViewMLA/version.json"):
		b = json.dumps(info, indent=1).encode()
	if b is not None:
		m.size = len(b); tf.addfile(m, io.BytesIO(b))
	else:
		tf.addfile(m)
tf.close()
assert hit == set(pycs), "module .pyc not found in the package: %s" % (set(pycs) - hit)
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
print("%s Python %s  %s" % (os.path.basename(path), py, hashlib.sha256(open(path, "rb").read()).hexdigest()))
