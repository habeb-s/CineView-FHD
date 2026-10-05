#!/usr/bin/env python3
"""Shared pieces for CineView EMC (EnhancedMovieCenter) screens.

Contract — EMC 4.0 git1790 installed on the receiver (Slot 8), read from its compiled modules (no source shipped):
* EMCSelection.__init__ (MovieSelection.pyc, line 580): skinName = "EMCSelectionOwn" when config.EMC.use_orig_skin is
  True (EMC's own CoolSkin), otherwise ["EMCSelectionExtended", "EMCSelection"]; the CoolSkin XML is only the embedded
  fallback (self.skin) used when the active skin has no such screen -> a design that ships "EMCSelection" replaces it,
  a design that does not (Classic) keeps EMC's own look (safe fallback).
* Widgets created by EMC: list (MovieCenter, "Cool*" layout attributes), wait (Label), key_red..key_blue (Button),
  spacefree (StaticText), Cover / CoverBg (Pixmap), CoverBgLbl (Label), Video (VideoWindow = EMC mini-TV),
  name / artistAT / ... (music tags, Labels), date / size (Labels); source "Service" = EMCServiceEvent (ServiceName,
  ServiceTime, MovieInfo, EventName converters as in EMC's CoolSkin).
* Only standard converters are used here (EMC's own EMCClockToText is not needed).
"""

# EMC CoolSkin "left" FHD list (1190 px wide): column positions; columns right of the title are kept at the same
# distance from the right edge, the title column takes the rest.
_COOL = {"CoolIconPos": 5, "CoolIconSize": "50,40", "CoolMoviePos": 65, "CoolMovieHPos": 6, "CoolPiconPos": 40, "CoolPiconHPos": 5,
	"CoolPiconHeight": 35, "CoolMoviePiconPos": 140, "CoolBarHPos": 14, "CoolDateHPos": 7, "CoolDateColor": 1, "CoolHighlightColor": 1,
	"CoolTitleColor": 1, "CoolSelNumTxtWidth": 50, "CoolDirInfoWidth": 300}
_RIGHT = {"CoolBarPos": 770, "CoolProgressPos": 840, "CoolCSPos": 860, "CoolDatePos": 920}
_BASE_W = 1190


def emc_list(x, y, w, h, item=45, font=30, date_font=28, extra=""):
	a = dict(_COOL)
	shift = w - _BASE_W
	for k, v in _RIGHT.items():
		a[k] = v + shift
	a["CoolDateWidth"] = 240
	a["CoolBarSizeSa"] = "120,21"
	a["CoolMovieSize"] = max(200, 700 + shift)
	a["CoolMoviePiconSize"] = max(200, 600 + shift)
	a["CoolFolderSize"] = max(300, 800 + shift)
	a["CoolFont"] = "Regular;%d" % font
	a["CoolSelectFont"] = "Regular;%d" % font
	a["CoolDateFont"] = "Regular;%d" % date_font
	attrs = " ".join('%s="%s"' % (k, v) for k, v in sorted(a.items()))
	return '\t\t<widget name="list" position="%d,%d" size="%d,%d" itemHeight="%d" DefaultColor="foreground" enableWrapAround="1" scrollbarMode="showOnDemand" transparent="1" zPosition="3" %s%s />' % (x, y, w, h, item, attrs, extra)


def emc_keys(y, x0=60, step=300, font=26):
	"""EMC's key_* are Buttons (named Labels): a colour bar + caption, like the CineView key row."""
	out = []
	for i, (k, col) in enumerate((("key_red", "#00a00000"), ("key_green", "#00008000"), ("key_yellow", "#00a08000"), ("key_blue", "#000040a0"))):
		x = x0 + i * step
		out.append('\t\t<eLabel position="%d,%d" size="8,36" backgroundColor="%s" zPosition="31" />' % (x, y + 6, col))
		out.append('\t\t<widget name="%s" position="%d,%d" size="%d,48" font="Regular;%d" valign="center" foregroundColor="foreground" transparent="1" noWrap="1" zPosition="40" />' % (k, x + 20, y, step - 30, font))
	return out


def emc_cover_under(x, y, w, h):
	"""EMC's own cover widgets at the CineView poster's place, BELOW it (EMC shows them only when its own cover
	option is on; the CineView poster -- local cover file first -- is drawn on top)."""
	return ['\t\t<widget name="CoverBg" position="%d,%d" size="%d,%d" zPosition="16" />' % (x, y, w, h),
		'\t\t<widget name="CoverBgLbl" position="%d,%d" size="%d,%d" zPosition="16" transparent="1" />' % (x, y, w, h),
		'\t\t<widget name="Cover" position="%d,%d" size="%d,%d" alphatest="blend" zPosition="17" />' % (x, y, w, h)]


# Attributes of the inherited Classic MovieSelection list that 57b7a51 does not know (device t61: 15 "[Skin] Error"
# lines per opening, no visual effect).  New packs drop them; the approved Classic screen is left as it is.
LEGACY_MOVIELIST_ATTRS = ("dateWidth", "fontSizesCompact", "fontSizesMinimal", "pbarHeight", "pbarLargeWidth", "spaceRight",
	"columnsOriginal", "columnsCompactDescription", "compactColumn", "treeDescription", "partIconeShiftMinimal",
	"partIconeShiftCompact", "partIconeShiftOriginal", "iconsWidth", "spaceIconeText")


def clean_movielist(widget_xml):
	import re
	for a in LEGACY_MOVIELIST_ATTRS:
		widget_xml = re.sub(r'\s%s="[^"]*"' % a, "", widget_xml)
	return widget_xml
