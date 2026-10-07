#!/usr/bin/env python3
"""Real preview pictures for CineView Designs (user 2026-10-07) from receiver grabs (devtools/device/t101.sh).

usage: compose_previews.py <previews_src> <repo>/mla/previews
  <src>/posters/<model>/{on,off}/<section>.png  -> posters/<section>/<layout>.png  (720x405, Posters On | Posters Off)
  <src>/themes/<theme>.png                      -> themes/<theme>.png             (720x405, the real screen)
  <src>/posters/<model>/on/<section>.png        -> layouts/<section>/<layout>.png (720x405, the design's real preview)
  <src>/extra/<section>/<layout>.png            -> layouts/<section>/<layout>.png (layouts outside the five models)
Only grabs that exist are used; a missing pair leaves that layout without a picture (CineView Designs then shows its
Info Card)."""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

MODELS = {
	# Classic PVR keeps the native live picture without a poster area (approved 2026-10-06 19:54): no On/Off picture
	"classic": {"infobar": "classic", "secondinfobar": "classic", "channelselection": "classic", "epg": "classic", "eventview": ["classic-lines", "classic"]},
	"details": {"infobar": "details", "secondinfobar": "details", "channelselection": "posterlist", "epg": "graphicalplus", "pvr": "cover", "eventview": "detailscard"},
	"cinema": {"infobar": "cinema", "secondinfobar": "cinema", "channelselection": "videofirst", "pvr": "cinema", "eventview": "feature"},
	"modern": {s: "modern" for s in ("infobar", "secondinfobar", "channelselection", "epg", "pvr", "eventview")},
	"minimal": {s: "minimal" for s in ("infobar", "secondinfobar", "channelselection", "epg", "pvr", "eventview")},
}
LABEL = {"infobar": "Main InfoBar", "secondinfobar": "Second InfoBar", "channelselection": "Channel Selection", "epg": "EPG", "pvr": "PVR / Movies", "eventview": "Event View"}
BG, GOLD, TXT, MUT = (10, 20, 34), (249, 199, 49), (240, 240, 240), (170, 182, 198)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(p, s):
	return ImageFont.truetype(p, s)


def pair(on, off, sec, model):
	a = Image.open(on).convert("RGB")
	b = Image.open(off).convert("RGB")
	im = Image.new("RGB", (720, 405), BG)
	d = ImageDraw.Draw(im)
	head = "%s - %s" % (LABEL[sec], model.capitalize())
	if sec == "infobar":  # the bar is at the bottom of the screen: two wide crops, one above the other
		box = (0, 653, 1920, 1080)
		for i, (src, lab) in enumerate(((a, "Posters On"), (b, "Posters Off"))):
			y = 6 + i * 200
			d.text((10, y), lab, font=font(FB, 20), fill=GOLD)
			if i == 0:
				w = d.textlength(head, font=font(FR, 18))
				d.text((710 - w, y + 2), head, font=font(FR, 18), fill=MUT)
			im.paste(src.crop(box).resize((720, 160), Image.LANCZOS), (0, y + 30))
	else:  # full-screen sections: side by side
		d.text((10, 10), head, font=font(FB, 22), fill=TXT)
		for i, (src, lab) in enumerate(((a, "Posters On"), (b, "Posters Off"))):
			x = 6 + i * 357
			d.text((x + 4, 56), lab, font=font(FB, 20), fill=GOLD)
			im.paste(src.resize((351, 197), Image.LANCZOS), (x, 88))
		d.text((10, 310), "Posters off: the other elements move to use the space.", font=font(FR, 19), fill=MUT)
	return im


def main(src, out):
	n = 0
	for model, secs in MODELS.items():
		for sec, lids in secs.items():
			on = os.path.join(src, "posters", model, "on", sec + ".png")
			off = os.path.join(src, "posters", model, "off", sec + ".png")
			if not (os.path.isfile(on) and os.path.isfile(off)):
				print("missing", model, sec)
				continue
			im = pair(on, off, sec, model)
			for lid in (lids if isinstance(lids, list) else [lids]):
				os.makedirs(os.path.join(out, "posters", sec), exist_ok=True)
				im.save(os.path.join(out, "posters", sec, lid + ".png"), optimize=True)
				n += 1
	# the design previews themselves: the posters-ON grab of every model (classic PVR included), plus extra layouts
	PVR_CLASSIC = {"pvr": "classic"}
	L = 0
	for model, secs in MODELS.items():
		for sec, lids in list(secs.items()) + (list(PVR_CLASSIC.items()) if model == "classic" else []):
			on = os.path.join(src, "posters", model, "on", sec + ".png")
			if not os.path.isfile(on):
				continue
			im = Image.open(on).convert("RGB").resize((720, 405), Image.LANCZOS)
			for lid in (lids if isinstance(lids, list) else [lids]):
				os.makedirs(os.path.join(out, "layouts", sec), exist_ok=True)
				im.save(os.path.join(out, "layouts", sec, lid + ".png"), optimize=True)
				L += 1
	for sec in sorted(os.listdir(os.path.join(src, "extra"))) if os.path.isdir(os.path.join(src, "extra")) else []:
		for f in sorted(os.listdir(os.path.join(src, "extra", sec))):
			os.makedirs(os.path.join(out, "layouts", sec), exist_ok=True)
			Image.open(os.path.join(src, "extra", sec, f)).convert("RGB").resize((720, 405), Image.LANCZOS).save(os.path.join(out, "layouts", sec, f), optimize=True)
			L += 1
	print("design previews: %d" % L)
	t = 0
	for f in sorted(os.listdir(os.path.join(src, "themes"))) if os.path.isdir(os.path.join(src, "themes")) else []:
		if f.endswith(".png"):
			os.makedirs(os.path.join(out, "themes"), exist_ok=True)
			Image.open(os.path.join(src, "themes", f)).convert("RGB").resize((720, 405), Image.LANCZOS).save(os.path.join(out, "themes", f), optimize=True)
			t += 1
	print("posters pictures: %d, theme pictures: %d" % (n, t))


if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2])
