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


FRAME_LINE_PNG = "px_3f4e65.png"  # the default image's inner frame line colour (63,78,101)


def inner_frame(skin, ind, src, x, y, w, h, z, close):
	"""The thin inner frame line of poster_default.jpg (3 px at 18 px inset on 600x900), scaled to the widget, as four
	stretched 4x4 strips: the default placeholder keeps its original look without a full-size bitmap."""
	from PIL import Image
	path = os.path.join(skin, FRAME_DIR, FRAME_LINE_PNG)
	if not os.path.isfile(path):
		Image.new("RGB", (4, 4), (63, 78, 101)).save(path)
	px = "%s/%s" % (FRAME_DIR, FRAME_LINE_PNG)
	i = int(round(18 * w / 600.0))
	t = max(1, int(round(3 * w / 600.0)))
	strips = ((x + i, y + i, w - 2 * i, t), (x + i, y + h - i - t, w - 2 * i, t), (x + i, y + i + t, t, h - 2 * i - 2 * t), (x + w - i - t, y + i + t, t, h - 2 * i - 2 * t))
	return "\n".join('%s<widget source="%s" render="Pixmap" pixmap="%s" position="%d,%d" size="%d,%d" scale="1" zPosition="%d"%s' % (
		ind, src, px, sx, sy, sw, sh, z, close) for sx, sy, sw, sh in strips)


def icon(skin, w, h):
	"""The film icon of poster_default.jpg exactly as the old per-size default showed it: the default image is scaled
	to the widget size (same LANCZOS resize as before) and only the icon area is kept, cut into vertical slices of
	< 48000 bytes each (never accelerated, never pinned).  Returns [(pixmap, dx, dy, sw, sh)] relative to the tile."""
	from PIL import Image
	src = os.path.join(skin, FRAME_DIR, "poster_default.jpg")
	rx, ry = int(round(170 * w / 600.0)), int(round(335 * h / 900.0))
	rw, rh = int(round(260 * w / 600.0)), int(round(190 * h / 900.0))
	step = max(8, 47000 // (rh * 4))
	out = []
	full = None
	for i, dx in enumerate(range(0, rw, step)):
		sw = min(step, rw - dx)
		name = "poster_icon_%dx%d_%d.png" % (w, h, i)
		path = os.path.join(skin, FRAME_DIR, name)
		if not os.path.isfile(path):
			if full is None:
				full = Image.open(src).convert("RGB").resize((w, h), Image.LANCZOS)
			full.crop((rx + dx, ry, rx + dx + sw, ry + rh)).save(path)
		out.append(("%s/%s" % (FRAME_DIR, name), rx + dx, ry, sw, rh))
	return out


def icon_widgets(skin, ind, src, x, y, w, h, z, close):
	return "\n".join('%s<widget source="%s" render="Pixmap" pixmap="%s" position="%d,%d" size="%d,%d" zPosition="%d"%s' % (
		ind, src, p, x + dx, y + dy, sw, sh, z, close) for p, dx, dy, sw, sh in icon(skin, w, h))


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
			return '%s<widget source="%s" render="Pixmap" pixmap="%s" position="%d,%d" size="%d,%d" scale="1"%s zPosition="%d"%s\n%s\n%s' % (
				ind, src, tile(skin), x, y, w, h, r, z - 1, close, icon_widgets(skin, ind, src, x, y, w, h, z, close),
				inner_frame(skin, ind, src, x, y, w, h, z, close))
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
