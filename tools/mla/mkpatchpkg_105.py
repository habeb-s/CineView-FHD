#!/usr/bin/env python3
"""CineView MLA 1.0.5 = each published 1.0.4 package with
  (a) the boot guardian started from Python's start-up hook instead of the shared pre-start hook file, and
  (b) CineView's own weather components: the weather of the designs works with or without OAWeather.

(a) Why: the images run ONE pre-start hook, the single file /usr/bin/enigma2_pre_start.sh (enigma2.sh of OpenATV
7.6/8.0, OpenBH 5.6/6.0, OpenViX 6.9).  1.0.0-1.0.4 owned that file, so an add-on that also uses it could not be
installed next to CineView MLA, and the Smart Installer / preinst refused CineView MLA where another add-on owned it.
(b) Why: the Classic, Details and Cinema designs show the weather with OAWeather's components (session.OAWeather,
converter OAWeather, renderer OAWeatherPixmap).  Without OAWeather 1.0.0-1.0.3 could not apply them (the reported
error); 1.0.4 left the weather out.  1.0.5 builds those widgets with CineView's own components (own code, own icons,
CineView names - no OAWeather file is copied, replaced or changed): OAWeather's own data while OAWeather runs,
CineView's own lookup (Open-Meteo) otherwise.

data.tar.gz:
  - ./usr/bin/enigma2_pre_start.sh                              removed (CineView MLA no longer owns that file)
  + ./usr/lib/python<PY>/site-packages/cineview_mla_guardian.pth  start-up hook (acts only inside the enigma2 process)
  + <skin>/mla/guardian/prestart.py, cineview_mla_guardian.pth  hook body / reference copy (mla/guardian/)
  ~ <skin>/mla/guardian/guardian.sh                             one run per start (ignores any other caller)
  + Components/CineViewMLAWeatherData.pyc, Converter/CineViewMLAWeather.pyc, Renderer/CineViewMLAWeatherPixmap.pyc
                                                                compiled with the package's Python (UNCHECKED_HASH,
                                                                sourceless, like every other CineView module)
  + <skin>/mla_assets/weather/*.png                             CineView's own weather icons (tools/mla/mk_weather_icons.py)
  ~ <skin>/mla/engine/composer.py                               weather widgets built with CineView's components
  ~ Plugins/Extensions/CineViewMLA/plugin.pyc                   CineView Designs: "Weather city" row (choose the city
                                                                when OAWeather has no saved location); compiled with
                                                                the package's Python like the published one
  ~ CineViewMLA/version.json
control.tar.gz:
  ~ preinst   the "foreign pre-start hook -> stop" check removed; checks the image's site-packages folder instead
  ~ postinst  removes a pre-start hook file left by an earlier CineView MLA - only if it is CineView's own text and
              no other package owns it; 'composer.py ensure' (active design built for the installed components)
  ~ control   Version / Source
Everything else (layout packs, factory generation, other compiled modules, other maintainer script lines) byte for
byte unchanged.  Runs on the build PC (needs Python 3.12 / 3.13 / 3.14 for the .pyc, see EXE).
usage: mkpatchpkg_105.py <1.0.4 ipk> <out dir>"""
import glob, hashlib, io, json, os, re, subprocess, sys, tarfile, tempfile, time

IPK, OUT = sys.argv[1:3]
MI = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
GD = os.path.join(MI, "mla", "guardian")
SKIN = "./usr/share/enigma2/CineView_FHD_MLA"
HOOK = "./usr/bin/enigma2_pre_start.sh"
NEW_FILES = {SKIN + "/mla/guardian/prestart.py": ("prestart.py", 0o644), SKIN + "/mla/guardian/cineview_mla_guardian.pth": ("cineview_mla_guardian.pth", 0o644)}
GUARDIAN = SKIN + "/mla/guardian/guardian.sh"
COMPOSER = SKIN + "/mla/engine/composer.py"
COMP = "./usr/lib/enigma2/python/Components"
WEATHER_MODULES = {  # installed module -> source in the repository
	COMP + "/CineViewMLAWeatherData.py": os.path.join(MI, "mla", "components", "_lib", "CineViewMLAWeatherData.py"),
	COMP + "/Converter/CineViewMLAWeather.py": os.path.join(MI, "mla", "components", "Converter", "CineViewMLAWeather.py"),
	COMP + "/Renderer/CineViewMLAWeatherPixmap.py": os.path.join(MI, "mla", "components", "Renderer", "CineViewMLAWeatherPixmap.py"),
}
PLUGIN_PYC = "./usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/plugin.pyc"
PLUGIN_SRC, PLUGIN_104 = os.path.join(MI, "mla", "plugin", "CineViewMLA", "plugin.py"), os.path.join(MI, "tools", "mla", "plugin_104.py")
SAME = r"""
import marshal, sys
co = marshal.loads(open(sys.argv[1], "rb").read()[16:])
src = compile(open(sys.argv[3], encoding="utf-8").read(), sys.argv[2], "exec")
def same(a, b):
	if type(a) is not type(b): return False
	if hasattr(a, "co_code"):
		keys = ("co_code", "co_names", "co_varnames", "co_filename", "co_name", "co_argcount", "co_flags")
		return all(getattr(a, k) == getattr(b, k) for k in keys) and len(a.co_consts) == len(b.co_consts) and all(same(x, y) for x, y in zip(a.co_consts, b.co_consts))
	return a == b
sys.exit(0 if same(src, co) else 1)
"""
ICON_DIR = SKIN + "/mla_assets/weather"
ICONS = sorted(glob.glob(os.path.join(MI, "mla", "assets", "weather", "*.png")))
R = os.path.expanduser("~/cineview-mla")
EXE = {"3.12": "/usr/bin/python3.12", "3.13": R + "/py313/python/bin/python3.13", "3.14": R + "/py314/python/bin/python3.14"}

PREINST_OLD = '''H=/usr/bin/enigma2_pre_start.sh
if [ -e "$H" ] && ! grep -q "CineView MLA guardian" "$H"; then
  echo "CineView MLA: $H belongs to something else - not replacing it. Stopped."; exit 1
fi
'''
PREINST_NEW = '''# /usr/bin/enigma2_pre_start.sh is not used any more (1.0.5): it is the images' single shared pre-start hook and may
# belong to another add-on.  The guardian starts from Python's start-up hook in this Python's site-packages folder.
if [ ! -d "/usr/lib/python$PYNEED/site-packages" ]; then
  echo "CineView MLA: /usr/lib/python$PYNEED/site-packages is missing on this image - the boot guardian could not start. Stopped - nothing was changed."; exit 1
fi
'''
POSTINST_ANCHOR = 'echo "CineView MLA installed. Select it in Menu > Setup > User Interface > Skin, then restart the GUI."\n'
POSTINST_ADD = '''# 1.0.5: the guardian starts from Python's start-up hook.  A pre-start hook file left by an earlier CineView MLA is
# removed only if it is still CineView's own text and no other package owns it; another add-on's hook is never touched.
H=/usr/bin/enigma2_pre_start.sh
if [ -f "$H" ] && grep -q "Only calls the CineView MLA guardian" "$H" 2>/dev/null; then
  OWNER=""
  for L in /var/lib/opkg/info/*.list /usr/lib/opkg/info/*.list; do
    [ -f "$L" ] || continue
    case "$L" in */enigma2-plugin-skins-cineview-fhd-mla.list) continue ;; esac
    grep -q "^/usr/bin/enigma2_pre_start.sh\\([[:space:]]\\|$\\)" "$L" 2>/dev/null && OWNER="$L"
  done
  if [ -z "$OWNER" ]; then
    rm -f "$H" && echo "CineView MLA: its pre-start hook of earlier versions was removed (the guardian now starts from Python's start-up hook)."
  fi
fi
# 1.0.5: the active design is built for the components installed now (CineView's own weather components) - also when
# the factory design is active, which an upgrade does not re-apply.  Never fatal: the guardian does the same at the
# next start.
$E ensure >>/tmp/cineview_mla_postinst.log 2>&1 || true
'''


def ar(p):
	d = open(p, "rb").read(); i, o = 8, {}
	while i < len(d):
		n = d[i:i+16].decode().strip().rstrip("/"); s = int(d[i+48:i+58]); i += 60; o[n] = d[i:i+s]; i += s + s % 2
	return o


parts = ar(IPK)
ctl = tarfile.open(fileobj=io.BytesIO(parts["control.tar.gz"])); cf = {m.name: ctl.extractfile(m).read() for m in ctl.getmembers() if m.isfile()}
dat = tarfile.open(fileobj=io.BytesIO(parts["data.tar.gz"])); members = [(m, dat.extractfile(m).read() if m.isfile() else None) for m in dat.getmembers()]
names = [m.name for m, b in members]
info = json.loads([b for m, b in members if m.name.endswith("CineViewMLA/version.json")][0])
old = re.search(rb"^Version: (.*)$", cf["./control"], re.M).group(1).decode()
assert old.startswith("1.0.4"), old
new = "1.0.5" + old[len("1.0.4"):]
pre = cf["./preinst"].decode()
py = re.search(r'^PYNEED="(3\.\d+)"$', pre, re.M).group(1)
assert py == info["python"], (py, info["python"])
assert HOOK in names and GUARDIAN in names and not any(n in names for n in NEW_FILES)
assert [n for n in names if n.startswith("./usr/bin")] == ["./usr/bin", HOOK], [n for n in names if n.startswith("./usr/bin")]
SITE = "./usr/lib/python%s/site-packages" % py
assert not any(n.startswith("./usr/lib/python") for n in names)
assert COMPOSER in names and not any(n.startswith(ICON_DIR) for n in names) and not any(n[:-1] in WEATHER_MODULES for n in names if n.endswith(".pyc"))
assert len(ICONS) == 10, ICONS
assert all(d in names for d in (COMP, COMP + "/Converter", COMP + "/Renderer", SKIN + "/mla_assets")), "component / asset folders"  # tarfile names dirs without "/"
assert [b for m, b in members if m.name == COMPOSER][0] == open(os.path.join(MI, "tools", "mla", "composer_104.py"), "rb").read(), "packaged composer differs from 1.0.4"
composer_new = open(os.path.join(MI, "mla", "engine", "composer.py"), "rb").read()
pycs = {}
with tempfile.TemporaryDirectory() as td:
	for rel, src in WEATHER_MODULES.items():
		out = os.path.join(td, "m.pyc")
		subprocess.run([EXE[py], "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], dfile=sys.argv[3], doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)", src, out, rel[1:]], check=True)
		pycs[rel + "c"] = open(out, "rb").read()
	# CineView Designs: the packaged plugin.pyc must be the published 1.0.4 source (tools/mla/plugin_104.py) compiled
	# with this Python; it is replaced by the repository's plugin.py compiled the same way
	old_pyc = os.path.join(td, "old.pyc"); open(old_pyc, "wb").write([b for m, b in members if m.name == PLUGIN_PYC][0])
	assert subprocess.run([EXE[py], "-c", SAME, old_pyc, PLUGIN_PYC[1:-1], PLUGIN_104]).returncode == 0, "packaged plugin.pyc is not the 1.0.4 plugin"
	out = os.path.join(td, "plugin.pyc")
	subprocess.run([EXE[py], "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], dfile=sys.argv[3], doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)", PLUGIN_SRC, out, PLUGIN_PYC[1:-1]], check=True)
	plugin_new = open(out, "rb").read()

guardian_new = open(os.path.join(GD, "guardian.sh"), "rb").read()
gold = [b for m, b in members if m.name == GUARDIAN][0]
# the packaged guardian must be exactly the 1.0.4 one, i.e. the new one minus the 1.0.5 header and single-run guard
assert gold == open(os.path.join(MI, "tools", "mla", "guardian_104.sh"), "rb").read(), "packaged guardian differs from 1.0.4"
info.update(version=new, date=time.strftime("%Y-%m-%d"), fix="boot guardian started by Python's start-up hook (/usr/bin/enigma2_pre_start.sh left to other add-ons); CineView's own weather components (OAWeather's data while it runs with its saved location, Open-Meteo otherwise); Weather city in CineView Designs")

buf = io.BytesIO(); tf = tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT)
for m, b in members:
	if m.name in (HOOK, "./usr/bin", "./usr/bin/"):
		continue  # no longer CineView's file
	if m.name == GUARDIAN:
		b = guardian_new
	elif m.name == COMPOSER:
		b = composer_new
	elif m.name == PLUGIN_PYC:
		b = plugin_new
	elif m.name.endswith("CineViewMLA/version.json"):
		b = json.dumps(info, indent=1).encode()
	if b is not None:
		m.size = len(b); tf.addfile(m, io.BytesIO(b))
	else:
		tf.addfile(m)
	if m.name == GUARDIAN:  # the two new guardian files next to it
		for rel, (src, mode) in NEW_FILES.items():
			data = open(os.path.join(GD, src), "rb").read()
			ti = tarfile.TarInfo(rel); ti.uid = ti.gid = 0; ti.uname = ti.gname = "root"; ti.mtime = int(time.time()); ti.mode = mode; ti.size = len(data)
			tf.addfile(ti, io.BytesIO(data))
for rel, data in sorted(pycs.items()):  # CineView's weather modules (their folders are already in the package)
	ti = tarfile.TarInfo(rel); ti.uid = ti.gid = 0; ti.uname = ti.gname = "root"; ti.mtime = int(time.time()); ti.mode = 0o644; ti.size = len(data)
	tf.addfile(ti, io.BytesIO(data))
ti = tarfile.TarInfo(ICON_DIR); ti.type = tarfile.DIRTYPE; ti.mode = 0o755; ti.uid = ti.gid = 0; ti.uname = ti.gname = "root"; ti.mtime = int(time.time())
tf.addfile(ti)
for icon in ICONS:
	data = open(icon, "rb").read()
	ti = tarfile.TarInfo(ICON_DIR + "/" + os.path.basename(icon)); ti.uid = ti.gid = 0; ti.uname = ti.gname = "root"; ti.mtime = int(time.time()); ti.mode = 0o644; ti.size = len(data)
	tf.addfile(ti, io.BytesIO(data))
for d in ("./usr/lib/python%s" % py, SITE):
	ti = tarfile.TarInfo(d); ti.type = tarfile.DIRTYPE; ti.mode = 0o755; ti.uid = ti.gid = 0; ti.uname = ti.gname = "root"; ti.mtime = int(time.time())
	tf.addfile(ti)
pth = open(os.path.join(GD, "cineview_mla_guardian.pth"), "rb").read()
ti = tarfile.TarInfo(SITE + "/cineview_mla_guardian.pth"); ti.uid = ti.gid = 0; ti.uname = ti.gname = "root"; ti.mtime = int(time.time()); ti.mode = 0o644; ti.size = len(pth)
tf.addfile(ti, io.BytesIO(pth))
tf.close()

assert PREINST_OLD in pre, "preinst hook check not found"
cf["./preinst"] = pre.replace(PREINST_OLD, PREINST_NEW).encode()
post = cf["./postinst"].decode()
assert post.count(POSTINST_ANCHOR) == 1, "postinst anchor"
cf["./postinst"] = post.replace(POSTINST_ANCHOR, POSTINST_ADD + POSTINST_ANCHOR).encode()
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
print("%s  python %s  %s" % (os.path.basename(path), py, hashlib.sha256(open(path, "rb").read()).hexdigest()))
