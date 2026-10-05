#!/usr/bin/env python3
"""PVR pack "cinema" — Cinema Shelf (Five_Models_Plan.md §4: the Cinema model's own PVR; look pending approval).

Cinema language (same as the Cinema InfoBar / SecondInfoBar / EventView Feature): the live picture stays behind a
full-screen scrim; the left column is the selected recording (large poster, big title, stacked details, short
description), the right column is the full-height recording list.

Contracts used (nothing invented):
* native MovieSelection (Screens/MovieSelection.py 57b7a51): every named widget of the Classic screen is kept
  (list, waitingtext, chosenletter, movie_sort, movie_off, DescriptionBorder, freeDiskSpace, TrashcanSize,
  coloured keys through the skin's ButtonTemplate), source "Service" = ServiceEvent of the selected movie;
* EMC (EnhancedMovieCenter = what the PVR key opens on this receiver): emc_common.py (list with Cool* columns
  from the right edge, wait, key_* Buttons, spacefree, Cover / CoverBg / CoverBgLbl, source "Service");
  description = MovieInfo ShortDescription (EMC returns the file path for FullDescription, device t61c).
Poster: 340x510 (the size device-tested in the Cover Library; t62 showed the larger poster surfaces are the ones
that fall back from accel memory).  Posters OFF: '<name>_CVPosterOff' screens, no poster, the text column and the
list start at the left edge (selected by the CineView MLA plugin while config.plugins.cineviewmla.poster_pvr is False).
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
POSTER = (90, 120, 340, 510)
# The list owns the full right column: the native MovieList derives its row height from the list height
# (Components/MovieList.py setItemsPerPage: listHeight // config.movielist.itemsperpage; device t66: a 552-px list gave
# 27-px rows), so it gets the full 860 px; the selected recording's card lives in the left column.
LX, LY, LW, LH, ITEM = 870, 120, 960, 860, 55
COL_W = 720


def _top(emc):
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="steThemeOverlay" zPosition="-4" />',
		'\t\t<widget source="Title" render="Label" position="90,40" size="1200,44" font="Regular;30" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="20" />',
		G.label("global.CurrentTime", {"x": 1430, "y": 46, "w": 250, "h": 34}, [("ClockToText", "Format:%a %d %b")], 24, "grey", ' halign="right"'),
		G.label("global.CurrentTime", {"x": 1690, "y": 34, "w": 140, "h": 54}, [("ClockToText", "Format:%H:%M")], 42, "foreground", ' halign="right"'),
		'\t\t<eLabel position="840,120" size="2,860" backgroundColor="#00444444" zPosition="-1" />',
		'\t\t<eLabel position="0,1000" size="1920,80" backgroundColor="steThemePanelAlt" zPosition="-2" />']
	if not emc:
		x.append('\t\t<widget name="movie_sort" pixmaps="icons/az.png,icons/newtop.png,icons/shuffle.png,icons/za.png,icons/oldtop.png,icons/faz.png,icons/fza.png,icons/default.png,icons/azold.png,icons/zanew.png,icons/longest.png,icons/shortest.png,icons/dtsrt.png,icons/dtsdt.png" position="1300,46" zPosition="5" size="52,30" transparent="1" alphatest="on" />')
		x.append('\t\t<widget name="movie_off" pixmaps="icons/ask.png,icons/movielist.png,icons/quit.png,icons/pause.png,icons/playlist.png,icons/playlistquit.png,icons/loop.png,icons/rep.png" position="1360,46" zPosition="5" size="52,30" transparent="1" alphatest="on" />')
	return x


def _lbl(conv, x, y, w, h, font, color, extra=""):
	c = "".join('\n\t\t\t<convert type="%s">%s</convert>' % cv for cv in conv)
	return '\t\t<widget source="Service" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="%s" transparent="1" zPosition="20"%s>%s\n\t\t</widget>' % (x, y, w, h, font, color, extra, c)


def _card(skin, on):
	"""Selected recording in the left column (source "Service"): ON = poster + stacked details beside it, description
	under both; OFF = no poster, the title and details take the column width, the description gets the rest."""
	date = [("ServiceTime", "StartTime"), ("ClockToText", "ShortDate")]
	dur = [("ServiceTime", "Duration"), ("ClockToText", "AsLength")]
	x = []
	if on:
		px, py, pw, ph = POSTER
		x += G.poster(skin, "Service", {"x": px, "y": py, "w": pw, "h": ph}, KEY)
		cx, cw = px + pw + 30, COL_W - pw - 30
		x.append(_lbl([("ServiceName", "Name")], cx, 114, cw, 156, 40, "foreground"))
		x.append(_lbl(date, cx, 286, cw, 36, 27, "grey", ' noWrap="1"'))
		x.append(_lbl(dur, cx, 326, cw, 36, 27, "grey", ' noWrap="1"'))
		x.append(_lbl([("MovieInfo", "RecordServiceName")], cx, 366, cw, 36, 27, "secondFG", ' noWrap="1"'))
		x.append(_lbl([("MovieInfo", "FileSize")], cx, 406, cw, 36, 25, "grey", ' noWrap="1"'))
		x.append(_lbl([("EventName", "Genre")], cx, 452, cw, 34, 24, "grey", ' noWrap="1"'))
		x.append(_lbl([("CineViewMLAIMDb", "Plain,hide")], cx, 494, 140, 36, 27, "foreground"))
		x.append(_lbl([("CineViewMLAIMDb", "Stars,hide")], cx + 140, 498, 140, 32, 22, "secondFG", ' noWrap="1"'))
		dy = 664
	else:
		x.append(_lbl([("ServiceName", "Name")], 90, 112, COL_W, 124, 48, "foreground"))
		x.append(_lbl(date, 90, 252, 220, 36, 27, "grey", ' noWrap="1"'))
		x.append(_lbl(dur, 320, 252, 160, 36, 27, "grey", ' noWrap="1"'))
		x.append(_lbl([("MovieInfo", "FileSize")], 490, 252, 320, 36, 25, "grey", ' halign="right" noWrap="1"'))
		x.append(_lbl([("MovieInfo", "RecordServiceName")], 90, 294, COL_W, 36, 27, "secondFG", ' noWrap="1"'))
		x.append(_lbl([("EventName", "Genre")], 90, 336, 500, 34, 24, "grey", ' noWrap="1"'))
		x.append(_lbl([("CineViewMLAIMDb", "Plain,hide")], 600, 334, 100, 36, 26, "foreground", ' halign="right"'))
		x.append(_lbl([("CineViewMLAIMDb", "Stars,hide")], 700, 338, 110, 32, 21, "secondFG", ' halign="right" noWrap="1"'))
		dy = 392
	x.append('\t\t<eLabel position="90,%d" size="%d,2" backgroundColor="#00444444" zPosition="-1" />' % (dy - 14, COL_W))
	# ShortDescription: on EMC's service FullDescription is the file path (t61c); the short one reads well in both
	x.append('\t\t<widget source="Service" render="RunningText" position="90,%d" size="%d,%d" font="Regular;26" foregroundColor="foreground" transparent="1" zPosition="20" options="%s">\n\t\t\t<convert type="MovieInfo">ShortDescription</convert>\n\t\t</widget>' % (dy, COL_W, 940 - dy, G.D_OPTS))
	return x


def native(skin, on):
	x = _top(False) + _card(skin, on)
	geo = 'position="%d,%d" size="%d,%d"' % (LX, LY, LW, LH)
	x.append('\t\t<widget name="waitingtext" %s font="Regular;33" halign="center" valign="center" transparent="1" zPosition="4" />' % geo)
	x.append('\t\t<widget name="chosenletter" %s foregroundColor="secondFG" font="Regular;112" halign="center" valign="center" transparent="1" zPosition="4" />' % geo)
	x.append('\t\t<widget name="list" %s scrollbarMode="showOnDemand" itemHeight="%d" font="Regular;29" transparent="1" zPosition="3" />' % (geo, ITEM))
	x.append('\t\t<widget name="DescriptionBorder" position="0,0" size="0,0" />')
	x.append('\t\t<widget name="freeDiskSpace" position="90,948" size="400,32" foregroundColor="grey" font="Regular;22" transparent="1" zPosition="20" />')
	x.append('\t\t<widget name="TrashcanSize" position="490,948" size="320,32" foregroundColor="grey" font="Regular;22" halign="right" transparent="1" zPosition="20" />')
	x.append('\t\t<panel name="ButtonTemplate" />')
	name = "MovieSelection" if on else "MovieSelection_CVPosterOff"
	return G.screen(name, "Movie Selection", [l for l in x if l])


def emc_screen(skin, on):
	x = _top(True) + _card(skin, on)
	x.append('\t\t<widget name="wait" position="%d,%d" size="%d,%d" font="Regular;33" halign="center" valign="center" transparent="1" zPosition="4" />' % (LX, LY, LW, LH))
	x.append(EMC.emc_list(LX, LY, LW, LH, ITEM, 29, 25))
	if on:
		px, py, pw, ph = POSTER
		x += EMC.emc_cover_under(px, py, pw, ph)
	else:
		x += EMC.emc_cover_under(1880, 900, 2, 2)  # EMC's cover widgets exist but are out of sight (no poster space)
	x.append('\t\t<widget source="spacefree" render="Label" position="90,948" size="720,32" foregroundColor="grey" font="Regular;22" transparent="1" zPosition="20" />')
	x += EMC.emc_keys(1016, 90, 440)
	name = "EMCSelection" if on else "EMCSelection_CVPosterOff"
	return G.screen(name, "EMC", [l for l in x if l])


def generate(skin):
	src = open(os.path.join(skin, "layouts", "pvr", "classic", "screens.openatv.xml"), encoding="utf-8").read()
	names = re.findall(r'<screen name="([^"]+)"', src)
	parts = [native(skin, True), native(skin, False), emc_screen(skin, True), emc_screen(skin, False)]
	for n in names:
		if n == "MovieSelection":
			continue
		m = re.search(r'\t?<screen name="%s".*?</screen>' % re.escape(n), src, re.S)
		parts.append("\t" + m.group(0).strip())
	d = os.path.join(skin, "layouts", "pvr", "cinema")
	os.makedirs(d, exist_ok=True)
	p = os.path.join(d, "screens.openatv.xml")
	open(p, "w", encoding="utf-8").write('<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Cinema — Cinema Shelf (PVR), generated by tools/mla/p7/gen_cinema_pvr.py. Look pending approval. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % "\n".join(parts))
	json.dump({"schema": 1, "id": "cinema", "section": "pvr", "name": "CineView Cinema Shelf", "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "docs/mla/Five_Models_Plan.md §4 (Cinema model, look pending approval)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}},
		"provides_screens": ["MovieSelection", "MovieSelection_CVPosterOff", "EMCSelection", "EMCSelection_CVPosterOff"] + [n for n in names if n != "MovieSelection"],
		"options": [], "preview": "preview.png"}, open(os.path.join(d, "manifest.json"), "w"), indent=1)
	import xml.etree.ElementTree as ET
	r = ET.parse(p).getroot()
	for scr in r.iter("screen"):
		if scr.get("name") not in ("MovieSelection", "MovieSelection_CVPosterOff", "EMCSelection", "EMCSelection_CVPosterOff"):
			continue
		for el in scr.iter():
			ps, ss = el.get("position"), el.get("size")
			if ps and ss and "," in ps and not ps.startswith(("c", "e")) and ps != "fill":
				px, py = (int(v) for v in ps.split(","))
				w, h = (int(v) for v in ss.split(","))
				assert 0 <= px and px + w <= 1920 and 0 <= py and py + h <= 1080, (scr.get("name"), el.attrib)
	return [d]


if __name__ == "__main__":
	print(generate(sys.argv[1]))
