#!/usr/bin/env python3
"""CineView Modern — InfoBar pack (layouts/infobar/modern), generated from the Modern mockup geometry
(tools/mla/p10models/render_models.py modern_infobar, shown to the user for approval 2026-10-04 night).

The look (floating rounded card over a bottom scrim, pill chips) is NOT approved yet: this pack exists so the
user judges real receiver output instead of a drawing.  Classic stays the default; nothing selects Modern.

Contract (enigma2 57b7a51, verified in source; skin features verified on the receiver by t41 before use):
* cornerRadius="r" / "r;top" (skin.py parseRadius -> eWidget::setCornerRadius) on eLabel / Label / Pixmap;
* backgroundColor="c1,c2,vertical,1" = two-colour vertical gradient with alpha blending (parseGradient);
* <fonts> inside an included skin file are loaded (loadSingleSkinData) -> "CVModernBold" = LiberationSans-Bold
  (present in /usr/share/fonts on the receiver); missing glyphs (Arabic) come from the skin's Fallback font;
* every data widget is a proven Classic/Details widget (Picon, ChannelNumber, RunningText, Label + EventName /
  EventTime / ClockToText, Progress, VideoSize, ServiceInfo, FrontendInfo, CineViewMLAPosterX, CineViewMLAIMDb,
  CineViewMLAShowIf) — live values only, nothing fixed.
Posters ON / OFF: every widget whose x depends on the poster has an ON and an OFF variant (CineViewMLAShowIf
<key>,True[,Invert]); OFF = no poster, no placeholder, the content starts at the card's left padding.
usage (build.py): generate(skin_dir) -> [pack dir]"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "p7"))
import gen_details as G  # noqa: E402

KEY = "config.plugins.cineviewmla.poster_infobar"
SRC_NOW, SRC_NEXT, SVC = "session.Event_Now", "session.Event_Next", "session.CurrentService"
BOLD = "CVModernBold"
# geometry (mockup modern_infobar)
CARD = (60, 790, 1800, 250)
SCRIM = (0, 700, 1920, 380)
POSTER = (84, 806, 146, 218)
X_ON, X_OFF = 254, 84
RIGHT = 1836
PILL_BG = "#00344660"  # mockup pill colour (52,70,94), opaque
CHIP_Y, CHIP_H = 818, 34
# chips right to left: (id, width)
CHIPS = (("db", 120), ("snr", 130), ("ar", 74), ("res", 160), ("hd", 70))
CHIP_GAP = 10


def E(x, y, w, h):
	return {"x": x, "y": y, "w": w, "h": h}


def show(key, inv):
	return '\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s</convert>' % (key, inv)


def chips():
	"""Live technical pills, right-aligned on the card's first row.  Each pill is ONE widget with its own rounded
	background, hidden as a whole when its condition is false (HD/UHD/SD, 16:9)."""
	out, cx, pos = [], RIGHT, {}
	for cid, w in CHIPS:
		cx -= w
		pos[cid] = E(cx, CHIP_Y, w, CHIP_H)
		cx -= CHIP_GAP
	pill = ' backgroundColor="%s" cornerRadius="%d" halign="center" valign="center" font="Regular;20" foregroundColor="grey" zPosition="15"' % (PILL_BG, CHIP_H // 2)
	for typ, text in (("IsSD", "SD"), ("IsHD", "HD"), ("Is4K", "UHD")):
		out.append('\t\t<widget source="%s" render="Label" %s%s>\n\t\t\t<convert type="ServiceInfo">%s</convert>\n\t\t\t<convert type="CineViewMLAShowIf">always,True,bool,text=%s</convert>\n\t\t</widget>' % (SVC, G.pos(pos["hd"]), pill, typ, text))
	out.append('\t\t<widget source="%s" render="Label" %s%s>\n\t\t\t<convert type="ServiceInfo">IsWidescreen</convert>\n\t\t\t<convert type="CineViewMLAShowIf">always,True,bool,text=16:9</convert>\n\t\t</widget>' % (SVC, G.pos(pos["ar"]), pill))
	out.append('\t\t<widget source="%s" render="VideoSize" %s%s />' % (SVC, G.pos(pos["res"]), pill))
	# SNR "%" and dB: rounded background (eLabel) + caption + live value
	for cid, conv, cap in (("snr", "SNR", "SNR"), ("db", "SNRdB", None)):
		p = pos[cid]
		out.append('\t\t<eLabel %s backgroundColor="%s" cornerRadius="%d" zPosition="-1" />' % (G.pos(p), PILL_BG, CHIP_H // 2))
		if cap:
			out.append('\t\t<eLabel text="%s" position="%d,%d" size="52,%d" font="Regular;20" foregroundColor="grey" halign="right" valign="center" transparent="1" zPosition="20" />' % (cap, p["x"] + 6, p["y"], p["h"]))
			out.append(G.label("session.FrontendStatus", E(p["x"] + 62, p["y"], p["w"] - 68, p["h"]), [("FrontendInfo", conv)], 20, "foreground", ' valign="center"'))
		else:
			out.append(G.label("session.FrontendStatus", p, [("FrontendInfo", conv)], 20, "foreground", ' halign="center" valign="center"'))
	return out, cx


def poster_slot():
	"""Rounded poster with the CineView default image under it (shown while no reliable poster exists); both follow
	the poster switch.  No square frame (Modern has none)."""
	x, y, w, h = POSTER
	gate = '<convert type="ConfigEntryTest">%s,False,Invert</convert><convert type="ConditionalShowHide" />' % KEY
	return ['\t\t<widget source="%s" render="Pixmap" pixmap="mla_assets/poster_default_%dx%d.png" position="%d,%d" size="%d,%d" cornerRadius="16" zPosition="19">%s</widget>' % (SVC, w, h, x, y, w, h, gate),
		'\t\t<widget source="%s" render="CineViewMLAPosterX" position="%d,%d" size="%d,%d" cornerRadius="16" zPosition="20" toggle="%s" />' % (SRC_NOW, x, y, w, h, KEY)]


def row_widgets(x0, inv, name_right):
	"""Everything whose x depends on the poster: picon, number, name, title, progress, next line."""
	s = show(KEY, inv)
	out = ['\t\t<widget source="%s" render="Picon" mode="infobar" scale="aspect" position="%d,812" size="130,64" alphatest="blend" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Reference</convert>%s\n\t\t</widget>' % (SVC, x0, s),
		'\t\t<widget source="%s" render="ChannelNumber" position="%d,816" size="80,40" transparent="1" zPosition="20" foregroundColor="foreground" font="%s;28"><convert type="CineViewMLAShowIf">%s,True%s</convert></widget>' % (SVC, x0 + 146, BOLD, KEY, inv),
		'\t\t<widget source="%s" render="RunningText" position="%d,816" size="%d,40" transparent="1" zPosition="20" foregroundColor="foreground" font="%s;28" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">NameOnly</convert>%s\n\t\t</widget>' % (SVC, x0 + 230, name_right - (x0 + 230), BOLD, G.RUN_OPTS, s)]
	tw = RIGHT - 250 - x0
	out.append('\t\t<widget source="%s" render="Progress" position="%d,950" size="%d,6" pixmap="infobar/pbar.png" backgroundColor="%s" cornerRadius="3" zPosition="20">\n\t\t\t<convert type="EventTime">Progress</convert>%s\n\t\t</widget>' % (SRC_NOW, x0, RIGHT - x0, PILL_BG, s))
	out.append('\t\t<widget source="%s" render="Label" position="%d,980" size="80,34" transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;24">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=NEXT</convert>\n\t\t</widget>' % (SRC_NEXT, x0, KEY, inv))
	out.append('\t\t<widget source="%s" render="Label" position="%d,978" size="84,34" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;26">\n\t\t\t<convert type="EventTime">StartTime</convert>\n\t\t\t<convert type="ClockToText">Format:%%H:%%M</convert>%s\n\t\t</widget>' % (SRC_NEXT, x0 + 86, s))
	out.append('\t\t<widget source="%s" render="RunningText" position="%d,978" size="%d,34" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;26" noWrap="1" options="%s">\n\t\t\t<convert type="EventName">Name</convert>%s\n\t\t</widget>' % (SRC_NEXT, x0 + 180, 1180 - (x0 + 180), G.H_OPTS, s))
	return out, tw


def title(x0, inv):
	"""Now title, bold 40, one line: ltr swims horizontally (start first), rtl right-aligned (pages)."""
	tw = RIGHT - 260 - x0
	e = {"x": x0, "y": 884, "w": tw, "h": 52}
	out = G.text_variants(SRC_NOW, [("EventName", "Name")], e, None, 40, "foreground", G.T_OPTS, "always")
	# text_variants gives ltr/rtl variants keyed "always"; add the poster switch and the bold face
	res = []
	for w in out:
		w = w.replace("CineViewMLAShowIf\">always,True,", "CineViewMLAShowIf\">%s,True%s," % (KEY, inv)).replace('font="Regular;40"', 'font="%s;40"' % BOLD)
		res.append(w)
	return res


def infobar(skin):
	x = ['\t\t<eLabel position="%d,%d" size="%d,%d" backgroundColor="#ff000000,#37000000,vertical,1" zPosition="-3" />' % SCRIM,
		'\t\t<eLabel position="%d,%d" size="%d,%d" backgroundColor="steThemeCard" cornerRadius="28" zPosition="-2" />' % CARD]
	cx, left_of_chips = chips()
	x += cx
	x += poster_slot()
	for x0, inv in ((X_ON, ""), (X_OFF, ",Invert")):
		rw, _ = row_widgets(x0, inv, left_of_chips - 16)
		x += rw
		x += title(x0, inv)
	# times pill (right of the title) and meta (genre / IMDb only when the identity is reliable)
	tp = E(RIGHT - 240, 890, 240, 38)
	x.append('\t\t<eLabel %s backgroundColor="%s" cornerRadius="19" zPosition="-1" />' % (G.pos(tp), PILL_BG))
	x += G.times(SRC_NOW, E(tp["x"] + 8, tp["y"] + 3, tp["w"] - 28, 32), 24, "foreground")
	x.append(G.label(SRC_NOW, E(1196, 980, 380, 34), [("EventName", "Genre")], 24, "secondFG", ' halign="right" noWrap="1"'))
	x.append(G.label(SRC_NOW, E(1586, 980, 110, 34), [("CineViewMLAIMDb", "Plain,hide")], 24, "secondFG", ' halign="right"'))
	x.append(G.label(SRC_NOW, E(1706, 982, 130, 34), [("CineViewMLAIMDb", "Stars,hide")], 22, "secondFG", ' halign="right"'))
	return G.screen("InfoBar", "InfoBar", [l for l in x if l])


def generate(skin):
	from PIL import Image
	# default poster image at the Modern slot size (same CineView default image as Details)
	w, h = POSTER[2], POSTER[3]
	dp = os.path.join(skin, G.FRAME_DIR, "poster_default_%dx%d.png" % (w, h))
	if not os.path.isfile(dp):
		Image.open(os.path.join(skin, G.FRAME_DIR, "poster_default.jpg")).convert("RGB").resize((w, h), Image.LANCZOS).save(dp)
	d = os.path.join(skin, "layouts", "infobar", "modern")
	os.makedirs(d, exist_ok=True)
	parts = [infobar(skin)]
	radio = G._classic_screen(skin, "infobar", "RadioInfoBar")
	if radio:
		parts.append(radio.strip("\n"))
	fonts = '\t<fonts>\n\t\t<font name="%s" filename="LiberationSans-Bold.ttf" scale="100" />\n\t</fonts>' % BOLD
	xml = '<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Modern (InfoBar) — generated by tools/mla/p10models/gen_modern.py. Look NOT approved yet. Do not edit by hand. -->\n<skin>\n%s\n%s\n</skin>\n' % (fonts, "\n".join("\t" + p.strip() if not p.startswith("\t") else p for p in parts))
	p = os.path.join(d, "screens.openatv.xml")
	open(p, "w", encoding="utf-8").write(xml)
	json.dump({"schema": 1, "id": "modern", "section": "infobar", "name": "CineView Modern", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "tools/mla/p10models (Modern model mockup, look pending approval)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}}, "provides_screens": ["InfoBar"] + (["RadioInfoBar"] if radio else []),
		"options": [], "preview": "preview.png"}, open(os.path.join(d, "manifest.json"), "w"), indent=1)
	import xml.etree.ElementTree as ET
	r = ET.parse(p).getroot()
	for el in r.find("screen").iter():
		ps, ss = el.get("position"), el.get("size")
		if ps and ss and not ps.startswith(("c", "e")):
			px, py = (int(v) for v in ps.split(","))
			sw, sh = (int(v) for v in ss.split(","))
			assert 0 <= px and px + sw <= 1920 and 0 <= py and py + sh <= 1080, el.attrib
	return [d]


if __name__ == "__main__":
	print(generate(sys.argv[1]))
