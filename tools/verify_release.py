#!/usr/bin/env python3
"""Check release packages against their base packages and against the repository source.

  - gzip members; file list = base list + managed files; unchanged modes for existing files;
  - the only differing files are the managed files, DEBIAN/control, DEBIAN/postinst and CineView Control plugin.py;
  - managed files and postinst are byte-identical to the repository (packaging/release.json, packaging/postinst.in);
  - control Version, plugin.py strings and updater PLUGIN_VERSION all equal the version.

Used by the release workflow before publishing, and on an already published version to detect source changes
that were not given a new PLUGIN_VERSION.  usage: verify_release.py <base dir> <package dir> [version]"""
import filecmp, hashlib, os, subprocess, sys, tempfile

from release_common import CFG, CTRL, ROOT, ipk_name, managed, new_version, plugin_edits, postinst


def tree(ipk):
	d = tempfile.mkdtemp()
	subprocess.check_call(["dpkg-deb", "-R", ipk, d])
	files = {}
	for base, dirs, names in os.walk(d):
		for n in dirs + names:
			p = os.path.join(base, n)
			files[os.path.relpath(p, d)] = os.lstat(p).st_mode
	return d, files


def verify(base_dir, pkg_dir, new):
	base, ok = CFG["base"], True
	for img in CFG["images"]:
		a, b = os.path.join(base_dir, ipk_name(img, base)), os.path.join(pkg_dir, ipk_name(img, new))
		da, fa = tree(a)
		db, fb = tree(b)
		mg = managed(img)
		allowed = set(mg) | {"DEBIAN/control", "DEBIAN/postinst", CTRL + "/plugin.py"}
		changed = {p for p in fa if p in fb and os.path.isfile(os.path.join(da, p))
		           and not filecmp.cmp(os.path.join(da, p), os.path.join(db, p), shallow=False)}
		ctl = open(os.path.join(db, "DEBIAN/control"), encoding="utf-8").read()
		plug = open(os.path.join(db, CTRL, "plugin.py"), encoding="utf-8").read()
		upd = open(os.path.join(db, CTRL, "updater.py"), encoding="utf-8").read()
		checks = [
			("gzip members", subprocess.check_output(["ar", "t", b], text=True).split() == ["debian-binary", "control.tar.gz", "data.tar.gz"]),
			("file list = base + managed (%d -> %d)" % (len(fa), len(fb)), set(fb) == set(fa) | set(mg) | {os.path.dirname(p) for p in mg}),
			("modes unchanged", all(fa[p] == fb[p] for p in fa if p in fb and p not in mg)),
			("only allowed files differ (%d)" % len(changed), changed <= allowed),
			("managed files = repository (%d)" % len(mg), all(filecmp.cmp(os.path.join(db, d), os.path.join(ROOT, s), shallow=False) for d, s in mg.items())),
			("postinst = packaging/postinst.in", open(os.path.join(db, "DEBIAN/postinst"), encoding="utf-8").read() == postinst(new)),
			("control Version %s" % new, "\nVersion: %s\n" % new in "\n" + ctl),
			("plugin.py strings %s" % new, all(x[1] in plug and x[0] not in plug for x in plugin_edits(base, new))),
			("updater PLUGIN_VERSION %s" % new, 'PLUGIN_VERSION = "%s"' % new in upd),
		]
		print("== %s  sha256 %s" % (os.path.basename(b), hashlib.sha256(open(b, "rb").read()).hexdigest()))
		for label, good in checks:
			print("  %s  %s" % ("PASS" if good else "FAIL", label))
			ok &= good
		if not changed <= allowed:
			print("  unexpected changes: %s" % ", ".join(sorted(changed - allowed)))
	return ok


if __name__ == "__main__":
	version = sys.argv[3] if len(sys.argv) > 3 else new_version()
	good = verify(sys.argv[1], sys.argv[2], version)
	print("RESULT", "PASS" if good else "FAIL")
	sys.exit(0 if good else 1)
