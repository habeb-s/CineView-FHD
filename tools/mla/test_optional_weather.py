#!/usr/bin/env python3
"""Optional weather (OAWeather) - engine tests on the REAL published packages (isolated copies, never a receiver).
usage: test_optional_weather.py <new composer.py> <ipk ...>
For every package: the skin is extracted to a scratch dir and run with two Components trees
  noweather = every renderer/converter/source the package's screens reference EXCEPT OAWeather/OAWeatherPixmap
  weather   = the same + the OAWeather trio
(MLA_COMPONENTS_ROOT, the same lookup the plugin and the CLI use on the receiver) and the package's own 1.0.3
composer (reproduction) or the new composer."""
import glob, importlib.util, io, json, os, shutil, subprocess, sys, tarfile, tempfile, xml.etree.ElementTree as ET

NEW, IPKS = sys.argv[1], sys.argv[2:]
TRIO = {"Renderer": {"OAWeatherPixmap"}, "Converter": {"OAWeather"}, "Sources": {"OAWeather"}}
BUILTIN_R = {"Label", "Pixmap", "Listbox", "FixedLabel", "Progress", "Canvas", "Pig"}
MODELS = {"classic": dict(infobar="classic", secondinfobar="classic", channelselection="classic", epg="classic", pvr="classic", eventview="classic"),
	"classic-lines": dict(infobar="classic", secondinfobar="classic", channelselection="classic", epg="classic", pvr="classic", eventview="classic-lines"),
	"details": dict(infobar="details", secondinfobar="details", channelselection="posterlist", epg="graphicalplus", pvr="cover", eventview="detailscard"),
	"cinema": dict(infobar="cinema", secondinfobar="cinema", channelselection="videofirst", epg="graphicalplus", pvr="cinema", eventview="feature"),
	"modern": dict(infobar="modern", secondinfobar="modern", channelselection="modern", epg="modern", pvr="modern", eventview="modern"),
	"minimal": dict(infobar="minimal", secondinfobar="minimal", channelselection="minimal", epg="minimal", pvr="minimal", eventview="minimal")}
THEMES = ["navy", "black", "graphite", "purple", "burgundy", "green"]
fails = []


def check(name, cond, detail=""):
	print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  [%s]" % detail))
	if not cond:
		fails.append(name)


def ar(p):
	d = open(p, "rb").read(); i, o = 8, {}
	while i < len(d):
		n = d[i:i+16].decode().strip().rstrip("/"); s = int(d[i+48:i+58]); i += 60; o[n] = d[i:i+s]; i += s + s % 2
	return o


def refs(paths):
	out = {"Renderer": set(), "Converter": set(), "Sources": set()}
	for f in paths:
		for n in ET.parse(f).getroot().iter():
			if n.get("render"): out["Renderer"].add(n.get("render"))
			if n.tag == "convert": out["Converter"].add(n.get("type"))
			s = n.get("source") or ""
			if s.startswith("session."): out["Sources"].add(s[8:])
	return out


def comp_root(base, names):
	shutil.rmtree(base, ignore_errors=True)
	for k, v in names.items():
		os.makedirs(os.path.join(base, k))
		for n in v:
			open(os.path.join(base, k, n + ".pyc"), "w").close()
	return base


def strict_missing(gen_dir, names):
	"""Every render/convert/session source in the built generation must exist in the Components tree."""
	r = refs(glob.glob(os.path.join(gen_dir, "*.xml")))
	return sorted(["%s %s" % (k, x) for k in r for x in r[k] if x not in names[k] | (BUILTIN_R if k == "Renderer" else set())
		and not (k == "Sources" and x not in TRIO["Sources"])])  # non-plugin session sources are Enigma2 globals


def weather_widgets(path):
	return sum(1 for n in ET.parse(path).getroot().iter("widget") if n.get("source") == "session.OAWeather")


def canon_without_weather(path):
	root = ET.parse(path).getroot()
	for p in list(root.iter()):
		for c in list(p):
			if c.tag == "widget" and c.get("source") == "session.OAWeather":
				p.remove(c)
	return ET.tostring(root)


for ipk in IPKS:
	name = os.path.basename(ipk)
	print("=" * 8, name)
	T = tempfile.mkdtemp(prefix="w104_")
	tarfile.open(fileobj=io.BytesIO(ar(ipk)["data.tar.gz"])).extractall(T + "/d", filter="tar")
	SRC = T + "/d/usr/share/enigma2/CineView_FHD_MLA"
	img = "openbh" if ".openbh" in name or "~openbh" in name else "openvix" if ".openvix" in name or "~openvix" in name else "openatv"
	pyc = T + "/d/usr/lib/enigma2/python/Components"
	allxml = glob.glob(SRC + "/layouts/*/*/*.xml") + glob.glob(SRC + "/core/*.xml") + glob.glob(SRC + "/generations/g000000/*.xml")
	names = refs(allxml)
	nw = {k: (names[k] - TRIO[k]) for k in names}
	ww = {k: names[k] | TRIO[k] for k in names}
	CR_NO, CR_W = comp_root(T + "/comp_noweather", nw), comp_root(T + "/comp_weather", ww)

	def run(composer, croot, *args):
		env = dict(os.environ, MLA_SKIN_DIR=T + "/skin", MLA_STATE_DIR=T + "/state", MLA_COMPONENTS_ROOT=croot, MLA_IMAGE=img)
		p = subprocess.run([sys.executable, composer] + list(args), env=env, capture_output=True, text=True)
		return p.returncode, p.stdout + p.stderr

	def fresh(composer_src):
		shutil.rmtree(T + "/skin", ignore_errors=True); shutil.rmtree(T + "/state", ignore_errors=True)
		shutil.copytree(SRC, T + "/skin", symlinks=True); os.makedirs(T + "/state")
		shutil.copyfile(composer_src, T + "/skin/mla/engine/composer.py")
		return T + "/skin/mla/engine/composer.py"

	def act():
		return os.path.basename(os.readlink(T + "/skin/active"))

	def gen(g=None):
		return T + "/skin/generations/" + (g or act())

	# --- reproduction with the published 1.0.3 composer
	old = T + "/old_composer.py"; shutil.copyfile(SRC + "/mla/engine/composer.py", old)
	c = fresh(old)
	rc, out = run(c, CR_NO, "validate", "--theme", "navy")
	check(name + " 1.0.3 reproduces: classic fails without OAWeather", rc == 1 and "converter OAWeather not installed" in out and "renderer OAWeatherPixmap not installed" in out, out[-300:])
	# --- new composer, image WITHOUT OAWeather
	c = fresh(NEW)
	rc, out = run(c, CR_NO, "rollback", "--to", "factory")  # what postinst does on a first install
	g1 = act()
	check(name + " first install without OAWeather: factory rebuilt", rc == 0 and g1 != "g000000", out[-300:])
	check(name + "   rebuilt factory has no weather widget and no missing component", not strict_missing(gen(), nw) and sum(weather_widgets(f) for f in glob.glob(gen() + "/*.xml")) == 0, strict_missing(gen(), nw))
	check(name + "   lkg follows the rebuilt factory", open(T + "/state/lkg").read().strip() == g1)
	check(name + "   features.json says weather omitted", json.load(open(gen() + "/features.json")) == {"omitted": ["weather"]})
	same = all(canon_without_weather(f) == canon_without_weather(os.path.join(gen("g000000"), os.path.basename(f))) for f in glob.glob(gen() + "/*.xml"))
	check(name + "   everything except the weather widgets identical to factory", same)
	rc, out = run(c, CR_NO, "recover")
	check(name + "   next start: recover is a no-op (stable)", act() == g1 and "rebuilt" not in out, out[-200:])
	ok_models = []
	for model, lay in MODELS.items():
		for theme in THEMES:
			args = ["apply", "--theme", theme] + sum([["--set", "%s=%s" % kv] for kv in lay.items()], [])
			rc, out = run(c, CR_NO, *args)
			miss = strict_missing(gen(), nw) if rc == 0 else ["rc=%d %s" % (rc, out[-200:])]
			if not miss and weather_widgets(gen() + "/infobar.xml") == 0:
				ok_models.append((model, theme))
			else:
				print("   ", model, theme, miss[:3])
	check(name + "   all 6 models x 6 themes apply without OAWeather, strict component check of every generation", len(ok_models) == 36, 36 - len(ok_models))
	# non-optional missing component still blocks
	victim = sorted(refs([SRC + "/layouts/infobar/classic/screens.openatv.xml"])["Converter"] - TRIO["Converter"])[0]
	broken = {k: set(v) for k, v in nw.items()}; broken["Converter"].discard(victim)
	CR_BR = comp_root(T + "/comp_broken", broken)
	rc, out = run(c, CR_BR, "validate", "--theme", "navy")
	rc, out = run(c, CR_BR, "validate", *sum([["--set", "%s=%s" % kv] for kv in MODELS["classic"].items()], []))
	check(name + "   validation still blocks a missing NON-optional component (%s)" % victim, rc == 1 and ("converter %s not installed" % victim) in out and "OAWeather" not in out, out[-300:])
	# --- the user installs OAWeather later: next start restores the weather
	rc, out = run(c, CR_NO, "apply", "--theme", "navy", *sum([["--set", "%s=%s" % kv] for kv in MODELS["classic"].items()], []))
	gp = act()
	rc, out = run(c, CR_W, "recover")
	gw = act()
	check(name + " OAWeather installed later: recover rebuilds with weather", gw != gp and weather_widgets(gen() + "/infobar.xml") > 0 and json.load(open(gen() + "/features.json")) == {"omitted": []}, out[-300:])
	byte_same = all(open(gen() + "/%s.xml" % s, "rb").read() == open(T + "/skin/layouts/%s/classic/screens.openatv.xml" % s, "rb").read() for s in ("infobar", "secondinfobar", "eventview"))
	check(name + "   weather generation byte-identical to the layout packs", byte_same)
	check(name + "   strict component check with OAWeather", not strict_missing(gen(), ww), strict_missing(gen(), ww))
	# --- receivers that HAVE OAWeather: nothing changes
	c = fresh(NEW)
	rc, out = run(c, CR_W, "rollback", "--to", "factory")
	check(name + " with OAWeather: factory stays g000000 (no rebuild)", rc == 0 and act() == "g000000", out[-200:])
	rc, out = run(c, CR_W, "apply", "--theme", "purple", "--set", "infobar=details", "--set", "secondinfobar=cinema")
	check(name + "   apply copies the packs byte for byte", rc == 0 and open(gen() + "/infobar.xml", "rb").read() == open(T + "/skin/layouts/infobar/details/screens.openatv.xml", "rb").read(), out[-200:])
	# --- OAWeather removed while its design is active (crash prevention before Enigma2 starts)
	rc, out = run(c, CR_NO, "recover")
	check(name + " OAWeather removed: pre-start recover drops the weather widgets", weather_widgets(gen() + "/infobar.xml") == 0 and not strict_missing(gen(), nw), out[-300:])
	sel = json.load(open(gen() + "/selection.json"))
	check(name + "   the user's selection is kept", sel["theme"] == "purple" and sel["layouts"]["infobar"] == "details" and sel["layouts"]["secondinfobar"] == "cinema")
	# --- trial semantics survive a rebuild
	c = fresh(NEW); run(c, CR_W, "rollback", "--to", "factory")
	rc, out = run(c, CR_W, "apply", "--trial", "--set", "infobar=details")
	gt = act(); j0 = json.load(open(T + "/state/txn.json"))
	rc, out = run(c, CR_NO, "ensure")
	j1 = json.load(open(T + "/state/txn.json"))
	check(name + " trial rebuilt keeps the TRIAL journal on the new generation", j0["state"] == "TRIAL" and j1["state"] == "TRIAL" and j1["gid"] == act() != gt, (j0, j1))
	shutil.rmtree(T, ignore_errors=True)

print("\nRESULT: %s (%d failures)" % ("PASS" if not fails else "FAIL", len(fails)))
sys.exit(1 if fails else 0)
