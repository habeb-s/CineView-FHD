#!/usr/bin/env python3
"""Mockups of the two NEW integrated models — Modern and Minimal — for visual approval (2026-10-04 night).
Five screens per model (InfoBar, SecondInfoBar, Channel Selection, Graphical EPG, EventView), posters ON and OFF,
drawn with the skin's real font (LiberationSans), the receiver's real line pitch and real receiver data
(OpenWebif EPG/services, picon crops, a live video frame, posters from the identity cache).

Only enigma2 57b7a51 features are used in the drawings: boxes, cornerRadius (skin.py cornerRadius ->
eWidget::setCornerRadius), two-colour vertical gradients (parseGradient), native list/grid widgets, the
CineView poster renderer.  Rounded corners and gradients are verified in source, not yet on this receiver
(device check is part of the implementation step).
usage: render_models.py <cs data.json> <epg data.json> <fonts dir> <out dir>"""
import datetime
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

CS, EP, FONTS, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
D = json.load(open(CS, encoding="utf-8"))
G = json.load(open(EP, encoding="utf-8"))
W, H = 1920, 1080
_fc = {}
# navy theme roles (same values as the build)
NAVY = {"primary": (10, 29, 53), "panel": (8, 24, 43), "panelAlt": (7, 19, 35), "sel": (49, 65, 85)}
TEXT, MUTED, ACCENT, BLUE = (240, 240, 240), (176, 186, 200), (249, 199, 49), (70, 140, 220)


def font(size, bold=False):
	k = (size, bold)
	if k not in _fc:
		_fc[k] = ImageFont.truetype(os.path.join(FONTS, "LiberationSans-%s.ttf" % ("Bold" if bold else "Regular")), size)
	return _fc[k]


def pitch(size):
	import math
	return int(round(size * 1854 / 2048.0)) + int(math.ceil(size * 434 / 2048.0))


def wrap(text, f, width):
	words, lines, cur = (text or "").split(), [], ""
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


def tbox(d, x, y, w, h, size, text, color=TEXT, bold=False, align="left", lines=None):
	f = font(size, bold)
	p = pitch(size)
	n = max(1, h // p) if lines is None else lines
	ls = wrap(text, f, w)
	if len(ls) > n:
		ls = ls[:n]
		while ls[-1] and f.getlength(ls[-1] + "…") > w:
			ls[-1] = ls[-1].rsplit(" ", 1)[0] if " " in ls[-1] else ls[-1][:-1]
		ls[-1] += "…"
	for i, ln in enumerate(ls):
		lx = x + (w - f.getlength(ln)) if align == "right" else (x + (w - f.getlength(ln)) / 2 if align == "center" else x)
		d.text((lx, y + i * p), ln, font=f, fill=color)
	return len(ls) * p


def layer(im):
	return Image.new("RGBA", im.size, (0, 0, 0, 0))


def rrect(im, box, color, alpha=255, r=0):
	x, y, w, h = box
	ov = layer(im)
	ImageDraw.Draw(ov).rounded_rectangle([x, y, x + w - 1, y + h - 1], r, fill=color + (alpha,))
	return Image.alpha_composite(im, ov)


def vgrad(im, box, color, a0, a1):
	x, y, w, h = box
	ov = layer(im)
	d = ImageDraw.Draw(ov)
	for i in range(h):
		a = int(a0 + (a1 - a0) * i / max(1, h - 1))
		d.line([x, y + i, x + w, y + i], fill=color + (a,))
	return Image.alpha_composite(im, ov)


def poster(im, box, path, r=0):
	x, y, w, h = box
	if path and os.path.isfile(path):
		p = Image.open(path).convert("RGB")
		k = max(w / p.width, h / p.height)
		p = p.resize((int(p.width * k) + 1, int(p.height * k) + 1))
		p = p.crop(((p.width - w) // 2, (p.height - h) // 2, (p.width - w) // 2 + w, (p.height - h) // 2 + h)).convert("RGBA")
	else:
		p = Image.new("RGBA", (w, h), (30, 44, 64, 255))
	m = Image.new("L", (w, h), 0)
	ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
	im.paste(p, (x, y), m)
	return im


def picon(im, box, path):
	x, y, w, h = box
	if path and os.path.isfile(path):
		pc = Image.open(path).convert("RGBA")
		pc.thumbnail((w, h))
		im.paste(pc, (int(x + (w - pc.width) / 2), int(y + (h - pc.height) / 2)), pc)
	return im


def pill(d, x, y, text, size=22, fg=TEXT, bg=(52, 70, 94, 255), pad=14, h=None):
	f = font(size)
	tw = f.getlength(text)
	h = h or pitch(size) + 10
	d.rounded_rectangle([x, y, x + tw + 2 * pad, y + h], h // 2, fill=bg)
	d.text((x + pad, y + (h - pitch(size)) / 2), text, font=f, fill=fg)
	return x + tw + 2 * pad


def bar(d, box, frac, r=3, track=(52, 70, 94, 255), fill=BLUE + (255,)):
	x, y, w, h = box
	d.rounded_rectangle([x, y, x + w, y + h], r, fill=track)
	d.rounded_rectangle([x, y, x + max(h, int(w * frac)), y + h], r, fill=fill)


def video():
	return Image.open(os.environ.get("MODEL_VIDEO", D["video"])).convert("RGBA").resize((W, H))


S = D["sel"]
N, X = S["now"], S["next"]
# genre / rating only from the data: a rating is shown only when the identity engine resolved the programme
# (never a placeholder number); the duration comes from the EPG times
META = [x for x in (N.get("genre"), ("★ %.1f IMDb" % N["rating"]) if N.get("rating") else None) if x]
DUR = (N.get("times", "").split("·")[-1].strip() if "min" in N.get("times", "") else "")
TECH_CHIPS = S.get("chips") or ["HD", "1920×1080", "16:9", "SNR 75 %", "12.1 dB"]


# ------------------------------------------------------------------------------------------------ MODERN
def modern_infobar(on):
	im = video()
	im = vgrad(im, (0, 700, W, 380), (0, 0, 0), 0, 200)
	card = (60, 790, 1800, 250)
	im = rrect(im, card, NAVY["panel"], 235, 28)
	d = ImageDraw.Draw(im, "RGBA")
	x0 = 84
	if on:
		im = poster(im, (84, 806, 146, 218), N.get("poster"), 16)
		d = ImageDraw.Draw(im, "RGBA")
		x0 = 254
	im = picon(im, (x0, 812, 130, 64), S.get("picon")); d = ImageDraw.Draw(im, "RGBA")
	d.text((x0 + 146, 816), "%s  %s" % (S["num"], S["name"]), font=font(28, True), fill=TEXT)
	cx = 1836
	for c in reversed(TECH_CHIPS):
		cx -= font(20).getlength(c) + 28 + 10
		pill(d, cx, 818, c, 20, MUTED)
	tbox(d, x0, 884, 1300, 52, 40, N["title"], TEXT, True, lines=1)
	pill(d, 1836 - font(24).getlength(N["times_short"]) - 28, 890, N["times_short"], 24)
	bar(d, (x0, 950, 1836 - x0, 6), N["progress"])
	tbox(d, x0, 978, 1100, 34, 26, "Next  %s   %s" % (X["start"], X["title"]), MUTED, lines=1)
	tbox(d, 1836 - 400, 980, 400, 34, 24, "  ·  ".join(META), ACCENT, align="right", lines=1)
	return im


def modern_sib(on):
	im = video()
	im = vgrad(im, (0, 480, W, 600), (0, 0, 0), 0, 210)
	d = ImageDraw.Draw(im, "RGBA")
	for i, (ev, label) in enumerate(((N, "NOW"), (X, "NEXT"))):
		cx = 60 + i * 910
		im = rrect(im, (cx, 540, 890, 480), NAVY["panel"], 232, 28)
		d = ImageDraw.Draw(im, "RGBA")
		tx = cx + 28
		if on:
			im = poster(im, (cx + 28, 568, 200, 300), ev.get("poster"), 18)
			d = ImageDraw.Draw(im, "RGBA")
			tx = cx + 252
		tw = cx + 890 - 28 - tx
		pill(d, tx, 570, label, 20, (26, 19, 0), ACCENT + (255,))
		tbox(d, tx, 616, tw, 90, 36, ev["title"], TEXT, True, lines=2)
		tbox(d, tx, 712, tw, 30, 24, ev.get("times_short") or ev.get("times", ""), ACCENT, lines=1)
		dh = 236 if on else 268
		tbox(d, tx, 756, tw, dh if on else dh, 23, ev.get("desc", ""), MUTED)
		if on:
			pass
	return im


def modern_cs(on):
	im = video()
	im = rrect(im, (0, 0, W, H), (0, 0, 0), 140, 0)
	im = rrect(im, (60, 60, 840, 960), NAVY["panel"], 240, 28)
	im = rrect(im, (920, 60, 940, 960), NAVY["panel"], 240, 28)
	d = ImageDraw.Draw(im, "RGBA")
	d.text((92, 84), D["bouquet"], font=font(32, True), fill=TEXT)
	rows = D["rows"][:14]
	for i, r in enumerate(rows):
		ry = 148 + i * 60
		if i == D["selected"]:
			d.rounded_rectangle([76, ry, 884, ry + 56], 14, fill=NAVY["sel"] + (255,))
		if r.get("marker"):
			d.text((110, ry + 14), r["name"], font=font(24), fill=MUTED)
			continue
		d.text((92, ry + 14), str(r["num"]), font=font(22), fill=MUTED)
		im = picon(im, (150, ry + 8, 80, 40), r.get("picon")); d = ImageDraw.Draw(im, "RGBA")
		tbox(d, 244, ry + 13, 380, 30, 26, r["name"], TEXT, lines=1)
		tbox(d, 630, ry + 16, 200, 28, 21, r.get("event", ""), ACCENT, lines=1)
	x0 = 952
	if on:
		im = poster(im, (952, 92, 300, 450), N.get("poster"), 22)
		d = ImageDraw.Draw(im, "RGBA")
		x0 = 1280
	w = 1828 - x0
	im = picon(im, (x0, 96, 150, 76), S.get("picon")); d = ImageDraw.Draw(im, "RGBA")
	tbox(d, x0, 186, w, 36, 28, "%s  ·  %s" % (S["num"], S["name"]), TEXT, True, lines=1)
	pill(d, x0, 236, "NOW", 20, (26, 19, 0), ACCENT + (255,))
	tbox(d, x0, 282, w, 96, 38, N["title"], TEXT, True, lines=2)
	pill(d, x0, 384, N["times_short"], 22)
	bar(d, (x0, 436, w, 6), N["progress"])
	tbox(d, x0, 462, w, 26 * (3 if on else 6), 22, N["desc"], MUTED)
	ny = 570 if on else 650
	d.line([952, ny, 1828, ny], fill=(40, 58, 80, 255), width=2)
	nx = 952
	if on:
		im = poster(im, (952, ny + 24, 160, 240), X.get("poster"), 16)
		d = ImageDraw.Draw(im, "RGBA")
		nx = 1136
	pill(d, nx, ny + 26, "NEXT  " + X["start"], 20)
	tbox(d, nx, ny + 72, 1828 - nx, 40, 30, X["title"], TEXT, True, lines=1)
	tbox(d, nx, ny + 120, 1828 - nx, 26 * (6 if on else 9), 22, X["desc"], MUTED)
	kx = 92
	for (c, lab) in zip(((200, 40, 40), (40, 160, 70), (210, 170, 30), (50, 100, 210)), D["keys"]):
		d.rounded_rectangle([kx, 986, kx + 14, 1000], 7, fill=c + (255,))
		d.text((kx + 22, 980), lab, font=font(20), fill=MUTED)
		kx += 200
	return im


def hm(t):
	return datetime.datetime.fromtimestamp(t).strftime("%H:%M")


def epg_grid(im, d, gx, gy, gw, gh, rows, span, radius):
	t0 = (G["now"] - 1800) // 1800 * 1800
	sw = 240
	pxm = (gw - sw) / (span * 60.0)
	for k in range(0, span + 1, 30):
		lx = gx + sw + int(k * 60 * pxm)
		if lx < gx + gw - 50:
			d.text((lx + 6, gy - 38), hm(t0 + k * 60), font=font(22), fill=ACCENT)
	rh = gh // rows
	for i, c in enumerate(G["channels"][:rows]):
		ry = gy + i * rh
		d.rounded_rectangle([gx, ry + 3, gx + sw - 6, ry + rh - 3], radius, fill=((24, 110, 90) if i == 0 else (34, 52, 74)) + (255,))
		im = picon(im, (gx + 8, ry + 10, 86, rh - 20), c.get("picon")); d = ImageDraw.Draw(im, "RGBA")
		tbox(d, gx + 102, ry + (rh - 27) // 2, sw - 112, 28, 22, c["name"], TEXT, lines=1)
		for e in c["events"]:
			b, en = max(e["begin"], t0), min(e["begin"] + e["dur"], t0 + span * 60)
			if en <= b:
				continue
			x0 = gx + sw + int((b - t0) * pxm)
			x1 = gx + sw + int((en - t0) * pxm)
			now = e["begin"] <= G["now"] < e["begin"] + e["dur"]
			sel = i == 0 and now
			col = (214, 152, 0) if sel else ((30, 96, 120) if now else (34, 52, 74))
			d.rounded_rectangle([x0 + 3, ry + 3, x1 - 3, ry + rh - 3], radius, fill=col + (255,))
			if x1 - x0 > 40:
				tbox(d, x0 + 14, ry + (rh - 27) // 2, x1 - x0 - 24, 28, 22, e["title"], TEXT, lines=1)
	nx = gx + sw + int((G["now"] - t0) * pxm)
	d.line([nx, gy - 6, nx, gy + gh], fill=(240, 70, 70, 255), width=3)
	return im, d


def modern_epg(on):
	im = Image.new("RGBA", (W, H), NAVY["primary"] + (255,))
	d = ImageDraw.Draw(im, "RGBA")
	d.text((60, 30), D["bouquet"], font=font(32, True), fill=TEXT)
	tbox(d, 1600, 30, 260, 50, 40, G["clock"], TEXT, align="right", lines=1)
	gw = 1250 if on else 1500
	im, d = epg_grid(im, d, 60, 150, gw, 800, 8, 180, 12)
	px = 60 + gw + 24
	im = rrect(im, (px, 100, 1860 - px, 850), NAVY["panel"], 255, 24)
	d = ImageDraw.Draw(im, "RGBA")
	s = G["selected"]
	tx = px + 24
	tw = 1860 - px - 48
	if on:
		im = poster(im, (tx, 124, 240, 360), s.get("poster"), 18)
		d = ImageDraw.Draw(im, "RGBA")
		im = picon(im, (tx + 260, 128, 130, 64), s.get("picon")); d = ImageDraw.Draw(im, "RGBA")
		pill(d, tx + 260, 212, s["times"], 20)
		pill(d, tx + 260, 256, s["duration"], 20)
		ty = 508
	else:
		tbox(d, tx, 124, tw, 30, 22, s["channel"], MUTED, lines=1)
		pill(d, tx, 164, s["times"], 20)
		pill(d, tx, 208, s["duration"], 20)
		ty = 260
	h = tbox(d, tx, ty, tw, 84, 34, s["title"], TEXT, True, lines=2)
	tbox(d, tx, ty + h + 14, tw, 920 - ty - h - 14, 22, s["desc"], MUTED)
	kx = 60
	for c, lab in zip(((200, 40, 40), (40, 160, 70), (210, 170, 30), (50, 100, 210)), G["keys"]):
		d.rounded_rectangle([kx, 1000, kx + 14, 1014], 7, fill=c + (255,))
		d.text((kx + 22, 993), lab, font=font(22), fill=MUTED)
		kx += 300
	return im


def modern_eventview(on):
	im = video()
	im = rrect(im, (0, 0, W, H), (0, 0, 0), 120, 0)
	im = rrect(im, (60, 60, 1800, 960), NAVY["panel"], 242, 32)
	d = ImageDraw.Draw(im, "RGBA")
	tx = 100
	if on:
		im = poster(im, (100, 100, 400, 600), N.get("poster"), 24)
		d = ImageDraw.Draw(im, "RGBA")
		tx = 540
	tw = 1820 - tx
	im = picon(im, (tx, 104, 150, 76), S.get("picon")); d = ImageDraw.Draw(im, "RGBA")
	tbox(d, tx + 170, 124, 600, 40, 28, S["name"], MUTED, lines=1)
	h = tbox(d, tx, 200, tw, 120, 52, N["title"], TEXT, True, lines=2)
	cx = tx
	for c in [N["times_short"]] + ([DUR] if DUR else []) + META:
		cx = pill(d, cx, 220 + h, c, 22) + 12
	tbox(d, tx, 290 + h, tw, 26 * (14 if on else 15), 24, N["desc"] + " " + N["desc"], TEXT)
	ny = 760 if on else 800
	d.line([100, ny, 1820, ny], fill=(40, 58, 80, 255), width=2)
	nx = 100
	if on:
		im = poster(im, (100, ny + 20, 110, 165), X.get("poster"), 12)
		d = ImageDraw.Draw(im, "RGBA")
		nx = 236
	pill(d, nx, ny + 24, "NEXT  " + X["times"], 20)
	tbox(d, nx, ny + 70, 1820 - nx, 40, 30, X["title"], TEXT, True, lines=1)
	tbox(d, nx, ny + 114, 1820 - nx, 52, 21, X["desc"], MUTED)
	return im


# ------------------------------------------------------------------------------------------------ MINIMAL
def minimal_infobar(on):
	im = video()
	im = vgrad(im, (0, 880, W, 200), (0, 0, 0), 0, 225)
	d = ImageDraw.Draw(im, "RGBA")
	x0 = 60
	if on:
		im = poster(im, (60, 948, 70, 105), N.get("poster"), 6)
		d = ImageDraw.Draw(im, "RGBA")
		x0 = 150
	d.text((x0, 960), "%s  %s" % (S["num"], S["name"]), font=font(24), fill=MUTED)
	tbox(d, x0, 994, 1060, 44, 34, N["title"], TEXT, lines=1)
	bar(d, (x0, 1046, 1060, 3), N["progress"], 1)
	tbox(d, 1240, 960, 620, 30, 24, N["times_short"], TEXT, align="right", lines=1)
	tbox(d, 1240, 1000, 620, 34, 26, "%s   %s" % (X["start"], X["title"]), MUTED, align="right", lines=1)
	return im


def minimal_sib(on):
	im = video()
	im = vgrad(im, (0, 500, W, 580), (0, 0, 0), 0, 230)
	d = ImageDraw.Draw(im, "RGBA")
	x0 = 60
	if on:
		im = poster(im, (60, 640, 220, 330), N.get("poster"), 8)
		d = ImageDraw.Draw(im, "RGBA")
		x0 = 310
	w = 1860 - x0
	d.text((x0, 640), "NOW   " + N["times_short"], font=font(22), fill=ACCENT)
	h = tbox(d, x0, 674, w, 90, 40, N["title"], TEXT, lines=2)
	tbox(d, x0, 690 + h, w, 26 * 5, 23, N["desc"], (210, 214, 222))
	d.line([x0, 920, 1860, 920], fill=(96, 104, 116, 255), width=1)
	tbox(d, x0, 936, w, 34, 26, "NEXT   %s   %s" % (X["start"], X["title"]), MUTED, lines=1)
	tbox(d, x0, 980, w, 52, 21, X["desc"], (150, 158, 170), lines=2)
	return im


def minimal_cs(on):
	im = video()
	im = vgrad(im, (0, 0, 820, H), (0, 0, 0), 215, 215)
	im = vgrad(im, (820, 0, 260, H), (0, 0, 0), 120, 120)
	d = ImageDraw.Draw(im, "RGBA")
	d.text((60, 40), D["bouquet"], font=font(26), fill=MUTED)
	rows = D["rows"][:17]
	for i, r in enumerate(rows):
		ry = 100 + i * 50
		if i == D["selected"]:
			d.rectangle([60, ry + 6, 64, ry + 44], fill=ACCENT + (255,))
		if r.get("marker"):
			d.text((90, ry + 12), r["name"], font=font(21), fill=(130, 138, 150))
			continue
		d.text((80, ry + 12), str(r["num"]), font=font(21), fill=(130, 138, 150))
		tbox(d, 140, ry + 10, 360, 30, 25, r["name"], TEXT if i == D["selected"] else (205, 210, 218), lines=1)
		tbox(d, 510, ry + 13, 280, 28, 20, r.get("event", ""), (150, 158, 170), lines=1)
	y0 = 960
	x0 = 60
	if on:
		im = poster(im, (900, 750, 140, 210), N.get("poster"), 6)
		d = ImageDraw.Draw(im, "RGBA")
	tbox(d, 900 if not on else 1070, 760, 900 if not on else 760, 44, 34, N["title"], TEXT, lines=1)
	tbox(d, 900 if not on else 1070, 810, 900 if not on else 760, 30, 22, "%s   %s" % (N["times_short"], N.get("genre") or ""), ACCENT, lines=1)
	tbox(d, 900 if not on else 1070, 850, 900 if not on else 760, 26 * 4, 21, N["desc"], (205, 210, 218))
	return im


def minimal_epg(on):
	im = Image.new("RGBA", (W, H), (6, 14, 26, 255))
	d = ImageDraw.Draw(im, "RGBA")
	s = G["selected"]
	x0 = 60
	if on:
		im = poster(im, (60, 40, 110, 165), s.get("poster"), 6)
		d = ImageDraw.Draw(im, "RGBA")
		x0 = 196
	tbox(d, x0, 44, 1300, 44, 34, s["title"], TEXT, lines=1)
	tbox(d, x0, 92, 1300, 30, 22, "%s   ·   %s   ·   %s" % (s["channel"], s["times"], s["duration"]), ACCENT, lines=1)
	tbox(d, x0, 128, 1860 - x0, 52, 21, s["desc"], (190, 196, 206), lines=2)
	tbox(d, 1600, 44, 260, 44, 34, G["clock"], MUTED, align="right", lines=1)
	im, d = epg_grid(im, d, 60, 260, 1800, 700, 8, 180, 0)
	kx = 60
	for c, lab in zip(((200, 40, 40), (40, 160, 70), (210, 170, 30), (50, 100, 210)), G["keys"]):
		d.rectangle([kx, 1003, kx + 4, 1023], fill=c + (255,))
		d.text((kx + 14, 1000), lab, font=font(20), fill=(150, 158, 170))
		kx += 260
	return im


def minimal_eventview(on):
	im = video()
	im = rrect(im, (0, 0, W, H), (0, 0, 0), 200, 0)
	d = ImageDraw.Draw(im, "RGBA")
	x0, w = 360, 1200
	if on:
		im = poster(im, (360, 120, 200, 300), N.get("poster"), 8)
		d = ImageDraw.Draw(im, "RGBA")
		tbox(d, 590, 130, 970, 30, 24, "%s   ·   %s" % (S["name"], N["times_short"]), ACCENT, lines=1)
		h = tbox(d, 590, 170, 970, 120, 46, N["title"], TEXT, lines=2)
		ty = 450
	else:
		tbox(d, x0, 130, w, 30, 24, "%s   ·   %s" % (S["name"], N["times_short"]), ACCENT, lines=1)
		h = tbox(d, x0, 170, w, 120, 46, N["title"], TEXT, lines=2)
		ty = 190 + h
	tbox(d, x0, ty, w, 26 * (13 if on else 18), 24, N["desc"] + " " + N["desc"], (220, 224, 230))
	tbox(d, x0, 960, w, 34, 24, "NEXT   %s   %s" % (X["start"], X["title"]), MUTED, lines=1)
	return im


MODELS = {
	"modern": {"infobar": modern_infobar, "secondinfobar": modern_sib, "channelselection": modern_cs, "epg": modern_epg, "eventview": modern_eventview},
	"minimal": {"infobar": minimal_infobar, "secondinfobar": minimal_sib, "channelselection": minimal_cs, "epg": minimal_epg, "eventview": minimal_eventview},
}
for m, screens in MODELS.items():
	for sec, fn in screens.items():
		for on in (True, False):
			fn(on).convert("RGB").save(os.path.join(OUT, "%s_%s_%s.png" % (m, sec, "on" if on else "off")))
print("rendered", len(os.listdir(OUT)))
