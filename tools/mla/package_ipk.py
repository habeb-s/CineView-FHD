#!/usr/bin/env python3
"""P8: package a built MLA tree (tools/mla/build.py output) as an opkg .ipk for OpenATV 8.0.x.

usage: package_ipk.py <build root> <version> <out dir>

Package contents (data.tar.gz, owner root:root, files 0644 / dirs+scripts 0755):
  usr/share/enigma2/CineView_FHD_MLA/...     skin, layout packs, themes, engine, guardian, factory generation g000000
  usr/lib/enigma2/python/Components/...      CineViewMLA* renderers/converters + CineViewMLAPosterMatch
  usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/   CineView Designs (control UI)
  usr/bin/enigma2_pre_start.sh               native OpenATV pre-start hook -> MLA guardian
NOT packaged (runtime state, created/kept on the receiver): the 'active'/'lkg' links, generations other than the
factory one, /etc/enigma2/cineview_mla (selection, journal, profiles).

Maintainer scripts:
  preinst  : refuses anything but OpenATV 8.0.x (distro/imageversion from /usr/lib/enigma.info; the screen
             contract was verified on 8.0.1 / enigma2 57b7a51) and refuses to replace a foreign
             /usr/bin/enigma2_pre_start.sh.  Missing/ambiguous image data -> stop (no guessing).
  postinst : first install -> 'active' = factory (Classic, navy).  Upgrade -> the user's current selection is
             re-applied with the new packs (new sealed generation); if that fails, factory is activated.
  prerm    : 'remove' is refused while CineView MLA is the selected skin (select another skin first), so the
             receiver never boots into a missing skin.
  postrm   : 'remove'/'purge' deletes the runtime generations/links and bytecode caches of MLA only;
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
Description: CineView FHD MLA skin for OpenATV 8.0.x (layout packs, six themes, CineView Designs control UI)
Section: skins
Priority: optional
Maintainer: habeb-s
License: CineView-Proprietary
Architecture: all
OE: {pkg}
Homepage: https://github.com/habeb-s/CineView-FHD
Depends: python3-requests, python3-pillow
Source: dev/mla-openatv {commit}
"""

PREINST = r"""#!/bin/sh
# CineView MLA preinst: OpenATV 8.0.x only; never replace a foreign pre-start hook.
INFO=/usr/lib/enigma.info
if [ ! -r "$INFO" ]; then echo "CineView MLA: $INFO missing - cannot identify the image, installation stopped."; exit 1; fi
DISTRO=$(sed -n "s/^distro='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" $INFO | head -1)
VER=$(sed -n "s/^imageversion='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" $INFO | head -1)
MODEL=$(sed -n "s/^machinebuild='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" $INFO | head -1)
echo "CineView MLA: image $DISTRO $VER on $MODEL"
if [ "$DISTRO" != "openatv" ]; then echo "CineView MLA: image '$DISTRO' is not supported by this package (OpenATV 8.0.x only). Stopped."; exit 1; fi
case "$VER" in 8.0|8.0.*) ;; *) echo "CineView MLA: OpenATV '$VER' is not verified for this package (8.0.x only). Stopped."; exit 1;; esac
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
  rm -f "$S/active"; ln -s generations/g000000 "$S/active"
  echo "CineView MLA: factory design (Classic, Navy) active."
elif [ "$(readlink $S/active)" != "generations/g000000" ]; then
  if $E apply >/tmp/cineview_mla_postinst.log 2>&1; then
    echo "CineView MLA: your design selection was rebuilt with the new version ($(tail -1 /tmp/cineview_mla_postinst.log))."
  else
    $E rollback --to factory >>/tmp/cineview_mla_postinst.log 2>&1
    echo "CineView MLA: the previous selection could not be rebuilt - factory design activated (see /tmp/cineview_mla_postinst.log)."
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
  S=/usr/share/enigma2/CineView_FHD_MLA
  rm -rf "$S/generations" "$S/active" "$S/active.tmp" "$S/lkg" 2>/dev/null
  rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA 2>/dev/null
  P=/usr/lib/enigma2/python/Components
  rm -f $P/__pycache__/CineViewMLA* $P/Renderer/__pycache__/CineViewMLA* $P/Converter/__pycache__/CineViewMLA* 2>/dev/null
  find "$S" -depth -type d -empty -exec rmdir {} \; 2>/dev/null
  rmdir "$S" 2>/dev/null
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


def build_ipk(build, ver, outdir):
	import subprocess
	commit = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
	members = data_members(build)
	assert any(m[0].endswith(SKIN + "/generations/g000000/selection.json") for m in members), "factory generation missing"
	data = io.BytesIO()
	_tar(members, data)
	ctrl = io.BytesIO()
	_tar([("./control", CONTROL.format(pkg=PKG, ver=ver, commit=commit).encode(), 0o644, "file", None),
		("./preinst", PREINST.encode(), 0o755, "file", None), ("./postinst", POSTINST.encode(), 0o755, "file", None),
		("./prerm", PRERM.encode(), 0o755, "file", None), ("./postrm", POSTRM.encode(), 0o755, "file", None)], ctrl)
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
	if len(sys.argv) != 4:
		print(__doc__)
		sys.exit(2)
	build_ipk(sys.argv[1], sys.argv[2], sys.argv[3])
