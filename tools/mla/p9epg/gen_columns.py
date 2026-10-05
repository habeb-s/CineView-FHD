#!/usr/bin/env python3
"""Generate the EPG layout pack "columns" (Columns on the native vertical EPG; user decision 2026-10-05 05:23:
finish the study, then build it if it proves compatible with OpenATV — t42: compatible).  Only the EPGvertical
screen is new; every other EPG screen (EPGverticalPIG included) is Classic's.

Contract (enigma2 57b7a51, verified in source Screens/EpgSelection.py + Components/EpgList.py):
* EPGvertical (vertical_pig off): Fields = 6 -> five columns.  Named widgets list1..list5 (EPGList vertical),
  currCh1..5 / Active1..5 (Labels), sources piconCh1..5 (ServiceEvent), Event / Service (selected event),
  key_red..key_blue, Title, bouquetlist.
* self["list"] is a MenuList used ONLY as the page index: native contract zero width, z=-10, height =
  itemHeight x (Fields-1) (receiver skin_default "DO NOT CHANGE THIS LINE"; build37 / t42).
* Row height = list height / config.epgselection.vertical_itemsperpage (user setting): the skin sets the box
  and the fonts (EventFontVertical / TimeFontVertical), nothing else.
* Posters OFF: only the event card changes (source widgets) -> CineViewMLAShowIf variants, one screen.
usage (from build.py): generate(skin_dir) -> list of created pack dirs"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "p7"))
import spec_epg as SP  # noqa: E402
import gen_details as G  # noqa: E402
import gen_epg as GE  # noqa: E402

KEY = GE.KEY
SRC = "Event"


def columns_screen(skin):
	c = SP.COLUMNS
	hy, hh = c["col_head"]
	ly, lh = c["col_list"]
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="-1" />']
	x += GE.header()
	x.append('\t\t<widget name="bouquetlist" position="40,%d" size="1840,%d" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="30" />' % (hy, ly + lh - hy))
	x.append('\t\t<widget name="list" position="0,0" size="0,%d" itemHeight="%d" font="Regular;0" enableWrapAround="0" zPosition="-10" />' % (c["row_h"] * 5, c["row_h"]))
	for i in range(5):
		cx = 40 + i * (c["col_w"] + c["col_gap"])
		w = c["col_w"]
		n = i + 1
		x.append('\t\t<eLabel position="%d,%d" size="%d,%d" backgroundColor="steThemePanel" zPosition="0" />' % (cx, hy, w, ly + lh - hy))
		x.append('\t\t<widget name="Active%d" position="%d,%d" size="%d,%d" backgroundColor="selectedBG" transparent="0" zPosition="2" />' % (n, cx, hy, w, hh))
		x.append('\t\t<widget source="piconCh%d" render="Picon" position="%d,%d" size="100,50" zPosition="4" alphatest="blend" scale="aspect" transparent="1">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % (n, cx + 10, hy + 11))
		x.append('\t\t<widget name="currCh%d" position="%d,%d" size="%d,%d" font="Regular;26" valign="center" noWrap="1" foregroundColor="foreground" transparent="1" zPosition="5" />' % (n, cx + 122, hy, w - 132, hh))
		x.append('\t\t<widget name="list%d" position="%d,%d" size="%d,%d" backgroundColor="steThemePanel" scrollbarMode="showNever" transparent="1" zPosition="3" EventFontVertical="Regular;24" TimeFontVertical="Regular;20" TimeForegroundColor="secondFG" EntryBackgroundColorSelected="selectedBG" />' % (n, cx, ly, w, lh))
	# event card (selected event): poster ON / OFF through the switch
	cd = c["posters_on"]
	card = GE.E(cd["card"])
	x.append(G.box(card, "steThemePanel", 1))
	x += G.poster(skin, SRC, GE.E(cd["poster"]), KEY)
	for L, inv in ((c["posters_on"], ""), (c["posters_off"], ",Invert")):
		sh = '\t<convert type="CineViewMLAShowIf">%s,True%s</convert>\n\t\t</widget>' % (KEY, inv)
		t = GE.E(L["title"])
		for w in G.text_variants(SRC, [("EventName", "Name")], t, None, L["title"][4], "foreground", G.H_OPTS, "always"):
			x.append(w.replace('CineViewMLAShowIf">always,True,', 'CineViewMLAShowIf">%s,True%s,' % (KEY, inv)).replace('zPosition="20"', 'zPosition="40"'))
		m = GE.E(L["meta"])
		x.append(G.label("Service", dict(m, w=360), [("ServiceName", "Name")], L["meta"][4], "grey", ' noWrap="1"', 40).replace("</widget>", sh))
		x.append(G.label(SRC, dict(m, x=m["x"] + 370, w=m["w"] - 370 - 260), [("EventName", "Genre")], L["meta"][4], "grey", ' noWrap="1"', 40).replace("</widget>", sh))
		x.append(G.label(SRC, dict(m, x=m["x"] + m["w"] - 250, w=120), [("CineViewMLAIMDb", "Plain,hide")], L["meta"][4], "foreground", ' halign="right"', 40).replace("</widget>", sh))
		x.append(G.label(SRC, dict(m, x=m["x"] + m["w"] - 120, w=120), [("CineViewMLAIMDb", "Stars,hide")], L["meta"][4] - 2, "secondFG", ' halign="right"', 40).replace("</widget>", sh))
		for w in G.text_variants(SRC, [("EventName", "FullDescription")], GE.E(L["desc"]), None, L["desc"][4], "foreground", G.D_OPTS, "always"):
			x.append(w.replace('CineViewMLAShowIf">always,True,', 'CineViewMLAShowIf">%s,True%s,' % (KEY, inv)).replace('zPosition="20"', 'zPosition="40"'))
	tm = GE.E(cd["times"])
	x += [w.replace('zPosition="20"', 'zPosition="40"') for w in G.times(SRC, dict(tm, w=tm["w"] - 120), cd["times"][4], "secondFG")]
	x.append(G.label(SRC, dict(tm, x=tm["x"] + tm["w"] - 110, w=110), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], cd["times"][4], "secondFG", ' halign="right"', 40))
	x += GE.keys()
	return '\t<screen name="EPGvertical" position="0,0" size="1920,1080" flags="wfNoBorder" title="Vertical EPG">\n%s\n\t</screen>' % "\n".join(l for l in x if l)


def generate(skin):
	src = open(os.path.join(skin, "layouts", "epg", "classic", "screens.openatv.xml"), encoding="utf-8").read()
	parts, keep = [columns_screen(skin)], []
	for n in re.findall(r'<screen name="([^"]+)"', src):
		if n == "EPGvertical":
			continue
		m = re.search(r'\t?<screen name="%s".*?</screen>' % re.escape(n), src, re.S)
		keep.append(n)
		parts.append(m.group(0) if m.group(0).startswith("\t") else "\t" + m.group(0))
	d = os.path.join(skin, "layouts", "epg", "columns")
	os.makedirs(d, exist_ok=True)
	xml = '<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Columns (EPG, native vertical EPG) — generated by tools/mla/p9epg/gen_columns.py from spec_epg.py. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % "\n".join(parts)
	p = os.path.join(d, "screens.openatv.xml")
	open(p, "w", encoding="utf-8").write(xml)
	json.dump({"schema": 1, "id": "columns", "section": "epg", "name": "CineView Columns", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "tools/mla/p9epg/spec_epg.py COLUMNS (user decision 2026-10-05 05:23; t42 compatible)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}},
		"provides_screens": ["EPGvertical"] + keep, "options": [], "preview": "preview.png"}, open(os.path.join(d, "manifest.json"), "w"), indent=1)
	import xml.etree.ElementTree as ET
	r = ET.parse(p).getroot()
	for scr in r.iter("screen"):
		if scr.get("name") != "EPGvertical":
			continue
		for el in scr.iter():
			ps, ss = el.get("position"), el.get("size")
			if ps and ss and "," in ps and not ps.startswith(("c", "e")):
				px, py = (int(v) for v in ps.split(","))
				w, h = (int(v) for v in ss.split(","))
				assert 0 <= px and px + w <= 1920 and 0 <= py and py + h <= 1080, el.attrib
	return [d]


if __name__ == "__main__":
	print(generate(sys.argv[1]))
