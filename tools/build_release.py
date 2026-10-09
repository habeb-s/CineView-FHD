#!/usr/bin/env python3
"""Build the release packages for PLUGIN_VERSION (updater/CineViewUpdater/plugin.py) from the packages of the base
release named in packaging/release.json.

Per package: the managed files of packaging/release.json are copied from the repository, DEBIAN/postinst is
packaging/postinst.in, the CineView Control plugin.py version strings and DEBIAN/control Version are set to the new
version.  Everything else stays byte-identical to the base package.  gzip members (unpackable by opkg and by the
smart installer's ar + tar fallback).

usage: build_release.py <dir with the base .ipk files> <output dir>"""
import os, shutil, subprocess, sys, tempfile

from release_common import CFG, CTRL, ROOT, ipk_name, managed, new_version, plugin_edits, postinst, vtuple


def build(img, base, new, src_dir, out_dir):
	src = os.path.join(src_dir, ipk_name(img, base))
	work = tempfile.mkdtemp()
	tree = os.path.join(work, "pkg")
	subprocess.check_call(["dpkg-deb", "-R", src, tree])
	for dst, rel in managed(img).items():
		p = os.path.join(tree, dst)
		os.makedirs(os.path.dirname(p), exist_ok=True)
		shutil.copyfile(os.path.join(ROOT, rel), p)
		os.chmod(p, 0o644)
	pi = os.path.join(tree, "DEBIAN", "postinst")
	open(pi, "w", encoding="utf-8").write(postinst(new))
	os.chmod(pi, 0o755)
	ctl = os.path.join(tree, "DEBIAN", "control")
	s = open(ctl, encoding="utf-8").read()
	assert s.count("\nVersion: %s\n" % base) == 1, "control Version is not %s" % base
	open(ctl, "w", encoding="utf-8").write(s.replace("\nVersion: %s\n" % base, "\nVersion: %s\n" % new))
	pp = os.path.join(tree, CTRL, "plugin.py")
	s = open(pp, encoding="utf-8").read()
	for a, b, n in plugin_edits(base, new):
		assert s.count(a) == n, "plugin.py: expected %d x %r" % (n, a)
		s = s.replace(a, b)
	open(pp, "w", encoding="utf-8").write(s)
	out = os.path.join(out_dir, ipk_name(img, new))
	subprocess.check_call(["dpkg-deb", "-Zgzip", "-b", tree, out], stdout=subprocess.DEVNULL)
	shutil.rmtree(work)
	return out


def main(src_dir, out_dir):
	base, new = CFG["base"], new_version()
	if vtuple(new) <= vtuple(base):
		sys.exit("PLUGIN_VERSION %s must be newer than the base release %s" % (new, base))
	os.makedirs(out_dir, exist_ok=True)
	for img in CFG["images"]:
		print(build(img, base, new, src_dir, out_dir))


if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2])
