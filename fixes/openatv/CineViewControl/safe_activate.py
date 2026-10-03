#!/usr/bin/env python3
"""ISS-02 guard for the stable CineViewControl (OpenATV).

Root cause (static + device evidence, docs/mla/ISS-01_ISS-02_evidence.md):
  Save in CineView Control (plugin.py keySave: shutil.copy2(layout, skin.xml)) and
  activate.sh (cp -f layout skin.xml, also triggered automatically by smartdeps.sh at
  session start when PosterX / weather / bitrate is missing) REPLACE the live skin.xml
  with a skin.layout-XYZ-*.xml file.  The accepted design only exists in the live
  skin.xml (it was produced by later live fixes that were never written back to the 30
  layout files), so the replacement silently reverts ~24-30 accepted screens
  (SecondInfoBar two-event layout, EPG, EventView, Hotkey, Language, ...).

Guard: replace skin.xml only if every screen OTHER than the ones the poster/weather
variants are allowed to change is identical; otherwise keep the live file and log why.

usage: safe_activate.py <layout source xml> <live skin.xml> [allowed screen,...]
exit 0 = replaced, 3 = refused (live file kept), 2 = usage / parse error
"""
import hashlib
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET

ALLOWED_DEFAULT = ("InfoBar", "ChannelSelection")
LOG = "/tmp/cineview-safe-activate.log"


def screens(path):
	return {s.get("name"): hashlib.sha1(ET.tostring(s)).hexdigest() for s in ET.parse(path).getroot().iter("screen") if s.get("name")}


def log(msg):
	try:
		with open(LOG, "a") as f:
			f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
	except OSError:
		pass
	print(msg)


def main(argv):
	if len(argv) < 2:
		print(__doc__)
		return 2
	src, live = argv[0], argv[1]
	allowed = set(argv[2].split(",")) if len(argv) > 2 else set(ALLOWED_DEFAULT)
	try:
		a, b = screens(src), screens(live)
	except (OSError, ET.ParseError) as e:
		log(f"refused: cannot parse ({e})")
		return 2
	changed = sorted(n for n in set(a) | set(b) if n not in allowed and a.get(n) != b.get(n))
	if changed:
		log(f"refused: {os.path.basename(src)} would change {len(changed)} accepted screen(s): {', '.join(changed[:12])}{' ...' if len(changed) > 12 else ''}")
		return 3
	backup = live + ".before-activate"
	shutil.copy2(live, backup)
	tmp = live + ".tmp"
	shutil.copy2(src, tmp)
	os.replace(tmp, live)
	log(f"replaced {live} from {os.path.basename(src)} (backup {backup})")
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
