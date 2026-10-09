#!/usr/bin/env python3
"""Compare each 2.3.5 package with its 2.3.4 base: same file list and modes, gzip members; the only differing files
must be the converter fix and the version strings.  usage: verify_2.3.5.py <2.3.4 dir> <2.3.5 dir>"""
import filecmp, hashlib, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CONVERTER = os.path.join(HERE, "..", "components", "Converter", "CineViewCPUTemp.py")
CTRL = "usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"
EXPECTED = {"DEBIAN/control", "DEBIAN/postinst", CTRL + "/plugin.py", CTRL + "/updater.py",
            "usr/lib/enigma2/python/Components/Converter/CineViewCPUTemp.py"}


def tree(ipk):
	d = tempfile.mkdtemp()
	subprocess.check_call(["dpkg-deb", "-R", ipk, d])
	files = {}
	for base, dirs, names in os.walk(d):
		for n in dirs + names:
			p = os.path.join(base, n)
			files[os.path.relpath(p, d)] = os.lstat(p).st_mode
	return d, files


ok = True
for img in ("openatv", "openvix", "openbh"):
	a = os.path.join(sys.argv[1], "enigma2-plugin-skins-cineview-%s_2.3.4_all.ipk" % img)
	b = os.path.join(sys.argv[2], "enigma2-plugin-skins-cineview-%s_2.3.5_all.ipk" % img)
	ma = subprocess.check_output(["ar", "t", a], text=True).split()
	mb = subprocess.check_output(["ar", "t", b], text=True).split()
	da, fa = tree(a)
	db, fb = tree(b)
	changed = sorted(p for p in fa if p in fb and os.path.isfile(os.path.join(da, p)) and not filecmp.cmp(os.path.join(da, p), os.path.join(db, p), shallow=False))
	conv_ok = filecmp.cmp(os.path.join(db, "usr/lib/enigma2/python/Components/Converter/CineViewCPUTemp.py"), CONVERTER, shallow=False)
	ctl = open(os.path.join(db, "DEBIAN/control")).read()
	checks = {
		"archive members %s" % " ".join(mb): mb == ["debian-binary", "control.tar.gz", "data.tar.gz"],
		"same file list (%d entries)" % len(fb): set(fa) == set(fb),
		"same file modes": all(fa[p] == fb[p] for p in fa if p in fb),
		"only expected files differ (%d)" % len(changed): set(changed) == EXPECTED,
		"converter = components/Converter/CineViewCPUTemp.py": conv_ok,
		"control Version 2.3.5": "\nVersion: 2.3.5\n" in "\n" + ctl,
	}
	for rel in EXPECTED - {"usr/lib/enigma2/python/Components/Converter/CineViewCPUTemp.py"}:
		s = open(os.path.join(db, rel), encoding="utf-8").read()
		checks["%s: no 2.3.4 left" % os.path.basename(rel)] = "2.3.4" not in s and "2.3.5" in s
	print("== %s  sha256 %s" % (os.path.basename(b), hashlib.sha256(open(b, "rb").read()).hexdigest()))
	for k, v in checks.items():
		print("  %s  %s" % ("PASS" if v else "FAIL", k))
		ok &= v
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
