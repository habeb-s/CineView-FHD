#!/usr/bin/env python3
"""Copy packaging/recording_guard.sh into every script that restarts Enigma2 (between the guard markers).
usage: sync_recording_guard.py [--check]   (--check: exit 1 when a copy differs, change nothing)"""
import os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BEGIN, END = "# >>> cineview recording guard >>>", "# <<< cineview recording guard <<<"
TARGETS = ("install.sh", "install-cineview-smart.sh", "install-openatv-live.sh", "install-openvix-live.sh",
           "install-openbh-live.sh", "activate-installed-safe.sh", "recover-openatv8.sh", "packaging/postinst.in")


def block():
	s = open(os.path.join(ROOT, "packaging", "recording_guard.sh"), encoding="utf-8").read()
	return s[s.index(BEGIN):s.index(END) + len(END)]


def main(check):
	b, bad = block(), 0
	for rel in TARGETS:
		p = os.path.join(ROOT, rel)
		s = open(p, encoding="utf-8").read()
		assert s.count(BEGIN) == 1 and s.count(END) == 1, "%s: guard markers missing" % rel
		new = s[:s.index(BEGIN)] + b + s[s.index(END) + len(END):]
		if new != s:
			bad += 1
			print("%s %s" % ("DIFFERS" if check else "updated", rel))
			if not check:
				open(p, "w", encoding="utf-8").write(new)
		else:
			print("ok      %s" % rel)
	return 1 if (check and bad) else 0


if __name__ == "__main__":
	sys.exit(main("--check" in sys.argv))
