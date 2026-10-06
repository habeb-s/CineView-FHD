#!/usr/bin/env python3
"""t87 analysis: are the information areas of the InfoBar family fully opaque on the receiver?
Input: OSD-only grabs (grab?mode=osd, RGBA = the real framebuffer alpha) named <model>_<theme>_<screen>.png and the
deployed build (screen XML).  For every information widget of that screen (same rule as tools/mla/infoplate.py) the
pixels inside its rectangle are checked: alpha must be 255 everywhere (video cannot show through or tint it).
A widget whose rectangle is fully transparent in the grab (alpha 0: hidden variant / empty) is skipped.
Also writes composites of the real OSD over solid red / yellow / white / dark: <name>_bg.png (2x2 sheet).
usage: osd_alpha.py <build root> <shots dir>"""
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import infoplate as IP  # noqa: E402

PACK = {  # model -> (infobar pack, secondinfobar pack, pvr pack)
	"classic": ("classic", "classic", "classic"), "details": ("details", "details", "cover"), "cinema": ("cinema", "cinema", "cinema"),
	"modern": ("modern", "modern", "modern"), "minimal": ("minimal", "minimal", "minimal")}
SCREEN = {"ib": ("infobar", 0, "InfoBar"), "sib": ("secondinfobar", 1, "SecondInfoBar"), "mp": ("pvr", 2, "MoviePlayer")}
CORNER = 17  # largest pill radius of the InfoBar family
BGS = (("red", (200, 20, 20)), ("yellow", (240, 220, 30)), ("white", (250, 250, 250)), ("dark", (12, 12, 14)))


def info_rects(skin, sec, pack, name):
	p = os.path.join(skin, "layouts", sec, pack, "screens.openatv.xml")
	src = open(p, encoding="utf-8").read()
	m = re.search(r'<screen name="%s"([^>]*)>(.*?)</screen>' % re.escape(name), src, re.S)
	out = []
	# widget positions are relative to the screen's own position (MoviePlayer bar at 150,67)
	sp = re.search(r'position="(\d+),(\d+)"', m.group(1)) if m else None
	ox, oy = (int(sp.group(1)), int(sp.group(2))) if sp else (0, 0)
	for t in IP.TAG.finditer(m.group(2) if m else ""):
		a = IP.attrs(t.group(3))
		r = IP.rect(a)
		if r and IP.is_info(t.group(2), a, t.group(5) or ""):
			out.append(((a.get("source") or a.get("name") or "?"), [r[0] + ox, r[1] + oy, r[2], r[3]]))
	# a bar-type screen (not full screen, e.g. MoviePlayer 150,67 1620x150 with its widgets in <panel
	# name="PlayerTemplate"/>): the whole bar is information and must be opaque
	sz = re.search(r'size="(\d+),(\d+)"', m.group(1)) if m else None
	if sz and (int(sz.group(1)), int(sz.group(2))) != (1920, 1080):
		out.append(("screen:" + name, [ox, oy, int(sz.group(1)), int(sz.group(2))]))
	return out


def main(build, shots):
	skin = os.path.join(build, "usr/share/enigma2/CineView_FHD_MLA")
	total_fail, total_edge = 0, 0
	for f in sorted(os.listdir(shots)):
		m = re.match(r"(\w+?)_(\w+?)_(ib|sib|mp)_osd\.png$", f)
		if not m:
			continue
		model, theme, scr = m.groups()
		sec, idx, name = SCREEN[scr]
		im = Image.open(os.path.join(shots, f)).convert("RGBA")
		a = im.getchannel("A")
		px = a.load()
		checked, fails, edges = 0, [], 0
		for src, r in info_rects(skin, sec, PACK[model][idx], name):
			box = (max(0, r[0]), max(0, r[1]), min(1920, r[0] + r[2]), min(1080, r[1] + r[3]))
			if box[2] <= box[0] or box[3] <= box[1]:
				continue
			reg = a.crop(box)
			hist = reg.histogram()
			n = sum(hist)
			if hist[0] == n:
				continue  # nothing drawn there (hidden variant / empty field)
			checked += 1
			if hist[255] == n:
				continue
			# classify every non-opaque pixel (2026-10-06, t87e Modern):
			#   edge  = alpha >= 250: anti-aliased edge of a rounded shape over an opaque base (<2 % video, invisible)
			#   corner = inside the CORNER x CORNER corner squares of the rectangle: outside a rounded pill / card shape
			#   REAL  = anything else -> video shows through or tints the information area (failure)
			real, corner, edge = 0, 0, 0
			for y in range(box[1], box[3]):
				for x in range(box[0], box[2]):
					v = px[x, y]
					if v == 255:
						continue
					dx = min(x - r[0], r[0] + r[2] - 1 - x)
					dy = min(y - r[1], r[1] + r[3] - 1 - y)
					if v >= 250:
						edge += 1
					elif dx < CORNER and dy < CORNER:
						corner += 1
					else:
						real += 1
			edges += 1 if (edge or corner) and not real else 0
			if real:
				fails.append("%s@%d,%d real %.1f%%(min %d)" % (src.split(".")[-1], r[0], r[1], 100.0 * real / n, reg.getextrema()[0]))
		total_fail += len(fails)
		total_edge += edges
		print("%-34s checked %3d  REAL not-opaque %3d  edge/corner-only %3d  %s" % (f, checked, len(fails), edges, " ".join(fails[:6])))
		sheet = Image.new("RGB", (1920, 1080))
		for i, (lab, col) in enumerate(BGS):
			bg = Image.new("RGBA", im.size, col + (255,))
			comp = Image.alpha_composite(bg, im).convert("RGB").resize((960, 540))
			sheet.paste(comp, ((i % 2) * 960, (i // 2) * 540))
		sheet.save(os.path.join(shots, f.replace("_osd.png", "_bg.png")))
	print("TOTAL REAL not-opaque info widgets:", total_fail, " (edge/corner-only widgets: %d)" % total_edge)


if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2])
