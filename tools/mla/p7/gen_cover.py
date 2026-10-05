#!/usr/bin/env python3
"""PVR pack "cover" — Details Cover Library (Five_Models_Plan.md §4; look pending the user's approval).

MovieSelection has no native cover grid (self["list"] = MovieList, fixed-row eListbox; a grid would need a new
list class = an invented widget, forbidden).  So: the Classic MovieSelection stays as it is (PiG, play position,
recording details, file size, trash / free space, sort / off icons, coloured keys) and the right panel splits:
* the native list narrows to 690 px (OpenATV 8 MovieList lays its columns out from the item width:
  Components/MovieList.py buildMovieListEntry, so a narrower list only shortens the title column);
* a large cover of the SELECTED recording beside it: CineViewMLAPosterX on source "Service" (the screen's
  ServiceEvent of the selected movie), CineView default image under it, Details' 3-px frame; under the cover
  the recording title and genre / IMDb (reliable identity only).
Posters OFF: "MovieSelection_CVPosterOff" = the Classic screen unchanged (wide list, no cover, no reserved gap);
the CineView MLA plugin puts it first in the skinName list while config.plugins.cineviewmla.poster_pvr is False
(only for the plain "MovieSelection" name; the user's MovieSelectionSlim keeps its own screen).
usage (build.py): generate(skin) -> [pack dir]"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_details as G  # noqa: E402
import emc_common as EMC  # noqa: E402

KEY = "config.plugins.cineviewmla.poster_pvr"
LIST = (790, 125, 690, 760)
COVER = (1512, 128, 340, 510)


def emc_screen(skin, on):
	"""EMC (the PVR key on this receiver opens EnhancedMovieCenter): the Cover Library in EMC's own contract
	(emc_common.py).  Same composition as the MovieSelection pack: live picture + details of the selected
	recording on the left, list + cover on the right; OFF = wide list, no cover."""
	x = ['\t\t<widget source="Title" render="Label" position="55,30" size="1300,50" font="Regular;34" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />',
		G.label("global.CurrentTime", {"x": 1380, "y": 40, "w": 300, "h": 34}, [("ClockToText", "Format:%a %d %b")], 24, "grey", ' halign="right"'),
		G.label("global.CurrentTime", {"x": 1690, "y": 28, "w": 175, "h": 54}, [("ClockToText", "Format:%H:%M")], 42, "foreground", ' halign="right"'),
		'\t\t<eLabel position="35,95" size="700,835" backgroundColor="steThemePanelAlt" zPosition="-3" />',
		'\t\t<eLabel position="26,116" size="728,413" backgroundColor="#007c7c7c" zPosition="0" />',
		'\t\t<widget source="session.VideoPicture" render="Pig" position="30,120" size="720,405" backgroundColor="transparent" zPosition="1" />',
		'\t\t<widget source="Service" render="Label" position="55,545" size="250,38" foregroundColor="secondFG" font="Regular;28" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceTime">StartTime</convert>\n\t\t\t<convert type="ClockToText">ShortDate</convert>\n\t\t</widget>',
		'\t\t<widget source="Service" render="Label" position="305,545" size="150,38" foregroundColor="foreground" font="Regular;28" halign="center" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceTime">Duration</convert>\n\t\t\t<convert type="ClockToText">AsLength</convert>\n\t\t</widget>',
		'\t\t<widget source="Service" render="Label" position="455,545" size="260,38" foregroundColor="foreground" font="Regular;28" halign="right" noWrap="1" transparent="1" zPosition="20">\n\t\t\t<convert type="MovieInfo">RecordServiceName</convert>\n\t\t</widget>',
		'\t\t<eLabel position="55,595" size="660,2" backgroundColor="#00444444" zPosition="1" />',
		# EMC: MovieInfo ShortDescription = the recording's description (.meta), EventName ExtendedDescription = .eit text
		# (as EMC's own skin); MovieInfo FullDescription returns the FILE PATH for EMC's service (device t61)
		'\t\t<widget source="Service" render="RunningText" position="55,610" size="660,96" foregroundColor="secondFG" font="Regular;26" transparent="1" zPosition="20" options="%s">\n\t\t\t<convert type="MovieInfo">ShortDescription</convert>\n\t\t</widget>' % G.D_OPTS,
		'\t\t<widget source="Service" render="RunningText" position="55,714" size="660,145" foregroundColor="foreground" font="Regular;25" transparent="1" zPosition="20" options="%s">\n\t\t\t<convert type="EventName">ExtendedDescription</convert>\n\t\t</widget>' % G.D_OPTS,
		'\t\t<widget source="Service" render="Label" position="55,875" size="200,34" foregroundColor="grey" font="Regular;25" transparent="1" zPosition="20">\n\t\t\t<convert type="MovieInfo">FileSize</convert>\n\t\t</widget>',
		'\t\t<widget source="spacefree" render="Label" position="260,875" size="455,34" foregroundColor="grey" font="Regular;25" halign="right" transparent="1" zPosition="20" />',
		'\t\t<eLabel position="760,95" size="1125,835" backgroundColor="steThemePanelAlt" zPosition="-3" />']
	lw = LIST[2] if on else 1060
	x.append('\t\t<widget name="wait" position="790,125" size="%d,760" font="Regular;33" halign="center" valign="center" transparent="1" zPosition="4" />' % lw)
	x.append(EMC.emc_list(790, 125, lw, 760, 52, 30, 26))
	if on:
		cx, cy, cw, ch = COVER
		x.append('\t\t<eLabel position="1490,110" size="2,800" backgroundColor="#00444444" zPosition="1" />')
		x += EMC.emc_cover_under(cx, cy, cw, ch)
		x += G.poster(skin, "Service", {"x": cx, "y": cy, "w": cw, "h": ch}, KEY)
		x.append(G.label("Service", {"x": cx, "y": cy + ch + 22, "w": cw, "h": 76}, [("ServiceName", "Name")], 28, "foreground", ' valign="top"', 20))
		x.append(G.label("Service", {"x": cx, "y": cy + ch + 106, "w": cw - 130, "h": 30}, [("EventName", "Genre")], 22, "grey", ' noWrap="1"', 20))
		x.append(G.label("Service", {"x": cx + cw - 120, "y": cy + ch + 106, "w": 120, "h": 30}, [("CineViewMLAIMDb", "Plain,hide")], 22, "secondFG", ' halign="right"', 20))
	else:
		x += EMC.emc_cover_under(1880, 900, 2, 2)  # EMC's cover widgets exist but are out of sight (no poster space)
	x.append('\t\t<eLabel position="55,958" size="1810,2" backgroundColor="#00444444" zPosition="1" />')
	x += EMC.emc_keys(972, 60, 450)
	name = "EMCSelection" if on else "EMCSelection_CVPosterOff"
	return '\t<screen name="%s" title="EMC" position="fill" backgroundColor="steThemePrimary" flags="wfNoBorder">\n%s\n\t</screen>' % (name, "\n".join(l for l in x if l))


def generate(skin):
	src = open(os.path.join(skin, "layouts", "pvr", "classic", "screens.openatv.xml"), encoding="utf-8").read()
	names = re.findall(r'<screen name="([^"]+)"', src)
	classic = re.search(r'\t?<screen name="MovieSelection".*?</screen>', src, re.S).group(0).strip()
	lists = re.findall(r'<widget name="list" [^>]*/>', classic)
	assert len(lists) == 1, "MovieSelection list anchor"
	on = re.sub(r'position="790,125" size="1060,760"', 'position="%d,%d" size="%d,%d"' % LIST, lists[0], count=1)
	assert on != lists[0], "MovieSelection list geometry changed in Classic"
	for w in ("waitingtext", "chosenletter"):
		on_w = re.search(r'<widget name="%s" position="790,125" size="1060,760"' % w, classic)
		assert on_w, w
	body = classic.replace(lists[0], EMC.clean_movielist(on))
	body = body.replace('<widget name="waitingtext" position="790,125" size="1060,760"', '<widget name="waitingtext" position="%d,%d" size="%d,%d"' % LIST)
	body = body.replace('<widget name="chosenletter" position="790,125" size="1060,760"', '<widget name="chosenletter" position="%d,%d" size="%d,%d"' % LIST)
	cx, cy, cw, ch = COVER
	extra = ['\t\t<eLabel position="1490,110" size="2,800" backgroundColor="#00444444" zPosition="1" />']
	extra += G.poster(skin, "Service", {"x": cx, "y": cy, "w": cw, "h": ch}, KEY)
	extra.append(G.label("Service", {"x": cx, "y": cy + ch + 22, "w": cw, "h": 76}, [("ServiceName", "Name")], 28, "foreground", ' valign="top"', 20)
		.replace("</widget>", '\t<convert type="CineViewMLAShowIf">%s,True</convert>\n\t\t</widget>' % KEY))
	extra.append(G.label("Service", {"x": cx, "y": cy + ch + 106, "w": cw - 130, "h": 30}, [("EventName", "Genre")], 22, "grey", ' noWrap="1"', 20)
		.replace("</widget>", '\t<convert type="CineViewMLAShowIf">%s,True</convert>\n\t\t</widget>' % KEY))
	extra.append(G.label("Service", {"x": cx + cw - 120, "y": cy + ch + 106, "w": 120, "h": 30}, [("CineViewMLAIMDb", "Plain,hide")], 22, "secondFG", ' halign="right"', 20)
		.replace("</widget>", '\t<convert type="CineViewMLAShowIf">%s,True</convert>\n\t\t</widget>' % KEY))
	body = body.replace("\t\t<panel name=\"ButtonTemplate\" />", "\n".join(extra) + "\n\t\t<panel name=\"ButtonTemplate\" />", 1)
	assert "\n".join(extra) in body, "ButtonTemplate anchor"
	off = classic.replace(lists[0], EMC.clean_movielist(lists[0])).replace('<screen name="MovieSelection"', '<screen name="MovieSelection_CVPosterOff"', 1)
	parts = ["\t" + body, "\t" + off, emc_screen(skin, True), emc_screen(skin, False)]
	for n in names:
		if n == "MovieSelection":
			continue
		m = re.search(r'\t?<screen name="%s".*?</screen>' % re.escape(n), src, re.S)
		parts.append("\t" + m.group(0).strip())
	d = os.path.join(skin, "layouts", "pvr", "cover")
	os.makedirs(d, exist_ok=True)
	p = os.path.join(d, "screens.openatv.xml")
	open(p, "w", encoding="utf-8").write('<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Details — Cover Library (PVR), generated by tools/mla/p7/gen_cover.py. Look pending approval. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % "\n".join(parts))
	json.dump({"schema": 1, "id": "cover", "section": "pvr", "name": "CineView Cover Library", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "docs/mla/Five_Models_Plan.md §4 (Details model, look pending approval)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}},
		"provides_screens": ["MovieSelection", "MovieSelection_CVPosterOff", "EMCSelection", "EMCSelection_CVPosterOff"] + [n for n in names if n != "MovieSelection"],
		"options": [], "preview": "preview.png"}, open(os.path.join(d, "manifest.json"), "w"), indent=1)
	import xml.etree.ElementTree as ET
	ET.parse(p)
	return [d]


if __name__ == "__main__":
	print(generate(sys.argv[1]))
