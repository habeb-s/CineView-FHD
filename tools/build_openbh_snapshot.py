#!/usr/bin/env python3
"""Build the OpenBH snapshot 20261009 = snapshot 9397853 (Plugin Browser / EPG fixes) + the three OpenBH
components it lost, restored from snapshot 26d1390 (the OpenBH smart-install snapshot until 2026-09-25):
  Components/Converter/CineViewMoviePath.py, Components/Renderer/LukaPosterXEMC.py  (MovieSelection poster, FILE/PATH)
  Components/Renderer/CineViewPosterX.py  (persistent poster cache; otherwise identical to the 9397853 file)
The restored files are kept in components/openbh/ (also used for the OpenBH package).  Everything else is copied
member by member from 9397853.  usage: build_openbh_snapshot.py <out.tar.gz>"""
import gzip, io, os, subprocess, sys, tarfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SNAP = "snapshots/openbh-final-20260923/cineview-live-openbh-final-20260923.tar.gz"
BASE_COMMIT = "93978534f8d36e1530a372db4edf64bbd98c150d"
E2 = "usr/lib/enigma2/python/"
RESTORE = ("Components/Converter/CineViewMoviePath.py", "Components/Renderer/LukaPosterXEMC.py",
           "Components/Renderer/CineViewPosterX.py")
MTIME = 1791504000  # 2026-10-09 00:00 UTC, fixed so the archive is reproducible


def main(out):
	base = subprocess.check_output(["git", "-C", ROOT, "show", "%s:%s" % (BASE_COMMIT, SNAP)])
	src = tarfile.open(fileobj=io.BytesIO(base), mode="r:gz")
	names = {E2 + r for r in RESTORE}
	raw = io.BytesIO()
	with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as dst:
		seen = set()
		for m in src.getmembers():
			if m.name in names:
				continue  # replaced below
			dst.addfile(m, src.extractfile(m) if m.isfile() else None)
			seen.add(m.name)
		for rel in RESTORE:
			data = open(os.path.join(ROOT, "components", "openbh", rel), "rb").read()
			ti = tarfile.TarInfo(E2 + rel)
			ti.size, ti.mode, ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = len(data), 0o644, MTIME, 0, 0, "root", "root"
			assert os.path.dirname(ti.name) in seen, "parent directory missing: " + ti.name
			dst.addfile(ti, io.BytesIO(data))
	with open(out, "wb") as f:
		with gzip.GzipFile(fileobj=f, mode="wb", mtime=MTIME, compresslevel=9, filename="") as gz:
			gz.write(raw.getvalue())
	print(out)


if __name__ == "__main__":
	main(sys.argv[1])
