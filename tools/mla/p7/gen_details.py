#!/usr/bin/env python3
"""Generate the CineView "Details" layout packs (infobar + secondinfobar) from spec_p7.py.

Geometry comes ONLY from the approved spec (no second copy of coordinates); this module maps each spec
element to OpenATV 8.0.1 (57b7a51) widgets that the Classic packs already use on the device:
Picon, ChannelNumber, RunningText, Label, Progress, Pixmap+ServiceInfo+ConditionalShowHide, VideoSize,
FrontendInfo, EventName/EventTime(+ClockToText), CineViewMLA* converters, CineViewMLAPosterX, OAWeather.
New EventInfo tokens used: EventTime Duration (+ClockToText InMinutes) and EventName Genre (native,
source-checked; shown only when the EPG provides them).

Rules implemented here:
* posters off  -> poster + frame hidden (renderer toggle / ConfigEntryTest chain) and the text widgets
                  switch to their wider variant (CineViewMLAShowIf <key>,True[,Invert]);
* right-to-left texts -> right-aligned variant (CineViewMLAShowIf ...,dir=rtl), as in Classic;
* long titles/descriptions -> RunningText swimming (vertical) inside boxes that are whole multiples of
  the line pitch: nothing is cut, the text scrolls inside its box;
* colours are theme roles (steTheme*, secondFG, foreground, grey) or Classic's neutral greys.
usage (called by build.py): generate(skin_dir) -> list of created files
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_p7 as S  # noqa: E402

FRAME_DIR = "mla_assets"
T_OPTS = "movetype=swimming,direction=top,step=1,steptime=70,startdelay=3000,pause=3000,repeat=0,always=0,wrap=1"
D_OPTS = "movetype=swimming,direction=top,step=1,steptime=60,startdelay=4000,pause=3000,repeat=0,always=0,wrap=1"
# one-line service/provider/city fields: horizontal SWIMMING (the start of the text is shown first; Classic's
# "running" mode slides the text in from the right edge, so a long name is half-missing for a while)
RUN_OPTS = "movetype=swimming,direction=left,step=2,steptime=55,startdelay=2500,pause=2500,repeat=0,always=0"
H_OPTS = "movetype=swimming,direction=left,step=2,steptime=50,startdelay=3000,pause=2500,repeat=0,always=0"
RTL_PAGE_OPTS = "movetype=swimming,direction=top,step=1,steptime=25,startdelay=3000,pagelength=%d,pagedelay=2500,pause=3000,repeat=0,always=0,wrap=1"
SWIM_SHORT = "movetype=swimming,direction=top,step=1,steptime=70,startdelay=2200,pause=1400,repeat=0,always=0"


def _geo(elements, off_rules):
	on = {e["id"]: e for e in S.variant(elements, off_rules, True)}
	off = {e["id"]: e for e in S.variant(elements, off_rules, False)}
	return on, off


def pos(e, dx=0, dw=0):
	return 'position="%d,%d" size="%d,%d"' % (e["x"] + dx, e["y"], e["w"] + dw, e["h"])


def label(src, e, conv, font, color="foreground", extra="", z=20):
	c = "".join("\n\t\t\t<convert type=\"%s\">%s</convert>" % (t, a) if a is not None else "\n\t\t\t<convert type=\"%s\" />" % t for t, a in conv)
	return '\t\t<widget source="%s" render="Label" %s transparent="1" zPosition="%d" foregroundColor="%s" font="Regular;%d"%s>%s\n\t\t</widget>' % (src, pos(e), z, color, font, extra, c)


def static(text, e, font, color="grey", extra=""):
	return '\t\t<eLabel text="%s" %s transparent="1" zPosition="20" foregroundColor="%s" font="Regular;%d"%s />' % (text, pos(e), color, font, extra)


def text_variants(src, conv, eon, eoff, font, color, opts, key, render="RunningText", halign=""):
	"""Poster on/off (if the geometry differs) x ltr/rtl variants of one EPG text widget."""
	out = []
	geo = lambda e: (e["x"], e["y"], e["w"], e["h"])
	geos = [(eon, "True", "")] if (eoff is None or geo(eon) == geo(eoff)) else [(eon, "True", ""), (eoff, "True", ",Invert")]
	one_line = eon["h"] < 2 * S.line_height(font)
	for g, val, inv in geos:
		k = key if len(geos) > 1 else "always"
		for d in ("ltr", "rtl"):
			ha = ' halign="right"' if d == "rtl" else halign
			o = ' options="%s"' % opts if render == "RunningText" else ""
			if render == "RunningText" and opts == T_OPTS and not one_line:
				# multi-line title boxes: page by one line pitch (whole lines on every pause, device 23:20 HRT1)
				o = ' options="%s"' % (RTL_PAGE_OPTS % S.line_height(font))
			if one_line and render == "RunningText":
				if d == "ltr":
					# one-line box, left-to-right: horizontal swimming, the start of the text first, never wraps
					o = ' options="%s" noWrap="1"' % H_OPTS
				else:
					# one-line box, right-to-left: 57b7a51 RunningText measures RTL widths wrongly in horizontal
					# mode (device rtltest 23:10: the box first shows the MIDDLE of an Arabic title).  Vertical
					# swimming shows the first line first; paging by exactly one line pitch -> whole lines only.
					o = ' options="%s"' % (RTL_PAGE_OPTS % S.line_height(font))
			c = "".join("\n\t\t\t<convert type=\"%s\">%s</convert>" % (t, a) for t, a in conv)
			out.append('\t\t<widget source="%s" render="%s" %s transparent="1" zPosition="20" foregroundColor="%s" font="Regular;%d"%s%s>%s\n\t\t\t<convert type="CineViewMLAShowIf">%s,%s%s,dir=%s</convert>\n\t\t</widget>'
				% (src, render, pos(g), color, font, ha, o, c, k, val, inv, d))
	return out


def progress(src, conv, eon, eoff, key, pixmap="infobar/pbar.png"):
	out = []
	geos = [(eon, "")] if (eoff is None or (eon["x"], eon["y"], eon["w"], eon["h"]) == (eoff["x"], eoff["y"], eoff["w"], eoff["h"])) else [(eon, ""), (eoff, ",Invert")]
	for g, inv in geos:
		c = "".join("\n\t\t\t<convert type=\"%s\">%s</convert>" % (t, a) for t, a in conv)
		sh = "\n\t\t\t<convert type=\"CineViewMLAShowIf\">%s,True%s</convert>" % (key, inv) if len(geos) > 1 else ""
		out.append('\t\t<widget source="%s" render="Progress" %s pixmap="%s" backgroundColor="un33333a" zPosition="20">%s%s\n\t\t</widget>' % (src, pos(g), pixmap, c, sh))
	return out


def poster(skin, src, e, key, nexts=None):
	"""Poster with a 3 px #505050 border (Classic style).  Under the poster widget sits the neutral CineView
	default image, so when no reliable poster exists the slot shows the default image, never an empty grey box.
	Border + default image follow the poster switch (ConfigEntryTest chain); the poster renderer its toggle."""
	from PIL import Image
	fw, fh = e["w"] + 6, e["h"] + 6
	fname = "frame_border_505050_%dx%d.png" % (fw, fh)
	fpath = os.path.join(skin, FRAME_DIR, fname)
	if not os.path.isfile(fpath):
		os.makedirs(os.path.dirname(fpath), exist_ok=True)
		im = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
		im.paste((0x50, 0x50, 0x50, 255), (0, 0, fw, 3))
		im.paste((0x50, 0x50, 0x50, 255), (0, fh - 3, fw, fh))
		im.paste((0x50, 0x50, 0x50, 255), (0, 0, 3, fh))
		im.paste((0x50, 0x50, 0x50, 255), (fw - 3, 0, fw, fh))
		im.save(fpath)
	dname = "poster_default_%dx%d.png" % (e["w"], e["h"])
	dpath = os.path.join(skin, FRAME_DIR, dname)
	if not os.path.isfile(dpath):
		src_def = os.path.join(skin, FRAME_DIR, "poster_default.jpg")
		Image.open(src_def).convert("RGB").resize((e["w"], e["h"]), Image.LANCZOS).save(dpath)
	n = ' nexts="%d"' % nexts if nexts is not None else ""
	gate = '<convert type="ConfigEntryTest">%s,False,Invert</convert><convert type="ConditionalShowHide" />' % key
	return ['\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="%s/%s" %s zPosition="19">%s</widget>' % (FRAME_DIR, dname, pos(e), gate),
		'\t\t<widget source="%s" render="CineViewMLAPosterX" %s zPosition="20"%s toggle="%s" />' % (src, pos(e), n, key),
		'\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="%s/%s" position="%d,%d" size="%d,%d" zPosition="21" alphatest="blend">%s</widget>' % (FRAME_DIR, fname, e["x"] - 3, e["y"] - 3, fw, fh, gate)]


def box(e, color, z=5):
	return '\t\t<eLabel %s backgroundColor="%s" zPosition="%d" />' % (pos(e), color, z)


def times(src, e, font, color):
	"""'HH:MM – HH:MM' right-aligned inside e: start | dash | end (Classic's proven converters)."""
	x, y, w, h = e["x"], e["y"], e["w"], e["h"]
	ew = int(font * 2.9)
	return [label(src, dict(e, x=x + w - ew, w=ew), [("EventTime", "EndTime"), ("ClockToText", "Format:%H:%M")], font, color, ' halign="right"'),
		# the dash comes from the event too (strftime of a literal), so a slot without an event shows nothing
		label(src, dict(e, x=x + w - ew - int(font * 0.9), w=int(font * 0.9)), [("EventTime", "StartTime"), ("ClockToText", "Format:–")], font, color, ' halign="center"'),
		label(src, dict(e, x=x + w - 2 * ew - int(font * 0.9), w=ew), [("EventTime", "StartTime"), ("ClockToText", "Format:%H:%M")], font, color, ' halign="right"')]


def details_strip(skin, key, on, off):
	"""The Details InfoBar strip (used by InfoBar and, unchanged, at the bottom of SecondInfoBar)."""
	x = []
	x.append(box(on["panel"], "steThemePanel", 5))
	x.append(box(on["frame_top"], "#007c7c7c", 6))
	x.append(box(on["colA_sep"], "#00444444", 8))
	x.append(box(on["colC_sep"], "#00444444", 8))
	x.append(box(on["sep_next"], "#00444444", 8) if "sep_next" in on else "")
	# column A — service
	x.append('\t\t<widget source="session.CurrentService" render="Picon" mode="infobar" scale="aspect" %s alphatest="blend" transparent="1" zPosition="20">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % pos(on["picon"]))
	x.append('\t\t<widget source="session.CurrentService" render="ChannelNumber" %s transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;34" />' % pos(on["ch_number"]))
	x.append('\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;25" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">NameOnly</convert>\n\t\t</widget>' % (pos(on["ch_name"]), RUN_OPTS))
	x.append('\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="grey" font="Regular;22" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">Provider</convert>\n\t\t</widget>' % (pos(on["provider"]), RUN_OPTS))
	x.append(label("session.CurrentService", on["tp"], [("CineViewMLATransponderInfo", "TransponderInfo")], 22, "grey", ' valign="top"'))
	x.append('\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="#0044dd44" font="Regular;21" valign="top" options="%s">\n\t\t\t<convert type="CineViewMLACamInfo">Info</convert>\n\t\t</widget>' % (pos(on["cam"]), SWIM_SHORT))
	# column B — now / next
	x += poster(skin, "session.Event_Now", on["poster_now"], key)
	x += text_variants("session.Event_Now", [("EventName", "Name")], on["now_title"], off["now_title"], 36, "foreground", T_OPTS, key)
	x += times("session.Event_Now", on["now_time"], 27, "secondFG")
	x += progress("session.Event_Now", [("EventTime", "Progress")], on["progress"], off["progress"], key)
	# now_info row: duration | genre | IMDb — separate boxes, each empty when the EPG has no data
	for g, inv in ((on["now_info"], ""), (off["now_info"], ",Invert")):
		x0 = g["x"]
		x.append(label("session.Event_Now", dict(g, x=x0, w=130), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 22, "grey", "", 20).replace("</widget>", "\t<convert type=\"CineViewMLAShowIf\">%s,True%s</convert>\n\t\t</widget>" % (key, inv)))
		x.append(label("session.Event_Now", dict(g, x=x0 + 140, w=g["w"] - 140 - 230), [("EventName", "Genre")], 22, "grey", ' noWrap="1"', 20).replace("</widget>", "\t<convert type=\"CineViewMLAShowIf\">%s,True%s</convert>\n\t\t</widget>" % (key, inv)))
		x.append(label("session.Event_Now", dict(g, x=g["x"] + g["w"] - 220, w=120), [("CineViewMLAIMDb", "Plain,hide")], 22, "foreground", ' halign="right"', 20).replace("</widget>", "\t<convert type=\"CineViewMLAShowIf\">%s,True%s</convert>\n\t\t</widget>" % (key, inv)))
		x.append(label("session.Event_Now", dict(g, x=g["x"] + g["w"] - 95, w=95), [("CineViewMLAIMDb", "Stars,hide")], 20, "secondFG", ' halign="right"', 20).replace("</widget>", "\t<convert type=\"CineViewMLAShowIf\">%s,True%s</convert>\n\t\t</widget>" % (key, inv)))
	x += text_variants("session.Event_Now", [("EventName", "ShortDescription")], on["now_short"], off["now_short"], 22, "foreground", D_OPTS, key)
	x.append(static("NEXT", on["next_label"], 22, "secondFG"))
	x += text_variants("session.Event_Next", [("EventName", "Name")], on["next_title"], off["next_title"], 28, "foreground", T_OPTS, key)
	x += times("session.Event_Next", on["next_time"], 24, "grey")
	x += text_variants("session.Event_Next", [("EventName", "ShortDescription")], on["next_short"], off["next_short"], 21, "grey", D_OPTS, key)
	# column C — technical (live sources only; no fixed values)
	x.append(static("SNR", on["snr_l"], 21, "grey"))
	x += progress("session.FrontendStatus", [("FrontendInfo", "SNR")], on["snr_bar"], None, key, "window/progress.png")
	x.append(label("session.FrontendStatus", on["snr_v"], [("FrontendInfo", "SNR")], 21, "foreground", ' halign="right"'))
	db = on["db"]
	x.append(label("session.FrontendStatus", dict(db, w=120), [("FrontendInfo", "SNRdB")], 21, "secondFG"))
	x.append(static("AGC", dict(db, x=db["x"] + 125, w=50), 21, "grey"))
	x.append(label("session.FrontendStatus", dict(db, x=db["x"] + 178, w=80), [("FrontendInfo", "AGC")], 21, "foreground"))
	x.append(static("BER", dict(db, x=db["x"] + 268, w=50), 21, "grey"))
	x.append(label("session.FrontendStatus", dict(db, x=db["x"] + 320, w=86), [("FrontendInfo", "BER")], 21, "foreground"))
	x.append('\t\t<widget render="VideoSize" source="session.CurrentService" %s font="Regular;21" transparent="1" zPosition="20" />' % pos(on["video"]))
	for eid, pm, cond in (("chips", "infobar/ico_format_hd.png", "IsHD"), ("chips", "infobar/ico_format_4k.png", "Is4K"), ("chips2", "infobar/ico_format_16_9.png", "IsWidescreen"), ("chips3", "infobar/ico_txt_on.png", "HasTelext")):
		e = on[eid]
		x.append('\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="%s" %s zPosition="22" alphatest="on" scale="1">\n\t\t\t<convert type="ServiceInfo">%s</convert>\n\t\t\t<convert type="ConditionalShowHide" />\n\t\t</widget>' % (pm, pos(e), cond))
	br = on["bitrate"]
	x.append(static("Bitrate", dict(br, w=90), 21, "grey"))
	x.append(label("session.CurrentService", dict(br, x=br["x"] + 92, w=br["w"] - 92), [("CineViewMLABitrate", "Mbps")], 21, "foreground"))
	x.append(label("session.CurrentService", on["cpu"], [("CineViewMLACPUTemp", "Short")], 21, "grey"))
	ob = on["orbital"]
	x.append(label("session.CurrentService", dict(ob, w=110), [("ServiceOrbitalPosition", None)], 21, "grey"))
	x.append('\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="grey" font="Regular;21" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">Provider</convert>\n\t\t</widget>' % (pos(dict(ob, x=ob["x"] + 115, w=ob["w"] - 115)), RUN_OPTS))
	we = on["weather"]
	x.append('\t\t<widget source="session.OAWeather" render="OAWeatherPixmap" position="%d,%d" size="30,30" transparent="1" zPosition="24" alphatest="blend">\n\t\t\t<convert type="OAWeather">weathericon,current</convert>\n\t\t</widget>' % (we["x"], we["y"]))
	x.append('\t\t<widget source="session.OAWeather" render="RunningText" position="%d,%d" size="%d,30" transparent="1" zPosition="24" foregroundColor="foreground" font="Regular;22" noWrap="1" options="%s">\n\t\t\t<convert type="OAWeather">city</convert>\n\t\t</widget>' % (we["x"] + 38, we["y"], we["w"] - 38 - 90, RUN_OPTS))
	x.append('\t\t<widget source="session.OAWeather" render="Label" position="%d,%d" size="86,30" transparent="1" zPosition="24" foregroundColor="secondFG" font="Regular;22" halign="right">\n\t\t\t<convert type="OAWeather">temperature_current</convert>\n\t\t</widget>' % (we["x"] + we["w"] - 86, we["y"]))
	return [l for l in x if l]


def screen(name, title, body, extra=""):
	return '\t<screen name="%s" title="%s" position="fill" backgroundColor="transparent" flags="wfNoBorder"%s>\n%s\n\t</screen>' % (name, title, extra, "\n".join(body))


def details_sib(skin, key, on, off, ib_on, ib_off):
	x = []
	for pid, role in (("p_now", "steThemePanel"), ("p_next", "steThemePanel"), ("p_tech", "steThemePanelAlt")):
		x.append(box(on[pid], role, 2))
	x.append(static("NOW", on["now_label"], 23, "secondFG"))
	x += times("session.Event_Now", on["now_time"], 24, "secondFG")
	x += poster(skin, "session.Event_Now", on["poster_now"], key, 0)
	x += text_variants("session.Event_Now", [("EventName", "Name")], on["now_title"], off["now_title"], 36, "foreground", T_OPTS, key)
	for g, inv in ((on["now_meta"], ""), (off["now_meta"], ",Invert")):
		sh = "\t<convert type=\"CineViewMLAShowIf\">%s,True%s</convert>\n\t\t</widget>" % (key, inv)
		x.append(label("session.Event_Now", dict(g, w=120), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], 23, "grey").replace("</widget>", sh))
		x.append(label("session.Event_Now", dict(g, x=g["x"] + 130, w=g["w"] - 130 - 230), [("EventName", "Genre")], 23, "grey", ' noWrap="1"').replace("</widget>", sh))
		x.append(label("session.Event_Now", dict(g, x=g["x"] + g["w"] - 220, w=120), [("CineViewMLAIMDb", "Plain,hide")], 23, "foreground", ' halign="right"').replace("</widget>", sh))
		x.append(label("session.Event_Now", dict(g, x=g["x"] + g["w"] - 95, w=95), [("CineViewMLAIMDb", "Stars,hide")], 20, "secondFG", ' halign="right"').replace("</widget>", sh))
	x += progress("session.Event_Now", [("EventTime", "Progress")], on["progress"], off["progress"], key)
	x += text_variants("session.Event_Now", [("EventName", "FullDescription")], on["now_desc"], off["now_desc"], 24, "foreground", D_OPTS, key)
	x.append(static("NEXT", on["next_label"], 23, "secondFG"))
	x += times("session.Event_Next", on["next_time"], 24, "grey")
	x += poster(skin, "session.Event_Now", on["poster_next"], key, 1)
	x += text_variants("session.Event_Next", [("EventName", "Name")], on["next_title"], off["next_title"], 32, "foreground", T_OPTS, key)
	x += text_variants("session.Event_Next", [("EventName", "FullDescription")], on["next_desc"], off["next_desc"], 23, "grey", D_OPTS, key)
	# technical column
	x.append(static("SIGNAL &amp; SERVICE", on["tech_label"], 21, "secondFG"))
	t = on["tech_snr"]
	x.append(static("SNR", dict(t, w=55), 21, "grey"))
	x.append(label("session.FrontendStatus", dict(t, x=t["x"] + 55, w=80), [("FrontendInfo", "SNR")], 21, "foreground"))
	x.append(label("session.FrontendStatus", dict(t, x=t["x"] + 140, w=150), [("FrontendInfo", "SNRdB")], 21, "secondFG", ' halign="right"'))
	x += progress("session.FrontendStatus", [("FrontendInfo", "SNR")], on["tech_bar"], None, key, "window/progress.png")
	a = on["tech_agc"]
	x.append(static("AGC", dict(a, w=50), 21, "grey"))
	x.append(label("session.FrontendStatus", dict(a, x=a["x"] + 52, w=80), [("FrontendInfo", "AGC")], 21, "foreground"))
	x.append(static("BER", dict(a, x=a["x"] + 150, w=50), 21, "grey"))
	x.append(label("session.FrontendStatus", dict(a, x=a["x"] + 202, w=88), [("FrontendInfo", "BER")], 21, "foreground"))
	x.append(label("session.CurrentService", on["tech_tp"], [("CineViewMLATransponderInfo", "TransponderInfo")], 21, "grey", ' valign="top"'))
	x.append('\t\t<widget source="session.CurrentService" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="#0044dd44" font="Regular;21" valign="top" options="%s">\n\t\t\t<convert type="CineViewMLACamInfo">Info</convert>\n\t\t</widget>' % (pos(on["tech_cam"]), SWIM_SHORT))
	v = on["tech_video"]
	x.append('\t\t<widget render="VideoSize" source="session.CurrentService" %s font="Regular;21" transparent="1" zPosition="20" />' % pos(dict(v, w=140)))
	for dx, pm, cond in ((150, "infobar/ico_format_hd.png", "IsHD"), (150, "infobar/ico_format_4k.png", "Is4K"), (216, "infobar/ico_format_16_9.png", "IsWidescreen")):
		x.append('\t\t<widget source="session.CurrentService" render="Pixmap" pixmap="%s" position="%d,%d" size="60,28" zPosition="22" alphatest="on" scale="1">\n\t\t\t<convert type="ServiceInfo">%s</convert>\n\t\t\t<convert type="ConditionalShowHide" />\n\t\t</widget>' % (pm, v["x"] + dx, v["y"], cond))
	b = on["tech_bitrate"]
	x.append(static("Bitrate", dict(b, w=90), 21, "grey"))
	x.append(label("session.CurrentService", dict(b, x=b["x"] + 92, w=b["w"] - 92), [("CineViewMLABitrate", "Mbps")], 21, "foreground"))
	x.append(label("session.CurrentService", on["tech_cpu"], [("CineViewMLACPUTemp", "Short")], 21, "grey"))
	we = on["tech_weather"]
	x.append('\t\t<widget source="session.OAWeather" render="OAWeatherPixmap" position="%d,%d" size="30,30" transparent="1" zPosition="24" alphatest="blend">\n\t\t\t<convert type="OAWeather">weathericon,current</convert>\n\t\t</widget>' % (we["x"], we["y"]))
	x.append('\t\t<widget source="session.OAWeather" render="RunningText" position="%d,%d" size="%d,30" transparent="1" zPosition="24" foregroundColor="foreground" font="Regular;22" noWrap="1" options="%s">\n\t\t\t<convert type="OAWeather">city</convert>\n\t\t</widget>' % (we["x"] + 38, we["y"], we["w"] - 38 - 90, RUN_OPTS))
	x.append('\t\t<widget source="session.OAWeather" render="Label" position="%d,%d" size="86,30" transparent="1" zPosition="24" foregroundColor="secondFG" font="Regular;22" halign="right">\n\t\t\t<convert type="OAWeather">temperature_current</convert>\n\t\t</widget>' % (we["x"] + we["w"] - 86, we["y"]))
	# bottom: the Details InfoBar strip (same family), its posters follow the SecondInfoBar switch
	x += details_strip(skin, key, ib_on, ib_off)
	return x


def _classic_screen(skin, section, name):
	src = open(os.path.join(skin, "layouts", section, "classic", "screens.openatv.xml"), encoding="utf-8").read()
	m = re.search(r'\t?<screen name="%s".*?</screen>' % re.escape(name), src, re.S)
	return m.group(0) if m else None


def manifest(section, provides, path):
	import json
	json.dump({"schema": 1, "id": "details", "section": section, "name": "CineView Details", "version": "0.1.0",
		"author": "habeb-s", "license": "CineView-Proprietary", "origin": "P7 spec tools/mla/p7/spec_p7.py (user-approved direction 2026-10-03)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}}, "provides_screens": provides, "options": [],
		"preview": "preview.png"}, open(path, "w"), indent=1)


def generate(skin):
	made = []
	ib_on, ib_off = _geo(S.DETAILS_INFOBAR, S.DETAILS_INFOBAR_OFF)
	sib_on, sib_off = _geo(S.DETAILS_SIB, S.DETAILS_SIB_OFF)
	for e in list(ib_on.values()) + list(sib_on.values()):
		assert 0 <= e["x"] and e["x"] + e["w"] <= 1920 and 0 <= e["y"] and e["y"] + e["h"] <= 1080, e["id"]
	# infobar pack: InfoBar = Details strip; RadioInfoBar kept as Classic (not part of the P7 spec).
	key = "config.plugins.cineviewmla.poster_infobar"
	d = os.path.join(skin, "layouts", "infobar", "details")
	os.makedirs(d, exist_ok=True)
	parts = [screen("InfoBar", "InfoBar", details_strip(skin, key, ib_on, ib_off))]
	radio = _classic_screen(skin, "infobar", "RadioInfoBar")
	if radio:
		parts.append(radio.strip("\n"))
	open(os.path.join(d, "screens.openatv.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Details (P7) — generated by tools/mla/p7/gen_details.py from spec_p7.py. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % "\n".join("\t" + p.strip() if not p.startswith("\t") else p for p in parts))
	manifest("infobar", ["InfoBar"] + (["RadioInfoBar"] if radio else []), os.path.join(d, "manifest.json"))
	made.append(d)
	# secondinfobar pack: SecondInfoBar + SecondInfoBarSimple (same Details layout); SecondInfoBarECM kept Classic.
	key = "config.plugins.cineviewmla.poster_secondinfobar"
	d = os.path.join(skin, "layouts", "secondinfobar", "details")
	os.makedirs(d, exist_ok=True)
	body = details_sib(skin, key, sib_on, sib_off, ib_on, ib_off)
	parts = [screen("SecondInfoBar", "Second Infobar", body), screen("SecondInfoBarSimple", "Second Infobar", body)]
	ecm = _classic_screen(skin, "secondinfobar", "SecondInfoBarECM")
	if ecm:
		parts.append(ecm.strip("\n"))
	open(os.path.join(d, "screens.openatv.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView Details (P7) — generated by tools/mla/p7/gen_details.py from spec_p7.py. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % "\n".join("\t" + p.strip() if not p.startswith("\t") else p for p in parts))
	manifest("secondinfobar", ["SecondInfoBar", "SecondInfoBarSimple"] + (["SecondInfoBarECM"] if ecm else []), os.path.join(d, "manifest.json"))
	made.append(d)
	return made


if __name__ == "__main__":
	print(generate(sys.argv[1]))
