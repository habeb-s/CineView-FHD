#!/usr/bin/env python3
"""P8: package a built MLA tree (tools/mla/build.py output) as an opkg .ipk for OpenATV 8.0.x.

usage: package_ipk.py <build root> <version> <out dir> [--pyc <dir>]

Light protection (user 2026-10-06 20:51, no obfuscation, no licence check, nothing at runtime depends on it):
  --pyc <dir>: the importable Python modules (Components/CineViewMLA*, Plugins/Extensions/CineViewMLA/*) are shipped as
  sourceless .pyc compiled by the RECEIVER's own Python (tools/mla/devtools/device/mkpyc.sh; <dir>/PYVER holds its
  version); preinst then refuses any other Python version with a clear message.  The engine (composer.py, run by path
  by postinst and the plugin) and the guardian scripts stay as they are.  The full source stays in the repository.
  Every package also carries Plugins/Extensions/CineViewMLA/version.json (version, build, commit, date).

Package contents (data.tar.gz, owner root:root, files 0644 / dirs+scripts 0755):
  usr/share/enigma2/CineView_FHD_MLA/...     skin, layout packs, themes, engine, guardian, factory generation g000000
  usr/lib/enigma2/python/Components/...      CineViewMLA* renderers/converters + CineViewMLAPosterMatch
  usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/   CineView Designs (control UI)
  usr/bin/enigma2_pre_start.sh               native OpenATV pre-start hook -> MLA guardian
NOT packaged (runtime state, created/kept on the receiver): the 'active'/'lkg' links, generations other than the
factory one, /etc/enigma2/cineview_mla (selection, journal, profiles).

Maintainer scripts:
  preinst  : OpenATV 7.6 or 8.0 only (distro/imageversion from /usr/lib/enigma.info; device-verified on 8.0.1 /
             enigma2 57b7a51, contracts of 7.6 checked statically: tools/mla/compat_image.py) and refuses to replace a foreign
             /usr/bin/enigma2_pre_start.sh.  Missing/ambiguous image data -> stop (no guessing).
  postinst : first install -> 'active' = factory (Classic, navy).  Upgrade -> the user's current selection is
             re-applied with the new packs (new sealed generation); if that fails, factory is activated.
  prerm    : 'remove' is refused while CineView MLA is the selected skin (select another skin first), so the
             receiver never boots into a missing skin.
  postrm   : 'remove'/'purge' deletes the MLA skin directory (runtime generations, links) and MLA bytecode only;
             /etc/enigma2/cineview_mla (profiles, journal) is kept on 'remove' and deleted on 'purge'.
"""
import io
import os
import sys
import tarfile
import time

PKG = "enigma2-plugin-skins-cineview-fhd-mla"
SKIN = "usr/share/enigma2/CineView_FHD_MLA"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

CONTROL = """Package: {pkg}
Version: {ver}
Description: CineView MLA - multi-layout skin for OpenATV{target}: five design models, six themes, CineView Designs - Design & Development by habeb-s (c) 2026
Section: skins
Priority: optional
Maintainer: habeb-s
License: CineView-Proprietary
Architecture: all
OE: {pkg}
Homepage: {homepage}
Depends: python3-requests, python3-pillow
Source: CineView MLA {ver}
"""

PREINST = r"""#!/bin/sh
# CineView MLA preinst: OpenATV 8.0.x only; never replace a foreign pre-start hook.
INFO=/usr/lib/enigma.info
if [ ! -r "$INFO" ]; then echo "CineView MLA: $INFO missing - cannot identify the image, installation stopped."; exit 1; fi
DISTRO=$(sed -n "s/^distro='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" $INFO | head -1)
VER=$(sed -n "s/^imageversion='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" $INFO | head -1)
MODEL=$(sed -n "s/^machinebuild='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" $INFO | head -1)
echo "CineView MLA: image $DISTRO $VER on $MODEL"
# Supported = the OpenATV enigma2 versions whose contracts were checked against this package (tools/mla/compat_image.py):
#   7.6 and 8.0: no difference.  7.5 and older lack the 'addon' widgets (ColorButtonsSequence / ButtonSequence),
#   MovieInfo FullDescription (7.3: also ServiceListLegacy), so the screens would not build.  Newer versions are
#   refused until they are checked.  No receiver model is excluded.
if [ "$DISTRO" != "openatv" ]; then echo "CineView MLA: image '$DISTRO' is not OpenATV - this package uses OpenATV-only screen contracts. Stopped."; exit 1; fi
case "$VER" in
  7.6|7.6.*|8.0|8.0.*) ;;
  7.[0-5]|7.[0-5].*|6.*|5.*) echo "CineView MLA: OpenATV '$VER' lacks skin features this package needs ('addon' widgets, MovieInfo FullDescription); OpenATV 7.6 or 8.0 required. Stopped."; exit 1;;
  *) echo "CineView MLA: OpenATV '$VER' has not been checked against this package yet (checked: 7.6, 8.0). Stopped."; exit 1;;
esac
PYNEED="@PYNEED@"
if [ -n "$PYNEED" ]; then
  PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)
  if [ "$PYV" != "$PYNEED" ]; then echo "CineView MLA: this package is built for Python $PYNEED (OpenATV 8.0.x); this image has Python '$PYV'. Stopped - nothing was changed."; exit 1; fi
fi
H=/usr/bin/enigma2_pre_start.sh
if [ -e "$H" ] && ! grep -q "CineView MLA guardian" "$H"; then
  echo "CineView MLA: $H belongs to something else - not replacing it. Stopped."; exit 1
fi
exit 0
"""

POSTINST = r"""#!/bin/sh
# CineView MLA postinst: activate factory on first install; re-apply the user's selection on upgrade.
[ -n "$D" ] && exit 0
S=/usr/share/enigma2/CineView_FHD_MLA
E="python3 $S/mla/engine/composer.py"
mkdir -p /etc/enigma2/cineview_mla
if [ ! -e "$S/active" ]; then  # first install (or a dangling link)
  # factory = active, last-known-good and the stored selection (also resets a selection kept from an earlier install)
  $E rollback --to factory >/tmp/cineview_mla_postinst.log 2>&1 || { rm -f "$S/active"; ln -s generations/g000000 "$S/active"; }
  echo "CineView MLA: factory design (Classic, Navy) active."
elif [ "$(readlink $S/active)" != "generations/g000000" ]; then
  if $E apply >/tmp/cineview_mla_postinst.log 2>&1; then
    echo "CineView MLA: your design, theme and settings were kept."
  else
    $E rollback --to factory >>/tmp/cineview_mla_postinst.log 2>&1
    echo "CineView MLA: the previous design could not be kept - the factory design (Classic, Navy) is active."
  fi
fi
echo "CineView MLA installed. Select it in Menu > Setup > User Interface > Skin, then restart the GUI."
exit 0
"""

PRERM = r"""#!/bin/sh
# CineView MLA prerm: do not remove the skin that is currently selected (the box would boot without its skin).
[ -n "$D" ] && exit 0
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
  if grep -q "^config.skin.primary_skin=CineView_FHD_MLA/" /etc/enigma2/settings 2>/dev/null; then
    echo "CineView MLA is the selected skin. Select another skin first (Menu > Setup > User Interface > Skin), then remove the package."
    exit 1
  fi
fi
exit 0
"""

POSTRM = r"""#!/bin/sh
# CineView MLA postrm: remove MLA runtime state only.
[ -n "$D" ] && exit 0
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
  # The whole skin directory is MLA's own namespace (runtime generations, links and the .pyc files OpenATV
  # compiles next to the sources).  Leftover sourceless .pyc converters would stay importable (T8 00:33).
  rm -rf /usr/share/enigma2/CineView_FHD_MLA /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA 2>/dev/null
  P=/usr/lib/enigma2/python/Components
  rm -f $P/CineViewMLA*.pyc $P/Renderer/CineViewMLA*.pyc $P/Converter/CineViewMLA*.pyc 2>/dev/null
  rm -f $P/__pycache__/CineViewMLA* $P/Renderer/__pycache__/CineViewMLA* $P/Converter/__pycache__/CineViewMLA* 2>/dev/null
  [ "$1" = "purge" ] && rm -rf /etc/enigma2/cineview_mla
  echo "CineView MLA removed (/etc/enigma2/cineview_mla kept unless purged)."
fi
exit 0
"""


def _tar(members, gz_path_or_buf):
	tf = tarfile.open(fileobj=gz_path_or_buf, mode="w:gz", format=tarfile.GNU_FORMAT)
	for name, data, mode, kind, target in members:
		ti = tarfile.TarInfo(name)
		ti.uid = ti.gid = 0
		ti.uname = ti.gname = "root"
		ti.mtime = int(time.time())
		if kind == "dir":
			ti.type, ti.mode = tarfile.DIRTYPE, 0o755
			tf.addfile(ti)
		elif kind == "link":
			ti.type, ti.linkname, ti.mode = tarfile.SYMTYPE, target, 0o777
			tf.addfile(ti)
		else:
			ti.size, ti.mode = len(data), mode
			tf.addfile(ti, io.BytesIO(data))
	tf.close()


def _excluded(rel):
	if rel in (SKIN + "/active", SKIN + "/active.tmp", SKIN + "/lkg"):
		return True
	g = SKIN + "/generations/"
	if rel.startswith(g) and not rel.startswith(g + "g000000"):
		return True
	return "__pycache__" in rel.split("/") or rel.endswith(".pyc")


def data_members(build):
	out, dirs = [], set()

	def add_dirs(rel):
		parts = rel.split("/")[:-1]
		for i in range(1, len(parts) + 1):
			d = "/".join(parts[:i])
			if d not in dirs:
				dirs.add(d)
				out.append(("./" + d + "/", None, 0o755, "dir", None))

	for root, dnames, fnames in os.walk(os.path.join(build, "usr")):
		dnames.sort()
		for f in sorted(fnames + [d for d in dnames if os.path.islink(os.path.join(root, d))]):
			full = os.path.join(root, f)
			rel = os.path.relpath(full, build)
			if _excluded(rel):
				continue
			add_dirs(rel)
			if os.path.islink(full):
				out.append(("./" + rel, None, 0, "link", os.readlink(full)))
			else:
				mode = 0o755 if f.endswith(".sh") else 0o644
				out.append(("./" + rel, open(full, "rb").read(), mode, "file", None))
	hook = "usr/bin/enigma2_pre_start.sh"
	add_dirs(hook)
	src = open(os.path.join(REPO, "mla", "guardian", "enigma2_pre_start.sh"), "rb").read()
	assert b"CineView MLA guardian" in src, "pre-start hook must carry the ownership marker"
	out.append(("./" + hook, src, 0o755, "file", None))
	return out


PYC_DIRS = ("usr/lib/enigma2/python/Components/", "usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/")
PLUGIN_DIR = "usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA"


def _pyc_target(rel):
	if not rel.endswith(".py"):
		return False
	if rel.startswith(PLUGIN_DIR + "/"):
		return True
	return rel.startswith(PYC_DIRS[0]) and os.path.basename(rel).startswith("CineViewMLA")


OPENATV_IMAGE_CHECK_START = 'if [ "$DISTRO" != "openatv" ]'
OPENATV_IMAGE_CHECK_END = "esac\n"
IMAGE_CHECKS = {
	# OpenBH: contracts from BlackHole/enigma2 52dedddc314a (5.6.008) and c06a87ef4c09 (6.0.003) - identical
	# differences vs OpenATV (docs/mla/OpenBH_P2_Discovery.md).  TEST BUILDS ONLY until device QA passes.
	"openbh": (
		'if [ "$DISTRO" != "openbh" ]; then echo "CineView MLA: image \'$DISTRO\' is not OpenBH - this is the OpenBH build. Stopped."; exit 1; fi\n'
		'case "$VER" in\n'
		'  5.6|5.6.*|6.0|6.0.*) ;;\n'
		'  *) echo "CineView MLA: OpenBH \'$VER\' has not been checked against this package yet (checked: 5.6, 6.0). Stopped."; exit 1;;\n'
		'esac\n'),
}


# OpenBH 5.6.008 (Slot 5, 2026-10-07): /bin/sh is bash, and bash itself crashes now and then with signal 11
# (1/25 runs of the preinst; 1/100 runs of a 2-line script with no CineView content; BusyBox sh 0/200).  opkg then
# aborts the install ("preinst script returned status -1") and leaves the package half-installed.  On that image
# the maintainer scripts run under BusyBox sh when it is there: the bash part is one test and an exec.  Without
# /bin/busybox the script just continues under /bin/sh, as before.  OpenATV packages are not touched.
SHELL_REEXEC = {
	"openbh": '[ -z "$CVMLA_BBSH" ] && [ -x /bin/busybox ] && CVMLA_BBSH=1 exec /bin/busybox sh "$0" "$@"  # OpenBH: bash /bin/sh crashes rarely (SIGSEGV)\n',
}


def image_shell(image, script):
	"""Maintainer script for `image`: BusyBox sh re-exec right after the shebang where the image needs it."""
	line = SHELL_REEXEC.get(image)
	if not line:
		return script
	assert script.startswith("#!/bin/sh\n")
	return "#!/bin/sh\n" + line + script[len("#!/bin/sh\n"):]


def image_scripts(image, control, preinst, pyneed):
	"""Per-image control description and preinst image check (the only packaging difference between images)."""
	assert image in IMAGE_CHECKS, "unknown image target %s" % image
	a = preinst.index(OPENATV_IMAGE_CHECK_START)
	b = preinst.index(OPENATV_IMAGE_CHECK_END, a) + len(OPENATV_IMAGE_CHECK_END)
	preinst = preinst[:a] + IMAGE_CHECKS[image] + preinst[b:]
	preinst = preinst.replace("(OpenATV 8.0.x)", "(%s)" % image).replace("OpenATV 8.0.x only", "%s only" % image)
	name = {"openbh": "OpenBH"}[image]
	control = control.replace("for OpenATV 8.0 / Python %s" % pyneed, "for %s / Python %s (test build)" % (name, pyneed))
	return control, preinst


def build_ipk(build, ver, outdir, pyc_dir=None):
	import json
	import subprocess
	commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
	members = data_members(build)
	pyneed = ""
	if pyc_dir:
		pyneed = open(os.path.join(pyc_dir, "PYVER")).read().strip()
		swapped = []
		for i, (name, data, mode, kind, target) in enumerate(members):
			rel = name[2:]
			if kind == "file" and _pyc_target(rel):
				blob = open(os.path.join(pyc_dir, rel + "c"), "rb").read()
				members[i] = ("./" + rel + "c", blob, 0o644, "file", None)
				swapped.append(rel)
		assert swapped, "no module compiled"
		print("pyc (Python %s): %d modules -> %s" % (pyneed, len(swapped), ", ".join(os.path.basename(x) for x in swapped)))
	info = {"version": ver, "build": os.path.basename(os.path.normpath(build)), "commit": commit,
		"date": time.strftime("%Y-%m-%d"), "python": pyneed or "source", "copyright": "Design & Development by habeb-s (c) 2026"}
	members.append(("./" + PLUGIN_DIR + "/version.json", json.dumps(info, indent=1).encode(), 0o644, "file", None))
	assert any(m[0].endswith(SKIN + "/generations/g000000/selection.json") for m in members), "factory generation missing"
	data = io.BytesIO()
	_tar(members, data)
	ctrl = io.BytesIO()
	target = " 8.0 / Python %s" % pyneed if pyneed else " 7.6 / 8.0"
	control = CONTROL.format(pkg=PKG, ver=ver, commit=commit, target=target, homepage=os.environ.get("MLA_HOMEPAGE", "https://github.com/habeb-s/CineView-FHD"))
	preinst = PREINST.replace("@PYNEED@", pyneed)
	image = os.environ.get("MLA_TARGET", "openatv")  # image adapter seam; openatv output is unchanged
	if image != "openatv":
		control, preinst = image_scripts(image, control, preinst, pyneed)
	scripts = {"preinst": preinst, "postinst": POSTINST, "prerm": PRERM, "postrm": POSTRM}
	scripts = {k: image_shell(image, v) for k, v in scripts.items()}
	_tar([("./control", control.encode(), 0o644, "file", None)] +
		[("./" + k, scripts[k].encode(), 0o755, "file", None) for k in ("preinst", "postinst", "prerm", "postrm")], ctrl)
	os.makedirs(outdir, exist_ok=True)
	path = os.path.join(outdir, "%s_%s_all.ipk" % (PKG, ver))
	# ipk = ar archive: debian-binary, control.tar.gz, data.tar.gz (opkg accepts ar)
	with open(path, "wb") as f:
		f.write(b"!<arch>\n")
		for name, blob in (("debian-binary", b"2.0\n"), ("control.tar.gz", ctrl.getvalue()), ("data.tar.gz", data.getvalue())):
			hdr = "%-16s%-12d%-6d%-6d%-8s%-10d`\n" % (name, int(time.time()), 0, 0, "100644", len(blob))
			f.write(hdr.encode())
			f.write(blob)
			if len(blob) % 2:
				f.write(b"\n")
	print("%s  (%d entries, data %.1f MB)" % (path, len(members), len(data.getvalue()) / 1e6))
	return path


if __name__ == "__main__":
	a = sys.argv[1:]
	pyc = None
	if "--pyc" in a:
		i = a.index("--pyc")
		pyc = a[i + 1]
		del a[i:i + 2]
	if len(a) != 3:
		print(__doc__)
		sys.exit(2)
	build_ipk(a[0], a[1], a[2], pyc)
