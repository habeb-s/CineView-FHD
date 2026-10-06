#!/usr/bin/env python3
"""CineView MLA brand assets (user 2026-10-06 20:51): plugin icon candidates, logo (full / compact / dark background)
and the review sheets.  Drawn with PIL at 4x and reduced with Lanczos; colours from the navy theme (steThemePrimary
#0A1D35, steThemePanel #08182B, steThemeAccent #F9C731, foreground #F0F0F0); type: Inter (SIL OFL), rendered to PNG.
The plugin icon is 160x69 (Plugin Browser slot 185x80, same ratio): 160*69*4 = 44 160 bytes < 48 000, so the receiver
keeps it in normal memory (accelAuto threshold), not in the 5400 kB fast graphics pool.
usage: make_brand.py <out dir>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

NAVY, PANEL, EDGE = (10, 29, 53), (8, 24, 43), (32, 58, 92)
GOLD, WHITE, MUTED = (249, 199, 49), (240, 240, 240), (150, 166, 186)
FD = "/usr/share/fonts/opentype/inter/"
K = 4  # supersampling


def font(name, px):
	return ImageFont.truetype(FD + name, int(px * K))


def canvas(w, h, bg=None):
	return Image.new("RGBA", (w * K, h * K), bg + (255,) if bg else (0, 0, 0, 0))


def done(im, w, h):
	return im.resize((w, h), Image.LANCZOS)


def tile(d, w, h, r=10):
	d.rounded_rectangle([0, 0, w * K - 1, h * K - 1], r * K, fill=PANEL + (255,), outline=EDGE + (255,), width=max(1, int(1.5 * K)))


# ---- marks (drawn into a box x, y, s = side, in K units) -----------------------------------------------------------
def mark_monogram(d, x, y, s, bg=PANEL):
	"""A: gold rounded frame with a bold 'CV' - a screen frame carrying the initials."""
	d.rounded_rectangle([x, y, x + s, y + s], s * 0.22, fill=GOLD + (255,))
	f = ImageFont.truetype(FD + "InterDisplay-ExtraBold.otf", int(s * 0.50))
	tw = d.textlength("CV", font=f)
	bb = d.textbbox((0, 0), "CV", font=f)
	d.text((x + (s - tw) / 2, y + (s - (bb[3] - bb[1])) / 2 - bb[1]), "CV", font=f, fill=bg + (255,))


def mark_lens(d, x, y, s, bg=PANEL):
	"""B: lens ring with a play triangle - cinema + view."""
	t = s * 0.12
	d.ellipse([x, y, x + s, y + s], outline=GOLD + (255,), width=int(t))
	cx, cy, r = x + s / 2, y + s / 2, s * 0.22
	d.polygon([(cx - r * 0.75, cy - r), (cx - r * 0.75, cy + r), (cx + r * 1.05, cy)], fill=GOLD + (255,))


def mark_layers(d, x, y, s, bg=PANEL):
	"""C: three stacked screens - several layouts (MLA = multi-layout) on one skin."""
	w, h = s * 0.78, s * 0.52
	back = WHITE if sum(bg) < 384 else NAVY  # light backgrounds get navy back layers (white would vanish)
	for i, (col, a) in enumerate(((back, 70), (back, 140), (GOLD, 255))):
		ox, oy = x + i * s * 0.11, y + s * 0.10 + i * s * 0.13
		d.rounded_rectangle([ox, oy, ox + w, oy + h], s * 0.07, fill=col + (a,))
	ox, oy = x + 2 * s * 0.11, y + s * 0.10 + 2 * s * 0.13
	cx, cy, r = ox + w / 2, oy + h / 2, h * 0.22
	d.polygon([(cx - r * 0.8, cy - r), (cx - r * 0.8, cy + r), (cx + r * 1.1, cy)], fill=PANEL + (255,))


MARKS = {"A": mark_monogram, "B": mark_lens, "C": mark_layers}


def wordmark(d, x, y, h, dark=True, compact=False):
	"""'CineView' + gold 'MLA' on one line; h = cap area height in K units."""
	f1 = ImageFont.truetype(FD + "InterDisplay-SemiBold.otf", int(h))
	f2 = ImageFont.truetype(FD + "InterDisplay-ExtraBold.otf", int(h))
	col = WHITE if dark else NAVY
	d.text((x, y), "CineView", font=f1, fill=col + (255,))
	w1 = d.textlength("CineView", font=f1)
	d.text((x + w1 + h * 0.28, y), "MLA", font=f2, fill=GOLD + (255,))
	return w1 + h * 0.28 + d.textlength("MLA", font=f2)


def icon(key, w=160, h=69):
	im = canvas(w, h)
	d = ImageDraw.Draw(im)
	tile(d, w, h)
	s = int(h * K * 0.66)
	mx, my = int(h * K * 0.17), int((h * K - s) / 2)
	MARKS[key](d, mx, my, s)
	tx = mx + s + int(h * K * 0.16)
	f1 = ImageFont.truetype(FD + "InterDisplay-SemiBold.otf", int(h * K * 0.27))
	f2 = ImageFont.truetype(FD + "InterDisplay-ExtraBold.otf", int(h * K * 0.27))
	d.text((tx, int(h * K * 0.17)), "CineView", font=f1, fill=WHITE + (255,))
	d.text((tx, int(h * K * 0.50)), "MLA", font=f2, fill=GOLD + (255,))
	return done(im, w, h)


def logo_full(key, dark=True, w=1200, h=300):
	im = canvas(w, h)
	d = ImageDraw.Draw(im)
	s = int(h * K * 0.62)
	mx, my = int(h * K * 0.12), int((h * K - s) / 2)
	MARKS[key](d, mx, my, s, bg=NAVY if dark else (244, 246, 249))
	tx = mx + s + int(h * K * 0.14)
	wordmark(d, tx, int(h * K * 0.20), h * K * 0.36, dark=dark)
	f3 = ImageFont.truetype(FD + "Inter-Medium.otf", int(h * K * 0.085))
	d.text((tx + 4 * K, int(h * K * 0.68)), "DESIGNS FOR ENIGMA2  ·  by habeb-s", font=f3, fill=(MUTED if dark else (90, 104, 124)) + (255,))
	return done(im, w, h)


def logo_compact(key, size=256, bg=True):
	im = canvas(size, size)
	d = ImageDraw.Draw(im)
	if bg:
		d.rounded_rectangle([0, 0, size * K - 1, size * K - 1], size * K * 0.2, fill=NAVY + (255,))
	s = int(size * K * 0.64)
	MARKS[key](d, (size * K - s) // 2, (size * K - s) // 2, s, bg=NAVY)
	return done(im, size, size)


def sheet(out, key_order=("A", "B", "C")):
	"""Review sheet: each icon at real size on the Plugin Browser row colours and 3x, plus logos on dark / light."""
	W = 1500
	rows = []
	for k in key_order:
		ic = icon(k)
		row = Image.new("RGB", (W, 260), NAVY)
		d = ImageDraw.Draw(row)
		d.text((30, 20), "Option %s" % k, font=ImageFont.truetype(FD + "Inter-SemiBold.otf", 34), fill=WHITE)
		d.text((30, 64), {"A": "Monogram: CV in a gold screen frame", "B": "Lens + play: cinema / view", "C": "Stacked screens: several designs"}[k],
			font=ImageFont.truetype(FD + "Inter-Medium.otf", 22), fill=MUTED)
		row.paste(ic, (40, 120), ic)  # real size, list background
		sel = Image.new("RGB", (240, 100), (36, 74, 120))
		sel.paste(ic, (40, 15), ic)
		row.paste(sel, (230, 105))
		big = ic.resize((480, 207), Image.LANCZOS)
		row.paste(big, (520, 30), big)
		lg = logo_compact(k, 200)
		row.paste(lg, (1060, 30), lg)
		d.text((240, 210), "selected row", font=ImageFont.truetype(FD + "Inter-Medium.otf", 18), fill=MUTED)
		d.text((40, 210), "actual size", font=ImageFont.truetype(FD + "Inter-Medium.otf", 18), fill=MUTED)
		rows.append(row)
	s = Image.new("RGB", (W, 260 * len(rows)), NAVY)
	for i, r in enumerate(rows):
		s.paste(r, (0, 260 * i))
	s.save(os.path.join(out, "icon_options.png"))


def main(out):
	os.makedirs(out, exist_ok=True)
	for k in MARKS:
		icon(k).save(os.path.join(out, "plugin_%s.png" % k))
		logo_full(k, True).save(os.path.join(out, "logo_%s_full_dark.png" % k))     # for dark backgrounds
		logo_full(k, False).save(os.path.join(out, "logo_%s_full_light.png" % k))   # for light backgrounds
		logo_compact(k, 256).save(os.path.join(out, "logo_%s_compact.png" % k))
		logo_compact(k, 256, bg=False).save(os.path.join(out, "logo_%s_mark.png" % k))
	sheet(out)
	# logo sheet: full on dark, full on light, compact
	ls = Image.new("RGB", (1500, 3 * 340), NAVY)
	for i, k in enumerate(MARKS):
		dk = logo_full(k, True)
		ls.paste(dk, (20, i * 340 + 20), dk)
		lt = Image.new("RGB", (1200, 300), (244, 246, 249))
		l2 = logo_full(k, False)
		lt.paste(l2, (0, 0), l2)
		ls.paste(lt.resize((400, 100)), (1080, i * 340 + 40))
		cp = logo_compact(k, 120)
		ls.paste(cp, (1220, i * 340 + 180), cp)
	ls.save(os.path.join(out, "logo_options.png"))
	print("written", sorted(os.listdir(out)))


if __name__ == "__main__":
	main(sys.argv[1])
