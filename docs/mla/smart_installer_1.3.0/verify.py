#!/usr/bin/env python3
"""Each variant vs its approved package: every data member byte-identical except the 15 .pyc + version.json;
postinst/prerm/postrm identical; every .pyc has the magic of its Python and unmarshals with that Python."""
import glob, io, json, os, subprocess, sys, tarfile
R = os.path.expanduser("~/cineview-mla")
EXE = {"3.12": "/usr/bin/python3.12", "3.13": R + "/py313/python/bin/python3.13", "3.14": R + "/py314/python/bin/python3.14"}
APP = {"openatv": "1.0.1", "openbh": "1.0.1~openbh1", "openvix": "1.0.1~openvix1"}
def ar(p):
	d = open(p, "rb").read(); i, o = 8, {}
	while i < len(d):
		n = d[i:i+16].decode().strip().rstrip("/"); s = int(d[i+48:i+58]); i += 60; o[n] = d[i:i+s]; i += s + s % 2
	return o
def tarmap(blob):
	t = tarfile.open(fileobj=io.BytesIO(blob)); return {m.name: (m.type, m.mode, m.linkname, t.extractfile(m).read() if m.isfile() else None) for m in t.getmembers()}
bad = 0
for v in sorted(glob.glob(R + "/rangecheck/pkg/*.ipk")):
	ver = v.split("_")[1]; img = ver.split("~")[1].split(".")[0]; py = "3." + ver.split(".py3")[1][:2]
	a, b = ar(R + "/final/pkg/enigma2-plugin-skins-cineview-fhd-mla_%s_all.ipk" % APP[img]), ar(v)
	da, db = tarmap(a["data.tar.gz"]), tarmap(b["data.tar.gz"])
	assert set(da) == set(db), "member list differs"
	diff = [n for n in da if da[n] != db[n]]
	pyc = [n for n in diff if n.endswith(".pyc")]; other = [n for n in diff if not n.endswith(".pyc")]
	ca, cb = tarmap(a["control.tar.gz"]), tarmap(b["control.tar.gz"])
	cdiff = sorted(n for n in ca if ca[n] != cb[n])
	APY = json.loads(da["./usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/version.json"][3])["python"]
	ok = len(pyc) == (0 if APY == py else 15) and other == ["./usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/version.json"] and cdiff == ["./control", "./preinst"]
	chk = "import importlib.util,marshal,sys\nfor f in sys.argv[1:]:\n d=open(f,'rb').read()\n assert d[:4]==importlib.util.MAGIC_NUMBER,f\n marshal.loads(d[16:])\nprint('ok')"
	tmp = R + "/rangecheck/tmp_pyc"; os.makedirs(tmp, exist_ok=True); fs = []
	for i, n in enumerate(pyc):
		p = "%s/%d.pyc" % (tmp, i); open(p, "wb").write(db[n][3]); fs.append(p)
	r = subprocess.run([EXE[py], "-c", chk] + fs, capture_output=True, text=True).stdout.strip()
	info = json.loads(db["./usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/version.json"][3])
	print("%-22s same data except .pyc(changed only if other Python)+version.json: %s | control/preinst only: %s | .pyc load with Python %s: %s | version.json python=%s" % (ver, ok, cdiff == ["./control", "./preinst"], py, r, info["python"]))
	bad += not (ok and r == "ok" and info["python"] == py)
print("RESULT", "PASS" if not bad else "FAIL %d" % bad)
