#!/usr/bin/env python3
"""Accelerated-pool optimizer for the CineView MLA design packs (all packs except the approved Classic ones).

Device facts (Slot 8, Vu+ Duo 4K SE, OpenATV 8.0.1 / enigma2 57b7a51):
* "[gFBDC] 5400kB available for acceleration surfaces" — the whole accelerated pool;
* every skin PNG >= 48000 bytes (gpixmap.cpp GFX_SURFACE_ACCELERATION_THRESHOLD) is put in that pool and stays there
  (LoadPixmap caches PNGs, PixmapCache); the per-size default posters and 3-px frame PNGs (RGBA, full poster size)
  pinned 0.3-1 MB each;
* the native channel list caches every row picon it draws (listboxservice.cpp loadPNG cached=1), so after ~40
  channels the pool is full for everybody (t72: Classic 230 failures in 5 rounds of the t67 navigation).
What this pass does (look unchanged):
* default poster PNG  -> gradient tile (4x90 PNG, stretched) + film icon PNG below the threshold;
* 3-px frame PNG      -> four 3-px strips of a 4x4 #505050 PNG (stretched);
* every CineViewMLAPosterX gets underlay="1": no 600x900 default decode, picture released when hidden or empty,
  decoded only where a running cursor stops, shown from a widget-size PNG loaded outside the pool
  (patches/posterx_identity.py).
Device result for Modern (t67/t74, 25 min of the same navigation): 741 failures -> see docs/mla evidence."""
import os
import re

FRAME_DIR = "mla_assets"
TILE_PNG = "poster_tile.png"
LINE_PNG = "px_505050.png"
ICON_MAX_W = 120  # 120x88x4 = 42240 bytes < 48000
SKIP_PACKS = ("classic", "classic-lines")


def tile(skin):
	from PIL import Image
	path = os.path.join(skin, FRAME_DIR, TILE_PNG)
	if not os.path.isfile(path):
		top, bot = (15, 23, 42), (23, 38, 61)  # poster_default.jpg top / bottom
		im = Image.new("RGB", (4, 90))
		for y in range(90):
			c = tuple(int(round(top[i] + (bot[i] - top[i]) * y / 89.0)) for i in range(3))
			for x in range(4):
				im.putpixel((x, y), c)
		im.save(path)
	return "%s/%s" % (FRAME_DIR, TILE_PNG)


def line(skin):
	from PIL import Image
	path = os.path.join(skin, FRAME_DIR, LINE_PNG)
	if not os.path.isfile(path):
		Image.new("RGB", (4, 4), (0x50, 0x50, 0x50)).save(path)
	return "%s/%s" % (FRAME_DIR, LINE_PNG)


def icon(skin, w):
	"""CineView default icon (film frame + play triangle, colours of poster_default.jpg), drawn at 4x."""
	from PIL import Image, ImageDraw
	iw = min(ICON_MAX_W, max(24, int(round(w * 0.433))))
	ih = int(round(iw * 190 / 260.0))
	name = "poster_icon_%dx%d.png" % (iw, ih)
	path = os.path.join(skin, FRAME_DIR, name)
	if not os.path.isfile(path):
		k = 4 * iw / 260.0
		im = Image.new("RGBA", (iw * 4, ih * 4), (0, 0, 0, 0))
		d = ImageDraw.Draw(im)
		d.rounded_rectangle([0, 0, iw * 4 - 1, ih * 4 - 1], radius=int(14 * k), outline=(123, 140, 168, 255), width=max(4, int(8 * k)))
		for i in range(6):
			sx = int((12 + 43 * i) * k)
			for sy in (int(12 * k), int(160 * k)):
				d.rounded_rectangle([sx, sy, sx + int(18 * k), sy + int(18 * k)], radius=int(4 * k), fill=(120, 140, 167, 255))
		d.polygon([(int(100 * k), int(60 * k)), (int(166 * k), int(95 * k)), (int(100 * k), int(130 * k))], fill=(231, 176, 49, 255))
		im.resize((iw, ih), Image.LANCZOS).save(path)
	return "%s/%s" % (FRAME_DIR, name), iw, ih


_W = re.compile(r'(\t*)<widget\b([^>]*?)\bpixmap="mla_assets/(poster_default|frame_border_505050)_(\d+)x(\d+)\.png"([^>]*?)(/>|>(.*?)</widget>)', re.S)
_A = re.compile(r'(\w+)="([^"]*)"')


def _attrs(s):
	return dict(_A.findall(s))


def optimize_xml(skin, xml):
	def sub(m):
		ind, a1, kind, _w, _h, a2, tail, body = m.groups()
		a = _attrs(a1 + " " + a2)
		x, y = (int(v) for v in a["position"].split(","))
		w, h = (int(v) for v in a["size"].split(","))
		z = int(a.get("zPosition", "0"))
		src = a.get("source", "session.CurrentService")
		inner = body or ""
		close = (">%s</widget>" % inner) if tail != "/>" else " />"
		if kind == "poster_default":
			r = (' cornerRadius="%s"' % a["cornerRadius"]) if "cornerRadius" in a else ""
			ic, iw, ih = icon(skin, w)
			return ('%s<widget source="%s" render="Pixmap" pixmap="%s" position="%d,%d" size="%d,%d" scale="1"%s zPosition="%d"%s\n'
				'%s<widget source="%s" render="Pixmap" pixmap="%s" position="%d,%d" size="%d,%d" alphatest="blend" zPosition="%d"%s') % (
				ind, src, tile(skin), x, y, w, h, r, z - 1, close, ind, src, ic, x + (w - iw) // 2, y + (h - ih) // 2, iw, ih, z, close)
		# frame: 3-px border of a (w x h) box -> four strips
		px = line(skin)
		strips = ((x, y, w, 3), (x, y + h - 3, w, 3), (x, y + 3, 3, h - 6), (x + w - 3, y + 3, 3, h - 6))
		return "\n".join('%s<widget source="%s" render="Pixmap" pixmap="%s" position="%d,%d" size="%d,%d" scale="1" zPosition="%d"%s' % (
			ind, src, px, sx, sy, sw, sh, z, close) for sx, sy, sw, sh in strips)
	xml = _W.sub(sub, xml)
	xml = re.sub(r'render="CineViewMLAPosterX"(?![^>]*underlay=)', 'render="CineViewMLAPosterX" underlay="1"', xml)
	return xml


def run(skin):
	"""Rewrites every non-Classic layout pack in place; returns [(pack file, defaults, frames)]."""
	done = []
	base = os.path.join(skin, "layouts")
	for sec in sorted(os.listdir(base)):
		for pack in sorted(os.listdir(os.path.join(base, sec))):
			if pack in SKIP_PACKS:
				continue
			p = os.path.join(base, sec, pack, "screens.openatv.xml")
			if not os.path.isfile(p):
				continue
			src = open(p, encoding="utf-8").read()
			nd, nf = src.count("poster_default_"), src.count("frame_border_505050_")
			out = optimize_xml(skin, src)
			assert "poster_default_" not in out and "frame_border_505050_" not in out, p
			import xml.etree.ElementTree as ET
			ET.fromstring(out.split("?>", 1)[1] if out.startswith("<?xml") else out)
			if out != src:
				open(p, "w", encoding="utf-8").write(out)
			done.append((os.path.relpath(p, skin), nd, nf))
	return done
