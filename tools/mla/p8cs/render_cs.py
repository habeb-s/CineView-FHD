#!/usr/bin/env python3
"""Render Channel Selection proposals (Poster List, Video First) from spec_cs.py with the skin's real font,
real receiver data (EPG/services from OpenWebif) and a real video frame from the receiver.
usage: render_cs.py <data.json> <fonts dir> <out dir>
Outputs: <design>_<on|off>[_<theme>][_<side>].png  and  <design>_on_dims.png (boxes + sizes)."""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_cs as S  # noqa: E402

DATA, FONTS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
D = json.load(open(DATA, encoding="utf-8"))
_fc = {}

# Theme roles = the real enigma2 colours of the build (alpha byte: 00 opaque .. FF transparent).
THEMES = {
	"navy": {"primary": "#000A1D35", "panel": "#0008182B", "panelAlt": "#00071323", "overlay": "#2D08182B", "overlayStrong": "#54071323", "selected": "#06314155"},
	"burgundy": {"primary": "#00501C2C", "panel": "#00421724", "panelAlt": "#0035121D", "overlay": "#2D421724", "overlayStrong": "#5435121D", "selected": "#066C404E"},
}
TEXT, MUTED, ACCENT = (240, 240, 240, 255), (182, 182, 182, 255), (249, 199, 49, 255)
KEYS = [("red", (160, 0, 0)), ("green", (0, 128, 0)), ("yellow", (160, 128, 0)), ("blue", (0, 64, 160))]


def font(size):
	if size not in _fc:
		_fc[size] = ImageFont.truetype(os.path.join(FONTS, "LiberationSans-Regular.ttf"), size)
	return _fc[size]


def e2col(v):
	v = v.lstrip("#")
	a = 255 - int(v[0:2], 16)
	return (int(v[2:4], 16), int(v[4:6], 16), int(v[6:8], 16), a)


def rtl(s):
	return any("֐" <= c <= "ࣿ" or "יִ" <= c <= "ﻼ" for c in s)


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
	"""Draw text in a skin box (x,y,w,h,size) with the receiver's line pitch; never beyond the box."""
	x, y, w, h, size = box
	f = font(size)
	p = S.pitch(size)
	n = max(1, h // p) if lines is None else lines
	ls = wrap(text, f, w)
	if len(ls) > n:
		ls = ls[:n]
		while ls[-1] and f.getlength(ls[-1] + "…") > w:
			ls[-1] = ls[-1].rsplit(" ", 1)[0] if " " in ls[-1] else ls[-1][:-1]
		ls[-1] += "…"
	for i, ln in enumerate(ls):
		lx = x + (w - f.getlength(ln)) if (align == "right" or rtl(ln)) else x
		d.text((lx, y + i * p), ln, font=f, fill=color)


def poster(im, box, path):
	x, y, w, h = box
	if path and os.path.isfile(path):
		p = Image.open(path).convert("RGB")
		r = max(w / p.width, h / p.height)
		p = p.resize((int(p.width * r) + 1, int(p.height * r) + 1))
		p = p.crop(((p.width - w) // 2, (p.height - h) // 2, (p.width - w) // 2 + w, (p.height - h) // 2 + h))
		im.paste(p, (x, y))
	ImageDraw.Draw(im).rectangle([x - 3, y - 3, x + w + 2, y + h + 2], outline=(80, 80, 80), width=3)


def bar(d, box, frac, th):
	x, y, w, h = box
	d.rectangle([x, y, x + w, y + h], fill=e2col(th["panelAlt"])[:3] + (255,))
	d.rectangle([x, y, x + int(w * frac), y + h], fill=(70, 140, 220, 255))


def list_rows(im, d, box, row_h, th, compact=False):
	x, y, w, h = box
	rows = D["rows"][: h // row_h]
	nsize = 22 if compact else 26
	for i, r in enumerate(rows):
		ry = y + i * row_h
		if i == D["selected"]:
			d.rectangle([x, ry, x + w, ry + row_h - 2], fill=e2col(th["selected"])[:3] + (255,))
		cy = ry + (row_h - S.pitch(nsize)) // 2
		d.text((x + 10, cy), str(r["num"]), font=font(nsize), fill=MUTED)
		px = x + 80
		if r.get("picon") and os.path.isfile(r["picon"]):
			pc = Image.open(r["picon"]).convert("RGBA")
			ph = row_h - 14
			pc = pc.resize((int(pc.width * ph / pc.height), ph))
			im.paste(pc, (px, ry + 7), pc)
		nx = px + (78 if compact else 100)
		name = r["name"]
		d.text((nx, cy), name, font=font(nsize), fill=TEXT)
		ex = nx + font(nsize).getlength(name) + 14
		pw = 70 if compact else 110
		ev_w = x + w - pw - 20 - ex
		if ev_w > 60 and r.get("event"):
			ev = r["event"]
			f2 = font(nsize - 4)
			while f2.getlength(ev) > ev_w and len(ev) > 3:
				ev = ev[:-2]
			if ev != r["event"]:
				ev = ev.rstrip() + "…"
			d.text((ex, cy + 3), ev, font=f2, fill=ACCENT)
		bx = x + w - pw - 10
		d.rectangle([bx, ry + row_h // 2 - 3, bx + pw, ry + row_h // 2 + 3], fill=(40, 52, 70, 255))
		d.rectangle([bx, ry + row_h // 2 - 3, bx + int(pw * r.get("progress", 0)), ry + row_h // 2 + 3], fill=(70, 140, 220, 255))


def keys(d, box, grid=False):
	x, y, w, h = box
	labels = D["keys"]
	if grid:
		cw, ch = w // 2, h // 2
		for i, ((_, col), lab) in enumerate(zip(KEYS, labels)):
			cx, cy = x + (i % 2) * cw, y + (i // 2) * ch
			d.rectangle([cx, cy + 8, cx + 8, cy + ch - 8], fill=col + (255,))
			d.text((cx + 20, cy + (ch - 26) // 2), lab, font=font(22), fill=TEXT)
	else:
		cw = w // 4
		for i, ((_, col), lab) in enumerate(zip(KEYS, labels)):
			cx = x + i * cw
			d.rectangle([cx, y + 8, cx + 8, y + h - 8], fill=col + (255,))
			d.text((cx + 22, y + (h - 28) // 2), lab, font=font(24), fill=TEXT)


def overlay(im, box, col):
	x, y, w, h = box
	ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
	ImageDraw.Draw(ov).rectangle([x, y, x + w - 1, y + h - 1], fill=e2col(col))
	return Image.alpha_composite(im, ov)


def dims(im, boxes):
	d = ImageDraw.Draw(im)
	for k, b in boxes.items():
		x, y, w, h = b[:4]
		d.rectangle([x, y, x + w, y + h], outline=(255, 64, 160, 255), width=2)
		d.text((x + 4, y + 2), "%s %dx%d" % (k, w, h), font=font(15), fill=(255, 64, 160, 255))
	return im


def render_posterlist(posters, th, out):
	sp = S.POSTER_LIST
	im = Image.open(D["video"]).convert("RGBA").resize((S.W, S.H))
	im = overlay(im, (0, 0, S.W, S.H), "#40000000")
	b = sp["boxes"]
	for k in ("list_panel", "detail_panel"):
		im = overlay(im, b[k], th["overlay"])
	d = ImageDraw.Draw(im)
	x, y, w, h = b["header"]
	d.text((x + 16, y + 10), D["bouquet"], font=font(34), fill=TEXT)
	d.text((x + w - 16 - font(46).getlength(D["clock"]), y + 2), D["clock"], font=font(46), fill=TEXT)
	d.text((x + w - 160 - font(21).getlength(D["date"]), y + 22), D["date"], font=font(21), fill=MUTED)
	list_rows(im, d, b["list"], sp["row_h"], th)
	L = sp["posters_on" if posters else "posters_off"]
	s = D["sel"]
	if s.get("picon") and os.path.isfile(s["picon"]):
		pc = Image.open(s["picon"]).convert("RGBA")
		x, y, w, h = L["svc_picon"]
		pc.thumbnail((w, h))
		im.paste(pc, (x + (w - pc.width) // 2, y + (h - pc.height) // 2), pc)
	text_box(d, L["svc_name"], s["name"], TEXT, 1)
	text_box(d, L["svc_tech"], s["tech"], MUTED, 1)
	for k in ("div1", "div2"):
		x, y, w, h = L[k]
		d.rectangle([x, y, x + w, y + h - 1], fill=e2col(th["panelAlt"])[:3] + (255,))
	n, nx = s["now"], s["next"]
	if posters:
		poster(im, L["now_poster"], n.get("poster"))
		poster(im, L["next_poster"], nx.get("poster"))
		d = ImageDraw.Draw(im)
	text_box(d, L["now_eyebrow"], "NOW", ACCENT, 1)
	text_box(d, L["now_title"], n["title"], TEXT, 2)
	text_box(d, L["now_times"], n["times"], TEXT, 1)
	bar(d, L["now_progress"], n["progress"], th)
	text_box(d, L["now_genre"], n.get("genre", ""), MUTED, 1)
	text_box(d, L["now_desc"], n["desc"], TEXT)
	text_box(d, L["next_eyebrow"], "NEXT  ·  " + nx["times"], ACCENT, 1)
	text_box(d, L["next_title"], nx["title"], TEXT, 1)
	text_box(d, L["next_desc"], nx["desc"], MUTED)
	keys(d, b["footer"])
	im.convert("RGB").save(out)
	if posters:
		dims(Image.open(out).convert("RGBA"), dict(list(b.items()) + [(k, v) for k, v in L.items()])).convert("RGB").save(out.replace(".png", "_dims.png"))


def mirror_x(box, w_total=S.W):
	x = box[0]
	return (w_total - x - box[2],) + tuple(box[1:])


def render_videofirst(posters, th, out, side="left"):
	sp = S.VIDEO_FIRST
	b = dict(sp["boxes"])
	L = dict(sp["posters_on" if posters else "posters_off"])
	if side == "right":  # list on the right, card on the left: every box mirrored on the vertical axis
		b = {k: mirror_x(v) for k, v in b.items()}
		dx = b["card"][0] - sp["boxes"]["card"][0]
		L = {k: (v[0] + dx,) + tuple(v[1:]) for k, v in L.items()}
	im = Image.open(D["video"]).convert("RGBA").resize((S.W, S.H))
	im = overlay(im, b["list_panel"], th["overlay"])
	im = overlay(im, b["card"], th["overlay"])
	im = overlay(im, b["clock"], th["overlay"])
	d = ImageDraw.Draw(im)
	text_box(d, b["title"], D["bouquet"], TEXT, 1)
	list_rows(im, d, b["list"], sp["row_h"], th, compact=True)
	keys(d, b["keys"], grid=True)
	x, y, w, h = b["clock"]
	d.text((x + 16, y + 6), D["clock"], font=font(40), fill=TEXT)
	d.text((x + 16, y + 48), D["date"], font=font(17), fill=MUTED)
	s = D["sel"]
	n, nx = s["now"], s["next"]
	if posters:
		poster(im, L["poster"], n.get("poster"))
		d = ImageDraw.Draw(im)
	text_box(d, L["svc_line"], "%s  ·  %s  ·  %s" % (s["num"], s["name"], s["tech"]), MUTED, 1)
	text_box(d, L["now_title"], n["title"], TEXT, 1)
	text_box(d, L["now_times"], n["times_short"], TEXT, 1, "right")
	bar(d, L["now_progress"], n["progress"], th)
	text_box(d, L["now_desc"], n["desc"], TEXT, 2)
	text_box(d, L["next_line"], "Next  %s   %s" % (nx["start"], nx["title"]), ACCENT, 1)
	text_box(d, L["tech_line"], s["live_tech"], MUTED, 1)
	im.convert("RGB").save(out)
	if posters and side == "left":
		dims(Image.open(out).convert("RGBA"), dict(list(b.items()) + list(L.items()))).convert("RGB").save(out.replace(".png", "_dims.png"))


for th_name in ("navy", "burgundy"):
	th = THEMES[th_name]
	sfx = "" if th_name == "navy" else "_" + th_name
	for on in (True, False):
		tag = "on" if on else "off"
		render_posterlist(on, th, os.path.join(OUT, "posterlist_%s%s.png" % (tag, sfx)))
		render_videofirst(on, th, os.path.join(OUT, "videofirst_%s%s.png" % (tag, sfx)))
		if th_name == "navy":
			render_videofirst(on, th, os.path.join(OUT, "videofirst_%s_right.png" % tag), side="right")
print("rendered", sorted(os.listdir(OUT)))
