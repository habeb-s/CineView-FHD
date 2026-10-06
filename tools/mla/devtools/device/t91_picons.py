#!/usr/bin/env python3
"""t91 analysis: one picon per place under fast channel switching.
For every model the Picon widgets of the deployed InfoBar screen (build XML) give the picon places; each fast-zap
grab (<model>_zap_*.png) is cut at the union of those places (+ margin) and put on one sheet per model, with the grab
name, so a second picon / fallback logo drawn next to or over the real one is visible at once.  Also writes a sheet of
the channel-list grabs taken while the cursor runs (<model>_csfast_*.png).
usage: t91_picons.py <build root> <shots dir>"""
import os
import re
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import infoplate as IP  # noqa: E402

M = 24


def picon_box(skin, pack):
	p = os.path.join(skin, "layouts", "infobar", pack, "screens.openatv.xml")
	src = open(p, encoding="utf-8").read()
	m = re.search(r'<screen name="InfoBar"([^>]*)>(.*?)</screen>', src, re.S)
	boxes = []
	for t in IP.TAG.finditer(m.group(2)):
		a = IP.attrs(t.group(3))
		r = IP.rect(a)
		if r and a.get("render") == "Picon":
			boxes.append(r)
	if not boxes:
		return None, 0
	x0 = min(b[0] for b in boxes) - M
	y0 = min(b[1] for b in boxes) - M
	x1 = max(b[0] + b[2] for b in boxes) + M
	y1 = max(b[1] + b[3] for b in boxes) + M
	return (max(0, x0), max(0, y0), min(1920, x1), min(1080, y1)), len(boxes)


def main(build, shots):
	skin = os.path.join(build, "usr/share/enigma2/CineView_FHD_MLA")
	for m in ("classic", "details", "cinema", "modern", "minimal"):
		box, n = picon_box(skin, m)
		files = sorted(f for f in os.listdir(shots) if f.startswith(m + "_zap_") and f.endswith(".png"))
		if not box or not files:
			print(m, "no picon widgets / no grabs")
			continue
		cw, ch = box[2] - box[0], box[3] - box[1]
		k = min(1.0, 420.0 / cw)
		tw, th = int(cw * k), int(ch * k)
		cols = 5
		rows = (len(files) + cols - 1) // cols
		sheet = Image.new("RGB", (cols * (tw + 10) + 10, rows * (th + 34) + 10), (24, 26, 32))
		d = ImageDraw.Draw(sheet)
		for i, f in enumerate(files):
			im = Image.open(os.path.join(shots, f)).convert("RGB").crop(box).resize((tw, th))
			x, y = 10 + (i % cols) * (tw + 10), 10 + (i // cols) * (th + 34)
			sheet.paste(im, (x, y + 22))
			d.text((x, y + 4), f[len(m) + 1:-4], fill=(230, 230, 230))
		out = os.path.join(shots, "picons_%s.png" % m)
		sheet.save(out)
		print("%-8s %d picon widget(s) in the InfoBar, box %s, %d grabs -> %s" % (m, n, box, len(files), out))
		cs = sorted(f for f in os.listdir(shots) if f.startswith(m + "_csfast_") and f.endswith(".png"))
		if cs:
			s2 = Image.new("RGB", (2 * 970, 560), (24, 26, 32))
			for i, f in enumerate(cs[:2]):
				s2.paste(Image.open(os.path.join(shots, f)).convert("RGB").resize((960, 540)), (i * 970, 10))
			s2.save(os.path.join(shots, "csfast_%s.png" % m))


if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2])
