"""Slot 8: installed CineView MLA files vs the published 1.0.0 package (data.tar), byte for byte.
usage: s8pkgcmp.py <package data dir> <slot8 root copy> <opkg .list>"""
import hashlib, os, sys
DATA, ROOT, LST = sys.argv[1:4]
def h(p):
	return hashlib.sha256(open(p, "rb").read()).hexdigest()
pkg = {}
for d, _, fs in os.walk(DATA):
	for f in fs:
		p = os.path.join(d, f)
		if os.path.isfile(p) and not os.path.islink(p):
			pkg["/" + os.path.relpath(p, DATA)] = h(p)
lst = set(l.split("\t")[0].strip() for l in open(LST) if l.strip())
same, diff, missing = [], [], []
for path, sha in sorted(pkg.items()):
	q = ROOT + path
	if not os.path.exists(q):
		missing.append(path)
	elif h(q) == sha:
		same.append(path)
	else:
		diff.append(path)
print("package files: %d   identical on Slot 8: %d   different: %d   not present: %d" % (len(pkg), len(same), len(diff), len(missing)))
print("opkg .list entries: %d   package files not in .list: %d" % (len(lst), len([p for p in pkg if p not in lst])))
for p in diff:
	print("DIFF", p)
for p in missing:
	print("MISSING", p)
