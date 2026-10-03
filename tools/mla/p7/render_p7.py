#!/usr/bin/env python3
"""Render the P7 mockups and dimension sheets from spec_p7.py with the skin's real font (LiberationSans).
usage: render_p7.py <fonts dir> <out dir>
Outputs per design × screen × posters on/off: <id>.png (clean) and <id>_dims.png (boxes + sizes), plus
text_fit.txt (every text measured with the real font: lines needed vs lines available)."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_p7 as S  # noqa: E402

FONTS, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
_fc = {}


def font(size):
	if size not in _fc:
		_fc[size] = ImageFont.truetype(os.path.join(FONTS, "LiberationSans-Regular.ttf"), size)
	return _fc[size]


def rgba(v):
	if isinstance(v, tuple):
		return v
	v = v.lstrip("#")
	return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), 255)


def tint(roles, theme_rgb):
	"""Theme roles for another base colour (same derivation as CineView's palette())."""
	if theme_rgb is None:
		return roles
	mix = lambda a, b, t: tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))
	base = theme_rgb
	r = dict(roles)
	r["primary"] = "#%02X%02X%02X" % base
	r["panel"] = "#%02X%02X%02X" % mix(base, (0, 0, 0), 0.18)
	r["panelAlt"] = "#%02X%02X%02X" % mix(base, (0, 0, 0), 0.34)
	p = mix(base, (0, 0, 0), 0.18)
	pa = mix(base, (0, 0, 0), 0.34)
	r["overlay"] = p + (210,)
	r["overlayStrong"] = pa + (171,)
	return r


def background():
	"""Neutral, generated 'video' frame (no broadcast content)."""
	im = Image.new("RGB", (S.W, S.H), (18, 20, 26))
	d = ImageDraw.Draw(im)
	for y in range(S.H):
		t = y / S.H
		d.line([(0, y), (S.W, y)], fill=(int(40 + 30 * (1 - t)), int(46 + 26 * (1 - t)), int(58 + 20 * (1 - t))))
	d.ellipse([1150, 120, 1750, 720], fill=(150, 120, 90))
	d.ellipse([300, 250, 900, 850], fill=(70, 90, 110))
	d.rectangle([0, 600, 1920, 1080], fill=(40, 44, 50))
	return im.filter(ImageFilter.GaussianBlur(60))


def wrap(text, f, width):
	lines = []
	for para in text.split("\n"):
		cur = ""
		for w in para.split(" "):
			t = (cur + " " + w).strip()
			if f.getlength(t) <= width:
				cur = t
			else:
				if cur:
					lines.append(cur)
				cur = w
		lines.append(cur)
	return lines


def poster(w, h):
	im = Image.new("RGB", (w, h))
	d = ImageDraw.Draw(im)
	for y in range(h):
		t = y / max(1, h - 1)
		d.line([(0, y), (w, y)], fill=(int(90 + 60 * t), int(60 + 30 * t), int(110 - 40 * t)))
	f = font(max(12, w // 9))
	d.text((w // 2, h // 2), "POSTER\n2:3", fill=(240, 240, 240), font=f, anchor="mm", align="center")
	return im


def draw(elements, roles, dims=False, fit=None, tag=""):
	im = background().convert("RGBA")
	ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
	d = ImageDraw.Draw(ov)
	for e in elements:
		x, y, w, h = e["x"], e["y"], e["w"], e["h"]
		k = e["kind"]
		if k == "band":
			for i in range(h):
				a = int(235 * min(1.0, (i / h) * 1.6))
				c = rgba(roles["overlayStrong"])[:3]
				d.line([(x, y + i), (x + w, y + i)], fill=c + (a,))
		elif k == "panel":
			d.rectangle([x, y, x + w - 1, y + h - 1], fill=rgba(roles[e["role"]]) if isinstance(roles[e["role"]], tuple) else rgba(roles[e["role"]])[:3] + (235,))
		elif k == "sep":
			d.rectangle([x, y, x + w - 1, y + h - 1], fill=rgba(roles["sep"]))
		elif k == "progress":
			d.rectangle([x, y, x + w - 1, y + h - 1], fill=(51, 51, 58, 255))
			d.rectangle([x, y, x + int(w * e.get("value", 0.5)) - 1, y + h - 1], fill=rgba(roles["accent"]))
	im = Image.alpha_composite(im, ov)
	d = ImageDraw.Draw(im)
	for e in elements:
		x, y, w, h = e["x"], e["y"], e["w"], e["h"]
		k = e["kind"]
		if k == "poster":
			im.paste(poster(w, h), (x, y))
			d.rectangle([x - 2, y - 2, x + w + 1, y + h + 1], outline=rgba(roles["frame"]), width=2)
		elif k == "picon":
			d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=(235, 235, 235, 255))
			d.text((x + w // 2, y + h // 2), "PICON", fill=(40, 40, 40), font=font(max(14, h // 4)), anchor="mm")
		elif k == "chip":
			d.rounded_rectangle([x, y, x + w, y + h], radius=5, outline=rgba(roles["muted"]), width=2)
			d.text((x + w // 2, y + h // 2), e["text"], fill=rgba(roles["text"]), font=font(h - 12), anchor="mm")
		elif k == "text":
			f = font(e["size"])
			lh = S.line_height(e["size"])
			lines = wrap(e["text"], f, w)
			avail = max(1, h // lh)
			if avail > 1 and h % lh:
				fit.append("WARNING %s %s: height %d is not a whole number of %d px lines" % (tag, e["id"], h, lh)) if fit is not None else None
			if fit is not None:
				widest = max(f.getlength(l) for l in lines)
				fit.append("%-10s %-22s %4dx%-4d font %2d: needs %d line(s), box holds %d%s" % (tag, e["id"], w, h, e["size"], len(lines), avail,
					"" if len(lines) <= avail else "  -> scrolls (RunningText)" if avail > 1 or "RunningText" in e.get("src", "") else "  -> CLIPPED"))
			col = rgba(roles[e["role"]])
			for i, l in enumerate(lines[:avail]):
				ty = y + i * lh + max(0, (h - lh * min(avail, len(lines))) // 2 if avail == 1 else 0)
				if e.get("align") == "right":
					d.text((x + w, ty), l, fill=col, font=f, anchor="ra")
				else:
					d.text((x, ty), l, fill=col, font=f)
	if dims:
		for e in elements:
			if e["kind"] in ("band",) or e["id"] in ("dim",):
				continue
			x, y, w, h = e["x"], e["y"], e["w"], e["h"]
			c = (0, 230, 255, 255) if e.get("status") != "verify" else (255, 120, 40, 255)
			d.rectangle([x, y, x + w - 1, y + h - 1], outline=c, width=1)
			lbl = "%s %dx%d @%d,%d" % (e["id"], w, h, x, y)
			tw = font(14).getlength(lbl)
			d.rectangle([x, y, x + tw + 6, y + 17], fill=(0, 0, 0, 200))
			d.text((x + 3, y + 1), lbl, fill=c, font=font(14))
	return im.convert("RGB")


fit = []
themes = {None: "navy", (0x38, 0x20, 0x4F): "purple"}
for key, des in S.DESIGNS.items():
	for sec in ("infobar", "secondinfobar"):
		el, off = des[sec]
		for on in (True, False):
			v = S.variant(el, off, on)
			if key == "details" and sec == "secondinfobar":
				v = v + S.variant(S.DETAILS_INFOBAR, S.DETAILS_INFOBAR_OFF, on)
			probs = S.check(v)
			assert not probs, (key, sec, on, probs)
			name = "%s_%s_%s" % (key, sec, "posters_on" if on else "posters_off")
			draw(v, S.ROLES, fit=fit, tag=name[:10]).save(os.path.join(OUT, name + ".png"))
			draw(v, S.ROLES, dims=True).save(os.path.join(OUT, name + "_dims.png"))
			if on:
				draw(v, tint(S.ROLES, (0x38, 0x20, 0x4F))).save(os.path.join(OUT, name + "_purple.png"))
open(os.path.join(OUT, "text_fit.txt"), "w").write("\n".join(fit) + "\n")
print("rendered", len(os.listdir(OUT)), "files;", sum(1 for l in fit if "CLIPPED" in l), "clipped text boxes")


# Element tables for the specification document (generated from the same data as the pictures).
md = []
for key, des in S.DESIGNS.items():
	for sec in ("infobar", "secondinfobar"):
		el, off = des[sec]
		md.append("\n### %s — %s\n" % (des["label"], "Main InfoBar" if sec == "infobar" else "SecondInfoBar"))
		md.append("| element | x,y | w×h | font | Enigma2 source / renderer | contract |")
		md.append("|---|---|---|---|---|---|")
		for e in el:
			if e["kind"] in ("sep",):
				continue
			md.append("| %s | %d,%d | %d×%d | %s | %s | %s |" % (e["id"], e["x"], e["y"], e["w"], e["h"], ("Regular;%d" % e["size"]) if "size" in e else "—", e.get("src", "—"), {"classic": "used by Classic, device ✔", "verify": "native 57b7a51 (source ✔, device ⚠)"}.get(e.get("status"), "—")))
		hide = ", ".join(off.get("hide", []))
		sh = ", ".join("%s %+d" % (k, v) for k, v in off.get("shift", {}).items())
		gr = ", ".join("%s +%d" % (k, v) for k, v in off.get("grow_left", {}).items())
		md.append("\n**Posters off:** hidden: %s. %s%s" % (hide, ("moved: " + sh + ". ") if sh else "", ("widened (to the left): " + gr + ".") if gr else ""))
open(os.path.join(OUT, "spec_tables.md"), "w").write("\n".join(md) + "\n")
