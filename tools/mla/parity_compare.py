#!/usr/bin/env python3
"""Visual parity: compare OSD-only screenshots (mode=osd) of the reference skin vs MLA.

usage: parity_compare.py <ref dir> <mla dir> <out dir> [--masks masks.json]
For each NAME_osd.png present in both dirs it writes:
  out/NAME_diff.png   difference heat-map (red = changed pixels) over the reference
  out/NAME_pair.jpg   reference | MLA | diff, side by side
and prints changed-pixel % and the bounding boxes of changed regions.
masks.json: {"NAME": [[x, y, w, h], ...]} excludes known-dynamic regions (clock, signal...).
"""
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw

THRESH = 24  # per-channel tolerance (scaler/antialias noise)


def regions(mask_img, step=16):
	"""Coarse bounding boxes of changed areas (grid flood)."""
	w, h = mask_img.size
	px = mask_img.load()
	cells = set()
	for y in range(0, h, step):
		for x in range(0, w, step):
			box = mask_img.crop((x, y, min(x + step, w), min(y + step, h)))
			if box.getbbox():
				cells.add((x // step, y // step))
	boxes, seen = [], set()
	for c in sorted(cells):
		if c in seen:
			continue
		stack, comp = [c], []
		while stack:
			cx, cy = stack.pop()
			if (cx, cy) in seen or (cx, cy) not in cells:
				continue
			seen.add((cx, cy))
			comp.append((cx, cy))
			stack += [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]
		xs = [a for a, _ in comp]
		ys = [b for _, b in comp]
		boxes.append([min(xs) * step, min(ys) * step, (max(xs) + 1) * step - min(xs) * step, (max(ys) + 1) * step - min(ys) * step])
	return boxes


def main():
	ref, mla, out = sys.argv[1:4]
	masks = {}
	if "--masks" in sys.argv:
		masks = json.load(open(sys.argv[sys.argv.index("--masks") + 1]))
	os.makedirs(out, exist_ok=True)
	summary = {}
	for f in sorted(os.listdir(ref)):
		if not f.endswith("_osd.png") or not os.path.exists(os.path.join(mla, f)):
			continue
		name = f[:-8]
		a = Image.open(os.path.join(ref, f)).convert("RGBA")
		b = Image.open(os.path.join(mla, f)).convert("RGBA")
		if a.size != b.size:
			summary[name] = {"error": f"size {a.size} vs {b.size}"}
			continue
		d = ImageChops.difference(a, b)
		r, g, bl, al = d.split()
		mx = ImageChops.lighter(ImageChops.lighter(r, g), ImageChops.lighter(bl, al))
		m = mx.point(lambda v: 255 if v > THRESH else 0)
		draw = ImageDraw.Draw(m)
		for x, y, w, h in masks.get(name, []):
			draw.rectangle([x, y, x + w, y + h], fill=0)
		changed = sum(1 for v in m.getdata() if v)
		pct = 100.0 * changed / (a.size[0] * a.size[1])
		boxes = regions(m) if changed else []
		heat = a.convert("RGB")
		red = Image.new("RGB", a.size, (255, 0, 0))
		heat.paste(red, (0, 0), m)
		heat.save(os.path.join(out, name + "_diff.png"))
		W, H = 640, 360
		pair = Image.new("RGB", (W * 3, H), "black")
		for i, im in enumerate([a.convert("RGB"), b.convert("RGB"), heat]):
			pair.paste(im.resize((W, H)), (i * W, 0))
		pair.save(os.path.join(out, name + "_pair.jpg"), quality=85)
		summary[name] = {"changed_pct": round(pct, 4), "changed_px": changed, "regions": boxes[:20]}
		print(f"{name:24} changed={pct:8.4f}%  regions={len(boxes)}  {boxes[:6]}")
	json.dump(summary, open(os.path.join(out, "parity.json"), "w"), indent=1)


if __name__ == "__main__":
	main()
