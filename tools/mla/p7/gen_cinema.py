#!/usr/bin/env python3
"""Generate the CineView "Cinema" layout packs (infobar + secondinfobar) from spec_p7.py.

Same contract and rules as gen_details.py (same verified widgets/converters, poster on/off variants via
CineViewMLAShowIf, RTL variants, swimming RunningText in whole-line boxes, theme roles only).  Cinema is a
separate family: no element is shared with Details except the generic helpers.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_p7 as S  # noqa: E402
from gen_details import (D_OPTS, RUN_OPTS, SWIM_SHORT, T_OPTS, _classic_screen, _geo, box, label, pos, poster,  # noqa: E402,F401
	progress, screen, static, text_variants, times)


def _shown(eon, eoff, key, body_fn):
	"""Emit body_fn(geometry) once, or twice with poster on/off ShowIf when the geometry moves."""
	if eoff is None or (eon["x"], eon["w"]) == (eoff["x"], eoff["w"]):
		return [body_fn(eon, None)]
	return [body_fn(eon, "%s,True" % key), body_fn(eoff, "%s,True,Invert" % key)]


def _with_showif(xml, arg):
	if not arg:
		return xml
	if xml.rstrip().endswith("/>"):
		return xml.rstrip()[:-2].rstrip() + '>\n\t\t\t<convert type="CineViewMLAShowIf">%s</convert>\n\t\t</widget>' % arg
	return xml.replace("</widget>", '\t<convert type="CineViewMLAShowIf">%s</convert>\n\t\t</widget>' % arg)


def caption(text, eon, eoff, key, font, color):
	"""Static caption that moves with the poster switch (Label + ShowIf text=)."""
	if eoff is None or (eon["x"], eon["w"]) == (eoff["x"], eoff["w"]):
		return [static(text, eon, font, color)]
	return ['\t\t<widget source="session.CurrentService" render="Label" %s transparent="1" zPosition="20" foregroundColor="%s" font="Regular;%d">\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,text=%s</convert>\n\t\t</widget>' % (pos(g), color, font, key, inv, text)
		for g, inv in ((eon, ""), (eoff, ",Invert"))]


def icon(pm, cond, eon, eoff, key, z):
	"""ServiceInfo icon; when it moves with the poster switch, ShowIf ANDs the boolean (bool)."""
	if eoff is None or (eon["x"], eon["w"]) == (eoff["x"], eoff["w"]):
		return ['\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="%s" %s zPosition="%d" alphatest="on" scale="1">\n\t\t\t<convert type="ServiceInfo">%s</convert>\n\t\t\t<convert type="ConditionalShowHide" />\n\t\t</widget>' % (pm, pos(eon), z, cond)]
	return ['\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="%s" %s zPosition="%d" alphatest="on" scale="1">\n\t\t\t<convert type="ServiceInfo">%s</convert>\n\t\t\t<convert type="CineViewMLAShowIf">%s,True%s,bool</convert>\n\t\t</widget>' % (pm, pos(g), z, cond, key, inv)
		for g, inv in ((eon, ""), (eoff, ",Invert"))]


def times_sw(src, g, font, color, arg):
	"""times() whose three parts follow a ShowIf argument (or none)."""
	out = []
	for l in times(src, g, font, color):
		if arg is None:
			out.append(l)
		elif "<eLabel" in l:
			import re as _re
			pp = _re.search(r'position="[^"]*" size="[^"]*"', l).group(0)
			out.append('\t\t<widget source="session.CurrentService" render="Label" %s transparent="1" zPosition="20" foregroundColor="%s" font="Regular;%d" halign="center">\n\t\t\t<convert type="CineViewMLAShowIf">%s,text=–</convert>\n\t\t</widget>' % (pp, color, font, arg))
		else:
			out.append(l.replace("</widget>", '\t<convert type="CineViewMLAShowIf">%s</convert>\n\t\t</widget>' % arg))
	return out


def cinema_infobar(skin, key, on, off):
	x = []
	b = on["band"]
	x.append('\t\t<ePixmap pixmap="infobar/bl80.png" position="%d,%d" size="%d,%d" zPosition="1" alphatest="blend" scale="1" />' % (b["x"], b["y"], b["w"], b["h"]))
	x += poster(skin, "session.Event_Now", on["poster_now"], key)
	for eid in ("picon",):
		x += _shown(on[eid], off[eid], key, lambda g, a: _with_showif('\t\t<widget source="session.CurrentService" render="Picon" mode="infobar" scale="aspect" %s alphatest="blend" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % pos(g), a))
	x += _shown(on["ch_number"], off["ch_number"], key, lambda g, a: _with_showif('\t\t<widget source="session.CurrentService" render="ChannelNumber" %s transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;26" />' % pos(g), a))
	x += _shown(on["ch_name"], off["ch_name"], key, lambda g, a: _with_showif('\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;26" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">NameOnly</convert>\n\t\t</widget>' % (pos(g), RUN_OPTS), a))
	x += text_variants("session.Event_Now", [("EventName", "Name")], on["now_title"], off["now_title"], 46, "foreground", T_OPTS, key)
	x += times("session.Event_Now", on["now_time"], 32, "secondFG")
	x += progress("session.Event_Now", [("EventTime", "Progress")], on["progress"], off["progress"], key)
	x += text_variants("session.Event_Now", [("EventName", "ShortDescription")], on["now_short"], off["now_short"], 25, "grey", D_OPTS, key)
	x += caption("NEXT", on["next_label"], off["next_label"], key, 24, "secondFG")
	x += text_variants("session.Event_Next", [("EventName", "Name")], on["next_title"], off["next_title"], 29, "foreground", T_OPTS, key)
	x += times("session.Event_Next", on["next_time"], 27, "grey")
	x += _shown(on["sep"], off["sep"], key, lambda g, a: box(g, "#00444444", 8) if not a else _with_showif('\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="mla_assets/sep_444444.png" %s zPosition="8" scale="1" />' % pos(g), a))
	# technical row (live sources; moved left together when posters are off)
	def tech(g, a, xml):
		return _with_showif(xml % pos(g), a)
	x += _shown(on["tech_snr"], off["tech_snr"], key, lambda g, a: tech(g, a, '\t\t<widget source="session.FrontendStatus" render="Label" %s transparent="1" zPosition="20" foregroundColor="grey" font="Regular;23">\n\t\t\t<convert type="FrontendInfo">SNR</convert>\n\t\t</widget>'))
	x += _shown(on["tech_res"], off["tech_res"], key, lambda g, a: tech(g, a, '\t\t<widget render="VideoSize" source="session.CurrentService" %s font="Regular;23" foregroundColor="grey" transparent="1" zPosition="20" />'))
	for eid, pm, cond, z in (("tech_hd", "infobar/ico_format_hd.png", "IsHD", 22), ("tech_hd", "infobar/ico_format_4k.png", "Is4K", 23), ("tech_169", "infobar/ico_format_16_9.png", "IsWidescreen", 22)):
		x += icon(pm, cond, on[eid], off[eid], key, z)
	x += _shown(on["tech_bitrate"], off["tech_bitrate"], key, lambda g, a: tech(g, a, '\t\t<widget source="session.CurrentService" render="Label" %s transparent="1" zPosition="20" foregroundColor="grey" font="Regular;23">\n\t\t\t<convert type="CineViewMLABitrate">Mbps</convert>\n\t\t</widget>'))
	x += _shown(on["tech_cam"], off["tech_cam"], key, lambda g, a: tech(g, a, '\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="#0044dd44" font="Regular;23" noWrap="1" options="' + RUN_OPTS + '">\n\t\t\t<convert type="CineViewMLACamInfo">Info</convert>\n\t\t</widget>'))
	x += _shown(on["tech_imdb"], off["tech_imdb"], key, lambda g, a: tech(g, a, '\t\t<widget source="session.Event_Now" render="Label" %s transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;23">\n\t\t\t<convert type="CineViewMLAIMDb">Plain</convert>\n\t\t</widget>'))
	we = on["tech_weather"]
	x.append('\t\t<widget source="session.OAWeather" render="Label" position="%d,%d" size="%d,%d" transparent="1" zPosition="24" foregroundColor="grey" font="Regular;23" halign="right">\n\t\t\t<convert type="OAWeather">temperature_current</convert>\n\t\t</widget>' % (we["x"] + we["w"] - 80, we["y"], 80, we["h"]))
	x.append('\t\t<widget source="session.OAWeather" render="RunningText" position="%d,%d" size="%d,%d" transparent="1" zPosition="24" foregroundColor="grey" font="Regular;23" noWrap="1" options="%s">\n\t\t\t<convert type="OAWeather">city</convert>\n\t\t</widget>' % (we["x"], we["y"], we["w"] - 86, we["h"], RUN_OPTS))
	return x


def cinema_sib(skin, key, on, off):
	x = []
	x.append(box(on["dim"], "steThemeOverlay", 1))
	x += poster(skin, "session.Event_Now", on["poster_now"], key, 0)
	x += _shown(on["now_label"], off["now_label"], key, lambda g, a: _with_showif('\t\t<widget source="session.CurrentService" render="Label" %s transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;24" noWrap="1">\n\t\t\t<convert type="ServiceName">NameOnly</convert>\n\t\t</widget>' % pos(g), a))
	x += text_variants("session.Event_Now", [("EventName", "Name")], on["now_title"], off["now_title"], 56, "foreground", T_OPTS, key)
	for g, inv in ((on["now_meta"], ""), (off["now_meta"], ",Invert")):
		arg = "%s,True%s" % (key, inv)
		sh = "\t<convert type=\"CineViewMLAShowIf\">%s</convert>\n\t\t</widget>" % arg
		x += times_sw("session.Event_Now", dict(g, w=260), 27, "grey", arg)
		x.append(label("session.Event_Now", dict(g, x=g["x"] + 280, w=140), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 27, "grey").replace("</widget>", sh))
		x.append(label("session.Event_Now", dict(g, x=g["x"] + 430, w=g["w"] - 430 - 260), [("EventName", "Genre")], 27, "grey", ' noWrap="1"').replace("</widget>", sh))
		x.append(label("session.Event_Now", dict(g, x=g["x"] + g["w"] - 250, w=130), [("CineViewMLAIMDb", "Plain")], 27, "foreground", ' halign="right"').replace("</widget>", sh))
		x.append(label("session.Event_Now", dict(g, x=g["x"] + g["w"] - 110, w=110), [("CineViewMLAIMDb", "Stars")], 22, "secondFG", ' halign="right"').replace("</widget>", sh))
	x += progress("session.Event_Now", [("EventTime", "Progress")], on["progress"], off["progress"], key)
	x += text_variants("session.Event_Now", [("EventName", "FullDescription")], on["now_desc"], off["now_desc"], 27, "foreground", D_OPTS, key)
	x.append(box(on["next_panel"], "steThemePanel", 2))
	x += poster(skin, "session.Event_Now", on["poster_next"], key, 1)
	x += caption("NEXT", on["next_label"], off["next_label"], key, 24, "secondFG")
	x += text_variants("session.Event_Next", [("EventName", "Name")], on["next_title"], off["next_title"], 36, "foreground", T_OPTS, key)
	x += times("session.Event_Next", on["next_time"], 29, "grey")
	x += text_variants("session.Event_Next", [("EventName", "FullDescription")], on["next_desc"], off["next_desc"], 25, "grey", D_OPTS, key)
	x.append(box(on["bottom_band"], "steThemePanelAlt", 2))
	x.append('\t\t<widget source="session.CurrentService" render="Picon" mode="infobar" scale="aspect" %s alphatest="blend" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % pos(on["picon"]))
	c = on["ch"]
	x.append('\t\t<widget source="session.CurrentService" render="ChannelNumber" %s transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;29" />' % pos(dict(c, w=80)))
	x.append('\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;29" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">NameOnly</convert>\n\t\t</widget>' % (pos(dict(c, x=c["x"] + 88, w=c["w"] - 88)), RUN_OPTS))
	x.append(label("session.CurrentService", on["tp"], [("CineViewMLATransponderInfo", "TransponderInfo")], 23, "grey", ' noWrap="1"'))
	t = on["tech"]
	r = t["x"] + t["w"]
	parts = [("session.FrontendStatus", "FrontendInfo", "SNR", 90, "foreground"), ("session.FrontendStatus", "FrontendInfo", "SNRdB", 120, "secondFG")]
	xx = t["x"] + 150
	x.append(static("SNR", dict(t, x=xx - 60, w=55), 23, "grey"))
	for srcn, conv, arg, w, col in parts:
		x.append(label(srcn, dict(t, x=xx, w=w), [(conv, arg)], 23, col))
		xx += w + 10
	x.append('\t\t<widget render="VideoSize" source="session.CurrentService" %s font="Regular;23" foregroundColor="grey" transparent="1" zPosition="20" />' % pos(dict(t, x=xx, w=150)))
	xx += 160
	for pm, cond, z in (("infobar/ico_format_hd.png", "IsHD", 22), ("infobar/ico_format_4k.png", "Is4K", 23)):
		x.append('\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="%s" position="%d,%d" size="60,30" zPosition="%d" alphatest="on" scale="1">\n\t\t\t<convert type="ServiceInfo">%s</convert>\n\t\t\t<convert type="ConditionalShowHide" />\n\t\t</widget>' % (pm, xx, t["y"], z, cond))
	xx += 68
	x.append('\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="infobar/ico_format_16_9.png" position="%d,%d" size="60,30" zPosition="22" alphatest="on" scale="1">\n\t\t\t<convert type="ServiceInfo">IsWidescreen</convert>\n\t\t\t<convert type="ConditionalShowHide" />\n\t\t</widget>' % (xx, t["y"]))
	xx += 70
	x.append(label("session.CurrentService", dict(t, x=xx, w=150), [("CineViewMLABitrate", "Mbps")], 23, "foreground"))
	xx += 160
	x.append('\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="#0044dd44" font="Regular;23" noWrap="1" options="%s">\n\t\t\t<convert type="CineViewMLACamInfo">Info</convert>\n\t\t</widget>' % (pos(dict(t, x=xx, w=r - xx)), RUN_OPTS))
	return [l for l in x if l]


def manifest(section, provides, path):
	import json
	json.dump({"schema": 1, "id": "cinema", "section": section, "name": "CineView Cinema", "version": "0.1.0",
		"author": "habeb-s", "license": "CineView-Proprietary", "origin": "P7 spec tools/mla/p7/spec_p7.py (user-approved direction 2026-10-03)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}}, "provides_screens": provides, "options": [],
		"preview": "preview.png"}, open(path, "w"), indent=1)


def generate(skin):
	from PIL import Image
	sep = os.path.join(skin, "mla_assets", "sep_444444.png")
	if not os.path.isfile(sep):
		os.makedirs(os.path.dirname(sep), exist_ok=True)
		Image.new("RGB", (8, 2), (0x44, 0x44, 0x44)).save(sep)
	made = []
	ib_on, ib_off = _geo(S.CINEMA_INFOBAR, S.CINEMA_INFOBAR_OFF)
	sib_on, sib_off = _geo(S.CINEMA_SIB, S.CINEMA_SIB_OFF)
	head = '<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Cinema (P7) — generated by tools/mla/p7/gen_cinema.py from spec_p7.py. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n'
	key = "config.plugins.cineviewmla.poster_infobar"
	d = os.path.join(skin, "layouts", "infobar", "cinema")
	os.makedirs(d, exist_ok=True)
	parts = [screen("InfoBar", "InfoBar", cinema_infobar(skin, key, ib_on, ib_off))]
	radio = _classic_screen(skin, "infobar", "RadioInfoBar")
	if radio:
		parts.append("\t" + radio.strip())
	open(os.path.join(d, "screens.openatv.xml"), "w", encoding="utf-8").write(head % "\n".join(parts))
	manifest("infobar", ["InfoBar"] + (["RadioInfoBar"] if radio else []), os.path.join(d, "manifest.json"))
	made.append(d)
	key = "config.plugins.cineviewmla.poster_secondinfobar"
	d = os.path.join(skin, "layouts", "secondinfobar", "cinema")
	os.makedirs(d, exist_ok=True)
	body = cinema_sib(skin, key, sib_on, sib_off)
	parts = [screen("SecondInfoBar", "Second Infobar", body), screen("SecondInfoBarSimple", "Second Infobar", body)]
	ecm = _classic_screen(skin, "secondinfobar", "SecondInfoBarECM")
	if ecm:
		parts.append("\t" + ecm.strip())
	open(os.path.join(d, "screens.openatv.xml"), "w", encoding="utf-8").write(head % "\n".join(parts))
	manifest("secondinfobar", ["SecondInfoBar", "SecondInfoBarSimple"] + (["SecondInfoBarECM"] if ecm else []), os.path.join(d, "manifest.json"))
	made.append(d)
	return made


if __name__ == "__main__":
	print(generate(sys.argv[1]))
