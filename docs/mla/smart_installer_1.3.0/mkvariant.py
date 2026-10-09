#!/usr/bin/env python3
"""Range variants of the APPROVED CineView MLA 1.0.1 packages (Smart Installer 1.3.0).

A variant = the approved package of the same image with ONLY these differences:
  * the 15 sourceless .pyc modules compiled from the same sources with another Python minor version
    (the sources are proven to be the approved ones: recompiling them with the approved package's Python gives
    byte-identical .pyc - checked here for every module before anything is written);
  * version.json (version / python fields);
  * control: Version + Description;
  * preinst: the single-version case is replaced by "image version >= minimum" and, on OpenATV, a capability check of
    the two Enigma2 components the design needs (Components/Addons, MovieInfo 'FullDescription').
Skin, layouts, themes, engine, guardian, postinst, prerm and postrm are copied byte for byte from the approved package.
usage: mkvariant.py <approved.ipk> <image> <python exe> <variant version> <min image version> <out dir>
"""
import hashlib, io, json, os, py_compile, re, subprocess, sys, tarfile, tempfile, time

APPROVED, IMAGE, PYEXE, VER, MINVER, OUT = sys.argv[1:7]
PKG = "enigma2-plugin-skins-cineview-fhd-mla"
BUILD = {"openatv": "build_fatv", "openbh": "build_fopenbh", "openvix": "build_fopenvix"}[IMAGE]
NAME = {"openatv": "OpenATV", "openbh": "OpenBH", "openvix": "OpenViX"}[IMAGE]
ROOT = os.path.expanduser("~/cineview-mla")


def ar_read(path):
	data = open(path, "rb").read(); assert data[:8] == b"!<arch>\n"; i, out = 8, {}
	while i < len(data):
		name = data[i:i + 16].decode().strip().rstrip("/"); size = int(data[i + 48:i + 58]); i += 60
		out[name] = data[i:i + size]; i += size + (size % 2)
	return out


def pyver(exe):
	return subprocess.run([exe, "-c", "import sys;print('%d.%d'%sys.version_info[:2])"], capture_output=True, text=True).stdout.strip()


def compile_with(exe, src, rel):
	with tempfile.TemporaryDirectory() as td:
		out = os.path.join(td, "m.pyc")
		subprocess.run([exe, "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], dfile='/'+sys.argv[3], doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)", src, out, rel], check=True)
		return open(out, "rb").read()


parts = ar_read(APPROVED)
ctl = tarfile.open(fileobj=io.BytesIO(parts["control.tar.gz"]))
cfiles = {m.name.lstrip("./"): ctl.extractfile(m).read() for m in ctl.getmembers() if m.isfile()}
dat = tarfile.open(fileobj=io.BytesIO(parts["data.tar.gz"]))
members = [(m, dat.extractfile(m).read() if m.isfile() else None) for m in dat.getmembers()]
appr_info = json.loads([b for m, b in members if m.name.endswith("CineViewMLA/version.json")][0])
appr_py = appr_info["python"]
exe_for = {"3.12": "/usr/bin/python3.12", "3.13": ROOT + "/py313/python/bin/python3.13", "3.14": ROOT + "/py314/python/bin/python3.14"}
newpy = pyver(PYEXE)

# 1. the sources in the build tree ARE the approved ones: recompile with the approved Python -> identical bytes
pycs = [(m, b) for m, b in members if m.isfile() and m.name.endswith(".pyc")]
assert len(pycs) == 15, len(pycs)
swap = {}
for m, blob in pycs:
	rel = m.name.lstrip("./")[:-1]
	src = os.path.join(ROOT, BUILD, rel)
	assert compile_with(exe_for[appr_py], src, rel) == blob, "source differs from the approved .pyc: " + rel
	swap[m.name] = compile_with(PYEXE, src, rel)
print("sources proven identical to the approved package (%d modules, Python %s); recompiled with Python %s" % (len(pycs), appr_py, newpy))

# 2. data: approved members, only .pyc + version.json replaced
info = dict(appr_info, version=VER, python=newpy, date=time.strftime("%Y-%m-%d"), variant_of=appr_info["version"])
buf = io.BytesIO(); tf = tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT)
for m, blob in members:
	if m.name in swap:
		blob = swap[m.name]
	elif m.name.endswith("CineViewMLA/version.json"):
		blob = json.dumps(info, indent=1).encode()
	if blob is not None:
		m.size = len(blob); tf.addfile(m, io.BytesIO(blob))
	else:
		tf.addfile(m)
tf.close(); data = buf.getvalue()

# 3. control + preinst
control = cfiles["control"].decode()
control = re.sub(r"^Version: .*$", "Version: " + VER, control, flags=re.M)
control = re.sub(r"(multi-layout skin for )[^:]*:", r"\g<1>%s %s+ / Python %s:" % (NAME, MINVER, newpy), control)
control = re.sub(r"^Source: .*$", "Source: CineView MLA " + VER, control, flags=re.M)
pre = cfiles["preinst"].decode()
a = pre.index('case "$VER" in'); b = pre.index("esac\n", a) + len("esac\n")
gate = (
	'# Smart Installer 1.3.0 range package: %s %s and newer whose Enigma2 provides what the design uses\n'
	'# (static contract check against every release line in the range - rangecheck/out).  No model is excluded.\n'
	'MAJ=${VER%%%%.*}; REST=${VER#*.}; MIN=${REST%%%%.*}\n'
	'case "$MAJ$MIN" in *[!0-9]*|"") echo "CineView MLA: %s version \'$VER\' cannot be read. Stopped."; exit 1;; esac\n'
	'if [ "$MAJ" -lt %s ] || { [ "$MAJ" -eq %s ] && [ "$MIN" -lt %s ]; }; then echo "CineView MLA: %s \'$VER\' is older than %s. Stopped."; exit 1; fi\n'
) % (NAME, MINVER, NAME, MINVER.split(".")[0], MINVER.split(".")[0], MINVER.split(".")[1], NAME, MINVER)
if IMAGE == "openatv":
	gate += (
		'E=/usr/lib/enigma2/python\n'
		'ls $E/Components/Addons/ColorButtonsSequence.py* >/dev/null 2>&1 || { echo "CineView MLA: this OpenATV has no Components/Addons (colour-button bars, pagers) - the design needs it. Stopped."; exit 1; }\n'
		'grep -aq FullDescription $E/Components/Converter/MovieInfo.py* 2>/dev/null || { echo "CineView MLA: this OpenATV MovieInfo has no FullDescription - the design needs it. Stopped."; exit 1; }\n')
pre = pre[:a] + gate + pre[b:]
pre = re.sub(r'PYNEED="[0-9.]*"', 'PYNEED="%s"' % newpy, pre)
pre = pre.replace("(OpenATV 8.0.x)", "(OpenATV %s+)" % MINVER).replace("OpenATV 8.0.x only", "OpenATV %s+ only" % MINVER)
if IMAGE != "openatv":
	pre = pre.replace("only; never replace", "%s+ only; never replace" % MINVER, 1)
pre = re.sub(r"^# Supported = .*\n(^#   .*\n)*", "", pre, flags=re.M)
cfiles["control"], cfiles["preinst"] = control.encode(), pre.encode()
cb = io.BytesIO(); ct = tarfile.open(fileobj=cb, mode="w:gz", format=tarfile.GNU_FORMAT)
for m in ctl.getmembers():
	if m.isfile():
		blob = cfiles[m.name.lstrip("./")]; m.size = len(blob); ct.addfile(m, io.BytesIO(blob))
	else:
		ct.addfile(m)
ct.close()

os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "%s_%s_all.ipk" % (PKG, VER))
with open(path, "wb") as f:
	f.write(b"!<arch>\n")
	for name, blob in (("debian-binary", parts["debian-binary"]), ("control.tar.gz", cb.getvalue()), ("data.tar.gz", data)):
		f.write(("%-16s%-12d%-6d%-6d%-8s%-10d`\n" % (name, int(time.time()), 0, 0, "100644", len(blob))).encode()); f.write(blob)
		if len(blob) % 2: f.write(b"\n")
print(path, hashlib.sha256(open(path, "rb").read()).hexdigest())
