#!/usr/bin/env python3
"""Static z-order check for enigma2 57b7a51 skins (CineView MLA).

Screen.createGUIScreen() creates renderers ("source=" widgets) and named widgets FIRST and the skin's plain
<eLabel>/<ePixmap> elements (additionalWidgets) LAST.  eWidget::insertIntoParent() puts a child after every
sibling with z <= its own z, so with equal zPosition the element created later is painted on top.
=> an opaque <eLabel backgroundColor=...> with zPosition >= a widget's zPosition covers that widget where they
overlap (the widget is invisible on the TV).

Reports every (screen, eLabel, widget) where an opaque eLabel/ePixmap overlaps a <widget> whose zPosition is
<= the eLabel's zPosition.  Usage: zorder_check.py file.xml [...]
"""
import sys
import xml.etree.ElementTree as ET


def rect(e, scr_size):
	try:
		pos = e.get("position", "0,0").split(",")
		size = e.get("size", "0,0").split(",")
		if size[0] in ("fill",) or e.get("position") == "fill":
			return (0, 0) + scr_size
		x = 0 if pos[0] in ("center", "fill") else int(pos[0])
		y = 0 if pos[1] in ("center", "fill") else int(pos[1])
		w, h = int(size[0]), int(size[1])
		return (x, y, w, h)
	except (ValueError, IndexError):
		return None


def overlap(a, b):
	return a and b and a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def z(e):
	try:
		return int(e.get("zPosition", "0"))
	except ValueError:
		return 0


def check(path):
	bad = []
	root = ET.parse(path).getroot()
	for scr in root.iter("screen"):
		try:
			ss = tuple(int(v) for v in scr.get("size", "1920,1080").split(","))
		except ValueError:
			ss = (1920, 1080)
		statics = [e for e in scr if e.tag in ("eLabel", "ePixmap") and e.get("transparent", "0") != "1"
			and ((e.tag == "ePixmap" and not e.get("alphatest")) or (e.tag == "eLabel" and e.get("backgroundColor")))]
		widgets = [e for e in scr.iter("widget")]
		for s in statics:
			rs = rect(s, ss)
			for w in widgets:
				if z(w) <= z(s) and overlap(rs, rect(w, ss)):
					bad.append((scr.get("name"), s.tag, s.get("position"), s.get("size"), z(s),
						w.get("name") or w.get("source"), w.get("position"), z(w)))
	return bad


def poster_overlaps(path):
	"""Text widgets that are visible while the poster is shown and overlap the poster box.
	A widget is 'visible with posters on' unless it carries CineViewMLAShowIf <toggle>,True,Invert (posters-off twin)
	or CineViewMLAShowIf with another always-false condition for that toggle."""
	bad = []
	root = ET.parse(path).getroot()
	for scr in root.iter("screen"):
		try:
			ss = tuple(int(v) for v in scr.get("size", "1920,1080").split(","))
		except ValueError:
			ss = (1920, 1080)
		posters = [w for w in scr.iter("widget") if w.get("render") == "CineViewMLAPosterX"]
		for pw in posters:
			toggle = pw.get("toggle", "")
			rp = rect(pw, ss)
			for w in scr.iter("widget"):
				if w is pw or w.get("render") not in ("Label", "RunningText", "FixedLabel", None) or (w.get("render") is None and w.get("source")):
					continue
				conv = [c.text or "" for c in w.findall("convert") if c.get("type") == "CineViewMLAShowIf"]
				if any(toggle and c.startswith(toggle) and "Invert" in c for c in conv):
					continue
				if z(w) < z(pw) and overlap(rp, rect(w, ss)):
					bad.append((scr.get("name"), pw.get("position"), pw.get("size"), w.get("name") or w.get("source"), w.get("position"), w.get("size")))
	return bad


if __name__ == "__main__":
	total = 0
	files = [a for a in sys.argv[1:] if not a.startswith("--")]
	for p in files:
		for b in check(p):
			total += 1
			print("%s: screen=%s %s@%s %s z=%d covers widget %s@%s z=%d" % ((p,) + b))
	print("ZORDER_SUMMARY covered=%d files=%d" % (total, len(files)))
	po = 0
	if "--posters" in sys.argv:
		for p in files:
			for b in poster_overlaps(p):
				po += 1
				print("%s: screen=%s poster@%s %s overlaps text %s@%s %s" % ((p,) + b))
		print("POSTER_OVERLAP_SUMMARY overlaps=%d" % po)
	sys.exit(1 if total or po else 0)
