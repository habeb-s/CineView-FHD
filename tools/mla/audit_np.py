#!/usr/bin/env python3
"""Static audit of a build (user request 2026-10-06 06:13): where can a poster placeholder still appear, and where can
two picons draw at once?
* PLACEHOLDER: screens that still carry the default-poster widgets (tile / icon slices / inner frame / per-size
  default bitmap) -> listed with the poster toggle key and whether the screen has poster-following variants.
* PICON: every Picon renderer per screen, with its converter chain.  Picons whose rectangles overlap inside one
  screen are reported as pairs, with whether their visibility conditions are mutually exclusive
  (ShowIf <key>,True vs <key>,True,Invert with the same poster flag).
usage: audit_np.py <build root>"""
import os
import re
import sys

PH = re.compile(r'pixmap="mla_assets/(poster_tile\.png|poster_icon_[^"]+|px_3f4e65\.png|poster_default_\d+x\d+\.png)"')
WIDGET = re.compile(r'<widget\b[^>]*?(?:/>|>.*?</widget>)', re.S)


def rect(w):
	p = re.search(r'position="(\d+),(\d+)"', w)
	s = re.search(r'size="(\d+),(\d+)"', w)
	if not (p and s):
		return None
	x, y, ww, hh = map(int, p.groups() + s.groups())
	return (x, y, x + ww, y + hh)


def overlap(a, b):
	return a and b and a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def cond(w):
	m = re.search(r'CineViewMLAShowIf">([^<]+)<', w)
	if not m:
		return None
	parts = [p.strip() for p in m.group(1).split(",")]
	key = parts[0]
	inv = "Invert" in parts
	pf = [p for p in parts if p.startswith("poster")]
	return (key, parts[1] if len(parts) > 1 else "True", inv, pf[0] if pf else "")


def exclusive(c1, c2):
	return c1 and c2 and c1[0] == c2[0] and c1[1] == c2[1] and c1[3] == c2[3] and c1[2] != c2[2]


def main(root):
	skin = os.path.join(root, "usr/share/enigma2/CineView_FHD_MLA")
	ph, pic = [], []
	for dp, dn, fn in os.walk(os.path.join(skin, "layouts")):
		for f in fn:
			if not f.endswith(".xml"):
				continue
			p = os.path.join(dp, f)
			rel = os.path.relpath(p, skin)
			src = open(p, encoding="utf-8").read()
			for m in re.finditer(r'<screen name="([^"]+)"[^>]*>(.*?)</screen>', src, re.S):
				name, body = m.group(1), m.group(2)
				n_ph = len(PH.findall(body))
				dyn = ",poster0" in body or ",poster1" in body
				if n_ph:
					keys = sorted(set(re.findall(r'toggle="([^"]+)"', body)))
					ph.append((rel, name, n_ph, dyn, ",".join(k.split(".")[-1] for k in keys)))
				ws = [w for w in WIDGET.findall(body) if 'render="Picon"' in w]
				for i in range(len(ws)):
					for j in range(i + 1, len(ws)):
						if overlap(rect(ws[i]), rect(ws[j])):
							c1, c2 = cond(ws[i]), cond(ws[j])
							pic.append((rel, name, rect(ws[i]), rect(ws[j]), c1, c2, exclusive(c1, c2)))
				vari = [w for w in ws if cond(w)]
				if vari:
					pic.append((rel, name, "variants", len(vari), [cond(w) for w in vari], None, None))
	print("== PLACEHOLDER widgets still present: %d screens" % len(ph))
	for r in sorted(ph):
		print("   %-58s %-32s %3d widgets  dynamic=%s  keys=%s" % r)
	print("== PICON: overlapping pairs and ShowIf variants")
	for r in pic:
		if r[2] == "variants":
			print("   VARIANTS %-50s %-30s %d picons: %s" % (r[0], r[1], r[3], r[4]))
		else:
			print("   OVERLAP  %-50s %-30s %s / %s exclusive=%s  %s | %s" % (r[0], r[1], r[2], r[3], r[6], r[4], r[5]))


if __name__ == "__main__":
	main(sys.argv[1])
