# -*- coding: utf-8 -*-
"""CineView MLA - OpenBH adapter: EPG screens built on OpenBH's NATIVE EPG contract (ViX EPG family) from the shared
CineView EPG design packs, so every pack keeps one design source.  Applied by tools/mla/build.py (MLA_IMAGE=openbh)
to layouts/epg/<pack>/screens.openatv.xml -> screens.openbh.xml.  Each rule cites the OpenBH source it follows
(BlackHole/enigma2 52dedddc314a = OpenBH 5.6.008; c06a87ef4c09 = 6.0.003 has the same code for all of them).

Screens and skin names (Screens/EpgSelection*.py): SingleEPG/EPGSelection, MultiEPG/EPGSelectionMulti,
GridEPG/GraphicalEPG, GridEPGPIG/GraphicalEPGPIG, InfoBarGridEPG/GraphicalInfoBarEPG, InfobarSingleEPG/QuickEPG.
The CineView screens keep the second (OpenATV-compatible) names, which OpenBH looks up as well.
"""
import re
import xml.etree.ElementTree as ET

# Not part of OpenBH (no class / skinName uses them): OpenATV's vertical EPG and GraphMultiEPG plugin screens.
DROP_SCREENS = ("EPGvertical", "EPGverticalPIG", "GraphMultiEPG", "GraphMultiEPGList")
# EpgSelectionBase.py: key_red/green/yellow/blue are Button components -> skin widgets by NAME (a source= render
# of a Button raises "source not found", seen on PluginBrowser in the first run).
KEYS = ("key_red", "key_green", "key_yellow", "key_blue")
GRID_SCREENS = ("GraphicalEPG", "GraphicalEPGPIG", "GraphicalEPG_CVPosterOff")
INFOBAR_GRID_SCREENS = ("GraphicalInfoBarEPG",)
SINGLE_SCREENS = ("EPGSelection",)
# Components/EpgListGrid.py EPGListGrid.applySkin: Service/Entry/Record/Zap colours, borders, paddings, fonts
# (EntryFontGraphical / ServiceFontGraphical, *Infobar for the InfoBar grid).  OpenATV-only grid attributes:
GRID_DROP = ("EntryBackgroundColorPast", "TimeBackgroundColor")
GRID_FONTS = {"graphical": ("ServiceFontGraphical", "Regular;28", "EntryFontGraphical", "Regular;27"),
	"infobar": ("ServiceFontInfobar", "Regular;28", "EntryFontInfobar", "Regular;27")}
# Components/EpgListSingle.py: event font attribute EventFontSingle; columns from the skin parameter
# EPGSingleColumnSpecs = (left, dateWidth, sepWidth, timesWidth, breakWidth).  OpenATV's list attributes have no
# OpenBH equivalent per widget (first run: "Attribute 'setColWidths' ... not implemented").
SINGLE_DROP = ("setEventTimeFont", "setColWidths", "setColGap", "setIconDistance")


def _single_specs(widget):
	cols = [int(x) for x in widget.get("setColWidths", "155,230").split(",")]
	gap = int(widget.get("setColGap", "18"))
	return "0,%d,%d,%d,%d" % (cols[0], gap, cols[1], gap)


def epg(text):
	"""OpenATV-contract EPG pack XML -> OpenBH-contract EPG pack XML (same positions, sizes, colours, fonts)."""
	root = ET.fromstring(text)
	specs = None
	for scr in list(root.findall("screen")):
		name = scr.get("name")
		if name in DROP_SCREENS:
			root.remove(scr)
			continue
		for w in scr.iter("widget"):
			if w.get("source") in KEYS and w.get("render") == "Label":
				w.set("name", w.get("source"))
				del w.attrib["source"]
				del w.attrib["render"]
			if w.get("name") in KEYS:
				# OpenBH's own colour-key texts can be much longer than OpenATV's in some languages (Arabic
				# key_red "IMDb Search" = 50 characters): eLabel wraps them into a 2nd line that the 45 px bar
				# clips (t106 Arabic run).  One line, as in English; skin.py noWrap -> eLabel::setNoWrap.
				w.attrib.setdefault("noWrap", "1")
			if w.get("name") != "list":
				continue
			if name in GRID_SCREENS or name in INFOBAR_GRID_SCREENS:
				for a in GRID_DROP:
					w.attrib.pop(a, None)
				sf, sv, ef, ev = GRID_FONTS["infobar" if name in INFOBAR_GRID_SCREENS else "graphical"]
				w.attrib.setdefault(sf, sv)
				w.attrib.setdefault(ef, ev)
			elif name in SINGLE_SCREENS:
				specs = specs or _single_specs(w)
				if "setEventItemFont" in w.attrib:
					w.set("EventFontSingle", w.attrib.pop("setEventItemFont"))
				for a in SINGLE_DROP:
					w.attrib.pop(a, None)
	if specs:
		params = ET.Element("parameters")
		ET.SubElement(params, "parameter", {"name": "EPGSingleColumnSpecs", "value": specs})
		root.insert(0, params)
	out = ET.tostring(root, encoding="unicode")
	head = '<?xml version="1.0" encoding="UTF-8"?>\n<!-- generated for OpenBH by mla/images/openbh/transform.py from screens.openatv.xml - do not edit -->\n'
	return head + out + "\n"


def check(text):
	"""Self-check of an OpenBH EPG file: no OpenATV-only screen / attribute / key source left."""
	root = ET.fromstring(text)
	problems = []
	for scr in root.findall("screen"):
		if scr.get("name") in DROP_SCREENS:
			problems.append("screen %s" % scr.get("name"))
		for w in scr.iter("widget"):
			if w.get("source") in KEYS:
				problems.append("%s: %s as source" % (scr.get("name"), w.get("source")))
			for a in GRID_DROP + SINGLE_DROP + ("setEventItemFont",):
				if a in w.attrib:
					problems.append("%s: %s" % (scr.get("name"), a))
	return problems


# Shared core files (core/common.openatv.xml, core/mla_ui.openatv.xml) in the OpenBH package:
# OpenATV 57b7a51 eListbox setValueFont <-> OpenBH 52dedddc314a skin.py "secondfont" -> eListbox::setSecondFont,
# used by eListboxPythonConfigContent::paint for the VALUE text (lib/gui/elistboxcontent.cpp fnt2; without it OpenBH
# draws values at font size - 20 %).  Keeps the approved 27 px setting values (user 2026-10-07).
CORE_ATTR_MAP = (("valueFont", "secondfont"),)


def core(text):
	for old, new in CORE_ATTR_MAP:
		text = re.sub(r'\s%s="' % old, ' %s="' % new, text)
	return text
