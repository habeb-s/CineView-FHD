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
import emc_common as EMC  # noqa: E402

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


SIB_KEY = "config.plugins.cineviewmla.poster_secondinfobar"
SIB_CARD_Y, SIB_CARD_W, SIB_CARD_H = 540, 890, 480
SIB_POSTER = (200, 300)


def _gate(w, key, inv):
	"""Append the poster switch (ON / OFF variant) to a widget that has no CineViewMLAShowIf yet."""
	return w.replace("</widget>", "\t<convert type=\"CineViewMLAShowIf\">%s,True%s</convert>\n\t\t</widget>" % (key, inv))


def sib_card(skin, i):
	"""One NOW (i=0) / NEXT (i=1) card of the Modern SecondInfoBar (mockup modern_sib)."""
	src = SRC_NOW if i == 0 else SRC_NEXT
	cx = 60 + i * 910
	x = ['\t\t<eLabel position="%d,%d" size="%d,%d" backgroundColor="steThemeCard" cornerRadius="28" zPosition="-2" />' % (cx, SIB_CARD_Y, SIB_CARD_W, SIB_CARD_H)]
	# poster (ON): rounded, CineView default image under it; NEXT uses the poster engine's "nexts" index
	pw, ph = SIB_POSTER
	px, py = cx + 28, 568
	G.poster(skin, src, {"x": px, "y": py, "w": pw, "h": ph}, SIB_KEY)  # creates the default image file
	gate = '<convert type="ConfigEntryTest">%s,False,Invert</convert><convert type="ConditionalShowHide" />' % SIB_KEY
	x.append('\t\t<widget source="%s" render="Pixmap" pixmap="mla_assets/poster_default_%dx%d.png" position="%d,%d" size="%d,%d" cornerRadius="18" zPosition="19">%s</widget>' % (SVC, pw, ph, px, py, pw, ph, gate))
	x.append('\t\t<widget source="%s" render="CineViewMLAPosterX" position="%d,%d" size="%d,%d" cornerRadius="18" zPosition="20" nexts="%d" toggle="%s" />' % (SRC_NOW, px, py, pw, ph, i, SIB_KEY))
	for tx, inv in ((cx + 252, ""), (cx + 28, ",Invert")):
		tw = cx + SIB_CARD_W - 28 - tx
		# NOW / NEXT accent pill (only when the event exists: text comes from the event via ShowIf text=)
		x.append('\t\t<widget source="%s" render="Label" position="%d,570" size="96,34" backgroundColor="secondFG" cornerRadius="17" halign="center" valign="center" foregroundColor="#001a1300" font="%s;20" zPosition="20">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=%s</convert>\n\t\t</widget>' % (src, tx, BOLD, SIB_KEY, inv, "NOW" if i == 0 else "NEXT"))
		# times beside the pill: "HH:MM – HH:MM"
		x += [_gate(w, SIB_KEY, inv) for w in G.times(src, E(tx + 112, 572, 160, 32), 24, "secondFG")]
		# duration (minutes), right side of the pill row
		x.append(_gate(G.label(src, E(cx + SIB_CARD_W - 28 - 160, 572, 160, 32), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 22, "grey", ' halign="right"'), SIB_KEY, inv))
		# title: bold 36, up to 2 lines (rtl/ltr variants)
		for w in G.text_variants(src, [("EventName", "Name")], E(tx, 616, tw, 90), None, 36, "foreground", G.T_OPTS, "always"):
			x.append(w.replace("CineViewMLAShowIf\">always,True,", "CineViewMLAShowIf\">%s,True%s," % (SIB_KEY, inv)).replace('font="Regular;36"', 'font="%s;36"' % BOLD))
		# genre / IMDb line (empty when the EPG has no genre; IMDb only when the identity is reliable)
		x.append(_gate(G.label(src, E(tx, 712, tw - 240, 32), [("EventName", "Genre")], 23, "secondFG", ' noWrap="1"'), SIB_KEY, inv))
		x.append(_gate(G.label(src, E(tx + tw - 230, 712, 120, 32), [("CineViewMLAIMDb", "Plain,hide")], 23, "foreground", ' halign="right"'), SIB_KEY, inv))
		x.append(_gate(G.label(src, E(tx + tw - 100, 714, 100, 32), [("CineViewMLAIMDb", "Stars,hide")], 21, "secondFG", ' halign="right"'), SIB_KEY, inv))
		if i == 0:
			x.append('\t\t<widget source="%s" render="Progress" position="%d,750" size="%d,6" pixmap="infobar/pbar.png" backgroundColor="%s" cornerRadius="3" zPosition="20">\n\t\t\t<convert type="EventTime">Progress</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s</convert>\n\t\t</widget>' % (src, tx, tw, PILL_BG, SIB_KEY, inv))
		# description: ON beside the poster (to the card bottom), OFF the full card width
		dy = 772
		for w in G.text_variants(src, [("EventName", "FullDescription")], E(tx, dy, tw, 1000 - dy), None, 23, "grey", G.D_OPTS, "always"):
			x.append(w.replace("CineViewMLAShowIf\">always,True,", "CineViewMLAShowIf\">%s,True%s," % (SIB_KEY, inv)))
	return x


def sib_header():
	"""Thin service line above the cards: picon, number, name (left); live chips (right) — same pills as the InfoBar."""
	x = ['\t\t<eLabel position="0,420" size="1920,660" backgroundColor="#ff000000,#2a000000,vertical,1" zPosition="-3" />']
	x.append('\t\t<widget source="%s" render="Picon" mode="infobar" scale="aspect" position="60,468" size="110,56" alphatest="blend" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % SVC)
	x.append('\t\t<widget source="%s" render="ChannelNumber" position="186,474" size="80,44" transparent="1" zPosition="20" foregroundColor="foreground" font="%s;30" />' % (SVC, BOLD))
	x.append('\t\t<widget source="%s" render="RunningText" position="270,474" size="700,44" transparent="1" zPosition="20" foregroundColor="foreground" font="%s;30" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">NameOnly</convert>\n\t\t</widget>' % (SVC, BOLD, G.RUN_OPTS))
	ch, _ = chips()
	# the InfoBar chip row sits at y 818; move it to the SecondInfoBar header row (y 478)
	x += [c.replace(',%d" size=' % CHIP_Y, ',478" size=') for c in ch]
	return x


def secondinfobar(skin):
	body = sib_header()
	for i in (0, 1):
		body += sib_card(skin, i)
	body = [l for l in body if l]
	return [G.screen("SecondInfoBar", "Second Infobar", body), G.screen("SecondInfoBarSimple", "Second Infobar", body)]


CS_KEY = "config.plugins.cineviewmla.poster_channelselection"
CS_SRC = "ServiceEvent"
CS_LIST = (76, 140, 808, 840)  # 14 rows x 60 inside the left card (60,60 840x960)
CS_ROW = 60


def _cs_selection(skin):
	"""Rounded, theme-neutral selection plate for the native service list (eListbox selectionPixmap: blitted with
	alpha blending on the selected row of a transparent list, listboxservice.cpp paint())."""
	from PIL import Image, ImageDraw
	w, h = CS_LIST[2], CS_ROW
	name = "modern_cs_sel_%dx%d.png" % (w, h)
	path = os.path.join(skin, G.FRAME_DIR, name)
	if not os.path.isfile(path):
		im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
		ImageDraw.Draw(im).rounded_rectangle([0, 2, w - 1, h - 3], 14, fill=(255, 255, 255, 46))
		im.save(path)
	return "%s/%s" % (G.FRAME_DIR, name)


def _classic_list(skin, screen_name):
	"""The Classic <widget name="list"> of a channel-selection screen (attribute contract kept as is)."""
	import xml.etree.ElementTree as ET
	scr = G._classic_screen(skin, "channelselection", screen_name)
	if not scr:
		return None
	for w in ET.fromstring(scr).iter("widget"):
		if w.get("name") == "list":
			return dict(w.attrib)
	return None


def _next_times(src, e, font, color):
	"""'HH:MM – HH:MM' of the NEXT event of the cursor service (EventTime NextStartTime / NextEndTime)."""
	return [w.replace(">StartTime<", ">NextStartTime<").replace(">EndTime<", ">NextEndTime<") for w in G.times(src, e, font, color)]


def channelselection(skin, screen_name, title):
	la = _classic_list(skin, screen_name)
	if la is None:
		return None
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="#73000000" zPosition="-4" />',
		'\t\t<eLabel position="60,60" size="840,960" backgroundColor="steThemeCard" cornerRadius="28" zPosition="-2" />',
		'\t\t<eLabel position="920,60" size="940,960" backgroundColor="steThemeCard" cornerRadius="28" zPosition="-2" />',
		'\t\t<widget source="Title" render="Label" position="92,78" size="620,48" font="%s;32" foregroundColor="foreground" transparent="1" noWrap="1" zPosition="20" />' % BOLD,
		'\t\t<widget source="global.CurrentTime" render="Label" position="720,82" size="150,40" font="%s;30" foregroundColor="secondFG" halign="right" transparent="1" zPosition="20">\n\t\t\t<convert type="ClockToText">Format:%%H:%%M</convert>\n\t\t</widget>' % BOLD]
	la.update({"position": "%d,%d" % CS_LIST[:2], "size": "%d,%d" % CS_LIST[2:], "itemHeight": str(CS_ROW), "serviceItemHeight": str(CS_ROW),
		"serviceNumberFont": "Regular;24", "serviceNameFont": "%s;27" % BOLD, "serviceInfoFont": "Regular;22", "selectionPixmap": _cs_selection(skin),
		"transparent": "1", "zPosition": "12", "colorServiceDescription": "secondFG", "colorServiceDescriptionFallback": "secondFG"})
	la.pop("backgroundColor", None)
	x.append('\t\t<widget name="list" %s />' % " ".join('%s="%s"' % (k, v) for k, v in la.items() if k != "name"))
	# right card: the event of the CURSOR service (ServiceEvent), NOW then NEXT
	pw, ph = 300, 450
	G.poster(skin, CS_SRC, {"x": 952, "y": 92, "w": pw, "h": ph}, CS_KEY)
	G.poster(skin, CS_SRC, {"x": 952, "y": 0, "w": 160, "h": 240}, CS_KEY)
	gate = '<convert type="ConfigEntryTest">%s,False,Invert</convert><convert type="ConditionalShowHide" />' % CS_KEY
	x.append('\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="mla_assets/poster_default_%dx%d.png" position="952,92" size="%d,%d" cornerRadius="22" zPosition="19">%s</widget>' % (pw, ph, pw, ph, gate))
	x.append('\t\t<widget source="%s" render="CineViewMLAPosterX" position="952,92" size="%d,%d" cornerRadius="22" zPosition="20" toggle="%s" />' % (CS_SRC, pw, ph, CS_KEY))
	for x0, inv, ny in ((1280, "", 570), (952, ",Invert", 650)):
		w = 1828 - x0
		x.append(_gate('\t\t<widget source="%s" render="Picon" scale="aspect" position="%d,96" size="150,76" alphatest="blend" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % (CS_SRC, x0), CS_KEY, inv))
		x.append(_gate('\t\t<widget source="%s" render="RunningText" position="%d,186" size="%d,40" transparent="1" zPosition="20" foregroundColor="foreground" font="%s;28" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">NameOnly</convert>\n\t\t</widget>' % (CS_SRC, x0, w, BOLD, G.RUN_OPTS), CS_KEY, inv))
		x.append('\t\t<widget source="%s" render="Label" position="%d,236" size="84,32" backgroundColor="secondFG" cornerRadius="16" halign="center" valign="center" foregroundColor="#001a1300" font="%s;20" zPosition="20">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=NOW</convert>\n\t\t</widget>' % (CS_SRC, x0, BOLD, CS_KEY, inv))
		x += [_gate(t, CS_KEY, inv) for t in G.times(CS_SRC, E(x0 + 100, 236, 160, 32), 23, "secondFG")]
		x.append(_gate(G.label(CS_SRC, E(x0 + w - 150, 236, 150, 32), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 22, "grey", ' halign="right"'), CS_KEY, inv))
		for t in G.text_variants(CS_SRC, [("EventName", "Name")], E(x0, 282, w, 96), None, 38, "foreground", G.T_OPTS, "always"):
			x.append(t.replace("CineViewMLAShowIf\">always,True,", "CineViewMLAShowIf\">%s,True%s," % (CS_KEY, inv)).replace('font="Regular;38"', 'font="%s;38"' % BOLD))
		x.append(_gate(G.label(CS_SRC, E(x0, 390, w - 240, 32), [("EventName", "Genre")], 22, "secondFG", ' noWrap="1"'), CS_KEY, inv))
		x.append(_gate(G.label(CS_SRC, E(x0 + w - 230, 390, 120, 32), [("CineViewMLAIMDb", "Plain,hide")], 22, "foreground", ' halign="right"'), CS_KEY, inv))
		x.append(_gate(G.label(CS_SRC, E(x0 + w - 100, 392, 100, 32), [("CineViewMLAIMDb", "Stars,hide")], 20, "secondFG", ' halign="right"'), CS_KEY, inv))
		x.append('\t\t<widget source="%s" render="Progress" position="%d,436" size="%d,6" pixmap="infobar/pbar.png" backgroundColor="%s" cornerRadius="3" zPosition="20">\n\t\t\t<convert type="EventTime">Progress</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s</convert>\n\t\t</widget>' % (CS_SRC, x0, w, PILL_BG, CS_KEY, inv))
		for t in G.text_variants(CS_SRC, [("EventName", "FullDescription")], E(x0, 462, w, ny - 16 - 462), None, 22, "grey", G.D_OPTS, "always"):
			x.append(t.replace("CineViewMLAShowIf\">always,True,", "CineViewMLAShowIf\">%s,True%s," % (CS_KEY, inv)))
		x.append('\t\t<widget source="session.CurrentService" render="Label" position="952,%d" size="876,2" backgroundColor="#00283a50" zPosition="20">\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=</convert>\n\t\t</widget>' % (ny, CS_KEY, inv))
		# NEXT of the cursor service: ON = small poster at the left of the card, text beside it
		nx = 1136 if not inv else 952
		if not inv:
			x.append('\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="mla_assets/poster_default_160x240.png" position="952,%d" size="160,240" cornerRadius="16" zPosition="19">%s</widget>' % (ny + 24, gate))
			x.append('\t\t<widget source="%s" render="CineViewMLAPosterX" position="952,%d" size="160,240" cornerRadius="16" zPosition="20" nexts="1" toggle="%s" />' % (CS_SRC, ny + 24, CS_KEY))
		nw = 1828 - nx
		x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="84,32" backgroundColor="%s" cornerRadius="16" halign="center" valign="center" foregroundColor="foreground" font="%s;20" zPosition="20">\n\t\t\t<convert type="EventName">NextNameOnly</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=NEXT</convert>\n\t\t</widget>' % (CS_SRC, nx, ny + 26, PILL_BG, BOLD, CS_KEY, inv))
		x += [_gate(t, CS_KEY, inv) for t in _next_times(CS_SRC, E(nx + 100, ny + 26, 160, 32), 23, "grey")]
		x.append(_gate('\t\t<widget source="%s" render="RunningText" position="%d,%d" size="%d,40" transparent="1" zPosition="20" foregroundColor="foreground" font="%s;30" noWrap="1" options="%s">\n\t\t\t<convert type="EventName">NextNameOnly</convert>\n\t\t</widget>' % (CS_SRC, nx, ny + 72, nw, BOLD, G.H_OPTS), CS_KEY, inv))
		nh = 1000 - (ny + 120)
		x.append(_gate('\t\t<widget source="%s" render="RunningText" position="%d,%d" size="%d,%d" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;22" options="%s">\n\t\t\t<convert type="EventName">NextDescription</convert>\n\t\t</widget>' % (CS_SRC, nx, ny + 120, nw, nh, G.D_OPTS), CS_KEY, inv))
	x.append('\t\t<panel name="ButtonTemplate" />')
	return G.screen(screen_name, title, [l for l in x if l])


EV_KEY = "config.plugins.cineviewmla.poster_eventview"
EV_KEYS = '\t\t<widget addon="ColorButtonsSequence" connection="key_red,key_green,key_yellow,key_blue" textColors="key_red:#00a00000,key_green:#00008000,key_yellow:#00a08000,key_blue:#000040a0" renderType="ColorTextOver" buttonCornerRadius="10" layoutStyle="fluid" alignment="left" foregroundColor="#00ffffff" font="Regular;%d" position="%s" size="%s" spacing="14" transparent="1" zPosition="40" />'


def _poster_pair(src, x, y, w, h, r, key, nexts=None, z=19):
	"""CineView default image (follows the poster switch) + the poster renderer, both rounded."""
	gate = '<convert type="ConfigEntryTest">%s,False,Invert</convert><convert type="ConditionalShowHide" />' % key
	n = ' nexts="%d"' % nexts if nexts is not None else ""
	return ['\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="mla_assets/poster_default_%dx%d.png" position="%d,%d" size="%d,%d" cornerRadius="%d" zPosition="%d">%s</widget>' % (w, h, x, y, w, h, r, z, gate),
		'\t\t<widget source="%s" render="CineViewMLAPosterX" position="%d,%d" size="%d,%d" cornerRadius="%d" zPosition="%d"%s toggle="%s" />' % (src, x, y, w, h, r, z + 1, n, key)]


def _bold_title(src, conv, e, font, key, inv, opts=None):
	out = []
	for t in G.text_variants(src, conv, e, None, font, "foreground", opts or G.T_OPTS, "always"):
		out.append(t.replace("CineViewMLAShowIf\">always,True,", "CineViewMLAShowIf\">%s,True%s," % (key, inv)).replace('font="Regular;%d"' % font, 'font="%s;%d"' % (BOLD, font)))
	return out


def eventview_live(skin):
	"""EventView = the event of the PLAYING service (plugin rule: other events open EventViewSimple).  Source-based
	(session.Event_Now / Event_Next), posters ON / OFF through CineViewMLAShowIf; the native named widgets of
	EventViewEPGSelect are not placed (as in the Classic dashboard)."""
	for w, h in ((400, 600), (110, 165)):
		G.poster(skin, "Event", {"x": 0, "y": 0, "w": w, "h": h}, EV_KEY)
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="#87000000" zPosition="-4" />',
		'\t\t<eLabel position="60,60" size="1800,960" backgroundColor="steThemeCard" cornerRadius="32" zPosition="-2" />']
	x += _poster_pair("Event", 100, 100, 400, 600, 24, EV_KEY, 0)
	for tx, inv, ny in ((540, "", 760), (100, ",Invert", 800)):
		tw = 1820 - tx
		pass  # picon: one fixed place for ON and OFF (below)
		x.append(_gate('\t\t<widget source="%s" render="RunningText" position="%d,122" size="%d,40" transparent="1" zPosition="20" foregroundColor="grey" font="%s;28" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">NameOnly</convert>\n\t\t</widget>' % (SVC, tx, 900, BOLD, G.RUN_OPTS), EV_KEY, inv))
		x += _bold_title(SRC_NOW, [("EventName", "Name")], E(tx, 196, tw, 128), 52, EV_KEY, inv)
		# meta row: times pill | duration | genre | IMDb
		x.append('\t\t<widget source="%s" render="Label" position="%d,340" size="196,40" backgroundColor="%s" cornerRadius="20" zPosition="18">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=</convert>\n\t\t</widget>' % (SRC_NOW, tx, PILL_BG, EV_KEY, inv))
		x += [_gate(t, EV_KEY, inv) for t in G.times(SRC_NOW, E(tx + 14, 344, 168, 32), 24, "foreground")]
		x.append(_gate(G.label(SRC_NOW, E(tx + 212, 344, 130, 32), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 24, "grey"), EV_KEY, inv))
		x.append(_gate(G.label(SRC_NOW, E(tx + 350, 344, tw - 350 - 260, 32), [("EventName", "Genre")], 24, "secondFG", ' noWrap="1"'), EV_KEY, inv))
		x.append(_gate(G.label(SRC_NOW, E(tx + tw - 250, 344, 130, 32), [("CineViewMLAIMDb", "Plain,hide")], 24, "foreground", ' halign="right"'), EV_KEY, inv))
		x.append(_gate(G.label(SRC_NOW, E(tx + tw - 110, 346, 110, 32), [("CineViewMLAIMDb", "Stars,hide")], 22, "secondFG", ' halign="right"'), EV_KEY, inv))
		x.append('\t\t<widget source="%s" render="Progress" position="%d,396" size="%d,6" pixmap="infobar/pbar.png" backgroundColor="%s" cornerRadius="3" zPosition="20">\n\t\t\t<convert type="EventTime">Progress</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s</convert>\n\t\t</widget>' % (SRC_NOW, tx, tw, PILL_BG, EV_KEY, inv))
		for t in G.text_variants(SRC_NOW, [("EventName", "FullDescription")], E(tx, 424, tw, ny - 20 - 424), None, 25, "foreground", G.D_OPTS, "always"):
			x.append(t.replace("CineViewMLAShowIf\">always,True,", "CineViewMLAShowIf\">%s,True%s," % (EV_KEY, inv)))
		x.append('\t\t<widget source="session.CurrentService" render="Label" position="100,%d" size="1720,2" backgroundColor="#00283a50" zPosition="20">\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=</convert>\n\t\t</widget>' % (ny, EV_KEY, inv))
		nx = 236 if not inv else 100
		if not inv:
			x += _poster_pair("Event", 100, ny + 20, 110, 165, 12, EV_KEY, 1)
		nw = 1820 - nx
		x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="84,32" backgroundColor="%s" cornerRadius="16" halign="center" valign="center" foregroundColor="foreground" font="%s;20" zPosition="20">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=NEXT</convert>\n\t\t</widget>' % (SRC_NEXT, nx, ny + 24, PILL_BG, BOLD, EV_KEY, inv))
		x += [_gate(t, EV_KEY, inv) for t in G.times(SRC_NEXT, E(nx + 100, ny + 24, 160, 32), 23, "grey")]
		x.append(_gate('\t\t<widget source="%s" render="RunningText" position="%d,%d" size="%d,40" transparent="1" zPosition="20" foregroundColor="foreground" font="%s;30" noWrap="1" options="%s">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t</widget>' % (SRC_NEXT, nx, ny + 66, nw, BOLD, G.H_OPTS), EV_KEY, inv))
		x.append(_gate('\t\t<widget source="%s" render="RunningText" position="%d,%d" size="%d,52" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;21" options="%s">\n\t\t\t<convert type="EventName">ShortDescription</convert>\n\t\t</widget>' % (SRC_NEXT, nx, ny + 110, nw, G.D_OPTS), EV_KEY, inv))
	# picon from the screen's own "Service" source (t57: session.CurrentService showed nothing here), at ONE fixed
	# place for ON and OFF: t57b showed that a Picon whose poster-switch variant is hidden still draws the default
	# picon (Picon shows itself on every change), so the picon must not have ON/OFF variants
	x.append('\t\t<widget source="Service" render="Picon" scale="aspect" position="1670,96" size="150,76" alphatest="blend" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>')
	x.append(EV_KEYS % (24, "100,972", "1720,40"))
	return G.screen("EventView", "Event View", [l for l in x if l])


def eventview_named(screen_name, on, infobar=False):
	"""EventViewSimple / InfoBarEventView (+_CVPosterOff): the native named widgets (channel, datetime, duration,
	FullDescription) and the Title / Event sources.  The poster switch selects the screen name (plugin rule), so ON
	and OFF are two screens with their own geometry (real reflow)."""
	if infobar:
		# InfoBarEventView: top card only, no dimming (the InfoBar EPG under it stays visible, as in Classic)
		x, cy, ch = [], 40, 400
	else:
		x, cy, ch = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="#87000000" zPosition="-4" />'], 60, 960
	x.append('\t\t<eLabel position="60,%d" size="1800,%d" backgroundColor="steThemeCard" cornerRadius="32" zPosition="-2" />' % (cy, ch))
	pw, ph = (220, 330) if infobar else (400, 600)
	tx = (100 + pw + 40) if on else 100
	tw = 1820 - tx
	if on:
		x += _poster_pair("Event", 100, cy + 35, pw, ph, 20 if infobar else 24, EV_KEY)
	y = cy + 40
	if not infobar:
		x.append('\t\t<widget name="channel" position="%d,%d" size="%d,40" font="%s;28" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />' % (tx, y, tw, BOLD))
		y += 56
	x.append('\t\t<widget source="Title" render="Label" position="%d,%d" size="%d,%d" font="%s;%d" foregroundColor="foreground" transparent="1" zPosition="20" />' % (tx, y, tw, 60 if infobar else 128, BOLD, 40 if infobar else 52))
	y += 76 if infobar else 144
	x.append('\t\t<widget name="datetime" position="%d,%d" size="440,40" font="Regular;24" foregroundColor="foreground" backgroundColor="%s" cornerRadius="20" halign="center" valign="center" zPosition="20" />' % (tx, y, PILL_BG))
	x.append('\t\t<widget name="duration" position="%d,%d" size="180,40" font="Regular;24" foregroundColor="foreground" backgroundColor="%s" cornerRadius="20" halign="center" valign="center" zPosition="20" />' % (tx + 452, y, PILL_BG))
	x.append(G.label("Event", E(tx + 648, y + 4, tw - 648 - 250, 32), [("EventName", "Genre")], 24, "secondFG", ' noWrap="1"'))
	x.append(G.label("Event", E(tx + tw - 240, y + 4, 130, 32), [("CineViewMLAIMDb", "Plain,hide")], 24, "foreground", ' halign="right"'))
	x.append(G.label("Event", E(tx + tw - 100, y + 6, 100, 32), [("CineViewMLAIMDb", "Stars,hide")], 22, "secondFG", ' halign="right"'))
	y += 64
	keys_y = cy + ch - 56
	x.append('\t\t<widget name="FullDescription" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="foreground" backgroundColor="steThemeCard" transparent="1" zPosition="20" />' % (tx, y, tw, keys_y - 16 - y, 24 if infobar else 26))
	x.append(EV_KEYS % (22 if infobar else 24, "%d,%d" % (tx, keys_y), "%d,40" % tw))
	extra = ""
	return G.screen(screen_name, "Event View", [l for l in x if l], extra)


EPG_KEY = "config.plugins.cineviewmla.poster_epg"


def graphical_epg(skin, on):
	"""Modern GraphicalEPG: Graphical Plus contract (gen_epg: native list / timeline / lab1 / bouquetlist widgets,
	sources Event / Service = highlighted cell, user time span) with a rounded detail card, bold title and pills.
	OFF = second screen GraphicalEPG_CVPosterOff (plugin rule): wider grid, narrow card, no poster."""
	sys.path.insert(0, os.path.join(HERE, "..", "p9epg"))
	import gen_epg as GE
	src = "Event"
	gw = 1250 if on else 1500
	px = 60 + gw + 24
	tx, tw = px + 24, 1860 - px - 48
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="-1" />',
		'\t\t<widget source="Title" render="Label" position="60,26" size="1100,50" font="%s;32" foregroundColor="foreground" transparent="1" zPosition="40" noWrap="1" />' % BOLD,
		G.label("global.CurrentTime", E(1250, 38, 330, 32), [("ClockToText", "Format:%a %d %b")], 22, "grey", ' halign="right"', 40),
		'\t\t<widget source="global.CurrentTime" render="Label" position="1600,24" size="260,54" font="%s;40" foregroundColor="foreground" halign="right" transparent="1" zPosition="40">\n\t\t\t<convert type="ClockToText">Format:%%H:%%M</convert>\n\t\t</widget>' % BOLD]
	x += GE.grid(E(60, 150, gw, 800), E(60, 106, gw, 40))
	x.append('\t\t<eLabel position="%d,100" size="%d,850" backgroundColor="steThemeCard" cornerRadius="24" zPosition="1" />' % (px, 1860 - px))
	pill = lambda e: '\t\t<eLabel %s backgroundColor="%s" cornerRadius="%d" zPosition="2" />' % (G.pos(e), PILL_BG, e["h"] // 2)
	if on:
		G.poster(skin, src, E(0, 0, 240, 360), EPG_KEY)
		x += _poster_pair(src, tx, 124, 240, 360, 18, EPG_KEY)
		mx, mw = tx + 260, tw - 260
		x.append('\t\t<widget source="Service" render="Picon" position="%d,128" size="130,64" alphatest="blend" scale="aspect" transparent="1" zPosition="40">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % mx)
		x.append(pill(E(mx, 208, mw, 36)))
		x += G.times(src, E(mx + 10, 210, mw - 28, 32), 23, "foreground")
		x.append(pill(E(mx, 252, 130, 36)))
		x.append(G.label(src, E(mx, 254, 130, 32), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 22, "foreground", ' halign="center"', 40))
		x.append(G.label("Service", E(mx, 300, mw, 30), [("ServiceName", "Name")], 22, "grey", ' noWrap="1"', 40))
		x.append(G.label(src, E(mx, 336, mw, 30), [("EventName", "Genre")], 21, "secondFG", ' noWrap="1"', 40))
		x.append(G.label(src, E(mx, 372, 110, 30), [("CineViewMLAIMDb", "Plain,hide")], 22, "foreground", "", 40))
		x.append(G.label(src, E(mx + 112, 374, mw - 112, 30), [("CineViewMLAIMDb", "Stars,hide")], 20, "secondFG", "", 40))
		ty, th, tf = 508, 84, 34
		dy, df = 606, 23
		dh = 930 - dy
	else:
		x.append(G.label("Service", E(tx, 122, tw, 30), [("ServiceName", "Name")], 22, "grey", ' noWrap="1"', 40))
		x.append(pill(E(tx, 162, tw, 36)))
		x += G.times(src, E(tx + 10, 164, tw - 28, 32), 23, "foreground")
		x.append(pill(E(tx, 206, 130, 36)))
		x.append(G.label(src, E(tx, 208, 130, 32), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 22, "foreground", ' halign="center"', 40))
		ty, th, tf = 258, 76, 30
		dy, df = 350, 22
		dh = 866 - dy
		x.append(G.label(src, E(tx, 878, tw, 28), [("EventName", "Genre")], 21, "secondFG", ' noWrap="1"', 40))
		x.append(G.label(src, E(tx, 908, 110, 30), [("CineViewMLAIMDb", "Plain,hide")], 22, "foreground", "", 40))
		x.append(G.label(src, E(tx + 112, 910, tw - 112, 30), [("CineViewMLAIMDb", "Stars,hide")], 20, "secondFG", "", 40))
	for t in G.text_variants(src, [("EventName", "Name")], E(tx, ty, tw, th), None, tf, "foreground", G.T_OPTS, "always"):
		x.append(t.replace('font="Regular;%d"' % tf, 'font="%s;%d"' % (BOLD, tf)).replace('zPosition="20"', 'zPosition="40"'))
	for t in G.text_variants(src, [("EventName", "FullDescription")], E(tx, dy, tw, dh), None, df, "grey", G.D_OPTS, "always"):
		x.append(t.replace('zPosition="20"', 'zPosition="40"'))
	x += GE.keys(985)
	name = "GraphicalEPG" if on else "GraphicalEPG_CVPosterOff"
	return '\t<screen name="%s" position="0,0" size="1920,1080" flags="wfNoBorder" title="Graphical EPG">\n%s\n\t</screen>' % (name, "\n".join(l for l in x if l))


PVR_KEY = "config.plugins.cineviewmla.poster_pvr"


def movieselection(skin, on):
	"""Modern MovieSelection (mockup modern_pvr): rounded list card (native MovieList; rounded selected row through
	the native itemCornerRadiusSelected path of eListboxPythonMultiContent::paint) + rounded detail card of the
	SELECTED recording (screen source "Service": ServiceName / ServiceTime / MovieInfo, cover = CineViewMLAPosterX).
	Every native named widget of the Classic screen is kept (list, waitingtext, chosenletter, movie_sort, movie_off,
	DescriptionBorder, TrashcanSize, freeDiskSpace, coloured keys).  OFF = MovieSelection_CVPosterOff (plugin)."""
	src = "Service"
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="-4" />',
		'\t\t<widget source="Title" render="Label" position="60,26" size="1300,50" font="%s;32" foregroundColor="foreground" transparent="1" noWrap="1" zPosition="20" />' % BOLD,
		'\t\t<widget source="global.CurrentTime" render="Label" position="1600,24" size="260,54" font="%s;40" foregroundColor="foreground" halign="right" transparent="1" zPosition="20">\n\t\t\t<convert type="ClockToText">Format:%%H:%%M</convert>\n\t\t</widget>' % BOLD,
		'\t\t<widget name="movie_sort" pixmaps="icons/az.png,icons/newtop.png,icons/shuffle.png,icons/za.png,icons/oldtop.png,icons/faz.png,icons/fza.png,icons/default.png,icons/azold.png,icons/zanew.png,icons/longest.png,icons/shortest.png,icons/dtsrt.png,icons/dtsdt.png" position="1460,36" zPosition="5" size="52,30" transparent="1" alphatest="on" />',
		'\t\t<widget name="movie_off" pixmaps="icons/ask.png,icons/movielist.png,icons/quit.png,icons/pause.png,icons/playlist.png,icons/playlistquit.png,icons/loop.png,icons/rep.png" position="1520,36" zPosition="5" size="52,30" transparent="1" alphatest="on" />',
		'\t\t<eLabel position="60,100" size="1180,860" backgroundColor="steThemeCard" cornerRadius="28" zPosition="-2" />',
		'\t\t<eLabel position="1264,100" size="596,860" backgroundColor="steThemeCard" cornerRadius="28" zPosition="-2" />',
		'\t\t<widget name="waitingtext" position="76,116" size="1148,828" font="Regular;33" halign="center" valign="center" transparent="1" zPosition="4" />',
		'\t\t<widget name="chosenletter" position="76,116" size="1148,828" foregroundColor="secondFG" font="Regular;112" halign="center" valign="center" transparent="1" zPosition="4" />',
		'\t\t<widget name="list" position="76,116" size="1148,828" scrollbarMode="showOnDemand" itemHeight="69" font="Regular;30" transparent="1" backgroundColorSelected="#00314155" itemCornerRadiusSelected="16" zPosition="3" />',
		'\t\t<widget name="DescriptionBorder" position="0,0" size="0,0" />']
	tx, tw = 1292, 540
	if on:
		G.poster(skin, src, E(0, 0, 300, 450), PVR_KEY)
		x += _poster_pair(src, 1412, 128, 300, 450, 22, PVR_KEY)
		ty = 600
	else:
		ty = 128
	x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="%d,84" font="%s;34" foregroundColor="foreground" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Name</convert>\n\t\t</widget>' % (src, tx, ty, tw, BOLD))
	py = ty + 98
	x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="170,36" backgroundColor="%s" cornerRadius="18" halign="center" valign="center" font="Regular;22" foregroundColor="foreground" zPosition="20">\n\t\t\t<convert type="ServiceTime">StartTime</convert>\n\t\t\t<convert type="ClockToText">ShortDate</convert>\n\t\t</widget>' % (src, tx, py, PILL_BG))
	x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="120,36" backgroundColor="%s" cornerRadius="18" halign="center" valign="center" font="Regular;22" foregroundColor="foreground" zPosition="20">\n\t\t\t<convert type="ServiceTime">Duration</convert>\n\t\t\t<convert type="ClockToText">AsLength</convert>\n\t\t</widget>' % (src, tx + 182, py, PILL_BG))
	x.append(G.label(src, E(tx + 314, py + 2, tw - 314, 32), [("MovieInfo", "FileSize")], 22, "grey", ' halign="right"'))
	x.append(G.label(src, E(tx, py + 50, tw, 32), [("MovieInfo", "RecordServiceName")], 23, "secondFG", ' noWrap="1"'))
	dy = py + 94
	x.append('\t\t<widget source="%s" render="RunningText" position="%d,%d" size="%d,%d" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;22" options="%s">\n\t\t\t<convert type="MovieInfo">FullDescription</convert>\n\t\t</widget>' % (src, tx, dy, tw, 936 - dy, G.D_OPTS))
	x.append('\t\t<widget name="freeDiskSpace" position="60,972" size="700,36" foregroundColor="grey" font="Regular;24" transparent="1" zPosition="20" />')
	x.append('\t\t<widget name="TrashcanSize" position="1160,972" size="700,36" foregroundColor="grey" font="Regular;24" halign="right" transparent="1" zPosition="20" />')
	x.append('\t\t<panel name="ButtonTemplate" />')
	name = "MovieSelection" if on else "MovieSelection_CVPosterOff"
	return '\t<screen name="%s" title="Movie Selection" position="fill" backgroundColor="steThemePrimary" flags="wfNoBorder">\n%s\n\t</screen>' % (name, "\n".join(l for l in x if l))


def emc_selection(skin, on):
	"""Modern EMC (EnhancedMovieCenter = what the PVR key opens here): the same two rounded cards as the Modern
	MovieSelection, built on EMC's own widgets (emc_common.py).  No mini-TV (Modern has none).  OFF =
	EMCSelection_CVPosterOff: the detail card without cover, text from the top of the card."""
	src = "Service"
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="-4" />',
		'\t\t<widget source="Title" render="Label" position="60,26" size="1300,50" font="%s;30" foregroundColor="foreground" transparent="1" noWrap="1" zPosition="20" />' % BOLD,
		'\t\t<widget source="global.CurrentTime" render="Label" position="1600,24" size="260,54" font="%s;40" foregroundColor="foreground" halign="right" transparent="1" zPosition="20">\n\t\t\t<convert type="ClockToText">Format:%%H:%%M</convert>\n\t\t</widget>' % BOLD,
		'\t\t<eLabel position="60,100" size="1180,860" backgroundColor="steThemeCard" cornerRadius="28" zPosition="-2" />',
		'\t\t<eLabel position="1264,100" size="596,860" backgroundColor="steThemeCard" cornerRadius="28" zPosition="-2" />',
		'\t\t<widget name="wait" position="76,116" size="1148,828" font="Regular;33" halign="center" valign="center" transparent="1" zPosition="4" />',
		EMC.emc_list(84, 124, 1132, 812, 58, 30, 26, ' backgroundColorSelected="#00314155" itemCornerRadiusSelected="16"')]
	tx, tw = 1292, 540
	if on:
		G.poster(skin, src, E(0, 0, 300, 450), PVR_KEY)
		x += EMC.emc_cover_under(1412, 128, 300, 450)
		x += _poster_pair(src, 1412, 128, 300, 450, 22, PVR_KEY)
		ty = 600
	else:
		x += EMC.emc_cover_under(1850, 950, 2, 2)
		ty = 128
	x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="%d,84" font="%s;34" foregroundColor="foreground" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Name</convert>\n\t\t</widget>' % (src, tx, ty, tw, BOLD))
	py = ty + 98
	x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="170,36" backgroundColor="%s" cornerRadius="18" halign="center" valign="center" font="Regular;22" foregroundColor="foreground" zPosition="20">\n\t\t\t<convert type="ServiceTime">StartTime</convert>\n\t\t\t<convert type="ClockToText">ShortDate</convert>\n\t\t</widget>' % (src, tx, py, PILL_BG))
	x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="120,36" backgroundColor="%s" cornerRadius="18" halign="center" valign="center" font="Regular;22" foregroundColor="foreground" zPosition="20">\n\t\t\t<convert type="ServiceTime">Duration</convert>\n\t\t\t<convert type="ClockToText">AsLength</convert>\n\t\t</widget>' % (src, tx + 182, py, PILL_BG))
	x.append(G.label(src, E(tx + 314, py + 2, tw - 314, 32), [("MovieInfo", "FileSize")], 22, "grey", ' halign="right"'))
	x.append(G.label(src, E(tx, py + 50, tw, 32), [("MovieInfo", "RecordServiceName")], 23, "secondFG", ' noWrap="1"'))
	dy = py + 94
	# EMC: the recording's description (MovieInfo ShortDescription); for EMC's service FullDescription and
	# ExtendedDescription return the FILE PATH (device t61, t61c)
	x.append('\t\t<widget source="%s" render="RunningText" position="%d,%d" size="%d,%d" transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;22" options="%s">\n\t\t\t<convert type="MovieInfo">ShortDescription</convert>\n\t\t</widget>' % (src, tx, dy, tw, 936 - dy, G.D_OPTS))
	x.append('\t\t<widget source="spacefree" render="Label" position="60,972" size="700,36" foregroundColor="grey" font="Regular;24" transparent="1" zPosition="20" />')
	x += EMC.emc_keys(1018, 60, 300, 24)
	name = "EMCSelection" if on else "EMCSelection_CVPosterOff"
	return '\t<screen name="%s" title="EMC" position="fill" backgroundColor="steThemePrimary" flags="wfNoBorder">\n%s\n\t</screen>' % (name, "\n".join(l for l in x if l))


FONTS = '\t<fonts>\n\t\t<font name="%s" filename="LiberationSans-Bold.ttf" scale="100" />\n\t</fonts>' % BOLD


# Modern "Optimized" (default) vs "Large" (MLA_MODERN_VARIANT=large, the build51-63 behaviour).
# Root cause (device t60 / t62 + enigma2 57b7a51 source): the receiver's accelerated surface pool is 5400 kB
# ("[gFBDC] 5400kB available for acceleration surfaces"); every PNG >= 48000 bytes loaded by the skin is put in it
# (gpixmap.cpp GFX_SURFACE_ACCELERATION_THRESHOLD) and stays there for good (LoadPixmap caches PNGs, PixmapCache).
# Modern's per-size default posters (400x600, 300x450, 240x360, 220x330, 200x300, 160x240, 146x218, 110x165)
# pinned ~3 MB of the pool, so the live posters (decoded per widget) kept failing accelAlloc -> RAM fallback.
# Optimized: the default under each poster is a gradient tile (no bitmap) + a small icon PNG below the
# threshold, and the poster widget gets underlay="1": it shows nothing (and releases its picture) when there
# is no poster, instead of decoding the 600x900 default.  Look: same tile, same icon, rounded corners kept.
VARIANT = os.environ.get("MLA_MODERN_VARIANT", "optimized")
TILE_PNG = "poster_tile.png"  # 4x90 vertical gradient of poster_default.jpg, stretched (1440 bytes: never accel)
ICON_MAX_W = 120  # 120x88x4 = 42240 bytes < 48000: never enters the accelerated pool


def _tile(skin):
	"""The default image's background gradient as a tiny PNG, stretched by the widget (scale="1").  Device t67: a
	Pixmap widget with only a gradient backgroundColor and no pixmap draws nothing (ePixmap paints no background)."""
	from PIL import Image
	path = os.path.join(skin, G.FRAME_DIR, TILE_PNG)
	if not os.path.isfile(path):
		top, bot = (15, 23, 42), (23, 38, 61)
		im = Image.new("RGB", (4, 90))
		for y in range(90):
			c = tuple(int(round(top[i] + (bot[i] - top[i]) * y / 89.0)) for i in range(3))
			for x in range(4):
				im.putpixel((x, y), c)
		im.save(path)
	return "%s/%s" % (G.FRAME_DIR, TILE_PNG)


def _icon(skin, w):
	"""CineView default icon (film frame + play triangle, colours of poster_default.jpg), RGBA, drawn at 4x and
	downsampled.  Width = 43 % of the poster width, capped at ICON_MAX_W."""
	from PIL import Image, ImageDraw
	iw = min(ICON_MAX_W, max(24, int(round(w * 0.433))))
	ih = int(round(iw * 190 / 260.0))
	name = "poster_icon_%dx%d.png" % (iw, ih)
	path = os.path.join(skin, G.FRAME_DIR, name)
	if not os.path.isfile(path):
		k = 4 * iw / 260.0
		im = Image.new("RGBA", (iw * 4, ih * 4), (0, 0, 0, 0))
		d = ImageDraw.Draw(im)
		fr = (123, 140, 168, 255)
		d.rounded_rectangle([0, 0, iw * 4 - 1, ih * 4 - 1], radius=int(14 * k), outline=fr, width=max(4, int(8 * k)))
		for i in range(6):
			sx = int((12 + 43 * i) * k)
			for sy in (int(12 * k), int(160 * k)):
				d.rounded_rectangle([sx, sy, sx + int(18 * k), sy + int(18 * k)], radius=int(4 * k), fill=(120, 140, 167, 255))
		d.polygon([(int(100 * k), int(60 * k)), (int(166 * k), int(95 * k)), (int(100 * k), int(130 * k))], fill=(231, 176, 49, 255))
		im.resize((iw, ih), Image.LANCZOS).save(path)
	return "%s/%s" % (G.FRAME_DIR, name), iw, ih


_DEFAULT_RE = re.compile(r'(\t*)<widget source="([^"]+)" render="Pixmap" pixmap="mla_assets/poster_default_(\d+)x(\d+)\.png" position="(\d+),(\d+)" size="(\d+),(\d+)" cornerRadius="([^"]+)" zPosition="(-?\d+)">(.*?)</widget>')


def _optimize(skin, xml):
	def tile(m):
		ind, src, w, h, x, y, _w, _h, r, z, gate = m.groups()
		x, y, w, h, z = int(x), int(y), int(w), int(h), int(z)
		icon, iw, ih = _icon(skin, w)
		return ('%s<widget source="%s" render="Pixmap" pixmap="%s" position="%d,%d" size="%d,%d" scale="1" cornerRadius="%s" zPosition="%d">%s</widget>\n'
			'%s<widget source="%s" render="Pixmap" pixmap="%s" position="%d,%d" size="%d,%d" alphatest="blend" zPosition="%d">%s</widget>') % (
			ind, src, _tile(skin), x, y, w, h, r, z - 1, gate, ind, src, icon, x + (w - iw) // 2, y + (h - ih) // 2, iw, ih, z, gate)
	xml, n = _DEFAULT_RE.subn(tile, xml)
	assert "poster_default_" not in xml, "a Modern default poster escaped the optimizer"
	xml = xml.replace('render="CineViewMLAPosterX" ', 'render="CineViewMLAPosterX" underlay="1" ')
	# picons stay native (t70): the channel list's own rows load the same picon files cached (listboxservice.cpp
	# loadPNG cached=1), so the native Picon renderer shares those blocks; an uncached copy only added allocations.
	return xml


def _write_pack(skin, section, parts, provides, label):
	d = os.path.join(skin, "layouts", section, "modern")
	os.makedirs(d, exist_ok=True)
	xml = '<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Modern (%s) — generated by tools/mla/p10models/gen_modern.py. Look NOT approved yet. Do not edit by hand. -->\n<skin>\n%s\n%s\n</skin>\n' % (label, FONTS, "\n".join("\t" + p.strip() if not p.startswith("\t") else p for p in parts))
	if VARIANT != "large":
		xml = _optimize(skin, xml)
	p = os.path.join(d, "screens.openatv.xml")
	open(p, "w", encoding="utf-8").write(xml)
	json.dump({"schema": 1, "id": "modern", "section": section, "name": "CineView Modern", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "tools/mla/p10models (Modern model mockup, look pending approval)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}}, "provides_screens": provides,
		"options": [], "preview": "preview.png"}, open(os.path.join(d, "manifest.json"), "w"), indent=1)
	import xml.etree.ElementTree as ET
	r = ET.parse(p).getroot()
	for scr in r.findall("screen"):
		for el in scr.iter():
			ps, ss = el.get("position"), el.get("size")
			if ps and ss and not ps.startswith(("c", "e")) and ps != "fill":
				px, py = (int(v) for v in ps.split(","))
				sw, sh = (int(v) for v in ss.split(","))
				assert 0 <= px and px + sw <= 1920 and 0 <= py and py + sh <= 1080, el.attrib
	return d


def generate(skin):
	from PIL import Image
	# default poster image at the Modern slot size (same CineView default image as Details)
	w, h = POSTER[2], POSTER[3]
	dp = os.path.join(skin, G.FRAME_DIR, "poster_default_%dx%d.png" % (w, h))
	if not os.path.isfile(dp):
		Image.open(os.path.join(skin, G.FRAME_DIR, "poster_default.jpg")).convert("RGB").resize((w, h), Image.LANCZOS).save(dp)
	made = []
	parts = [infobar(skin)]
	radio = G._classic_screen(skin, "infobar", "RadioInfoBar")
	if radio:
		parts.append(radio.strip("\n"))
	made.append(_write_pack(skin, "infobar", parts, ["InfoBar"] + (["RadioInfoBar"] if radio else []), "InfoBar"))
	parts = secondinfobar(skin)
	ecm = G._classic_screen(skin, "secondinfobar", "SecondInfoBarECM")
	if ecm:
		parts.append(ecm.strip("\n"))
	made.append(_write_pack(skin, "secondinfobar", parts, ["SecondInfoBar", "SecondInfoBarSimple"] + (["SecondInfoBarECM"] if ecm else []), "SecondInfoBar"))
	# channelselection: ChannelSelection (+ the radio / simple variants with the same list contract); others Classic
	parts, provides = [], []
	# only ChannelSelection is Modern; Radio (RDS widgets), Simple / Slim (PiG templates) keep their Classic contract
	for name, title in (("ChannelSelection", "Channel Selection"),):
		scr = channelselection(skin, name, title)
		if scr:
			parts.append(scr)
			provides.append(name)
	for name in ("ChannelSelectionRadio", "SimpleChannelSelection", "SlimChannelSelection"):
		c = G._classic_screen(skin, "channelselection", name)
		if c:
			parts.append(c.strip("\n"))
			provides.append(name)
	made.append(_write_pack(skin, "channelselection", parts, provides, "Channel Selection"))
	# epg: GraphicalEPG (+_CVPosterOff) Modern; every other EPG screen keeps its Classic contract
	csrc = open(os.path.join(skin, "layouts", "epg", "classic", "screens.openatv.xml"), encoding="utf-8").read()
	parts, provides = [graphical_epg(skin, True), graphical_epg(skin, False)], ["GraphicalEPG", "GraphicalEPG_CVPosterOff"]
	for n in re.findall(r'<screen name="([^"]+)"', csrc):
		if n in ("GraphicalEPG", "GraphicalEPG_CVPosterOff"):
			continue
		parts.append(G._classic_screen(skin, "epg", n).strip("\n"))
		provides.append(n)
	made.append(_write_pack(skin, "epg", parts, provides, "EPG"))
	# pvr: MovieSelection (+_CVPosterOff) Modern; MoviePlayer, PVRState, Timeshift*, MovieContextMenu Classic
	psrc = open(os.path.join(skin, "layouts", "pvr", "classic", "screens.openatv.xml"), encoding="utf-8").read()
	parts = [movieselection(skin, True), movieselection(skin, False), emc_selection(skin, True), emc_selection(skin, False)]
	provides = ["MovieSelection", "MovieSelection_CVPosterOff", "EMCSelection", "EMCSelection_CVPosterOff"]
	for n in re.findall(r'<screen name="([^"]+)"', psrc):
		if n == "MovieSelection":
			continue
		parts.append(G._classic_screen(skin, "pvr", n).strip("\n"))
		provides.append(n)
	made.append(_write_pack(skin, "pvr", parts, provides, "PVR"))
	# eventview: live dashboard + the named-widget screens (ON / _CVPosterOff); context menu stays Classic
	G.poster(skin, "Event", {"x": 0, "y": 0, "w": 220, "h": 330}, EV_KEY)
	parts = [eventview_live(skin)]
	for name, ib in (("EventViewSimple", False), ("InfoBarEventView", True)):
		parts.append(eventview_named(name, True, ib))
		parts.append(eventview_named(name + "_CVPosterOff", False, ib))
	ctx = G._classic_screen(skin, "eventview", "EventViewContextMenu")
	if ctx:
		parts.append(ctx.strip("\n"))
	made.append(_write_pack(skin, "eventview", parts, ["EventView", "EventViewSimple", "EventViewSimple_CVPosterOff", "InfoBarEventView", "InfoBarEventView_CVPosterOff"] + (["EventViewContextMenu"] if ctx else []), "EventView"))
	return made


if __name__ == "__main__":
	print(generate(sys.argv[1]))
