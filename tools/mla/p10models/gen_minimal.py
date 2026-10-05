#!/usr/bin/env python3
"""CineView Minimal — prototype packs for the six sections (docs/mla/Minimal_Spec.md; direction approved
2026-10-05 05:23 / 08:45, final look pending the user's approval of device pictures).

Identity (spec §1): no cards, no borders, no chips; typography and spacing carry the hierarchy; one accent per
screen; text only on the solid part of a theme-tinted scrim; small thumbnails; technical data only as one plain line
in the expanded layer.  Colours are theme roles only (steThemeOverlay = theme-tinted ~82 % scrim, secondFG = accent).

Contracts are the ones already verified for the other packs (see gen_modern.py / gen_epg.py / gen_cover.py /
emc_common.py): source widgets switch with CineViewMLAShowIf, named Python widgets get '<screen>_CVPosterOff'
screens through the CineView MLA plugin, EMC uses its own widgets.  usage (build.py): generate(skin) -> [pack dirs]"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "p7"))
sys.path.insert(0, os.path.join(HERE, "..", "p9epg"))
import gen_details as G  # noqa: E402
import emc_common as EMC  # noqa: E402

SVC, NOW, NXT = "session.CurrentService", "session.Event_Now", "session.Event_Next"
SCRIM = "steThemeOverlay"
EDGE = "#ff000000,steThemeOverlay,vertical,1"  # transparent -> theme tint (soft upper edge only)
TRACK = "#B0FFFFFF"
KEYS = '\t\t<widget addon="ColorButtonsSequence" connection="key_red,key_green,key_yellow,key_blue" textColors="key_red:#00a00000,key_green:#00008000,key_yellow:#00a08000,key_blue:#000040a0" renderType="ColorTextOver" buttonCornerRadius="6" layoutStyle="fluid" alignment="left" foregroundColor="#00ffffff" font="Regular;%d" position="%s" size="%s" spacing="12" transparent="1" zPosition="40" />'


def E(x, y, w, h):
	return {"x": x, "y": y, "w": w, "h": h}


def box(x, y, w, h, color, z=-3):
	return '\t\t<eLabel position="%d,%d" size="%d,%d" backgroundColor="%s" zPosition="%d" />' % (x, y, w, h, color, z)


def sw(key, inv):
	return '\t<convert type="CineViewMLAShowIf">%s,True%s</convert>\n\t\t</widget>' % (key, inv)


def gate(w, key, inv):
	return w.replace("</widget>", sw(key, inv), 1) if key else w


def thumb(skin, src, x, y, w, h, key, nexts=None):
	"""Small thumbnail, 6-px radius, CineView default image under it, no frame (Minimal has none)."""
	G.poster(skin, src, E(0, 0, w, h), key)  # creates the default image at this size
	g = '<convert type="ConfigEntryTest">%s,False,Invert</convert><convert type="ConditionalShowHide" />' % key
	n = ' nexts="%d"' % nexts if nexts is not None else ""
	return ['\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="mla_assets/poster_default_%dx%d.png" position="%d,%d" size="%d,%d" cornerRadius="6" zPosition="19">%s</widget>' % (w, h, x, y, w, h, g),
		'\t\t<widget source="%s" render="CineViewMLAPosterX" position="%d,%d" size="%d,%d" cornerRadius="6" zPosition="20"%s toggle="%s" />' % (src, x, y, w, h, n, key)]


def text(src, conv, e, font, color, key, inv, opts=None):
	"""ltr / rtl variants of one text box, switched by the poster key (or always when key is None)."""
	out = []
	for t in G.text_variants(src, conv, e, None, font, color, opts or G.D_OPTS, "always"):
		if key:
			t = t.replace('CineViewMLAShowIf">always,True,', 'CineViewMLAShowIf">%s,True%s,' % (key, inv))
		out.append(t)
	return out


def screen(name, body, extra=' position="fill" backgroundColor="transparent"'):
	title = "" if "title=" in extra else ' title="%s"' % name
	return '\t<screen name="%s"%s%s flags="wfNoBorder">\n%s\n\t</screen>' % (name, title, extra, "\n".join(l for l in body if l))


# ------------------------------------------------------------------------------------------------ InfoBar (§3.1)
def infobar(skin):
	key = "config.plugins.cineviewmla.poster_infobar"
	x = [box(0, 820, 1920, 120, EDGE), box(0, 940, 1920, 140, SCRIM)]
	x += thumb(skin, NOW, 60, 948, 70, 105, key)
	for x0, inv in ((150, ""), (60, ",Invert")):
		x.append('\t\t<widget source="%s" render="ChannelNumber" position="%d,960" size="66,30" font="Regular;24" foregroundColor="grey" transparent="1" zPosition="20"><convert type="CineViewMLAShowIf">%s,True%s</convert></widget>' % (SVC, x0, key, inv))
		x.append(gate('\t\t<widget source="%s" render="Label" position="%d,960" size="%d,30" font="Regular;24" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20">\n\t\t\t<convert type="ServiceName">NameOnly</convert>\n\t\t</widget>' % (SVC, x0 + 72, 1060 - 72), key, inv))
		x += text(NOW, [("EventName", "Name")], E(x0, 994, 1060, 44), 34, "foreground", key, inv, G.T_OPTS)
		x.append('\t\t<widget source="%s" render="Progress" position="%d,1046" size="1060,3" foregroundColor="secondFG" backgroundColor="%s" zPosition="20">\n\t\t\t<convert type="EventTime">Progress</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s</convert>\n\t\t</widget>' % (NOW, x0, TRACK, key, inv))
	x += G.times(NOW, E(1240, 960, 620, 30), 24, "grey")
	x.append(G.label(NXT, E(1240, 1000, 90, 34), [("EventTime", "StartTime"), ("ClockToText", "Format:%H:%M")], 26, "grey"))
	x += text(NXT, [("EventName", "Name")], E(1336, 1000, 524, 34), 26, "grey", None, "", G.H_OPTS)
	return screen("InfoBar", x)


# ------------------------------------------------------------------------------------------------ SecondInfoBar (§3.2)
def secondinfobar(skin):
	key = "config.plugins.cineviewmla.poster_secondinfobar"
	x = [box(0, 460, 1920, 160, EDGE), box(0, 620, 1920, 460, SCRIM)]
	x += thumb(skin, NOW, 60, 640, 220, 330, key)
	for x0, inv in ((310, ""), (60, ",Invert")):
		w = 1860 - x0
		x.append('\t\t<widget source="%s" render="Label" position="%d,640" size="70,30" font="Regular;22" foregroundColor="secondFG" transparent="1" zPosition="20">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=NOW</convert>\n\t\t</widget>' % (NOW, x0, key, inv))
		x += [gate(t, key, inv) for t in G.times(NOW, E(x0 + 76, 640, 150, 30), 22, "secondFG")]
		x += text(NOW, [("EventName", "Name")], E(x0, 674, w, 96), 40, "foreground", key, inv, G.T_OPTS)
		x += text(NOW, [("EventName", "FullDescription")], E(x0, 780, w, 140), 23, "foreground", key, inv)
		x.append('\t\t<widget source="%s" render="Label" position="%d,930" size="%d,1" backgroundColor="#80FFFFFF" zPosition="20">\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=</convert>\n\t\t</widget>' % (SVC, x0, w, key, inv))
		x.append('\t\t<widget source="%s" render="Label" position="%d,942" size="70,32" font="Regular;24" foregroundColor="grey" transparent="1" zPosition="20">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=NEXT</convert>\n\t\t</widget>' % (NXT, x0, key, inv))
		x.append(gate(G.label(NXT, E(x0 + 76, 942, 80, 32), [("EventTime", "StartTime"), ("ClockToText", "Format:%H:%M")], 26, "grey"), key, inv))
		x += text(NXT, [("EventName", "Name")], E(x0 + 166, 942, w - 166, 32), 26, "grey", key, inv, G.H_OPTS)
		x += text(NXT, [("EventName", "FullDescription")], E(x0, 980, w, 50), 21, "grey", key, inv)
	# one plain technical line (live converters only), the only technical data Minimal shows
	t, y = 60, 1040
	parts = [(SVC, [("ServiceOrbitalPosition", None)], 100), (SVC, [("CineViewMLATransponderInfo", "TransponderInfo")], 560)]
	for src, conv, w in parts:
		x.append(G.label(src, E(t, y, w, 28), conv, 20, "grey", ' noWrap="1"'))
		t += w + 10
	x.append('\t\t<widget render="VideoSize" source="%s" position="%d,%d" size="140,28" font="Regular;20" foregroundColor="grey" transparent="1" zPosition="20" />' % (SVC, t, y))
	t += 150
	x.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="60,28" font="Regular;20" foregroundColor="grey" transparent="1" zPosition="20">\n\t\t\t<convert type="CineViewMLAServiceInfo">IsWidescreen</convert>\n\t\t\t<convert type="CineViewMLAShowIf">always,True,bool,text=16:9</convert>\n\t\t</widget>' % (SVC, t, y))
	t += 70
	x.append(G.static("SNR", E(t, y, 50, 28), 20, "grey"))
	x.append(G.label("session.FrontendStatus", E(t + 52, y, 70, 28), [("FrontendInfo", "SNR")], 20, "grey"))
	x.append(G.label("session.FrontendStatus", E(t + 130, y, 110, 28), [("FrontendInfo", "SNRdB")], 20, "grey"))
	return [screen("SecondInfoBar", x), screen("SecondInfoBarSimple", x)]


# ------------------------------------------------------------------------------------------------ Channel Selection (§3.3)
def _selection_bar(skin, w, h):
	from PIL import Image
	name = "minimal_cs_sel_%dx%d.png" % (w, h)
	p = os.path.join(skin, G.FRAME_DIR, name)
	if not os.path.isfile(p):
		im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
		im.paste((0xF9, 0xC7, 0x31, 255), (0, 8, 4, h - 8))
		im.save(p)
	return "%s/%s" % (G.FRAME_DIR, name)


def channelselection(skin):
	import xml.etree.ElementTree as ET
	key = "config.plugins.cineviewmla.poster_channelselection"
	scr = G._classic_screen(skin, "channelselection", "ChannelSelection")
	la = [dict(w.attrib) for w in ET.fromstring(scr).iter("widget") if w.get("name") == "list"][0]
	src = "ServiceEvent"
	x = [box(0, 0, 820, 1080, SCRIM), box(820, 600, 1100, 130, EDGE), box(820, 730, 1100, 350, SCRIM),
		'\t\t<widget source="Title" render="Label" position="60,34" size="740,40" font="Regular;26" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />']
	la.update({"position": "56,90", "size": "744,900", "itemHeight": "50", "serviceItemHeight": "50", "serviceNumberFont": "Regular;21",
		"serviceNameFont": "Regular;25", "serviceInfoFont": "Regular;20", "selectionPixmap": _selection_bar(skin, 744, 50), "transparent": "1",
		"zPosition": "12", "colorServiceDescription": "grey", "colorServiceDescriptionFallback": "grey", "colorServiceDescriptionSelected": "foreground"})
	la.pop("backgroundColor", None)
	x.append('\t\t<widget name="list" %s />' % " ".join('%s="%s"' % (k, v) for k, v in la.items() if k != "name"))
	x += thumb(skin, src, 900, 750, 140, 210, key)
	for x0, inv in ((1070, ""), (900, ",Invert")):
		w = 1860 - x0
		x += text(src, [("EventName", "Name")], E(x0, 760, w, 44), 34, "foreground", key, inv, G.T_OPTS)
		x += [gate(t, key, inv) for t in G.times(src, E(x0, 810, 160, 30), 22, "secondFG")]
		x.append(gate(G.label(src, E(x0 + 176, 810, w - 176, 30), [("EventName", "Genre")], 22, "secondFG", ' noWrap="1"'), key, inv))
		x += text(src, [("EventName", "FullDescription")], E(x0, 850, w, 104), 21, "foreground", key, inv)
	x.append('\t\t<panel name="ButtonTemplate" />')
	return screen("ChannelSelection", x, ' position="fill" backgroundColor="transparent" title="Channel Selection"')


# ------------------------------------------------------------------------------------------------ EPG (§3.4)
def graphical(skin):
	import gen_epg as GE
	key = "config.plugins.cineviewmla.poster_epg"
	src = "Event"
	x = [box(0, 0, 1920, 1080, "steThemePrimary", -1)]
	x += thumb(skin, src, 60, 40, 110, 165, key)
	for x0, inv in ((196, ""), (60, ",Invert")):
		w = 1560 - x0
		x += text(src, [("EventName", "Name")], E(x0, 44, w, 44), 34, "foreground", key, inv, G.T_OPTS)
		x.append(gate(G.label("Service", E(x0, 92, 300, 30), [("ServiceName", "Name")], 22, "secondFG", ' noWrap="1"', 40), key, inv))
		x += [gate(t.replace('zPosition="20"', 'zPosition="40"'), key, inv) for t in G.times(src, E(x0 + 310, 92, 160, 30), 22, "secondFG")]
		x.append(gate(G.label(src, E(x0 + 480, 92, 140, 30), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 22, "secondFG", "", 40), key, inv))
		x += [t.replace('zPosition="20"', 'zPosition="40"') for t in text(src, [("EventName", "FullDescription")], E(x0, 128, 1860 - x0, 52), 21, "grey", key, inv)]
	x.append(G.label("global.CurrentTime", E(1600, 44, 260, 44), [("ClockToText", "Format:%H:%M")], 34, "grey", ' halign="right"', 40))
	x += GE.grid(E(60, 260, 1800, 700), E(60, 220, 1800, 36))
	x += GE.keys(980)
	return '\t<screen name="GraphicalEPG" position="0,0" size="1920,1080" flags="wfNoBorder" title="Graphical EPG">\n%s\n\t</screen>' % "\n".join(l for l in x if l)


# ------------------------------------------------------------------------------------------------ PVR (§3.5)
def _pvr_strip(skin, src, key):
	x = [box(60, 770, 1800, 1, "#60FFFFFF", 1)]
	x += thumb(skin, src, 60, 790, 110, 165, key)
	for x0, inv in ((196, ""), (60, ",Invert")):
		w = 1860 - x0
		x.append(gate('\t\t<widget source="%s" render="Label" position="%d,790" size="%d,44" font="Regular;34" foregroundColor="foreground" transparent="1" noWrap="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Name</convert>\n\t\t</widget>' % (src, x0, w), key, inv))
		x.append(gate('\t\t<widget source="%s" render="Label" position="%d,838" size="170,30" font="Regular;22" foregroundColor="secondFG" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceTime">StartTime</convert>\n\t\t\t<convert type="ClockToText">ShortDate</convert>\n\t\t</widget>' % (src, x0), key, inv))
		x.append(gate(G.label(src, E(x0 + 180, 838, 420, 30), [("MovieInfo", "RecordServiceName")], 22, "secondFG", ' noWrap="1"'), key, inv))
		x.append(gate('\t\t<widget source="%s" render="Label" position="%d,838" size="140,30" font="Regular;22" foregroundColor="secondFG" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceTime">Duration</convert>\n\t\t\t<convert type="ClockToText">AsLength</convert>\n\t\t</widget>' % (src, x0 + 610), key, inv))
		x += text(src, [("MovieInfo", "FullDescription")], E(x0, 876, w, 78), 21, "foreground", key, inv)
	return x


def movieselection(skin):
	key = "config.plugins.cineviewmla.poster_pvr"
	classic = G._classic_screen(skin, "pvr", "MovieSelection")
	lst = re.findall(r'<widget name="list" [^>]*/>', classic)[0]
	lst = EMC.clean_movielist(re.sub(r'position="[^"]*" size="[^"]*"', 'position="60,120" size="1800,640"', lst, count=1))
	x = [box(0, 0, 1920, 1080, "steThemePrimary", -4),
		'\t\t<widget source="Title" render="Label" position="60,40" size="1300,40" font="Regular;26" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />',
		G.label("global.CurrentTime", E(1600, 34, 260, 44), [("ClockToText", "Format:%H:%M")], 34, "grey", ' halign="right"'),
		'\t\t<widget name="movie_sort" pixmaps="icons/az.png,icons/newtop.png,icons/shuffle.png,icons/za.png,icons/oldtop.png,icons/faz.png,icons/fza.png,icons/default.png,icons/azold.png,icons/zanew.png,icons/longest.png,icons/shortest.png,icons/dtsrt.png,icons/dtsdt.png" position="1460,44" zPosition="5" size="52,30" transparent="1" alphatest="on" />',
		'\t\t<widget name="movie_off" pixmaps="icons/ask.png,icons/movielist.png,icons/quit.png,icons/pause.png,icons/playlist.png,icons/playlistquit.png,icons/loop.png,icons/rep.png" position="1520,44" zPosition="5" size="52,30" transparent="1" alphatest="on" />',
		'\t\t<widget name="waitingtext" position="60,120" size="1800,640" font="Regular;33" halign="center" valign="center" transparent="1" zPosition="4" />',
		'\t\t<widget name="chosenletter" position="60,120" size="1800,640" foregroundColor="secondFG" font="Regular;112" halign="center" valign="center" transparent="1" zPosition="4" />',
		"\t\t" + lst.strip(),
		'\t\t<widget name="DescriptionBorder" position="0,0" size="0,0" />']
	x += _pvr_strip(skin, "Service", key)
	x.append('\t\t<widget name="freeDiskSpace" position="60,1000" size="700,30" foregroundColor="grey" font="Regular;20" transparent="1" zPosition="20" />')
	x.append('\t\t<widget name="TrashcanSize" position="760,1000" size="300,30" foregroundColor="grey" font="Regular;20" transparent="1" zPosition="20" />')
	x.append('\t\t<panel name="ButtonTemplate" />')
	return '\t<screen name="MovieSelection" title="Movie Selection" position="fill" backgroundColor="steThemePrimary" flags="wfNoBorder">\n%s\n\t</screen>' % "\n".join(l for l in x if l)


def emcselection(skin):
	key = "config.plugins.cineviewmla.poster_pvr"
	x = [box(0, 0, 1920, 1080, "steThemePrimary", -4),
		'\t\t<widget source="Title" render="Label" position="60,40" size="1300,40" font="Regular;26" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />',
		G.label("global.CurrentTime", E(1600, 34, 260, 44), [("ClockToText", "Format:%H:%M")], 34, "grey", ' halign="right"'),
		'\t\t<widget name="wait" position="60,120" size="1800,640" font="Regular;33" halign="center" valign="center" transparent="1" zPosition="4" />',
		EMC.emc_list(60, 120, 1800, 640, 50, 28, 24)]
	x += EMC.emc_cover_under(1880, 1040, 2, 2)
	x += _pvr_strip(skin, "Service", key)
	x.append('\t\t<widget source="spacefree" render="Label" position="60,976" size="560,30" foregroundColor="grey" font="Regular;20" transparent="1" zPosition="20" />')
	x += EMC.emc_keys(1018, 640, 300, 22)
	return '\t<screen name="EMCSelection" title="EMC" position="fill" backgroundColor="steThemePrimary" flags="wfNoBorder">\n%s\n\t</screen>' % "\n".join(l for l in x if l)


# ------------------------------------------------------------------------------------------------ EventView (§3.6)
def eventview(skin, name, on, live=False):
	key = "config.plugins.cineviewmla.poster_eventview"
	x = [box(0, 0, 1920, 1080, SCRIM, -4)]
	if on:
		x += thumb(skin, "Event", 360, 120, 200, 300, key)
		tx, dy, dh = 590, 450, 13 * 32
	else:
		tx, dy, dh = 360, 290, 18 * 32
	tw = 1560 - tx
	x.append('\t\t<widget name="channel" position="%d,124" size="400,32" font="Regular;24" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />' % tx)
	x.append('\t\t<widget name="datetime" position="%d,124" size="420,32" font="Regular;24" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />' % (tx + 410))
	x.append('\t\t<widget name="duration" position="%d,124" size="%d,32" font="Regular;24" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />' % (tx + 840, max(80, tw - 840)))
	x.append('\t\t<widget source="Title" render="Label" position="%d,164" size="%d,112" font="Regular;46" foregroundColor="foreground" transparent="1" zPosition="20" />' % (tx, tw))
	x.append('\t\t<widget name="FullDescription" position="360,%d" size="1200,%d" font="Regular;24" foregroundColor="foreground" backgroundColor="steThemeOverlay" transparent="1" zPosition="20" />' % (dy, dh))
	if live:
		x.append('\t\t<widget source="%s" render="Label" position="360,960" size="70,32" font="Regular;24" foregroundColor="grey" transparent="1" zPosition="20">\n\t\t\t<convert type="EventName">Name</convert>\n\t\t\t<convert type="CineViewMLAShowIf">always,True,text=NEXT</convert>\n\t\t</widget>' % NXT)
		x.append(G.label(NXT, E(436, 960, 80, 32), [("EventTime", "StartTime"), ("ClockToText", "Format:%H:%M")], 24, "grey"))
		x += text(NXT, [("EventName", "Name")], E(526, 960, 1034, 32), 24, "grey", None, "", G.H_OPTS)
	x.append(KEYS % (22, "360,1010", "1200,38"))
	return screen(name, x, ' position="fill" backgroundColor="transparent" title="Event View"')


def infobar_eventview(skin, name, on):
	key = "config.plugins.cineviewmla.poster_eventview"
	x = [box(0, 0, 1920, 360, SCRIM, -4)]
	if on:
		x += thumb(skin, "Event", 60, 40, 140, 210, key)
	tx = 230 if on else 60
	tw = 1860 - tx
	x.append('\t\t<widget name="datetime" position="%d,40" size="420,30" font="Regular;22" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />' % tx)
	x.append('\t\t<widget name="duration" position="%d,40" size="200,30" font="Regular;22" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />' % (tx + 430))
	x.append('\t\t<widget source="Title" render="Label" position="%d,74" size="%d,52" font="Regular;40" foregroundColor="foreground" transparent="1" noWrap="1" zPosition="20" />' % (tx, tw))
	x.append('\t\t<widget name="FullDescription" position="%d,136" size="%d,168" font="Regular;23" foregroundColor="foreground" backgroundColor="steThemeOverlay" transparent="1" zPosition="20" />' % (tx, tw))
	x.append(KEYS % (20, "%d,314" % tx, "%d,34" % tw))
	return '\t<screen name="%s" position="0,0" size="1920,360" flags="wfNoBorder" title="Event View">\n%s\n\t</screen>' % (name, "\n".join(l for l in x if l))


# ------------------------------------------------------------------------------------------------ packs
def _write(skin, section, parts, provides):
	d = os.path.join(skin, "layouts", section, "minimal")
	os.makedirs(d, exist_ok=True)
	p = os.path.join(d, "screens.openatv.xml")
	open(p, "w", encoding="utf-8").write('<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Minimal (%s) — generated by tools/mla/p10models/gen_minimal.py. Prototype, look pending approval. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % (section, "\n".join("\t" + q.strip() for q in parts)))
	json.dump({"schema": 1, "id": "minimal", "section": section, "name": "CineView Minimal", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "docs/mla/Minimal_Spec.md (prototype; look pending approval)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}}, "provides_screens": provides,
		"options": [], "preview": "preview.png"}, open(os.path.join(d, "manifest.json"), "w"), indent=1)
	import xml.etree.ElementTree as ET
	r = ET.parse(p).getroot()
	for scr in r.iter("screen"):
		for el in scr.iter():
			ps, ss = el.get("position"), el.get("size")
			if ps and ss and "," in ps and not ps.startswith(("c", "e")) and ps != "fill" and not ss.startswith("e"):
				px, py = (int(v) for v in ps.split(","))
				w, h = (int(v) for v in ss.split(","))
				assert 0 <= px and px + w <= 1920 and 0 <= py and py + h <= 1080, (section, scr.get("name"), el.attrib)
	return d


def _keep(skin, section, names, skip):
	parts, prov = [], []
	src = open(os.path.join(skin, "layouts", section, "classic", "screens.openatv.xml"), encoding="utf-8").read()
	for n in re.findall(r'<screen name="([^"]+)"', src):
		if n in skip or (names and n not in names):
			continue
		parts.append(G._classic_screen(skin, section, n))
		prov.append(n)
	return parts, prov


def generate(skin):
	made = []
	p, v = _keep(skin, "infobar", None, ("InfoBar",))
	made.append(_write(skin, "infobar", [infobar(skin)] + p, ["InfoBar"] + v))
	p, v = _keep(skin, "secondinfobar", None, ("SecondInfoBar", "SecondInfoBarSimple"))
	made.append(_write(skin, "secondinfobar", secondinfobar(skin) + p, ["SecondInfoBar", "SecondInfoBarSimple"] + v))
	p, v = _keep(skin, "channelselection", None, ("ChannelSelection",))
	made.append(_write(skin, "channelselection", [channelselection(skin)] + p, ["ChannelSelection"] + v))
	p, v = _keep(skin, "epg", None, ("GraphicalEPG",))
	made.append(_write(skin, "epg", [graphical(skin)] + p, ["GraphicalEPG"] + v))
	p, v = _keep(skin, "pvr", None, ("MovieSelection",))
	made.append(_write(skin, "pvr", [movieselection(skin), emcselection(skin)] + p, ["MovieSelection", "EMCSelection"] + v))
	ev = [eventview(skin, "EventView", True, True), eventview(skin, "EventView_CVPosterOff", False, True),
		eventview(skin, "EventViewSimple", True), eventview(skin, "EventViewSimple_CVPosterOff", False),
		infobar_eventview(skin, "InfoBarEventView", True), infobar_eventview(skin, "InfoBarEventView_CVPosterOff", False)]
	p, v = _keep(skin, "eventview", None, ("EventView", "EventViewSimple", "InfoBarEventView", "EventViewSimple_CVPosterOff", "InfoBarEventView_CVPosterOff"))
	made.append(_write(skin, "eventview", ev + p, ["EventView", "EventView_CVPosterOff", "EventViewSimple", "EventViewSimple_CVPosterOff", "InfoBarEventView", "InfoBarEventView_CVPosterOff"] + v))
	return made


if __name__ == "__main__":
	print(generate(sys.argv[1]))
