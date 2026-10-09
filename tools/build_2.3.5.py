#!/usr/bin/env python3
"""Build the CineView FHD 2.3.5 packages from the published 2.3.4 packages.

2.3.5 = 2.3.4 with one fix: Components/Converter/CineViewCPUTemp.py is replaced by
components/Converter/CineViewCPUTemp.py (receiver temperature on every sensor layout).  The only other changes are
the version strings the online updater and the package manager need (control Version, postinst banner,
CineViewControl VERSION / "Official" footer / updater PLUGIN_VERSION).  Skin XML, images, other converters and
renderers are left byte-identical.

All packages are gzip-compressed (as the 2.3.4 OpenViX / OpenBH packages already were).  The 2.3.4 OpenATV package
was zstd-compressed, which the smart installer cannot unpack on receivers without dpkg-deb and without a zstd
binary for tar (device evidence: Octagon SF8008, OpenATV 7.6.0 - "tar (child): zstd: Cannot exec").

usage: build_2.3.5.py <dir with the three 2.3.4 .ipk> <output dir>"""
import os, shutil, subprocess, sys, tempfile

OLD, NEW = "2.3.4", "2.3.5"
HERE = os.path.dirname(os.path.abspath(__file__))
CONVERTER = os.path.join(HERE, "..", "components", "Converter", "CineViewCPUTemp.py")
CTRL = "usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"
TARGET = "usr/lib/enigma2/python/Components/Converter/CineViewCPUTemp.py"
# file -> (old text, new text, exact number of occurrences in 2.3.4)
EDITS = {
	"DEBIAN/control": [("Version: %s\n" % OLD, "Version: %s\n" % NEW, 1)],
	"DEBIAN/postinst": [("CineView FHD %s" % OLD, "CineView FHD %s" % NEW, 1)],
	CTRL + "/plugin.py": [("VERSION='%s'" % OLD, "VERSION='%s'" % NEW, 1), ("Official %s" % OLD, "Official %s" % NEW, 1)],
	CTRL + "/updater.py": [('PLUGIN_VERSION = "%s"' % OLD, 'PLUGIN_VERSION = "%s"' % NEW, 1)],
}


def build(src_ipk, out_dir):
	comp = "gzip"
	work = tempfile.mkdtemp()
	tree = os.path.join(work, "pkg")
	subprocess.check_call(["dpkg-deb", "-R", src_ipk, tree])
	old_conv = os.path.join(tree, TARGET)
	assert os.path.isfile(old_conv), "CineViewCPUTemp.py missing in " + src_ipk
	assert "class CineViewCPUTemp(Poll, Converter)" in open(old_conv, encoding="utf-8").read()
	shutil.copyfile(CONVERTER, old_conv)
	for rel, edits in EDITS.items():
		p = os.path.join(tree, rel)
		s = open(p, encoding="utf-8").read()
		for a, b, n in edits:
			assert s.count(a) == n, "%s: expected %d x %r, found %d" % (rel, n, a, s.count(a))
			s = s.replace(a, b)
		assert OLD not in s, "%s still mentions %s" % (rel, OLD)
		open(p, "w", encoding="utf-8").write(s)
	name = os.path.basename(src_ipk).replace("_%s_" % OLD, "_%s_" % NEW)
	out = os.path.join(out_dir, name)
	subprocess.check_call(["dpkg-deb", "-Z" + comp, "-b", tree, out], stdout=subprocess.DEVNULL)
	shutil.rmtree(work)
	return out, comp


if __name__ == "__main__":
	src, out_dir = sys.argv[1], sys.argv[2]
	os.makedirs(out_dir, exist_ok=True)
	for img in ("openatv", "openvix", "openbh"):
		print("%s (%s)" % build(os.path.join(src, "enigma2-plugin-skins-cineview-%s_%s_all.ipk" % (img, OLD)), out_dir))
