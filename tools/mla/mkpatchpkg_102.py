#!/usr/bin/env python3
"""CineView MLA 1.0.2 = each published 1.0.1 package with ONE module replaced: Components/Converter/CineViewMLACPUTemp
(source: mi tools/mla/patches/cputemp.py, the file build.py now installs for every image), compiled with the package's
own Python.  version.json and control Version/Source updated; preinst/postinst/prerm/postrm and every other file byte
for byte unchanged.  usage: mkpatchpkg.py <1.0.1 ipk> <out dir>"""
import hashlib, io, json, os, re, subprocess, sys, tarfile, tempfile, time
IPK, OUT = sys.argv[1:3]
R = os.path.expanduser("~/cineview-mla")
SRC = R + "/mi/tools/mla/patches/cputemp.py"
REL = "usr/lib/enigma2/python/Components/Converter/CineViewMLACPUTemp.py"
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
assert old.startswith("1.0.1"), old
new = "1.0.2" + old[len("1.0.1"):]
py = info["python"]
with tempfile.TemporaryDirectory() as td:
	out = td + "/m.pyc"
	subprocess.run([EXE[py], "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], dfile='/'+sys.argv[3], doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)", SRC, out, REL], check=True)
	pyc = open(out, "rb").read()
info.update(version=new, date=time.strftime("%Y-%m-%d"), fix="receiver temperature: more sensor sources, N/A when none")
hit = 0
buf = io.BytesIO(); tf = tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT)
for m, b in members:
	if m.name == "./" + REL + "c":
		b = pyc; hit += 1
	elif m.name.endswith("CineViewMLA/version.json"):
		b = json.dumps(info, indent=1).encode()
	if b is not None:
		m.size = len(b); tf.addfile(m, io.BytesIO(b))
	else:
		tf.addfile(m)
tf.close()
assert hit == 1, "converter .pyc not found in the package"
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
