#!/usr/bin/env python3
"""Audit (user request 2026-10-06 06:42): in the InfoBar / SecondInfoBar screens of every pack, which text / info
widgets have NO fully opaque layer behind them (video shows through, its colour tints the panel)?
For every info widget (Label / RunningText / Progress / Picon / named text widget ...) the layers below it (lower
zPosition, rectangle covering the widget's centre) are collected:
  * eLabel / Label / widget backgroundColor -> alpha from the colour (#AARRGGBB, AA=00 opaque) or the theme colour;
  * Pixmap / ePixmap -> alpha of the PNG pixel at the widget's centre (per-pixel alpha).
A widget is OK when at least one layer under it is opaque at that point.
usage: audit_infobg.py <build root> [theme]   -> one line per screen: info widgets, of which not covered + list"""
import os
import re
import sys

from PIL import Image

SCREENS = ("InfoBar", "SecondInfoBar", "SecondInfoBarSimple", "SecondInfoBarECM", "SecondInfoBarECM_CVPosterOff",
	"SecondInfoBar_CVPosterOff", "SecondInfoBarSimple_CVPosterOff")
TAG = re.compile(r'<(eLabel|widget|ePixmap)\b([^>]*?)(/>|>(.*?)</widget>)', re.S)


def attrs(s):
	return dict(re.findall(r'(\w+)="([^"]*)"', s))


def colors(skin, theme):
	c = {}
	gen = os.path.join(skin, "active", "theme.xml")
	for p in [gen] + [os.path.join(skin, "themes", f) for f in sorted(os.listdir(os.path.join(skin, "themes")))]:
		pass
	src = os.path.join(skin, "themes")
	cand = [os.path.join(src, f) for f in os.listdir(src) if theme in f and f.endswith(".xml")]
	files = cand or [gen]
	for p in files:
		if os.path.isfile(p):
			for n, v in re.findall(r'<color name="([^"]+)" value="(#[0-9A-Fa-f]{8})"', open(p, errors="replace").read()):
				c.setdefault(n, v)
	return c


def alpha_of(val, cols):
	v = cols.get(val, val)
	if not v or not v.startswith("#"):
		return None
	if len(v) == 9:
		return int(v[1:3], 16)  # 00 = opaque, FF = transparent
	return 0  # #RRGGBB = opaque


def rect(a):
	try:
		x, y = (int(v) for v in a["position"].split(","))
		w, h = (int(v) for v in a["size"].split(","))
		return x, y, w, h
	except Exception:
		return None


def main(build, theme="navy"):
	skin = os.path.join(build, "usr/share/enigma2/CineView_FHD_MLA")
	cols = colors(skin, theme)
	for sec in ("infobar", "secondinfobar"):
		base = os.path.join(skin, "layouts", sec)
		for pack in sorted(os.listdir(base)):
			p = os.path.join(base, pack, "screens.openatv.xml")
			if not os.path.isfile(p):
				continue
			src = open(p, encoding="utf-8").read()
			for m in re.finditer(r'<screen name="([^"]+)"([^>]*)>(.*?)</screen>', src, re.S):
				name = m.group(1)
				if name not in SCREENS:
					continue
				sa = attrs(m.group(2))
				layers, info = [], []
				for t in TAG.finditer(m.group(3)):
					kind, a = t.group(1), attrs(t.group(2))
					r = rect(a)
					if not r:
						continue
					z = int(a.get("zPosition", "0") or 0)
					render = a.get("render", "")
					if kind == "eLabel" or (kind == "widget" and render == "Label" and "backgroundColor" in a and "transparent" not in a and not (t.group(4) or "").strip().startswith("<convert type=\"CineViewMLAShowIf\">") and "text=" not in (t.group(4) or "")):
						al = alpha_of(a.get("backgroundColor", ""), cols)
						if al is not None and (kind == "eLabel" or a.get("transparent") != "1"):
							layers.append(("color", r, z, al, a.get("backgroundColor")))
					if kind == "ePixmap" or render == "Pixmap":
						px = a.get("pixmap", "")
						fp = os.path.join(skin, px)
						if px and os.path.isfile(fp):
							layers.append(("png", r, z, fp, px))
					if kind == "widget" and render in ("Label", "RunningText", "Progress", "Picon", "CineViewMLALineText") or (kind == "widget" and "name" in a and "render" not in a):
						if render == "Label" and "text=" in (t.group(4) or "") and not re.search(r'<convert type="(?!CineViewMLAShowIf)', t.group(4) or ""):
							continue  # empty decoration label
						info.append((a.get("source") or a.get("name"), r, z))
				bad = []
				for nm, r, z in info:
					cx, cy = r[0] + r[2] // 2, r[1] + r[3] // 2
					opaque = False
					for kind, lr, lz, v, lab in layers:
						if lz >= z or not (lr[0] <= cx < lr[0] + lr[2] and lr[1] <= cy < lr[1] + lr[3]):
							continue
						if kind == "color" and v == 0:
							opaque = True
						elif kind == "png":
							try:
								im = Image.open(v).convert("RGBA")
								sx = int((cx - lr[0]) * im.width / max(1, lr[2])); sy = int((cy - lr[1]) * im.height / max(1, lr[3]))
								if im.getpixel((min(sx, im.width - 1), min(sy, im.height - 1)))[3] == 255:
									opaque = True
							except Exception:
								pass
					bg = alpha_of(sa.get("backgroundColor", ""), cols)
					if bg == 0:
						opaque = True
					if not opaque:
						bad.append("%s@%d,%d" % (nm, r[0], r[1]))
				print("%-14s %-10s %-34s info=%3d  not-opaque=%3d  %s" % (sec, pack, name, len(info), len(bad), " ".join(bad[:8])))


if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "navy")
