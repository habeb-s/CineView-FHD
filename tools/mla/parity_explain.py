#!/usr/bin/env python3
"""M7 visual parity with PROVEN dynamic regions (no automatic acceptance).

usage: parity_explain.py <ref dir> <mla dir> <mla repeat dir> <skin dir> <out dir>

For every NAME_osd.png present in ref, mla and mla-repeat:
  D = pixels that differ between the reference skin and MLA (same channel/event, |delta| > THRESH)
  S = pixels that differ between two MLA captures of the same screen taken minutes apart
      (same skin, same files => any change is live data: clock, signal, CPU, bitrate, ECM...)
  Each connected region of D is
     DYNAMIC (observed)  if >= 95 % of its pixels lie inside S dilated by 6 px, and it is mapped
                         to the skin element(s) covering it (source / converter printed as the cause);
     UNEXPLAINED         otherwise  (=> a real design difference, must be reviewed / fixed).
  The exclusion mask of a screen = rectangles of the skin elements that cover DYNAMIC regions.
  The masked diff is recomputed; PASS only if no pixel remains.
Writes out/NAME_review.jpg (reference | MLA, then the diff with regions: yellow = dynamic,
red = unexplained), out/masks.json and out/explain.json.
"""
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw, ImageFilter

THRESH = 24
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from parity_compare import regions  # noqa: E402

# capture name -> candidate skin screens (first match wins per element lookup)
CAPMAP = {
	"01_infobar": ["InfoBar"],
	"02_secondinfobar": ["SecondInfoBar", "InfoBar"],
	"03_channelselection": ["ChannelSelection"],
	"04_epg": ["GraphicalEPG", "EPGSelection", "EPGSelectionMulti", "QuickEPG", "GraphMultiEPG", "EPGverticalPIG", "EPGvertical"],
	"05_eventview": ["EventView", "InfoBarEventView", "EventViewSimple"],
	"06_menu": ["Menu", "menu_mainmenu", "MenuHorizontal"],
	"07_setupmenu": ["Menu", "menu_setup", "MenuHorizontal"],
	"08_plugins": ["PluginBrowser"],
	"09_blue": ["QuickMenu", "ChoiceBox", "PluginBrowser"],
	"10_osdsettings": ["Setup"],
	"11_hotkey": ["HotkeySetup"],
	"12_language": ["LanguageSelection", "LocaleSelection"],
	"13_about": ["About", "Information", "AboutInformation", "ImageInformation"],
	"14_multiboot": ["MultiBootSelection", "MultiBootSelector", "MultiBoot"],
	"15_timers": ["TimerEditList", "RecordTimerOverview", "TimerOverview"],
	"16_audio": ["AudioSelection"],
	"17_subtitle": ["SubtitleSelection", "AudioSelection"],
	"18_usagegui": ["Menu", "MenuHorizontal"],
}


def mask_of(a, b):
	d = ImageChops.difference(a, b)
	r, g, bl, al = d.split()
	mx = ImageChops.lighter(ImageChops.lighter(r, g), ImageChops.lighter(bl, al))
	return mx.point(lambda v: 255 if v > THRESH else 0)


def load_screens(skin):
	files = sorted(glob.glob(os.path.join(skin, "active", "*.xml")) + glob.glob(os.path.join(skin, "core", "*.xml")))
	screens = {}
	for f in files:
		try:
			root = ET.parse(f).getroot()
		except ET.ParseError:
			continue
		for s in root.iter("screen"):
			if s.get("name"):
				screens[s.get("name")] = s  # later file wins, like the skin loader (sections after core)
	return screens


def rect(el, off=(0, 0)):
	try:
		x, y = [int(v) for v in el.get("position", "").split(",")]
		w, h = [int(v) for v in el.get("size", "").split(",")]
		return (x + off[0], y + off[1], w, h)
	except ValueError:
		return None


def describe(el):
	conv = [c.get("type", "") + ("(" + (c.text or "").strip() + ")" if (c.text or "").strip() else "") for c in el.findall("convert")]
	if el.tag == "widget":
		what = "widget " + (("source=" + el.get("source")) if el.get("source") else ("name=" + el.get("name", "?")))
		if el.get("render"):
			what += " render=" + el.get("render")
	else:
		what = el.tag + (" text=%r" % el.get("text") if el.get("text") else "")
	return what + (" convert=" + ">".join(conv) if conv else "")


def elements_over(screens, names, box):
	bx, by, bw, bh = box
	hits = []
	for n in names:
		s = screens.get(n)
		if s is None:
			continue
		off = (0, 0)
		r = rect(s)
		if r and s.get("position", "").replace(",", "").isdigit():
			off = (r[0], r[1])
		for el in s:
			if el.tag not in ("widget", "eLabel", "ePixmap"):
				continue
			r = rect(el, off)
			if not r:
				continue
			x, y, w, h = r
			if x < bx + bw and bx < x + w and y < by + bh and by < y + h and (el.tag == "widget" or el.get("text")):
				hits.append((n, r, describe(el)))
		if hits:
			return hits
	return hits


def main(ref, mla, rep, skin, out):
	os.makedirs(out, exist_ok=True)
	screens = load_screens(skin)
	masks, report = {}, {}
	for f in sorted(os.listdir(ref)):
		if not f.endswith("_osd.png") or not (os.path.exists(os.path.join(mla, f)) and os.path.exists(os.path.join(rep, f))):
			continue
		name = f[:-8]
		a = Image.open(os.path.join(ref, f)).convert("RGBA")
		b = Image.open(os.path.join(mla, f)).convert("RGBA")
		c = Image.open(os.path.join(rep, f)).convert("RGBA")
		D = mask_of(a, b)
		S = mask_of(b, c).filter(ImageFilter.MaxFilter(13))
		total = a.size[0] * a.size[1]
		dpx = sum(1 for v in D.getdata() if v)
		entry = {"diff_pct": round(100.0 * dpx / total, 4), "regions": []}
		mrects = []
		for box in (regions(D) if dpx else []):
			x, y, w, h = box
			dr = D.crop((x, y, x + w, y + h))
			sr = S.crop((x, y, x + w, y + h))
			inside = sum(1 for p, q in zip(dr.getdata(), sr.getdata()) if p and q)
			n = sum(1 for p in dr.getdata() if p) or 1
			els = elements_over(screens, CAPMAP.get(name, []), box)
			dyn = inside / n >= 0.95
			entry["regions"].append({"box": box, "class": "DYNAMIC" if dyn else "UNEXPLAINED", "observed_change": round(inside / n, 3), "elements": [e[2] + " @" + ",".join(map(str, e[1])) + " [" + e[0] + "]" for e in els][:4]})
			if dyn:
				for e in els:
					if "source=" in e[2] and e[1] not in mrects:
						mrects.append(e[1])
				if not els:
					mrects.append(tuple(box))  # observed dynamic but no element mapped: masked by region, flagged below
		# residual after masking the proven-dynamic element rectangles
		R = D.copy()
		dr = ImageDraw.Draw(R)
		for x, y, w, h in mrects:
			dr.rectangle([x, y, x + w - 1, y + h - 1], fill=0)
		res = sum(1 for v in R.getdata() if v)
		entry["mask"] = [list(m) for m in mrects]
		entry["residual_px"] = res
		entry["unexplained"] = sum(1 for r in entry["regions"] if r["class"] == "UNEXPLAINED")
		entry["unmapped_dynamic"] = sum(1 for r in entry["regions"] if r["class"] == "DYNAMIC" and not r["elements"])
		entry["verdict"] = "PASS" if res == 0 and entry["unexplained"] == 0 else "REVIEW"
		masks[name] = entry["mask"]
		report[name] = entry
		# review sheet: ref | mla (top), diff overlay (bottom-left), legend (bottom-right)
		W, H = 960, 540
		sheet = Image.new("RGB", (W * 2, H * 2 + 40), (18, 18, 18))
		full_a = os.path.join(ref, name + "_all.png")
		full_b = os.path.join(mla, name + "_all.png")
		va = Image.open(full_a).convert("RGB") if os.path.exists(full_a) else a.convert("RGB")
		vb = Image.open(full_b).convert("RGB") if os.path.exists(full_b) else b.convert("RGB")
		sheet.paste(va.resize((W, H)), (0, 40))
		sheet.paste(vb.resize((W, H)), (W, 40))
		heat = a.convert("RGB")
		heat.paste(Image.new("RGB", a.size, (255, 0, 0)), (0, 0), D)
		hd = ImageDraw.Draw(heat)
		for r in entry["regions"]:
			x, y, w, h = r["box"]
			hd.rectangle([x, y, x + w, y + h], outline=(255, 220, 0) if r["class"] == "DYNAMIC" else (255, 0, 0), width=4)
		sheet.paste(heat.resize((W, H)), (0, H + 40))
		d = ImageDraw.Draw(sheet)
		d.text((10, 12), "REFERENCE  CineView_FHD (approved, Slot 3 = golden 0926)", fill=(255, 255, 0))
		d.text((W + 10, 12), "MLA  CineView_FHD_MLA classic/navy", fill=(255, 255, 0))
		ty = H + 50
		d.text((W + 10, ty), "%s   diff %.4f%%   %s   residual after mask: %d px" % (name, entry["diff_pct"], entry["verdict"], res), fill=(255, 255, 255))
		for r in entry["regions"][:14]:
			ty += 34
			d.text((W + 10, ty), "%s %s seen-changing=%.2f" % (r["class"], r["box"], r["observed_change"]), fill=(255, 220, 0) if r["class"] == "DYNAMIC" else (255, 80, 80))
			d.text((W + 24, ty + 15), (r["elements"][0] if r["elements"] else "no skin element mapped")[:110], fill=(190, 190, 190))
		sheet.save(os.path.join(out, name + "_review.jpg"), quality=82)
		print("%-22s diff=%7.4f%%  regions=%2d  unexplained=%d  residual=%d  %s" % (name, entry["diff_pct"], len(entry["regions"]), entry["unexplained"], res, entry["verdict"]))
		for r in entry["regions"]:
			print("     %-11s %-22s seen=%.2f  %s" % (r["class"], r["box"], r["observed_change"], " | ".join(r["elements"][:2]) or "-"))
	json.dump(masks, open(os.path.join(out, "masks.json"), "w"), indent=1)
	json.dump(report, open(os.path.join(out, "explain.json"), "w"), indent=1)


if __name__ == "__main__":
	if len(sys.argv) != 6:
		print(__doc__)
		sys.exit(2)
	main(*sys.argv[1:])
