"""Which openatv/enigma2 commit is Slot 8 built from?  Slot 8 ships checked hash-based .pyc (Python 3.14): the
16-byte header holds siphash(source), so a source file matches only if it is byte-identical.
usage: s8src.py <slot8 python dir> <enigma2 git dir> <rev-range>"""
import importlib.util, os, subprocess, sys
PYC, GIT, RANGE = sys.argv[1:4]
files = {}
for d, _, fs in os.walk(PYC):
	for f in fs:
		if f.endswith(".pyc") and "__pycache__" not in d and os.path.isfile(os.path.join(d, f)):
			p = os.path.join(d, f)
			h = open(p, "rb").read(16)
			if int.from_bytes(h[4:8], "little") & 1:
				files[os.path.relpath(p, PYC)[:-1]] = h[8:16]
print("hash-based pyc files:", len(files))
def match(rev):
	ok = bad = miss = 0
	for rel, h in files.items():
		r = subprocess.run(["git", "-C", GIT, "show", "%s:lib/python/%s" % (rev, rel)], capture_output=True)
		if r.returncode:
			miss += 1
			continue
		if importlib.util.source_hash(r.stdout) == h:
			ok += 1
		else:
			bad += 1
	return ok, bad, miss
mode = os.environ.get("MODE", "scan")
revs = subprocess.run(["git", "-C", GIT, "rev-list", RANGE], capture_output=True, text=True).stdout.split()
print("candidate commits:", len(revs))
best = None
for rev in revs:
	ok, bad, miss = match(rev)
	print(rev[:10], "match", ok, "differ", bad, "not in repo", miss, flush=True)
	if bad == 0:
		best = rev
		break
print("RESULT", best)
