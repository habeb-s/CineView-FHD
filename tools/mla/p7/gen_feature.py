#!/usr/bin/env python3
"""EventView pack "feature" — Cinema EventView Feature (Five_Models_Plan.md §4; look pending the user's approval).

Cinema family (same language as the Cinema SecondInfoBar): dimmed picture, big poster on the left, title 56,
times / duration / genre / IMDb in one muted row, the description in the NATIVE ScrollLabel "FullDescription"
(paging stays native), channel at the top, coloured-key captions in a bottom band (native ColorButtonsSequence,
only captioned keys).

Contract (Screens/EventView.py 57b7a51, verified): EventViewBase widgets Service / Event sources, Title,
FullDescription / epg_description (ScrollLabel), datetime / channel / duration (Labels), key_red..key_blue.
EventViewSimple, EventViewEPGSelect (live INFO: skinName ["EventView"]) and InfoBarEventView all derive from it, so
every screen of the pack uses the named widgets; nothing comes from session.Event_Now.
Posters OFF: '<name>_CVPosterOff' screens (no poster, the text column starts at the left edge), selected by the
CineView MLA plugin (EventViewSimple, InfoBarEventView, EPG-opened EventView; live EventView since this change).
usage (build.py): generate(skin) -> [pack dir]"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_details as G  # noqa: E402

KEY = "config.plugins.cineviewmla.poster_eventview"
KEYS = '\t\t<widget addon="ColorButtonsSequence" connection="key_red,key_green,key_yellow,key_blue" textColors="key_red:#00a00000,key_green:#00008000,key_yellow:#00a08000,key_blue:#000040a0" renderType="ColorTextOver" buttonCornerRadius="8" layoutStyle="fluid" alignment="left" foregroundColor="#00ffffff" font="Regular;%d" position="%s" size="%s" spacing="12" transparent="1" zPosition="40" />'


def full(skin, name, on):
	"""EventView / EventViewSimple: full screen."""
	# all plain eLabels BELOW z 0: the native ScrollLabel draws its text label at the default z (device t59/t64: with
	# the dim layer at z 1 the whole description was hidden)
	x = [G.box({"x": 0, "y": 0, "w": 1920, "h": 1080}, "steThemeOverlay", -4)]
	tx = 530 if on else 90
	tw = 1830 - tx
	if on:
		x += G.poster(skin, "Event", {"x": 90, "y": 110, "w": 400, "h": 600}, KEY)
	x.append('\t\t<widget name="channel" position="%d,112" size="%d,36" font="Regular;24" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />' % (tx, tw))
	x.append('\t\t<widget source="Title" render="Label" position="%d,152" size="%d,134" font="Regular;56" foregroundColor="foreground" transparent="1" zPosition="20" />' % (tx, tw))
	x.append('\t\t<widget name="datetime" position="%d,300" size="440,38" font="Regular;27" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />' % tx)
	x.append('\t\t<widget name="duration" position="%d,300" size="200,38" font="Regular;27" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />' % (tx + 450))
	x.append(G.label("Event", {"x": tx + 660, "y": 300, "w": tw - 660 - 260, "h": 38}, [("EventName", "Genre")], 27, "grey", ' noWrap="1"'))
	x.append(G.label("Event", {"x": tx + tw - 250, "y": 300, "w": 130, "h": 38}, [("CineViewMLAIMDb", "Plain,hide")], 27, "foreground", ' halign="right"'))
	x.append(G.label("Event", {"x": tx + tw - 110, "y": 302, "w": 110, "h": 38}, [("CineViewMLAIMDb", "Stars,hide")], 22, "secondFG", ' halign="right"'))
	x.append(G.box({"x": tx, "y": 352, "w": tw, "h": 2}, "#00444444", -1))
	x.append('\t\t<widget name="FullDescription" position="%d,374" size="%d,540" font="Regular;27" foregroundColor="foreground" backgroundColor="steThemePanel" transparent="1" zPosition="20" />' % (tx, tw))
	x.append(G.box({"x": 0, "y": 960, "w": 1920, "h": 120}, "steThemePanelAlt", -2))
	x.append(KEYS % (26, "90,995", "1740,46"))
	title = "Event View"
	return G.screen(name, title, [l for l in x if l])


def infobar(skin, name, on):
	"""InfoBarEventView: top band over the InfoBar EPG (Classic 1920x360 band; Feature 1920x420)."""
	x = [G.box({"x": 0, "y": 0, "w": 1920, "h": 420}, "steThemeOverlay", -4)]
	tx = 300 if on else 60
	tw = 1860 - tx
	if on:
		x += G.poster(skin, "Event", {"x": 60, "y": 40, "w": 210, "h": 315}, KEY)
	x.append('\t\t<widget source="Title" render="Label" position="%d,34" size="%d,60" font="Regular;44" foregroundColor="foreground" transparent="1" noWrap="1" zPosition="20" />' % (tx, tw))
	x.append('\t\t<widget name="datetime" position="%d,102" size="440,34" font="Regular;25" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />' % tx)
	x.append('\t\t<widget name="duration" position="%d,102" size="190,34" font="Regular;25" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />' % (tx + 450))
	x.append(G.label("Event", {"x": tx + 650, "y": 102, "w": tw - 650 - 250, "h": 34}, [("EventName", "Genre")], 25, "grey", ' noWrap="1"'))
	x.append(G.label("Event", {"x": tx + tw - 240, "y": 102, "w": 130, "h": 34}, [("CineViewMLAIMDb", "Plain,hide")], 25, "foreground", ' halign="right"'))
	x.append(G.label("Event", {"x": tx + tw - 100, "y": 104, "w": 100, "h": 34}, [("CineViewMLAIMDb", "Stars,hide")], 21, "secondFG", ' halign="right"'))
	x.append('\t\t<widget name="FullDescription" position="%d,148" size="%d,212" font="Regular;25" foregroundColor="foreground" backgroundColor="steThemePanel" transparent="1" zPosition="20" />' % (tx, tw))
	x.append(KEYS % (22, "%d,372" % tx, "%d,36" % tw))
	return '\t<screen name="%s" position="0,0" size="1920,420" flags="wfNoBorder" title="Event View">\n%s\n\t</screen>' % (name, "\n".join(l for l in x if l))


def generate(skin):
	src = open(os.path.join(skin, "layouts", "eventview", "classic", "screens.openatv.xml"), encoding="utf-8").read()
	parts = []
	for base in ("EventView", "EventViewSimple"):
		parts.append(full(skin, base, True))
		parts.append(full(skin, base + "_CVPosterOff", False))
	parts.append(infobar(skin, "InfoBarEventView", True))
	parts.append(infobar(skin, "InfoBarEventView_CVPosterOff", False))
	provides = ["EventView", "EventView_CVPosterOff", "EventViewSimple", "EventViewSimple_CVPosterOff", "InfoBarEventView", "InfoBarEventView_CVPosterOff"]
	m = re.search(r'\t?<screen name="EventViewContextMenu".*?</screen>', src, re.S)
	if m:
		parts.append("\t" + m.group(0).strip())
		provides.append("EventViewContextMenu")
	d = os.path.join(skin, "layouts", "eventview", "feature")
	os.makedirs(d, exist_ok=True)
	p = os.path.join(d, "screens.openatv.xml")
	open(p, "w", encoding="utf-8").write('<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Cinema — EventView Feature, generated by tools/mla/p7/gen_feature.py. Look pending approval. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % "\n".join(parts))
	json.dump({"schema": 1, "id": "feature", "section": "eventview", "name": "CineView Feature", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "docs/mla/Five_Models_Plan.md §4 (Cinema model, look pending approval)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}}, "provides_screens": provides,
		"options": [], "preview": "preview.png"}, open(os.path.join(d, "manifest.json"), "w"), indent=1)
	import xml.etree.ElementTree as ET
	r = ET.parse(p).getroot()
	for scr in r.iter("screen"):
		for el in scr.iter():
			ps, ss = el.get("position"), el.get("size")
			if ps and ss and "," in ps and not ps.startswith(("c", "e")) and ps != "fill":
				px, py = (int(v) for v in ps.split(","))
				w, h = (int(v) for v in ss.split(","))
				assert 0 <= px and px + w <= 1920 and 0 <= py and py + h <= 1080, (scr.get("name"), el.attrib)
	return [d]


if __name__ == "__main__":
	print(generate(sys.argv[1]))
