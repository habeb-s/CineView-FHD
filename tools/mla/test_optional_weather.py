#!/usr/bin/env python3
"""Weather widgets (OAWeather / CineView's own weather components) - engine tests on the REAL published packages
(isolated copies of the skin, never a receiver).  This is a simulation of the composer only: Enigma2 is not run.
usage: test_optional_weather.py <new composer.py> <ipk ...>
For every package the skin is extracted to a scratch dir and the composer runs with Components trees
(MLA_COMPONENTS_ROOT, the same lookup the plugin and the CLI use on the receiver):
  noweather_b = every renderer/converter/source the package's screens reference EXCEPT the OAWeather trio, PLUS
                CineView's own weather components (= 1.0.5 on an image without OAWeather)
  weather_b   = the same + the OAWeather trio (= 1.0.5 on an image with OAWeather)
  noweather   = without the trio and without CineView's own (fallback: widgets left out)
  weather     = the trio, without CineView's own (fallback: the packs as they are)
Reproduction: the published 1.0.3 composer (git 4087114) on noweather (the user's report)."""
import glob, io, json, os, shutil, subprocess, sys, tarfile, tempfile, xml.etree.ElementTree as ET

NEW, IPKS = sys.argv[1], sys.argv[2:]
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TRIO = {"Renderer": {"OAWeatherPixmap"}, "Converter": {"OAWeather"}, "Sources": {"OAWeather"}}
OWN = {"Renderer": {"CineViewMLAWeatherPixmap"}, "Converter": {"CineViewMLAWeather"}, "Sources": set()}
SUBST = {"source": ("session.OAWeather", "global.CurrentTime"), "render": ("OAWeatherPixmap", "CineViewMLAWeatherPixmap"),
	"convert": ("OAWeather", "CineViewMLAWeather")}
BUILTIN_R = {"Label", "Pixmap", "Listbox", "FixedLabel", "Progress", "Canvas", "Pig"}
MODELS = {"classic": dict(infobar="classic", secondinfobar="classic", channelselection="classic", epg="classic", pvr="classic", eventview="classic"),
	"classic-lines": dict(infobar="classic", secondinfobar="classic", channelselection="classic", epg="classic", pvr="classic", eventview="classic-lines"),
	"details": dict(infobar="details", secondinfobar="details", channelselection="posterlist", epg="graphicalplus", pvr="cover", eventview="detailscard"),
	"cinema": dict(infobar="cinema", secondinfobar="cinema", channelselection="videofirst", epg="graphicalplus", pvr="cinema", eventview="feature"),
	"modern": dict(infobar="modern", secondinfobar="modern", channelselection="modern", epg="modern", pvr="modern", eventview="modern"),
	"minimal": dict(infobar="minimal", secondinfobar="minimal", channelselection="minimal", epg="minimal", pvr="minimal", eventview="minimal")}
THEMES = ["navy", "black", "graphite", "purple", "burgundy", "green"]
fails = []
OLD103 = subprocess.run(["git", "-C", REPO, "show", "4087114:mla/engine/composer.py"], capture_output=True, text=True, check=True).stdout


def check(name, cond, detail=""):
	print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  [%s]" % (detail,)))
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


def widgets(path, kind):
	root = ET.parse(path).getroot()
	if kind == "native":
		return [n for n in root.iter("widget") if n.get("source") == "session.OAWeather"]
	return [n for n in root.iter("widget") if any(c.tag == "convert" and c.get("type") == "CineViewMLAWeather" for c in n.iter())]


def count(gen_dir, kind):
	return sum(len(widgets(f, kind)) for f in glob.glob(os.path.join(gen_dir, "*.xml")))


def canon(path, mode):
	"""The screen file with the weather widgets normalised: 'native' -> left as they are; 'builtin' -> CineView's
	names put back to the OAWeather names; then compared with the factory files."""
	root = ET.parse(path).getroot()
	for n in root.iter():
		if mode == "builtin":
			if n.tag == "widget" and n.get("source") == SUBST["source"][1] and any(c.tag == "convert" and c.get("type") == SUBST["convert"][1] for c in n.iter()):
				n.set("source", SUBST["source"][0])
			if n.get("render") == SUBST["render"][1]:
				n.set("render", SUBST["render"][0])
			if n.tag == "convert" and n.get("type") == SUBST["convert"][1]:
				n.set("type", SUBST["convert"][0])
	return ET.tostring(root)


def drop_weather(path):
	root = ET.parse(path).getroot()
	for p in list(root.iter()):
		for c in list(p):
			if c.tag == "widget" and (c.get("source") in ("session.OAWeather",) or any(x.tag == "convert" and x.get("type") in ("OAWeather", "CineViewMLAWeather") for x in c.iter())):
				p.remove(c)
	return ET.tostring(root)


# CineView's own components must exist under exactly the names the composer writes
check("component files: Converter/CineViewMLAWeather.py, Renderer/CineViewMLAWeatherPixmap.py, CineViewMLAWeatherData.py",
	os.path.isfile(os.path.join(REPO, "mla/components/Converter/CineViewMLAWeather.py")) and os.path.isfile(os.path.join(REPO, "mla/components/Renderer/CineViewMLAWeatherPixmap.py"))
	and os.path.isfile(os.path.join(REPO, "mla/components/_lib/CineViewMLAWeatherData.py")))

for ipk in IPKS:
	name = os.path.basename(ipk)
	print("=" * 8, name)
	T = tempfile.mkdtemp(prefix="w105_")
	tarfile.open(fileobj=io.BytesIO(ar(ipk)["data.tar.gz"])).extractall(T + "/d", filter="tar")
	SRC = T + "/d/usr/share/enigma2/CineView_FHD_MLA"
	img = "openbh" if ".openbh" in name or "~openbh" in name else "openvix" if ".openvix" in name or "~openvix" in name else "openatv"
	allxml = glob.glob(SRC + "/layouts/*/*/*.xml") + glob.glob(SRC + "/core/*.xml") + glob.glob(SRC + "/generations/g000000/*.xml")
	names = refs(allxml)
	base = {k: names[k] - TRIO[k] for k in names}
	trees = {
		"noweather_b": {k: base[k] | OWN[k] for k in base},
		"weather_b": {k: base[k] | TRIO[k] | OWN[k] for k in base},
		"noweather": {k: set(base[k]) for k in base},
		"weather": {k: base[k] | TRIO[k] for k in base},
	}
	CR = {k: comp_root(T + "/comp_" + k, v) for k, v in trees.items()}
	FACT = SRC + "/generations/g000000"
	fact_weather = count(FACT, "native")

	def run(composer, tree, *args):
		env = dict(os.environ, MLA_SKIN_DIR=T + "/skin", MLA_STATE_DIR=T + "/state", MLA_COMPONENTS_ROOT=CR[tree], MLA_IMAGE=img)
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

	def feats():
		return json.load(open(gen() + "/features.json"))

	def lay_args(model, theme=None):
		return (["--theme", theme] if theme else []) + sum([["--set", "%s=%s" % kv] for kv in MODELS[model].items()], [])

	# --- reproduction of the user's report with the published 1.0.3 composer
	old = T + "/old103.py"; open(old, "w").write(OLD103)
	c = fresh(old)
	rc, out = run(c, "noweather", "validate", "--theme", "navy")
	check(name + " [repro] 1.0.3 composer fails without OAWeather (the reported error)", rc == 1 and "converter OAWeather not installed" in out and "renderer OAWeatherPixmap not installed" in out, out[-300:])

	# --- 1.0.5 on an image WITHOUT OAWeather
	c = fresh(NEW)
	rc, out = run(c, "noweather_b", "rollback", "--to", "factory")  # what postinst does on a first install
	g1 = act()
	check(name + " no OAWeather, first install: factory rebuilt with CineView's weather", rc == 0 and g1 != "g000000" and feats() == {"omitted": [], "builtin": ["weather"]}, (rc, out[-300:]))
	check(name + "   no session.OAWeather widget left, every weather widget kept (%d)" % fact_weather, count(gen(), "native") == 0 and count(gen(), "builtin") == fact_weather and fact_weather > 0, (count(gen(), "native"), count(gen(), "builtin")))
	check(name + "   strict component check (no missing renderer/converter/source)", not strict_missing(gen(), trees["noweather_b"]), strict_missing(gen(), trees["noweather_b"]))
	same = all(canon(f, "builtin") == canon(os.path.join(FACT, os.path.basename(f)), "native") for f in glob.glob(gen() + "/*.xml"))
	check(name + "   identical to the factory design except the 3 names per weather widget (source/converter/renderer)", same)
	check(name + "   lkg follows the rebuilt factory", open(T + "/state/lkg").read().strip() == g1)
	rc, out = run(c, "noweather_b", "recover")
	check(name + "   next start: recover changes nothing", act() == g1 and "rebuilt" not in out, out[-200:])
	ok_models = []
	for model in MODELS:
		for theme in THEMES:
			rc, out = run(c, "noweather_b", "apply", *lay_args(model, theme))
			miss = strict_missing(gen(), trees["noweather_b"]) if rc == 0 else ["rc=%d %s" % (rc, out[-200:])]
			if not miss and count(gen(), "native") == 0 and feats()["builtin"] == ["weather"]:
				ok_models.append((model, theme))
			else:
				print("   ", model, theme, miss[:3])
	check(name + "   6 models x 6 themes apply, strict component check of every generation", len(ok_models) == 36, 36 - len(ok_models))
	rc, out = run(c, "noweather_b", "apply", *lay_args("details"))
	check(name + "   details: InfoBar / Second InfoBar weather widgets present (CineView)", rc == 0 and len(widgets(gen() + "/infobar.xml", "builtin")) > 0 and len(widgets(gen() + "/secondinfobar.xml", "builtin")) > 0)
	victim = sorted(refs([SRC + "/layouts/infobar/classic/screens.openatv.xml"])["Converter"] - TRIO["Converter"])[0]
	broken = {k: set(v) for k, v in trees["noweather_b"].items()}; broken["Converter"].discard(victim)
	CR["broken"] = comp_root(T + "/comp_broken", broken)
	rc, out = run(c, "broken", "validate", *lay_args("classic"))
	check(name + "   validation still blocks a missing NON-optional component (%s)" % victim, rc == 1 and ("converter %s not installed" % victim) in out and "OAWeather" not in out, out[-300:])

	# --- 1.0.5 on an image WITH OAWeather: CineView's components too (they show OAWeather's data while it runs)
	c = fresh(NEW)
	rc, out = run(c, "weather_b", "rollback", "--to", "factory")
	check(name + " with OAWeather: factory rebuilt with CineView's weather components", rc == 0 and act() != "g000000" and count(gen(), "builtin") == fact_weather and count(gen(), "native") == 0, out[-200:])
	rc, out = run(c, "weather_b", "apply", "--theme", "purple", "--set", "infobar=details", "--set", "secondinfobar=cinema")
	check(name + "   apply: strict check", rc == 0 and not strict_missing(gen(), trees["weather_b"]), out[-200:])

	# --- upgrade: a 1.0.4 generation built without the weather (OAWeather missing) -> 1.0.5 brings it back
	c = fresh(SRC + "/mla/engine/composer.py")  # the package's own (1.0.4) composer
	rc, out = run(c, "noweather", "apply", *lay_args("classic", "green"))
	g104 = act()
	check(name + " [1.0.4] generation without weather built by the package's own composer", rc == 0 and count(gen(), "native") == 0 and json.load(open(gen() + "/features.json")) == {"omitted": ["weather"]}, out[-200:])
	shutil.copyfile(NEW, T + "/skin/mla/engine/composer.py")  # upgrade: new engine, state kept
	rc, out = run(T + "/skin/mla/engine/composer.py", "noweather_b", "recover")
	check(name + "   upgrade to 1.0.5 + next start: weather back with CineView's components, selection kept",
		act() != g104 and count(gen(), "builtin") > 0 and json.load(open(gen() + "/selection.json"))["theme"] == "green", out[-300:])
	# --- upgrade from 1.0.0-1.0.3: generation with the OAWeather widgets as they are (no features.json)
	c = fresh(old)
	rc, out = run(c, "weather", "apply", *lay_args("details", "black"))
	g103 = act()
	shutil.copyfile(NEW, T + "/skin/mla/engine/composer.py")
	rc, out = run(T + "/skin/mla/engine/composer.py", "noweather_b", "recover")
	check(name + " [1.0.3] generation with OAWeather widgets, OAWeather removed later: next start rebuilds with CineView's",
		act() != g103 and count(gen(), "native") == 0 and count(gen(), "builtin") > 0 and not strict_missing(gen(), trees["noweather_b"]), out[-300:])

	# --- fallbacks when CineView's own weather components are missing (damaged install)
	c = fresh(NEW)
	rc, out = run(c, "weather", "rollback", "--to", "factory")
	check(name + " [fallback] CineView's components missing, OAWeather present: packs as they are (factory not rebuilt)", rc == 0 and act() == "g000000", out[-200:])
	rc, out = run(c, "noweather", "recover")
	check(name + " [fallback] neither present: weather widgets left out, design applies", count(gen(), "native") == 0 and count(gen(), "builtin") == 0 and not strict_missing(gen(), trees["noweather"]), out[-300:])
	same = all(drop_weather(f) == drop_weather(os.path.join(FACT, os.path.basename(f))) for f in glob.glob(gen() + "/*.xml"))
	check(name + "   everything except the weather widgets identical to factory", same)
	rc, out = run(c, "noweather_b", "recover")
	check(name + " [fallback] CineView's components installed again: next start uses them", count(gen(), "builtin") == fact_weather, out[-300:])

	# --- trial semantics survive a rebuild
	c = fresh(NEW); run(c, "weather", "rollback", "--to", "factory")
	rc, out = run(c, "weather", "apply", "--trial", "--set", "infobar=details")
	gt = act(); j0 = json.load(open(T + "/state/txn.json"))
	rc, out = run(c, "weather_b", "ensure")
	j1 = json.load(open(T + "/state/txn.json"))
	check(name + " trial rebuilt keeps the TRIAL journal on the new generation", j0["state"] == "TRIAL" and j1["state"] == "TRIAL" and j1["gid"] == act() != gt, (j0, j1))
	shutil.rmtree(T, ignore_errors=True)

print("\nRESULT: %s (%d failures)" % ("PASS" if not fails else "FAIL", len(fails)))
sys.exit(1 if fails else 0)
