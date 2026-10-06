#!/usr/bin/env python3
"""Opaque information areas on the InfoBar family (user request 2026-10-06 06:42).

The InfoBar / SecondInfoBar keep the design's overall transparency, but every area that carries information
(channel name and picon, tuning data, CAM, current / next event, times, IMDb, SNR / AGC / BER, resolution, bitrate,
weather ...) must have a fully opaque background in the theme colour: the video must not show through or tint it.

For every screen of the InfoBar family in every pack (InfoBar, RadioInfoBar, SecondInfoBar*, MoviePlayer, PVRState,
TimeshiftState), each information widget is checked at its centre: is there a fully opaque layer under it?
(colour layers: alpha byte 00; PNG layers: pixel alpha 255).  When not, the topmost translucent layer under it
decides the fix:
  * a translucent CARD / PANEL (colour layer up to 40 % of the screen): the same element gets the opaque twin of its
    colour ('<token>Solid' = same RGB, alpha 00; build.py adds the twins to every theme) -> same geometry, same hue,
    no video behind it;
  * a translucent PNG panel up to 40 % of the screen: an opaque plate in the theme panel colour with the PNG's
    rectangle is put under it (the PNG keeps its look, nothing shows through);
  * a large translucent layer (scrim / gradient over the whole picture) or no layer at all: the scrim keeps its
    transparency; opaque plates are put only behind the information groups (union of the group's widgets + a margin);
  * an information widget's own translucent fill (progress track, pill) stays: it sits on an opaque layer now.
Positions and sizes of the approved elements are never changed.
usage: run(skin) -> [(file, screen, action, detail)]"""
import os
import re

from PIL import Image

W, H = 1920, 1080
FAMILY = ("InfoBar", "RadioInfoBar", "SecondInfoBar", "SecondInfoBarSimple", "SecondInfoBarECM", "SecondInfoBar_CVPosterOff",
	"SecondInfoBarSimple_CVPosterOff", "SecondInfoBarECM_CVPosterOff", "MoviePlayer", "PVRState", "TimeshiftState")
SECTIONS = ("infobar", "secondinfobar", "pvr")
TAG = re.compile(r'(\t*)<(eLabel|widget|ePixmap)\b([^>]*?)(/>|>(.*?)</widget>)', re.S)
MARGIN = 14
LARGE = 0.40
MIXES = set()  # (literal #AARRGGBB, base theme token): opaque mixed colours build.py adds to every theme


def attrs(s):
	return dict(re.findall(r'(\w+)="([^"]*)"', s))


def theme_colors(skin):
	p = os.path.join(skin, "themes", "navy", "theme.xml")
	return dict(re.findall(r'<color name="([^"]+)" value="(#[0-9A-Fa-f]{8})"', open(p, encoding="utf-8").read()))


def alpha(val, cols):
	v = cols.get(val, val)
	if v and v.startswith("#") and len(v) == 9:
		return int(v[1:3], 16)
	if v and v.startswith("#") and len(v) == 7:
		return 0
	return None


def solid(val, cols):
	if val in cols:
		return val + "Solid"
	if val.startswith("#") and len(val) == 9:
		return "#00" + val[3:]
	return val


def rect(a):
	try:
		x, y = (int(v) for v in a["position"].split(","))
		w, h = (int(v) for v in a["size"].split(","))
		return [x, y, w, h]
	except Exception:
		return None


def is_info(kind, a, inner):
	render = a.get("render", "")
	if kind != "widget":
		return False
	if render in ("Label", "RunningText", "Progress", "Picon", "CineViewMLALineText", "FixedLabel", "VRunningText"):
		if render == "Label" and "text=" in (inner or "") and not re.search(r'<convert type="(?!CineViewMLAShowIf)', inner or ""):
			return False  # decoration / caption label without data
		return True
	return "name" in a and "render" not in a and "source" not in a


def png_alpha_at(skin, px, lr, x, y):
	fp = os.path.join(skin, px)
	try:
		im = Image.open(fp).convert("RGBA")
	except Exception:
		return None
	sx = int((x - lr[0]) * im.width / max(1, lr[2]))
	sy = int((y - lr[1]) * im.height / max(1, lr[3]))
	return im.getpixel((min(max(sx, 0), im.width - 1), min(max(sy, 0), im.height - 1)))[3]


def rows(boxes):
	"""Plates on one row (vertical overlap > 50 % of the lower one) become one band: no patchwork of small plates."""
	boxes = sorted(boxes, key=lambda b: b[1])
	out = []
	for b in boxes:
		for o in out:
			ov = min(o[1] + o[3], b[1] + b[3]) - max(o[1], b[1])
			if ov > 0.5 * min(o[3], b[3]):
				x0, y0 = min(o[0], b[0]), min(o[1], b[1])
				x1, y1 = max(o[0] + o[2], b[0] + b[2]), max(o[1] + o[3], b[1] + b[3])
				o[:] = [x0, y0, x1 - x0, y1 - y0]
				break
		else:
			out.append(list(b))
	return out


def cluster(rs):
	boxes = [list(r) for r in rs]
	changed = True
	while changed:
		changed = False
		out = []
		while boxes:
			b = boxes.pop()
			merged = True
			while merged:
				merged = False
				for o in boxes[:]:
					if not (b[0] + b[2] + 2 * MARGIN < o[0] or o[0] + o[2] + 2 * MARGIN < b[0] or b[1] + b[3] + 2 * MARGIN < o[1] or o[1] + o[3] + 2 * MARGIN < b[1]):
						x0, y0 = min(b[0], o[0]), min(b[1], o[1])
						x1, y1 = max(b[0] + b[2], o[0] + o[2]), max(b[1] + b[3], o[1] + o[3])
						b = [x0, y0, x1 - x0, y1 - y0]
						boxes.remove(o)
						merged = changed = True
			out.append(b)
		boxes = out
		if not changed:
			return out
	return boxes


def screen(skin, cols, body):
	els = []
	for m in TAG.finditer(body):
		a = attrs(m.group(3))
		els.append({"m": m, "kind": m.group(2), "a": a, "inner": m.group(5) or "", "r": rect(a), "z": int(a.get("zPosition", "0") or 0)})
	layers = []
	for e in els:
		a, r = e["a"], e["r"]
		if not r:
			continue
		if e["kind"] == "eLabel" and "backgroundColor" in a:
			al = alpha(a["backgroundColor"], cols)
			if al is not None:
				layers.append((e, "color", al))
		elif e["kind"] == "widget" and a.get("render") == "Label" and "backgroundColor" in a and a.get("transparent") != "1" and not is_info(e["kind"], a, e["inner"]):
			al = alpha(a["backgroundColor"], cols)
			if al is not None:
				layers.append((e, "color", al))
		elif (e["kind"] == "ePixmap" or a.get("render") == "Pixmap") and a.get("pixmap"):
			layers.append((e, "png", None))
	groups, own, covered = {}, [], []
	for e in els:
		if not e["r"] or not is_info(e["kind"], e["a"], e["inner"]):
			continue
		# an information widget that paints its OWN background (transparent != "1") REPLACES the pixels under it (no
		# blending): a translucent theme colour there punches through any opaque card (t87, Classic SIB labels with
		# backgroundColor="steSecondInfoBG": alpha 135 inside their rectangles on build81) -> its opaque twin.
		# Literal translucent fills (e.g. a progress track #B0FFFFFF) are only reported.
		a = e["a"]
		if a.get("transparent") != "1" and "backgroundColor" in a and (alpha(a["backgroundColor"], cols) or 0) > 0:
			own.append(e)
		cx, cy = e["r"][0] + e["r"][2] // 2, e["r"][1] + e["r"][3] // 2
		opaque, top = False, None
		for le, kind, al in layers:
			lr = le["r"]
			if le["z"] >= e["z"] or not (lr[0] <= cx < lr[0] + lr[2] and lr[1] <= cy < lr[1] + lr[3]):
				continue
			if kind == "png":
				al = png_alpha_at(skin, le["a"]["pixmap"], lr, cx, cy)
				al = None if al is None else 255 - al
			if al == 0:
				opaque = True
				covered.append((e, le["z"], le["r"]))  # info widget already on an opaque layer (pill / card): its z and rect
				break
			if al is not None and (top is None or le["z"] > top[0]["z"]):
				top = (le, kind)
		if opaque:
			continue
		key = id(top[0]) if top else None
		groups.setdefault(key, [top, []])[1].append(e)
	edits, inserts, report, mixes = {}, [], [], {}
	for key, (top, ws) in groups.items():
		if top:
			le, kind = top
			lr = le["r"]
			large = lr[2] * lr[3] > LARGE * W * H
		else:
			le, kind, large = None, None, True
		if not large and kind == "color":
			edits[id(le)] = le
			report.append(("card", le["a"].get("backgroundColor"), "%d,%d %dx%d" % tuple(lr)))
		elif not large and kind == "png":
			inserts.append((le, dict(r=lr, z=le["z"] - 1, color="steThemePanel", radius=le["a"].get("cornerRadius"), before=True)))
			report.append(("png-plate", le["a"]["pixmap"], "%d,%d %dx%d" % tuple(lr)))
		else:
			col = solid(le["a"]["backgroundColor"], cols) if (le and kind == "color") else "steThemePanel"
			zmin = min(w["z"] for w in ws)
			for b in rows(cluster([w["r"] for w in ws])):
				# a row band absorbs the information pills of the SAME row right next to it (already opaque, so not in
				# the cluster): otherwise the band ends mid-row and those pills hang over the scrim (t87e, Modern SIB
				# status row: SNR / dB pills past x 1580).  The band then goes under those pills' own layer.
				zcap = None
				grown = True
				while grown:
					grown = False
					for ce, cz, lrr in covered:
						# the pill's own rectangle (the caption "SNR" and the value share one pill), else the widget
						cr = lrr if lrr[3] <= 1.5 * b[3] else ce["r"]
						ov = min(b[1] + b[3], cr[1] + cr[3]) - max(b[1], cr[1])
						gap = max(cr[0] - (b[0] + b[2]), b[0] - (cr[0] + cr[2]))
						inside = b[0] <= cr[0] and cr[0] + cr[2] <= b[0] + b[2]
						if (ov > 0.5 * min(b[3], cr[3]) and gap <= 2 * MARGIN and not inside and cr[3] <= 1.5 * b[3]
								and (le is None or le["z"] < cz - 1)):
							nx0, nx1 = min(b[0], cr[0]), max(b[0] + b[2], cr[0] + cr[2])
							b = [nx0, b[1], nx1 - nx0, b[3]]
							zcap = cz if zcap is None else min(zcap, cz)
							grown = True
				x0, y0 = max(0, b[0] - MARGIN), max(0, b[1] - MARGIN)
				x1, y1 = min(W, b[0] + b[2] + MARGIN), min(H, b[1] + b[3] + MARGIN)
				z = (le["z"] if le else zmin - 1)
				if zcap is not None and z >= zcap:
					z = zcap - 1
				inserts.append((le, dict(r=[x0, y0, x1 - x0, y1 - y0], z=z, color=col, radius="14", before=False)))
				report.append(("plate", col, "%d,%d %dx%d" % (x0, y0, x1 - x0, y1 - y0)))
	def base_under(e):
		# opaque colour of the region under e's centre after this pass: topmost colour layer / new plate below it;
		# None when that topmost layer stays translucent (outer design layer, nothing to match)
		cx, cy = e["r"][0] + e["r"][2] // 2, e["r"][1] + e["r"][3] // 2
		best = None
		for le, kind, al in layers:
			lr = le["r"]
			if kind == "color" and le["z"] < e["z"] and lr[0] <= cx < lr[0] + lr[2] and lr[1] <= cy < lr[1] + lr[3]:
				if best is None or le["z"] >= best[1]:
					tok = le["a"]["backgroundColor"]
					best = ((solid(tok, cols) if id(le) in edits else tok) if (al == 0 or id(le) in edits) else None, le["z"])
		for le, p in inserts:
			lr = p["r"]
			if p["z"] < e["z"] and lr[0] <= cx < lr[0] + lr[2] and lr[1] <= cy < lr[1] + lr[3]:
				if best is None or p["z"] >= best[1]:
					best = (p["color"], p["z"])
		return best[0] if best else None

	clear = set()  # fully transparent own fills (alpha FF) handled here
	for e in own:
		bg = e["a"]["backgroundColor"]
		if alpha(bg, cols) == 255:
			# 'transparent' (#FF000000) painted by the widget itself punches a fully transparent hole into the opaque
			# region under it; its 'Solid' twin would be opaque BLACK (t87c: PVRState 'state' on the playback bar).
			# -> the region's own opaque colour (same look as the panel, no hole).
			b = base_under(e)
			if b:
				mixes[id(e)] = b
				clear.add(id(e))
				report.append(("own-clear", e["a"].get("source") or e["a"].get("name") or "?", "%s -> %s" % (bg, b)))
			continue
		if bg in cols:
			edits[id(e)] = e
			report.append(("own-bg", e["a"].get("source") or e["a"].get("name") or "?", bg + " -> Solid"))
		else:
			# a literal translucent fill (e.g. progress track #B0FFFFFF) on an opaque region: the same look, opaque =
			# the literal blended over the region's theme colour ('mix<AARRGGBB>_<token>', added per theme by build.py)
			base = None
			cx, cy = e["r"][0] + e["r"][2] // 2, e["r"][1] + e["r"][3] // 2
			for le, kind, al in layers:
				lr = le["r"]
				if kind == "color" and le["z"] < e["z"] and lr[0] <= cx < lr[0] + lr[2] and lr[1] <= cy < lr[1] + lr[3]:
					tok = le["a"]["backgroundColor"]
					if tok in cols and (base is None or le["z"] > base[1]):
						base = (tok, le["z"])
			if base and bg.startswith("#") and len(bg) == 9:
				MIXES.add((bg.upper(), base[0]))
				mixes[id(e)] = "mix%s_%s" % (bg[1:].upper(), base[0])
				report.append(("own-mix", e["a"].get("source") or e["a"].get("name") or "?", "%s over %s" % (bg, base[0])))
			else:
				report.append(("own-lit", e["a"].get("source") or e["a"].get("name") or "?", bg + " (kept)"))
	# Every element with a translucent THEME fill drawn above an opaque region (existing opaque layer, card made
	# opaque here, new plate) replaces the pixels there -> its opaque twin as well (caption labels, pills ...).
	# (rect, z, draw order): with equal z, Enigma2 draws in document order, so a plate inserted right AFTER a layer is
	# above it (t87c: the full-screen Cinema SIB scrim, z 1, got the plate after it and was wrongly made opaque)
	regions = [(le["r"], le["z"], le["m"].start()) for le, kind, al in layers if kind == "color" and al == 0]
	regions += [(le["r"], le["z"], le["m"].start()) for k, le in edits.items() if le.get("kind") in ("eLabel", "widget")]
	regions += [(p["r"], p["z"], (le["m"].start() + (-0.5 if p["before"] else 0.5)) if le else -1) for le, p in inserts]
	for e in els:
		a, r = e["a"], e["r"]
		if not r or id(e) in edits or "backgroundColor" not in a or a.get("transparent") == "1":
			continue
		bg = a["backgroundColor"]
		if bg not in cols or (alpha(bg, cols) or 0) == 0 or id(e) in mixes:
			continue
		if alpha(bg, cols) == 255:
			# fully transparent fill above an opaque region: a hole -> the region's colour, never the black twin.
			# Only text-bearing elements: a bare eLabel hole can be a deliberate video window (kept).
			if e["kind"] == "eLabel" and "text" not in a:
				continue
			b = base_under(e)
			if b and b != bg:
				mixes[id(e)] = b
				report.append(("fill-clear", a.get("source") or a.get("name") or e["kind"], "%s -> %s" % (bg, b)))
			continue
		cx, cy = r[0] + r[2] // 2, r[1] + r[3] // 2
		for rr, rz, ro in regions:
			below = rz < e["z"] or (rz == e["z"] and ro < e["m"].start())
			if below and rr[0] <= cx < rr[0] + rr[2] and rr[1] <= cy < rr[1] + rr[3] and not (rr == r and rz == e["z"]):
				edits[id(e)] = e
				report.append(("fill", a.get("source") or a.get("name") or e["kind"], bg + " -> Solid"))
				break
	if not edits and not inserts and not mixes:
		return body, report
	out, last = [], 0
	plates_after, plates_before, plates_top = {}, {}, []
	for le, p in inserts:
		ind = le["m"].group(1) if le else "\t\t"
		tag = '%s<eLabel position="%d,%d" size="%d,%d" backgroundColor="%s"%s zPosition="%d" />\n' % (
			ind, p["r"][0], p["r"][1], p["r"][2], p["r"][3], p["color"], ' cornerRadius="%s"' % p["radius"] if p["radius"] else "", p["z"])
		if le is None:
			plates_top.append(tag)
		elif p["before"]:
			plates_before.setdefault(id(le), []).append(tag)
		else:
			plates_after.setdefault(id(le), []).append(tag)
	for e in els:
		m = e["m"]
		out.append(body[last:m.start()])
		k = id(e)
		if k in plates_before:
			out.append("".join(plates_before[k]))
		seg = m.group(0)
		if k in edits:
			bg = e["a"]["backgroundColor"]
			seg = seg.replace('backgroundColor="%s"' % bg, 'backgroundColor="%s"' % solid(bg, cols), 1)
		elif k in mixes:
			seg = seg.replace('backgroundColor="%s"' % e["a"]["backgroundColor"], 'backgroundColor="%s"' % mixes[k], 1)
		out.append(seg)
		if k in plates_after:
			out.append("\n" + "".join(plates_after[k]).rstrip("\n"))
		last = m.end()
	out.append(body[last:])
	new = "".join(out)
	if plates_top:
		new = "\n" + "".join(plates_top) + new.lstrip("\n")
	return new, report


def add_mixes(skin):
	"""Opaque mixed colours for every theme: literal #AARRGGBB (alpha byte AA, 00 = opaque) blended over the theme's
	value of the base token."""
	n = 0
	tdir = os.path.join(skin, "themes")
	for key in sorted(os.listdir(tdir)):
		tx = os.path.join(tdir, key, "theme.xml")
		if key == "golden" or not os.path.isfile(tx):
			continue
		x = open(tx, encoding="utf-8").read()
		cols = dict(re.findall(r'<color name="([^"]+)" value="(#[0-9A-Fa-f]{8})"', x))
		add = []
		for lit, tok in sorted(MIXES):
			if tok not in cols:
				continue
			a = 1.0 - int(lit[1:3], 16) / 255.0
			fg = [int(lit[i:i + 2], 16) for i in (3, 5, 7)]
			bgc = [int(cols[tok][i:i + 2], 16) for i in (3, 5, 7)]
			mixed = "".join("%02X" % int(round(f * a + b * (1 - a))) for f, b in zip(fg, bgc))
			add.append('\t<color name="mix%s_%s" value="#00%s" />\n' % (lit[1:], tok, mixed))
		if add:
			x = x.replace("</colors>", "".join(add) + "\t</colors>", 1)
			open(tx, "w", encoding="utf-8").write(x)
			n += len(add)
	return n


def run(skin):
	cols = theme_colors(skin)
	rep = []
	for sec in SECTIONS:
		base = os.path.join(skin, "layouts", sec)
		for pack in sorted(os.listdir(base)):
			p = os.path.join(base, pack, "screens.openatv.xml")
			if not os.path.isfile(p):
				continue
			src = open(p, encoding="utf-8").read()
			out, last = [], 0
			for m in re.finditer(r'(<screen name="([^"]+)"[^>]*>)(.*?)(</screen>)', src, re.S):
				if m.group(2) not in FAMILY:
					continue
				body, r = screen(skin, cols, m.group(3))
				for x in r:
					rep.append((os.path.relpath(p, skin), m.group(2)) + x)
				out.append(src[last:m.start(3)] + body)
				last = m.end(3)
			out.append(src[last:])
			new = "".join(out)
			if new != src:
				import xml.etree.ElementTree as ET
				ET.fromstring(new.split("?>", 1)[1] if new.startswith("<?xml") else new)
				open(p, "w", encoding="utf-8").write(new)
	add_mixes(skin)
	return rep
