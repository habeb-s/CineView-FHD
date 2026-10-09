#!/usr/bin/env python3
"""verify105.py <1.0.4 dir> <1.0.5 dir>: every 1.0.5 package = its 1.0.4 package with exactly the planned changes:
data: - usr/bin/enigma2_pre_start.sh (+ the usr/bin dir entry); + site-packages/cineview_mla_guardian.pth for the
package's Python (+ its two dir entries); + mla/guardian/prestart.py, mla/guardian/cineview_mla_guardian.pth;
+ Components/CineViewMLAWeatherData.pyc, Converter/CineViewMLAWeather.pyc, Renderer/CineViewMLAWeatherPixmap.pyc
(compiled for the package's Python, unchecked-hash, from the repository sources); + mla_assets/weather/ (10 icons);
~ mla/guardian/guardian.sh, ~ mla/engine/composer.py (= repository), ~ version.json.
control: ~ preinst (hook check -> site-packages check), ~ postinst (legacy hook clean-up, composer ensure),
~ control (Version/Source).
Nothing else.  The .pyc are checked by their header (magic of the package's Python, unchecked-hash flag) and by
running them with that Python's marshal (the code object's file name is the installed path)."""
import glob, io, os, re, subprocess, sys, tarfile
A, B = sys.argv[1:3]
R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
G = os.path.join(R, "mla", "guardian")
SK = "./usr/share/enigma2/CineView_FHD_MLA/mla/guardian/"
SKIN = "./usr/share/enigma2/CineView_FHD_MLA"
COMP = "./usr/lib/enigma2/python/Components"
MODS = {COMP + "/CineViewMLAWeatherData.pyc": "mla/components/_lib/CineViewMLAWeatherData.py",
	COMP + "/Converter/CineViewMLAWeather.pyc": "mla/components/Converter/CineViewMLAWeather.py",
	COMP + "/Renderer/CineViewMLAWeatherPixmap.pyc": "mla/components/Renderer/CineViewMLAWeatherPixmap.py"}
ICONS = {SKIN + "/mla_assets/weather/" + os.path.basename(f): open(f, "rb").read() for f in glob.glob(os.path.join(R, "mla", "assets", "weather", "*.png"))}
EXE = {"3.12": "/usr/bin/python3.12", "3.13": os.path.expanduser("~/cineview-mla/py313/python/bin/python3.13"), "3.14": os.path.expanduser("~/cineview-mla/py314/python/bin/python3.14")}
CHECK_PYC = r"""
import importlib.util, marshal, sys
d = open(sys.argv[1], "rb").read()
assert d[:4] == importlib.util.MAGIC_NUMBER, "magic"
assert int.from_bytes(d[4:8], "little") == 1, "flags: unchecked hash"
co = marshal.loads(d[16:])
assert co.co_filename == sys.argv[2], co.co_filename
src = compile(open(sys.argv[3], encoding="utf-8").read(), sys.argv[2], "exec")
def same(a, b):
	if type(a) is not type(b):
		return False
	if hasattr(a, "co_code"):
		keys = ("co_code", "co_names", "co_varnames", "co_filename", "co_name", "co_argcount", "co_flags")
		return all(getattr(a, k) == getattr(b, k) for k in keys) and len(a.co_consts) == len(b.co_consts) and all(same(x, y) for x, y in zip(a.co_consts, b.co_consts))
	return a == b
assert same(src, co), "code differs from the repository source"
print("ok")
"""


def ar(p):
	d = open(p, "rb").read(); i, o = 8, {}
	while i < len(d):
		n = d[i:i+16].decode().strip().rstrip("/"); s = int(d[i+48:i+58]); i += 60; o[n] = d[i:i+s]; i += s + s % 2
	return o


def files(blob):
	t = tarfile.open(fileobj=io.BytesIO(blob)); return {m.name: (t.extractfile(m).read() if m.isfile() else ("dir" if m.isdir() else (m.type, m.linkname))) for m in t.getmembers()}


ok = True
for f in sorted(x for x in os.listdir(A) if x.endswith(".ipk")):
	g = f.replace("_1.0.4", "_1.0.5")
	pa, pb = ar(os.path.join(A, f)), ar(os.path.join(B, g))
	da, db = files(pa["data.tar.gz"]), files(pb["data.tar.gz"])
	py = re.search(rb'PYNEED="(3\.\d+)"', files(pb["control.tar.gz"])["./preinst"]).group(1).decode()
	site = "./usr/lib/python%s/site-packages" % py
	removed = sorted(set(da) - set(db)); added = sorted(set(db) - set(da)); changed = sorted(n for n in set(da) & set(db) if da[n] != db[n])
	exp_removed = ["./usr/bin", "./usr/bin/enigma2_pre_start.sh"]
	exp_added = sorted(["./usr/lib/python%s" % py, site, site + "/cineview_mla_guardian.pth", SK + "cineview_mla_guardian.pth", SK + "prestart.py",
		SKIN + "/mla_assets/weather"] + list(MODS) + list(ICONS))
	exp_changed = sorted([SK + "guardian.sh", SKIN + "/mla/engine/composer.py", "./usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/version.json",
		"./usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/plugin.pyc"])
	good = removed == exp_removed and added == exp_added and changed == exp_changed and len(ICONS) == 10
	good &= db[SKIN + "/mla/engine/composer.py"] == open(os.path.join(R, "mla", "engine", "composer.py"), "rb").read()
	good &= da[SKIN + "/mla/engine/composer.py"] == open(os.path.join(R, "tools", "mla", "composer_104.py"), "rb").read()
	good &= all(db[k] == v for k, v in ICONS.items())
	for rel, src in list(MODS.items()) + [("./usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/plugin.pyc", "mla/plugin/CineViewMLA/plugin.py")]:
		tmp = "/tmp/verify105_%d.pyc" % os.getpid()
		open(tmp, "wb").write(db[rel])
		r = subprocess.run([EXE[py], "-c", CHECK_PYC, tmp, rel[1:-1], os.path.join(R, src)], capture_output=True, text=True)
		os.remove(tmp)
		if r.stdout.strip() != "ok":
			print("   pyc", rel, r.stdout.strip(), r.stderr.strip()[-200:])
			good = False
	good &= db[site + "/cineview_mla_guardian.pth"] == db[SK + "cineview_mla_guardian.pth"] == open(os.path.join(G, "cineview_mla_guardian.pth"), "rb").read()
	good &= db[SK + "prestart.py"] == open(os.path.join(G, "prestart.py"), "rb").read() and db[SK + "guardian.sh"] == open(os.path.join(G, "guardian.sh"), "rb").read()
	ca, cb = files(pa["control.tar.gz"]), files(pb["control.tar.gz"])
	cch = sorted(n for n in set(ca) | set(cb) if ca.get(n) != cb.get(n))
	good &= cch == ["./control", "./postinst", "./preinst"]
	good &= b"belongs to something else" not in cb["./preinst"] and b"site-packages" in cb["./preinst"] and b"Only calls the CineView MLA guardian" in cb["./postinst"]
	good &= b'E="python3 $S/mla/engine/composer.py"' in cb["./postinst"] and b"$E ensure >>/tmp/cineview_mla_postinst.log 2>&1 || true" in cb["./postinst"]
	# preinst/postinst: only the planned lines differ
	dpre = [l for l in cb["./preinst"].decode().splitlines() if l not in ca["./preinst"].decode().splitlines()]
	dpost = [l for l in ca["./postinst"].decode().splitlines() if l not in cb["./postinst"].decode().splitlines()]
	good &= not dpost and all("site-packages" in l or l.startswith(("#", "if [", "fi", "  echo")) for l in dpre)
	ctl_diff = [l for l in cb["./control"].decode().splitlines() if l not in ca["./control"].decode().splitlines()]
	good &= all(re.match(r"^(Version|Source): .*1\.0\.5", l) for l in ctl_diff) and pa["debian-binary"] == pb["debian-binary"]
	ok &= good
	print("%s %s  python %s  removed=%s added=%d changed=%d control=%s" % ("PASS" if good else "FAIL", g, py, [r.split("/")[-1] for r in removed], len(added), len(changed), cch))
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
