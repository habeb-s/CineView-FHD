#!/usr/bin/env python3
"""Generate the EPG layout pack "graphicalplus" (Graphical Plus, user-approved for implementation 2026-10-04 22:06)
from spec_epg.py.  Only the GraphicalEPG screen is new; every other EPG screen is Classic's.

Contract (enigma2 57b7a51, verified in source):
* GraphicalEPG: named widgets list (EPGList graph), timeline_text, timeline0..5 / timeline_now (pixmaps the code
  positions), lab1, bouquetlist, date; sources Event / Service (the HIGHLIGHTED cell), key_red..key_blue, Title.
* The visible time span is the user's setting config.epgselection.graph_prevtimeperiod (default 180 min) and the
  row count config.epgselection.graph_itemsperpage (default 8): the skin sets only the grid box.
* Posters OFF: the grid is a NAMED widget, its size cannot follow a converter, so the posters-off geometry is a
  second screen "GraphicalEPG_CVPosterOff" that the CineView MLA plugin puts first in the skinName list while
  config.plugins.cineviewmla.poster_epg is False (same proven mechanism as SecondInfoBarECM / EventViewSimple).
usage (from build.py): generate(skin_dir) -> list of created pack dirs
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "p7"))
import spec_epg as SP  # noqa: E402
import gen_details as G  # noqa: E402

KEY = "config.plugins.cineviewmla.poster_epg"
SRC = "Event"


def E(t):
	return {"x": t[0], "y": t[1], "w": t[2], "h": t[3]}


def keys(y=980):
	out = []
	for i, (k, col) in enumerate((("key_red", "#00a00000"), ("key_green", "#00008000"), ("key_yellow", "#00a08000"), ("key_blue", "#000040a0"))):
		x = 40 + i * 460
		out.append('\t\t<eLabel position="%d,%d" size="8,%d" backgroundColor="%s" zPosition="31" />' % (x, y + 10, 40, col))
		out.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="%d,%d" font="Regular;26" valign="center" foregroundColor="foreground" transparent="1" zPosition="40" noWrap="1" />' % (k, x + 22, y, 420, 60))
	return out


def grid(g, t):
	"""Native grid + its helper widgets on the grid box g and timeline box t (Classic attributes)."""
	gx, gy, gw, gh = g["x"], g["y"], g["w"], g["h"]
	out = ['\t\t<widget name="timeline_text" position="%d,%d" size="%d,%d" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="40" />' % (t["x"], t["y"], t["w"], t["h"]),
		'\t\t<widget name="lab1" position="%d,%d" size="%d,%d" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="20" />' % (gx, gy, gw, gh),
		'\t\t<widget name="bouquetlist" position="%d,%d" size="%d,%d" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15" />' % (gx, gy, gw, gh),
		'\t\t<widget name="list" position="%d,%d" size="%d,%d" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10" EntryBackgroundColor="steEpgCell" EntryBackgroundColorPast="steEpgCell" ServiceBackgroundColor="steEpgCell" TimeBackgroundColor="steEpgCell" />' % (gx, gy, gw, gh)]
	for i in range(6):
		out.append('\t\t<widget name="timeline%d" pixmap="window/timeline.png" position="0,%d" size="1,%d" zPosition="22" />' % (i, gy, gh))
	out.append('\t\t<widget name="timeline_now" position="6,%d" size="4,%d" zPosition="21" pixmap="window/timeline-now.png" alphatest="blend" />' % (gy, gh))
	return out


def header():
	t = E(SP.HEADER["title"])
	d = E(SP.HEADER["date"])
	c = E(SP.HEADER["clock"])
	return ['\t\t<widget source="Title" render="Label" %s font="Regular;%d" foregroundColor="secondFG" transparent="1" zPosition="40" noWrap="1" />' % (G.pos(t), SP.HEADER["title"][4]),
		# no named "date" widget: EPGSelection creates self["date"] only for some EPG types (device t37: SkinError
		# 'date' not found in GraphicalEPG) -> the date comes from the clock source
		G.label("global.CurrentTime", d, [("ClockToText", "Format:%a %d %b")], SP.HEADER["date"][4], "grey", ' halign="right"', 40),
		G.label("global.CurrentTime", c, [("ClockToText", "Format:%H:%M")], SP.HEADER["clock"][4], "foreground", ' halign="right"', 40)]


def panel_texts(L, poster_on):
	f = lambda k: L[k][4]
	e = lambda k: E(L[k])
	out = []
	out.append(G.label("Service", e("ch_name"), [("ServiceName", "Name")], f("ch_name"), "grey", ' noWrap="1"', 40))
	out += G.text_variants(SRC, [("EventName", "Name")], e("title"), None, f("title"), "foreground", G.T_OPTS, KEY)
	out += G.times(SRC, e("times"), f("times"), "secondFG")
	out.append(G.label(SRC, e("duration"), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], f("duration"), "grey", "", 40))
	out.append(G.label(SRC, e("genre"), [("EventName", "Genre")], f("genre"), "grey", ' noWrap="1"', 40))
	out.append(G.label(SRC, dict(e("rating"), w=120), [("CineViewMLAIMDb", "Plain,hide")], f("rating"), "foreground", "", 40))
	out.append(G.label(SRC, dict(e("rating"), x=e("rating")["x"] + 124, w=e("rating")["w"] - 124), [("CineViewMLAIMDb", "Stars,hide")], f("rating") - 2, "secondFG", "", 40))
	out += G.text_variants(SRC, [("EventName", "FullDescription")], e("desc"), None, f("desc"), "foreground", G.D_OPTS, KEY, halign=' halign="block"' if poster_on else "")
	return out


def graphical(skin, on):
	sp = SP.GRAPHICAL_PLUS
	L = sp["posters_on" if on else "posters_off"]
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="-1" />']
	x += header()
	x += grid(E(L["grid"]), E(L["timeline"]))
	x.append(G.box(E(L["panel"]), "steThemePanel", 1))
	if on:
		x += G.poster(skin, SRC, E(L["poster"]), KEY)
		x.append('\t\t<widget source="Service" render="Picon" %s alphatest="blend" scale="aspect" transparent="1" zPosition="40">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % G.pos(E(L["ch_picon"])))
	x += panel_texts(L, on)
	x.append('\t\t<eLabel position="40,964" size="1840,2" backgroundColor="steThemePanelAlt" zPosition="30" />')
	x += keys()
	name = "GraphicalEPG" if on else "GraphicalEPG_CVPosterOff"
	return '\t<screen name="%s" position="0,0" size="1920,1080" flags="wfNoBorder" title="Graphical EPG">\n%s\n\t</screen>' % (name, "\n".join(l for l in x if l))


def generate(skin):
	src = open(os.path.join(skin, "layouts", "epg", "classic", "screens.openatv.xml"), encoding="utf-8").read()
	names = re.findall(r'<screen name="([^"]+)"', src)
	parts = [graphical(skin, True), graphical(skin, False)]
	keep = []
	for n in names:
		if n in ("GraphicalEPG",):
			continue
		m = re.search(r'\t?<screen name="%s".*?</screen>' % re.escape(n), src, re.S)
		keep.append(n)
		parts.append(m.group(0) if m.group(0).startswith("\t") else "\t" + m.group(0))
	d = os.path.join(skin, "layouts", "epg", "graphicalplus")
	os.makedirs(d, exist_ok=True)
	xml = '<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Graphical Plus (EPG) — generated by tools/mla/p9epg/gen_epg.py from spec_epg.py. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % "\n".join(parts)
	open(os.path.join(d, "screens.openatv.xml"), "w", encoding="utf-8").write(xml)
	json.dump({"schema": 1, "id": "graphicalplus", "section": "epg", "name": "CineView Graphical Plus", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "tools/mla/p9epg/spec_epg.py (user approval to implement 2026-10-04 22:06)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}},
		"provides_screens": ["GraphicalEPG", "GraphicalEPG_CVPosterOff"] + keep, "options": [], "preview": "preview.png"},
		open(os.path.join(d, "manifest.json"), "w"), indent=1)
	import xml.etree.ElementTree as ET
	r = ET.parse(os.path.join(d, "screens.openatv.xml")).getroot()
	for scr in r.iter("screen"):
		if not scr.get("name", "").startswith("GraphicalEPG"):
			continue
		for el in scr.iter():
			p, s = el.get("position"), el.get("size")
			if p and s and "," in p and not p.startswith(("c", "e")):
				px, py = (int(v) for v in p.split(","))
				w, h = (int(v) for v in s.split(","))
				assert 0 <= px and px + w <= 1920 and 0 <= py and py + h <= 1080, (scr.get("name"), el.attrib)
	return [d]


if __name__ == "__main__":
	print(generate(sys.argv[1]))
