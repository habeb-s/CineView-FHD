#!/usr/bin/env python3
# Each 1.0.3 package vs its 1.0.2 base: only the two poster modules + version.json differ in data, only ./control in
# control; each new .pyc loads with the package's Python and is the right module.  Also checks pkg102 = published.
import glob, io, json, os, subprocess, tarfile
R = os.path.expanduser("~/cineview-mla")
EXE = {"3.12": "/usr/bin/python3.12", "3.13": R + "/py313/python/bin/python3.13", "3.14": R + "/py314/python/bin/python3.14"}
def ar(p):
	d = open(p, "rb").read(); i, o = 8, {}
	while i < len(d):
		n = d[i:i+16].decode().strip().rstrip("/"); s = int(d[i+48:i+58]); i += 60; o[n] = d[i:i+s]; i += s + s % 2
	return o
def tm(b):
	t = tarfile.open(fileobj=io.BytesIO(b)); return {m.name: (m.type, m.mode, m.linkname, t.extractfile(m).read() if m.isfile() else None) for m in t.getmembers()}
E = "./usr/lib/enigma2/python/"
exp = [E + "Components/CineViewMLAPosterMatch.pyc", E + "Components/Renderer/CineViewMLAPosterX.pyc", E + "Plugins/Extensions/CineViewMLA/version.json"]
probe = ("import importlib.util,marshal,sys;d=open(sys.argv[1],'rb').read();assert d[:4]==importlib.util.MAGIC_NUMBER;"
	"c=marshal.loads(d[16:]);t=type(c);w=lambda c:str(c.co_names)+str(c.co_consts)+''.join(w(k) for k in c.co_consts if isinstance(k,t));"
	"print('ok' if sys.argv[2] in w(c) else 'missing')")
bad = 0
for n in sorted(glob.glob(R + "/oct/pkg103/*.ipk")):
	v = n.split("_")[1]; base = R + "/oct/pkg102/enigma2-plugin-skins-cineview-fhd-mla_1.0.2%s_all.ipk" % v[5:]
	a, b = ar(base), ar(n); da, db = tm(a["data.tar.gz"]), tm(b["data.tar.gz"]); ca, cb = tm(a["control.tar.gz"]), tm(b["control.tar.gz"])
	dd = sorted(k for k in da if da[k] != db.get(k)) + sorted(set(db) - set(da))
	cd = sorted(k for k in ca if ca[k] != cb[k])
	py = json.loads(db[exp[2]][3])["python"]
	res = []
	for rel, marker in ((exp[0], "orig_norm"), (exp[1], "kind_soft")):
		open("/tmp/t103.pyc", "wb").write(db[rel][3])
		res.append(subprocess.run([EXE[py], "-c", probe, "/tmp/t103.pyc", marker], capture_output=True, text=True).stdout.strip() or "error")
	ver = json.loads(db[exp[2]][3])["version"]
	ok = dd == exp and cd == ["./control"] and res == ["ok", "ok"] and ver == v and b"Version: %s\n" % v.encode() in cb["./control"][3]
	bad += not ok
	print("%-24s data diff=%s control=%s pyc(Python %s)=%s %s" % (v, [x.split('/')[-1] for x in dd], cd, py, res, "OK" if ok else "FAIL"))
print("RESULT", "PASS" if not bad else "FAIL")
