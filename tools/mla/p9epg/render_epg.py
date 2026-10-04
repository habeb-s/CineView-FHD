#!/usr/bin/env python3
"""Render EPG proposals (Graphical Plus, Columns) from spec_epg.py with the skin's real font and real receiver
EPG data (OpenWebif, read-only).  usage: render_epg.py <data.json> <fonts dir> <out dir>
Outputs <design>_<on|off>.png and <design>_on_dims.png (boxes + sizes)."""
import datetime
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_epg as S  # noqa: E402

DATA, FONTS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
D = json.load(open(DATA, encoding="utf-8"))
_fc = {}
# navy theme roles (real enigma2 colours of the build) + the native graph-EPG cell colours seen on the device
BG, PANEL, PANEL_ALT, SELBG = (10, 29, 53), (8, 24, 43), (7, 19, 35), (49, 65, 85)
CELL, CELL_NOW, CELL_SEL, SVC_SEL, CELL_LINE = (45, 69, 94), (24, 128, 100), (212, 152, 0), (24, 128, 100), (84, 104, 126)
TEXT, MUTED, ACCENT = (240, 240, 240), (182, 182, 182), (249, 199, 49)
KEYS = [(160, 0, 0), (0, 128, 0), (160, 128, 0), (0, 64, 160)]


def font(size):
	if size not in _fc:
		_fc[size] = ImageFont.truetype(os.path.join(FONTS, "LiberationSans-Regular.ttf"), size)
	return _fc[size]


def wrap(text, f, width):
	words, lines, cur = text.split(), [], ""
	for w in words:
		t = (cur + " " + w).strip()
		if f.getlength(t) <= width:
			cur = t
		else:
			if cur:
				lines.append(cur)
			cur = w
	if cur:
		lines.append(cur)
	return lines


def text_box(d, box, text, color=TEXT, lines=None, align="left"):
	x, y, w, h, size = box
	f = font(size)
	p = S.pitch(size)
	n = max(1, h // p) if lines is None else lines
	ls = wrap(text or "", f, w)
	if len(ls) > n:
		ls = ls[:n]
		while ls[-1] and f.getlength(ls[-1] + "…") > w:
			ls[-1] = ls[-1].rsplit(" ", 1)[0] if " " in ls[-1] else ls[-1][:-1]
		ls[-1] += "…"
	for i, ln in enumerate(ls):
		lx = x + (w - f.getlength(ln)) if align == "right" else x
		d.text((lx, y + i * p), ln, font=f, fill=color)


def fit(text, f, w):
	if f.getlength(text) <= w:
		return text
	while text and f.getlength(text + "…") > w:
		text = text[:-1]
	return text.rstrip() + "…" if text else ""


def poster(im, box, path):
	x, y, w, h = box[:4]
	if path and os.path.isfile(path):
		p = Image.open(path).convert("RGB")
		r = max(w / p.width, h / p.height)
		p = p.resize((int(p.width * r) + 1, int(p.height * r) + 1))
		p = p.crop(((p.width - w) // 2, (p.height - h) // 2, (p.width - w) // 2 + w, (p.height - h) // 2 + h))
		im.paste(p, (x, y))
	ImageDraw.Draw(im).rectangle([x - 3, y - 3, x + w + 2, y + h + 2], outline=(80, 80, 80), width=3)


def picon(im, box, path):
	x, y, w, h = box[:4]
	if path and os.path.isfile(path):
		pc = Image.open(path).convert("RGBA")
		pc.thumbnail((w, h))
		im.paste(pc, (x + (w - pc.width) // 2, y + (h - pc.height) // 2), pc)


def hm(t):
	return datetime.datetime.fromtimestamp(t).strftime("%H:%M")


def header_footer(d):
	text_box(d, S.HEADER["title"], D["bouquet"], ACCENT, 1)
	text_box(d, S.HEADER["date"], D["date"], MUTED, 1, "right")
	text_box(d, S.HEADER["clock"], D["clock"], TEXT, 1, "right")
	x, y, w, h = S.FOOTER
	cw = w // 4
	for i, (col, lab) in enumerate(zip(KEYS, D["keys"])):
		cx = x + i * cw
		d.rectangle([cx, y + 12, cx + 8, y + h - 12], fill=col)
		d.text((cx + 22, y + (h - 28) // 2), lab, font=font(24), fill=TEXT)


def dims(path, boxes):
	im = Image.open(path).convert("RGB")
	d = ImageDraw.Draw(im)
	for k, b in boxes.items():
		x, y, w, h = b[:4]
		d.rectangle([x, y, x + w, y + h], outline=(255, 64, 160), width=2)
		d.text((x + 4, y + 2), "%s %dx%d" % (k, w, h), font=font(15), fill=(255, 64, 160))
	im.save(path.replace(".png", "_dims.png"))


def render_graphical(on, out):
	sp = S.GRAPHICAL_PLUS
	L = sp["posters_on" if on else "posters_off"]
	im = Image.new("RGB", (S.W, S.H), BG)
	d = ImageDraw.Draw(im)
	x, y, w, h = L["panel"]
	d.rectangle([x, y, x + w, y + h], fill=PANEL)
	gx, gy, gw, gh = L["grid"]
	sw = sp["service_w"]
	span = 180 if not on else 150  # minutes visible: the grid is wider with posters off
	t0 = (D["now"] - 1800) // 1800 * 1800
	t1 = t0 + span * 60
	px_min = (gw - sw) / (span * 60.0)
	tx, ty, tw, th = L["timeline"]
	for k in range(0, span + 1, 30):
		lx = gx + sw + int(k * 60 * px_min)
		if lx < gx + gw - 40:
			d.text((lx + 4, ty + 6), hm(t0 + k * 60), font=font(24), fill=ACCENT)
		d.line([lx, ty + th - 6, lx, gy + gh], fill=(30, 48, 70), width=1)
	nowx = gx + sw + int((D["now"] - t0) * px_min)
	rh = gh // sp["rows"]
	for i, c in enumerate(D["channels"][: sp["rows"]]):
		ry = gy + i * rh
		d.rectangle([gx, ry + 1, gx + sw - 2, ry + rh - 2], fill=SVC_SEL if i == 0 else CELL)
		picon(im, (gx + 6, ry + 8, 90, rh - 16), c.get("picon"))
		d.text((gx + 104, ry + (rh - 27) // 2), fit(c["name"], font(24), sw - 112), font=font(24), fill=TEXT)
		for e in c["events"]:
			b, en = max(e["begin"], t0), min(e["begin"] + e["dur"], t1)
			if en <= b:
				continue
			cx0 = gx + sw + int((b - t0) * px_min)
			cx1 = gx + sw + int((en - t0) * px_min)
			is_now = e["begin"] <= D["now"] < e["begin"] + e["dur"]
			sel = i == 0 and is_now
			d.rectangle([cx0 + 1, ry + 1, cx1 - 1, ry + rh - 2], fill=CELL_SEL if sel else (CELL_NOW if is_now else CELL), outline=CELL_LINE)
			if cx1 - cx0 > 30:
				d.text((cx0 + 8, ry + (rh - 27) // 2), fit(e["title"], font(24), cx1 - cx0 - 14), font=font(24), fill=TEXT)
	d.line([nowx, ty + 4, nowx, gy + gh], fill=(240, 60, 60), width=3)
	s = D["selected"]
	if on:
		poster(im, L["poster"], s.get("poster"))
		picon(im, L["ch_picon"], s.get("picon"))
		d = ImageDraw.Draw(im)
	text_box(d, L["ch_name"], s["channel"], MUTED, 1)
	text_box(d, L["title"], s["title"], TEXT)
	text_box(d, L["times"], s["times"], ACCENT, 1)
	text_box(d, L["duration"], s["duration"], MUTED, 1)
	text_box(d, L["genre"], s.get("genre") or "", MUTED, 1)
	text_box(d, L["rating"], "", MUTED, 1)  # rating only when the identity engine recognises a film/series
	text_box(d, L["desc"], s["desc"], TEXT)
	header_footer(d)
	im.save(out)
	if on:
		dims(out, dict(L, **{"footer": S.FOOTER}))


def render_columns(on, out):
	sp = S.COLUMNS
	L = sp["posters_on" if on else "posters_off"]
	im = Image.new("RGB", (S.W, S.H), BG)
	d = ImageDraw.Draw(im)
	hy, hh = sp["col_head"]
	ly, lh = sp["col_list"]
	rh = sp["row_h"]
	for i, c in enumerate(D["channels"][: sp["cols"]]):
		cx = 40 + i * (sp["col_w"] + sp["col_gap"])
		cw = sp["col_w"]
		d.rectangle([cx, hy, cx + cw, hy + hh], fill=SELBG if i == 0 else PANEL)
		picon(im, (cx + 8, hy + 8, 100, hh - 16), c.get("picon"))
		d.text((cx + 118, hy + (hh - 30) // 2), fit(c["name"], font(26), cw - 126), font=font(26), fill=ACCENT if i == 0 else TEXT)
		d.rectangle([cx, ly, cx + cw, ly + lh], fill=PANEL)
		evs = [e for e in c["events"] if e["begin"] + e["dur"] > D["now"]][: lh // rh]
		for k, e in enumerate(evs):
			ry = ly + k * rh
			if i == 0 and k == 0:
				d.rectangle([cx, ry, cx + cw, ry + rh - 2], fill=SELBG)
			d.text((cx + 12, ry + 6), hm(e["begin"]), font=font(22), fill=ACCENT)
			ls = wrap(e["title"], font(24), cw - 90)[:2]
			if len(wrap(e["title"], font(24), cw - 90)) > 2:
				ls[-1] = fit(ls[-1] + " …", font(24), cw - 90)
			for j, ln in enumerate(ls):
				d.text((cx + 80, ry + 6 + j * S.pitch(24)), ln, font=font(24), fill=TEXT)
			d.line([cx + 8, ry + rh - 1, cx + cw - 8, ry + rh - 1], fill=(30, 48, 70), width=1)
	x, y, w, h = L["card"]
	d.rectangle([x, y, x + w, y + h], fill=PANEL)
	s = D["selected"]
	if on:
		poster(im, L["poster"], s.get("poster"))
		d = ImageDraw.Draw(im)
	text_box(d, L["title"], s["title"], TEXT, 1)
	text_box(d, L["times"], "%s  ·  %s" % (s["times"], s["duration"]), ACCENT, 1, "right")
	text_box(d, L["meta"], "  ·  ".join(v for v in (s["channel"], s.get("genre")) if v), MUTED, 1)
	text_box(d, L["desc"], s["desc"], TEXT)
	header_footer(d)
	im.save(out)
	if on:
		boxes = dict(L, **{"footer": S.FOOTER})
		for i in range(sp["cols"]):
			cx = 40 + i * (sp["col_w"] + sp["col_gap"])
			boxes["col%d_head" % (i + 1)] = (cx, hy, sp["col_w"], hh)
			boxes["list%d" % (i + 1)] = (cx, ly, sp["col_w"], lh)
		dims(out, boxes)


for on in (True, False):
	tag = "on" if on else "off"
	render_graphical(on, os.path.join(OUT, "graphicalplus_%s.png" % tag))
	render_columns(on, os.path.join(OUT, "columns_%s.png" % tag))
print("rendered", sorted(os.listdir(OUT)))
