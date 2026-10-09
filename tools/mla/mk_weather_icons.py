#!/usr/bin/env python3
"""CineView MLA weather icons (own artwork, drawn here; no third-party icon set).

usage: mk_weather_icons.py <out dir> [--preview <png>]
Writes 64x64 RGBA PNGs named by weather type - the names Components/CineViewMLAWeatherData uses:
  clear_day clear_night partly_day partly_night cloudy fog drizzle rain snow thunder
Drawn at 512x512 and reduced (LANCZOS) for smooth edges; the designs show them at 30-34 px (CineViewMLAWeatherPixmap
scales them keeping the aspect ratio), on the dark CineView themes.  --preview: all icons at 34 px on every theme
background, for a visual check."""
import math
import os
import sys

from PIL import Image, ImageDraw

S = 512          # drawing size
OUT = 64         # icon size
SUN, SUN_RAY = (255, 196, 61, 255), (255, 170, 20, 255)
MOON, MOON_SHADE = (232, 238, 246, 255), (196, 208, 224, 255)
CLOUD, CLOUD_BACK, CLOUD_DARK, CLOUD_DARK_BACK = (242, 245, 248, 255), (176, 188, 200, 255), (150, 160, 172, 255), (104, 116, 130, 255)
RAIN, DRIZZLE, SNOW, SNOW_EDGE = (79, 163, 255, 255), (130, 190, 255, 255), (255, 255, 255, 255), (170, 205, 245, 255)
BOLT, BOLT_EDGE, FOG = (255, 210, 63, 255), (255, 150, 0, 255), (205, 213, 222, 255)


def canvas():
	return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def circle(d, cx, cy, r, fill):
	d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)


def sun(img, cx, cy, r):
	d = ImageDraw.Draw(img)
	for i in range(8):
		a = math.radians(i * 45 + 22.5)
		x0, y0 = cx + math.cos(a) * r * 1.32, cy + math.sin(a) * r * 1.32
		x1, y1 = cx + math.cos(a) * r * 1.72, cy + math.sin(a) * r * 1.72
		d.line((x0, y0, x1, y1), fill=SUN_RAY, width=int(r * 0.24))
		circle(d, x0, y0, r * 0.12, SUN_RAY)
		circle(d, x1, y1, r * 0.12, SUN_RAY)
	circle(d, cx, cy, r, SUN)


def moon(img, cx, cy, r, cut=0.86):
	m = Image.new("L", (S, S), 0)
	md = ImageDraw.Draw(m)
	circle(md, cx, cy, r, 255)
	circle(md, cx + r * 0.62, cy - r * 0.42, r * cut, 0)  # crescent
	layer = Image.new("RGBA", (S, S), MOON)
	shade = Image.new("L", (S, S), 0)
	circle(ImageDraw.Draw(shade), cx - r * 0.18, cy + r * 0.2, r * 0.75, 255)
	layer.paste(Image.new("RGBA", (S, S), MOON_SHADE), (0, 0), Image.composite(shade, Image.new("L", (S, S), 0), m))
	img.alpha_composite(Image.composite(layer, Image.new("RGBA", (S, S), (0, 0, 0, 0)), m))


def cloud(img, cx, cy, w, fill, edge=None):
	"""Cloud of width w centred at (cx, cy) (cy = middle of its flat base band)."""
	m = Image.new("L", (S, S), 0)
	d = ImageDraw.Draw(m)
	h = w * 0.24
	d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=h / 2, fill=255)
	circle(d, cx - w * 0.20, cy - h * 0.40, w * 0.20, 255)
	circle(d, cx + w * 0.06, cy - h * 0.85, w * 0.27, 255)
	circle(d, cx + w * 0.30, cy - h * 0.25, w * 0.17, 255)
	if edge:  # thin darker rim so a light cloud stays separate from what is behind it
		grow = m.resize((S, S))
		rim = Image.new("RGBA", (S, S), edge)
		from PIL import ImageFilter
		img.alpha_composite(Image.composite(rim, Image.new("RGBA", (S, S), (0, 0, 0, 0)), grow.filter(ImageFilter.MaxFilter(13))))
	img.alpha_composite(Image.composite(Image.new("RGBA", (S, S), fill), Image.new("RGBA", (S, S), (0, 0, 0, 0)), m))


def drops(img, xs, y0, length, color, width):
	d = ImageDraw.Draw(img)
	for x in xs:
		d.line((x, y0, x - length * 0.35, y0 + length), fill=color, width=width)
		circle(d, x, y0, width / 2, color)
		circle(d, x - length * 0.35, y0 + length, width / 2, color)


def flake(img, cx, cy, r):
	d = ImageDraw.Draw(img)
	for i in range(3):
		a = math.radians(i * 60 + 90)
		dx, dy = math.cos(a) * r, math.sin(a) * r
		d.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=SNOW_EDGE, width=int(r * 0.55))
	for i in range(3):
		a = math.radians(i * 60 + 90)
		dx, dy = math.cos(a) * r, math.sin(a) * r
		d.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=SNOW, width=int(r * 0.32))
	circle(d, cx, cy, r * 0.28, SNOW)


def bolt(img, x, y, s):
	d = ImageDraw.Draw(img)
	pts = [(x + 0.10 * s, y), (x - 0.30 * s, y + 0.62 * s), (x - 0.02 * s, y + 0.62 * s), (x - 0.16 * s, y + 1.10 * s),
		(x + 0.34 * s, y + 0.42 * s), (x + 0.05 * s, y + 0.42 * s), (x + 0.22 * s, y)]
	d.polygon(pts, fill=BOLT_EDGE)
	inner = [(px + (x + 0.03 * s - px) * 0.18, py + (y + 0.55 * s - py) * 0.12) for px, py in pts]
	d.polygon(inner, fill=BOLT)


def make():
	icons = {}
	im = canvas(); sun(im, 256, 256, 112); icons["clear_day"] = im
	im = canvas(); moon(im, 250, 262, 150); icons["clear_night"] = im
	im = canvas(); sun(im, 300, 190, 88); cloud(im, 236, 352, 360, CLOUD, edge=CLOUD_BACK); icons["partly_day"] = im
	im = canvas(); moon(im, 300, 170, 130, cut=0.74); cloud(im, 230, 372, 360, CLOUD, edge=CLOUD_BACK); icons["partly_night"] = im
	im = canvas(); cloud(im, 300, 230, 300, CLOUD_BACK); cloud(im, 230, 340, 380, CLOUD); icons["cloudy"] = im
	im = canvas(); cloud(im, 256, 214, 380, CLOUD_BACK)
	d = ImageDraw.Draw(im)
	for y, x0, x1 in ((318, 96, 400), (380, 136, 436), (442, 86, 360)):
		d.rounded_rectangle((x0, y - 17, x1, y + 17), radius=17, fill=FOG)
	icons["fog"] = im
	im = canvas(); cloud(im, 256, 236, 400, CLOUD); drops(im, (196, 286, 376), 340, 60, DRIZZLE, 24); icons["drizzle"] = im
	im = canvas(); cloud(im, 256, 226, 400, CLOUD); drops(im, (176, 266, 356, 446), 326, 120, RAIN, 30); icons["rain"] = im
	im = canvas(); cloud(im, 256, 226, 400, CLOUD)
	for cx, cy in ((176, 372), (296, 352), (226, 452), (356, 444)):
		flake(im, cx, cy, 44)
	icons["snow"] = im
	im = canvas(); cloud(im, 256, 222, 400, CLOUD_DARK); bolt(im, 262, 268, 220); icons["thunder"] = im
	return {k: v.resize((OUT, OUT), Image.LANCZOS) for k, v in icons.items()}


def preview(icons, path):
	themes = {"navy": (16, 30, 58), "black": (8, 8, 10), "graphite": (40, 44, 50), "purple": (40, 22, 60),
		"burgundy": (60, 16, 26), "green": (14, 46, 34)}
	names = sorted(icons)
	cell = 44
	img = Image.new("RGBA", (cell * len(names) + 8, cell * len(themes) + 8), (0, 0, 0, 255))
	for r, (t, col) in enumerate(themes.items()):
		ImageDraw.Draw(img).rectangle((0, 4 + r * cell, img.width, 4 + (r + 1) * cell), fill=col + (255,))
		for c, n in enumerate(names):
			ic = icons[n].resize((34, 34), Image.BILINEAR)
			img.alpha_composite(ic, (4 + c * cell + 5, 4 + r * cell + 5))
	img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
	img.save(path)


if __name__ == "__main__":
	out = sys.argv[1]
	os.makedirs(out, exist_ok=True)
	icons = make()
	for name, im in icons.items():
		im.save(os.path.join(out, name + ".png"), optimize=True)
	print("%d icons -> %s" % (len(icons), out))
	if "--preview" in sys.argv:
		preview(icons, sys.argv[sys.argv.index("--preview") + 1])
