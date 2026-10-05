#!/usr/bin/env python3
"""EventView pack "detailscard" — Details EventView Card (Five_Models_Plan.md §4: the Details model's own EventView;
look pending approval).

Details language (same as the Details InfoBar / SecondInfoBar / Poster List / Cover Library): an opaque panel card
with Classic's grey top frame line, the poster with the 3-px #505050 frame, muted metadata row, separators #444444.
Unlike the Cinema Feature (full-screen scrim over the picture, huge title) it is a framed card over the picture.

Contract: identical to gen_feature.py (Screens/EventView.py 57b7a51, verified): named widgets channel / datetime /
duration / FullDescription (native ScrollLabel; paging stays native) + Title, sources Event / Service,
key_red..key_blue through the native ColorButtonsSequence (only captioned keys are drawn).
Every plain eLabel is BELOW z 0: the ScrollLabel draws its text at the default z (device t64: a dim layer at z 1 hid
the description).  No picon: an EventView picon needs a Service-source Picon and the card already names the channel.
Posters OFF: '<name>_CVPosterOff' (no poster, text from the card's left edge; CineView MLA plugin).
usage (build.py): generate(skin) -> [pack dir]"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_details as G  # noqa: E402
from gen_feature import KEYS, KEY  # noqa: E402


def full(skin, name, on):
	x = [G.box({"x": 120, "y": 90, "w": 1680, "h": 880}, "steThemePanel", -4),
		G.box({"x": 120, "y": 90, "w": 1680, "h": 3}, "#007c7c7c", -3),
		'\t\t<widget name="channel" position="160,110" size="1200,40" font="Regular;27" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />',
		G.label("global.CurrentTime", {"x": 1500, "y": 110, "w": 260, "h": 40}, [("ClockToText", "Format:%H:%M")], 30, "foreground", ' halign="right"'),
		G.box({"x": 160, "y": 162, "w": 1600, "h": 2}, "#00444444", -1)]
	tx = 500 if on else 160
	tw = 1760 - tx
	if on:
		x += G.poster(skin, "Event", {"x": 160, "y": 196, "w": 300, "h": 450}, KEY)
	x.append('\t\t<widget source="Title" render="Label" position="%d,190" size="%d,116" font="Regular;46" foregroundColor="foreground" transparent="1" zPosition="20" />' % (tx, tw))
	x.append('\t\t<widget name="datetime" position="%d,318" size="440,36" font="Regular;26" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />' % tx)
	x.append('\t\t<widget name="duration" position="%d,318" size="190,36" font="Regular;26" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />' % (tx + 450))
	x.append(G.label("Event", {"x": tx + 650, "y": 318, "w": tw - 650 - 250, "h": 36}, [("EventName", "Genre")], 26, "grey", ' noWrap="1"'))
	x.append(G.label("Event", {"x": tx + tw - 240, "y": 318, "w": 130, "h": 36}, [("CineViewMLAIMDb", "Plain,hide")], 26, "foreground", ' halign="right"'))
	x.append(G.label("Event", {"x": tx + tw - 100, "y": 320, "w": 100, "h": 36}, [("CineViewMLAIMDb", "Stars,hide")], 21, "secondFG", ' halign="right"'))
	x.append(G.box({"x": tx, "y": 368, "w": tw, "h": 2}, "#00444444", -1))
	x.append('\t\t<widget name="FullDescription" position="%d,386" size="%d,486" font="Regular;27" foregroundColor="foreground" backgroundColor="steThemePanel" transparent="1" zPosition="20" />' % (tx, tw))
	x.append(G.box({"x": 120, "y": 892, "w": 1680, "h": 78}, "steThemePanelAlt", -2))
	x.append(KEYS % (25, "160,908", "1600,46"))
	return G.screen(name, "Event View", [l for l in x if l])


def infobar(skin, name, on):
	"""InfoBarEventView: a framed band at the top of the picture (Classic 1920x360; card 1920x400)."""
	x = [G.box({"x": 0, "y": 0, "w": 1920, "h": 400}, "steThemePanel", -4),
		G.box({"x": 0, "y": 397, "w": 1920, "h": 3}, "#007c7c7c", -3)]
	tx = 290 if on else 60
	tw = 1860 - tx
	if on:
		x += G.poster(skin, "Event", {"x": 60, "y": 34, "w": 200, "h": 300}, KEY)
	x.append('\t\t<widget source="Title" render="Label" position="%d,30" size="%d,56" font="Regular;40" foregroundColor="foreground" transparent="1" noWrap="1" zPosition="20" />' % (tx, tw))
	x.append('\t\t<widget name="datetime" position="%d,94" size="440,34" font="Regular;25" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />' % tx)
	x.append('\t\t<widget name="duration" position="%d,94" size="190,34" font="Regular;25" foregroundColor="grey" transparent="1" noWrap="1" zPosition="20" />' % (tx + 450))
	x.append(G.label("Event", {"x": tx + 650, "y": 94, "w": tw - 650 - 250, "h": 34}, [("EventName", "Genre")], 25, "grey", ' noWrap="1"'))
	x.append(G.label("Event", {"x": tx + tw - 240, "y": 94, "w": 130, "h": 34}, [("CineViewMLAIMDb", "Plain,hide")], 25, "foreground", ' halign="right"'))
	x.append(G.label("Event", {"x": tx + tw - 100, "y": 96, "w": 100, "h": 34}, [("CineViewMLAIMDb", "Stars,hide")], 21, "secondFG", ' halign="right"'))
	x.append(G.box({"x": tx, "y": 136, "w": tw, "h": 2}, "#00444444", -1))
	x.append('\t\t<widget name="FullDescription" position="%d,148" size="%d,196" font="Regular;25" foregroundColor="foreground" backgroundColor="steThemePanel" transparent="1" zPosition="20" />' % (tx, tw))
	x.append(KEYS % (22, "%d,352" % tx, "%d,36" % tw))
	return '\t<screen name="%s" position="0,0" size="1920,400" flags="wfNoBorder" title="Event View">\n%s\n\t</screen>' % (name, "\n".join(l for l in x if l))


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
	d = os.path.join(skin, "layouts", "eventview", "detailscard")
	os.makedirs(d, exist_ok=True)
	p = os.path.join(d, "screens.openatv.xml")
	open(p, "w", encoding="utf-8").write('<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Details — EventView Card, generated by tools/mla/p7/gen_details_ev.py. Look pending approval. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % "\n".join(parts))
	json.dump({"schema": 1, "id": "detailscard", "section": "eventview", "name": "CineView Details Card", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "docs/mla/Five_Models_Plan.md §4 (Details model, look pending approval)",
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
