#!/usr/bin/env python3
"""P7 design specification — CineView "Cinema" and "Details" for Main InfoBar and SecondInfoBar (OpenATV 8.0.1).

Single source of truth: every element below has its exact 1920x1080 geometry, its Enigma2 source/converter
(contract status) and its style.  render_p7.py draws the mockups and the dimension sheets from THIS data,
and the later XML implementation will be generated/checked against it, so the approved picture and the
implementation cannot drift apart.

Contract status per element:
  "classic"  = the same source+converter/renderer is already used by the approved Classic layout and is
               device-verified on 57b7a51 (Slot 8);
  "verify"   = native token of the unified EventInfo converter on 57b7a51 (source-checked: ShortDescription,
               Duration, Remaining, Genre exist in lib/python/Components/Converter/EventInfo.py) but not yet used
               by CineView -> runtime-verified on the device when implemented.
Colours are THEME ROLES (steTheme*), never literal navy, so every design follows the 6 themes.
"""

W, H = 1920, 1080


def line_height(size):
	"""Enigma2 line pitch of LiberationSans at <size>: hinted ascent (round) + descent (ceil) of the 2048-unit
	face (asc 1854, desc 434).  Device-measured 2026-10-03 on 57b7a51: 21->24, 22->25, 23->26, 24->28, 25->29.
	(The earlier linear fit int(size*1.16+0.5) was wrong for 22 and 23: a 10-line 23-px box showed half an 11th line.)"""
	import math
	return int(round(size * 1854 / 2048.0)) + int(math.ceil(size * 434 / 2048.0))

# Theme role -> navy value (for the mockups only; the skin uses the role names)
ROLES = {
	"primary": "#0A1D35", "panel": "#08182B", "panelAlt": "#071323", "top": "#06111F",
	"overlay": (8, 24, 43, 210), "overlayStrong": (7, 19, 35, 171),
	"text": "#F0F0F0", "muted": "#B6B6B6", "accent": "#F9C731", "frame": "#7C7C7C", "sep": "#444444",
	"green": "#44DD44",
}

# element: id, kind, x, y, w, h, extra
#  kind: band(img/gradient), panel(role), poster, picon, text, progress, chip, sep
# "src" = Enigma2 source / renderer(converter) used, "status" = contract status


def E(id, kind, x, y, w, h, **kw):
	d = {"id": id, "kind": kind, "x": x, "y": y, "w": w, "h": h}
	d.update(kw)
	return d


TECH_CLASSIC = "classic"
VERIFY = "verify"

# ---------------------------------------------------------------------------------------------- CINEMA
CINEMA_INFOBAR = [
	E("band", "band", 0, 730, 1920, 350, role="overlayStrong", src="ePixmap active/assets/infobar/bl80.png (theme bitmap, scaled)", status=TECH_CLASSIC),
	E("poster_now", "poster", 60, 742, 186, 279, src="session.Event_Now → CineViewMLAPosterX (toggle poster_infobar)", status=TECH_CLASSIC, poster=True),
	E("picon", "picon", 276, 786, 220, 132, src="session.CurrentService → Picon (ServiceName Reference)", status=TECH_CLASSIC),
	E("ch_number", "text", 276, 930, 64, 34, text="146", size=26, role="accent", src="session.CurrentService → ChannelNumber", status=TECH_CLASSIC),
	E("ch_name", "text", 344, 930, 152, 34, text="HBO HD", size=26, role="text", src="ServiceName NameOnly (RunningText)", status=TECH_CLASSIC),
	E("now_title", "text", 540, 774, 1010, 53, text="21 Jump Street", size=46, role="text", src="session.Event_Now → EventName Name (RunningText swimming)", status=TECH_CLASSIC),
	E("now_time", "text", 1580, 784, 280, 40, text="19:10 – 21:01", size=32, role="accent", align="right", src="EventTime StartTime/EndTime + ClockToText", status=TECH_CLASSIC),
	E("progress", "progress", 540, 842, 1320, 6, value=0.42, src="EventTime Progress (Progress renderer)", status=TECH_CLASSIC),
	E("now_short", "text", 540, 864, 1320, 29, text="Smušeni policijski dvojac dobije zadatak da se infiltrira među srednjoškolce…", size=25, role="muted", src="session.Event_Now → EventName ShortDescription (1 line; EventInfo token)", status=VERIFY),
	E("next_label", "text", 540, 914, 110, 34, text="NEXT", size=24, role="accent", src="static text", status=TECH_CLASSIC),
	E("next_title", "text", 650, 914, 900, 34, text="22 Jump Street", size=29, role="text", src="session.Event_Next → EventName Name", status=TECH_CLASSIC),
	E("next_time", "text", 1580, 912, 280, 36, text="21:01 – 22:51", size=27, role="muted", align="right", src="Event_Next EventTime + ClockToText", status=TECH_CLASSIC),
	E("sep", "sep", 540, 968, 1320, 2),
	E("tech_snr", "text", 540, 990, 150, 30, text="SNR 76%", size=23, role="muted", src="FrontendInfo SNR", status=TECH_CLASSIC),
	E("tech_res", "text", 700, 990, 150, 30, text="1920x1080", size=23, role="muted", src="VideoSize", status=TECH_CLASSIC),
	E("tech_hd", "chip", 860, 988, 60, 32, text="HD", src="ServiceInfo IsHD/Is4K + ConditionalShowHide", status=TECH_CLASSIC),
	E("tech_169", "chip", 930, 988, 60, 32, text="16:9", src="ServiceInfo IsWidescreen", status=TECH_CLASSIC),
	E("tech_bitrate", "text", 1010, 990, 190, 30, text="4.76 Mbps", size=23, role="muted", src="CineViewMLABitrate Mbps (T6-verified)", status=TECH_CLASSIC),
	E("tech_cam", "text", 1210, 990, 280, 30, text="ncam · Reader cccam", size=23, role="green", src="CineViewMLACamInfo Info", status=TECH_CLASSIC),
	E("tech_imdb", "text", 1500, 990, 160, 30, text="IMDb 7.2", size=23, role="accent", src="CineViewMLAIMDb Plain", status=TECH_CLASSIC),
	E("tech_weather", "text", 1670, 990, 190, 30, text="Hamburg 17°C", size=23, role="muted", align="right", src="OAWeather city/temperature_current", status=TECH_CLASSIC),
]
# Posters OFF: poster hidden (no frame), picon block moves left, text block widens by 216 px.
CINEMA_INFOBAR_OFF = {"hide": ["poster_now"],
	"shift": {k: -216 for k in ("picon", "ch_number", "ch_name", "next_label", "tech_snr", "tech_res", "tech_hd", "tech_169", "tech_bitrate", "tech_cam", "tech_imdb")},
	"grow_left": {k: 216 for k in ("now_title", "progress", "now_short", "next_title", "sep")}}

CINEMA_SIB = [
	E("dim", "panel", 0, 0, 1920, 1080, role="overlay", src="eLabel steThemeOverlay (full screen)", status=TECH_CLASSIC),
	E("poster_now", "poster", 90, 110, 360, 540, src="session.Event_Now → CineViewMLAPosterX (toggle poster_secondinfobar)", status=TECH_CLASSIC, poster=True),
	E("now_label", "text", 500, 112, 300, 34, text="NOW ON HBO HD", size=24, role="accent", src="static + ServiceName NameOnly", status=TECH_CLASSIC),
	E("now_title", "text", 500, 152, 1330, 65, text="21 Jump Street", size=56, role="text", src="Event_Now EventName Name (RunningText, RTL variant)", status=TECH_CLASSIC),
	E("now_meta", "text", 500, 228, 1330, 36, text="19:10 – 21:01   ·   111 min   ·   IMDb 7.2/10", size=27, role="muted", src="EventTime StartTime/EndTime + EventTime Duration (EventInfo token) + CineViewMLAIMDb", status=VERIFY),
	E("progress", "progress", 500, 276, 1330, 6, value=0.42, src="EventTime Progress", status=TECH_CLASSIC),
	E("now_desc", "text", 500, 300, 1330, 330, text="(SAD, 2012, film) Kad se policajci Schmidt i Jenko pridruže tajnoj jedinici Jump Street, iskoriste svoj mladenački izgled kako bi otišli na tajni zadatak prerušeni u srednjoškolce. Pištolje i značke zamijene ruksacima te krenu uništiti opasan lanac droge. Uloge: Jonah Hill, Channing Tatum, Brie Larson, Dave Franco, Rob Riggle.", size=27, role="text", lines=11, src="Event_Now EventName FullDescription (RunningText swimming, 11×30 px lines (pitch formula, device-check in the Cinema test), RTL variant)", status=TECH_CLASSIC),
	E("next_panel", "panel", 60, 690, 1800, 220, role="panel", src="eLabel steThemePanel", status=TECH_CLASSIC),
	E("poster_next", "poster", 90, 705, 127, 190, src="CineViewMLAPosterX nexts=1 (event-chained, 83adaa3)", status=TECH_CLASSIC, poster=True),
	E("next_label", "text", 250, 712, 200, 32, text="NEXT", size=24, role="accent", src="static", status=TECH_CLASSIC),
	E("next_title", "text", 250, 747, 1250, 42, text="22 Jump Street", size=36, role="text", src="Event_Next EventName Name", status=TECH_CLASSIC),
	E("next_time", "text", 1520, 750, 310, 40, text="21:01 – 22:51", size=29, role="muted", align="right", src="Event_Next EventTime + ClockToText", status=TECH_CLASSIC),
	E("next_desc", "text", 250, 800, 1580, 87, text="Nakon što su dvaput prošli kroz srednju školu, velike promjene čekaju policajce na tajnom zadatku Schmidta i Jenka…", size=25, role="muted", lines=3, src="Event_Next EventName FullDescription (3 lines, swimming)", status=TECH_CLASSIC),
	E("bottom_band", "panel", 0, 940, 1920, 140, role="panelAlt", src="eLabel steThemePanelAlt", status=TECH_CLASSIC),
	E("picon", "picon", 60, 958, 170, 102, src="Picon", status=TECH_CLASSIC),
	E("ch", "text", 250, 966, 400, 36, text="146  HBO HD", size=29, role="text", src="ChannelNumber + ServiceName", status=TECH_CLASSIC),
	E("tp", "text", 250, 1010, 600, 30, text="DVB-S2 11636 H 30000 5/6 8PSK · 16.0°E", size=23, role="muted", src="CineViewMLATransponderInfo", status=TECH_CLASSIC),
	E("tech", "text", 900, 1010, 960, 30, text="SNR 76% · 12.3 dB · 1920x1080 · HD · 16:9 · 4.76 Mbps · ncam", size=23, role="muted", align="right", src="FrontendInfo, VideoSize, ServiceInfo, CineViewMLABitrate, CamInfo", status=TECH_CLASSIC),
]
CINEMA_SIB_OFF = {"hide": ["poster_now", "poster_next"], "grow_left": {"now_label": 410, "now_title": 410, "now_meta": 410, "progress": 410, "now_desc": 410, "next_label": 160, "next_title": 160, "next_desc": 160}}

# ---------------------------------------------------------------------------------------------- DETAILS
DETAILS_INFOBAR = [
	E("panel", "panel", 24, 770, 1872, 290, role="panel", src="eLabel steThemePanel", status=TECH_CLASSIC),
	E("frame_top", "sep", 24, 770, 1872, 2),
	E("colA_sep", "sep", 440, 786, 2, 258),
	E("colC_sep", "sep", 1450, 786, 2, 258),
	# column A: service
	E("picon", "picon", 44, 786, 220, 132, src="Picon", status=TECH_CLASSIC),
	E("ch_number", "text", 276, 790, 150, 40, text="146", size=34, role="accent", src="ChannelNumber", status=TECH_CLASSIC),
	E("ch_name", "text", 276, 836, 150, 30, text="HBO HD", size=25, role="text", src="ServiceName NameOnly", status=TECH_CLASSIC),
	E("provider", "text", 276, 870, 150, 28, text="A1 HR", size=22, role="muted", src="ServiceName Provider", status=TECH_CLASSIC),
	E("tp", "text", 44, 930, 380, 50, text="DVB-S2 11636 H 30000\n5/6 8PSK · 16.0°E", size=22, role="muted", lines=2, src="CineViewMLATransponderInfo", status=TECH_CLASSIC),
	E("cam", "text", 44, 1000, 380, 48, text="ncam-15.8 · Reader: cccam", size=21, role="green", src="CineViewMLACamInfo Info", status=TECH_CLASSIC),
	# column B: now / next
	E("poster_now", "poster", 462, 790, 105, 158, src="Event_Now CineViewMLAPosterX (toggle poster_infobar)", status=TECH_CLASSIC, poster=True),
	E("now_title", "text", 585, 786, 600, 42, text="21 Jump Street", size=36, role="text", src="Event_Now EventName Name", status=TECH_CLASSIC),
	E("now_time", "text", 1190, 790, 240, 36, text="19:10 – 21:01", size=27, role="accent", align="right", src="EventTime + ClockToText", status=TECH_CLASSIC),
	E("progress", "progress", 585, 836, 845, 6, value=0.42, src="EventTime Progress", status=TECH_CLASSIC),
	E("now_info", "text", 585, 850, 845, 30, text="111 min  ·  +64 min left  ·  Film  ·  IMDb 7.2", size=22, role="muted", src="EventTime Duration / Remaining + EventName Genre (EventInfo tokens), CineViewMLAIMDb", status=VERIFY),
	E("now_short", "text", 585, 884, 845, 50, text="Smušeni policijski dvojac dobije zadatak da se infiltrira među srednjoškolce kako bi otkrili tko stoji iza prodaje…", size=22, role="text", lines=2, src="EventName ShortDescription (2 lines)", status=VERIFY),
	E("sep_next", "sep", 462, 958, 968, 2),
	E("next_label", "text", 462, 972, 110, 32, text="NEXT", size=22, role="accent", src="static", status=TECH_CLASSIC),
	E("next_title", "text", 585, 970, 600, 32, text="22 Jump Street", size=28, role="text", src="Event_Next EventName Name", status=TECH_CLASSIC),
	E("next_time", "text", 1190, 972, 240, 32, text="21:01 – 22:51", size=24, role="muted", align="right", src="Event_Next EventTime", status=TECH_CLASSIC),
	E("next_short", "text", 585, 1010, 845, 24, text="Nakon što su dvaput prošli kroz srednju školu…", size=21, role="muted", src="Event_Next ShortDescription (1 line)", status=VERIFY),
	# column C: technical
	E("snr_l", "text", 1470, 790, 120, 28, text="SNR", size=21, role="muted", src="static", status=TECH_CLASSIC),
	E("snr_bar", "progress", 1590, 801, 180, 8, value=0.76, src="FrontendInfo SNR (Progress, theme bitmap window/progress.png)", status=TECH_CLASSIC),
	E("snr_v", "text", 1780, 790, 96, 28, text="76%", size=21, role="text", align="right", src="FrontendInfo SNR", status=TECH_CLASSIC),
	E("db", "text", 1470, 824, 406, 28, text="12.3 dB · AGC 76% · BER 0", size=21, role="muted", src="FrontendInfo SNRdB / AGC / BER", status=TECH_CLASSIC),
	E("video", "text", 1470, 858, 200, 28, text="1920x1080", size=21, role="text", src="VideoSize", status=TECH_CLASSIC),
	E("chips", "chip", 1680, 856, 60, 30, text="HD", src="ServiceInfo IsHD/Is4K", status=TECH_CLASSIC),
	E("chips2", "chip", 1746, 856, 60, 30, text="16:9", src="ServiceInfo IsWidescreen", status=TECH_CLASSIC),
	E("chips3", "chip", 1812, 856, 64, 30, text="TXT", src="ServiceInfo HasTelext", status=TECH_CLASSIC),
	E("bitrate", "text", 1470, 894, 406, 28, text="Bitrate 4.76 Mbps", size=21, role="text", src="CineViewMLABitrate Mbps", status=TECH_CLASSIC),
	E("cpu", "text", 1470, 928, 406, 28, text="CPU 57°C", size=21, role="muted", src="CineViewMLACPUTemp Short", status=TECH_CLASSIC),
	E("orbital", "text", 1470, 962, 406, 28, text="16.0°E · A1 HR", size=21, role="muted", src="ServiceOrbitalPosition + Provider", status=TECH_CLASSIC),
	E("weather", "text", 1470, 1008, 406, 30, text="Hamburg 17°C", size=22, role="text", src="OAWeather", status=TECH_CLASSIC),
]
DETAILS_INFOBAR_OFF = {"hide": ["poster_now"], "grow_left": {k: 123 for k in ("now_title", "progress", "now_info", "now_short", "next_short")}}

DETAILS_SIB = [
	E("p_now", "panel", 24, 110, 900, 600, role="panel", src="eLabel steThemePanel", status=TECH_CLASSIC),
	E("p_next", "panel", 940, 110, 610, 600, role="panel", src="eLabel steThemePanel", status=TECH_CLASSIC),
	E("p_tech", "panel", 1566, 110, 330, 600, role="panelAlt", src="eLabel steThemePanelAlt", status=TECH_CLASSIC),
	E("now_label", "text", 50, 126, 200, 30, text="NOW", size=23, role="accent", src="static", status=TECH_CLASSIC),
	E("now_time", "text", 600, 126, 300, 30, text="19:10 – 21:01", size=24, role="accent", align="right", src="EventTime + ClockToText", status=TECH_CLASSIC),
	E("poster_now", "poster", 50, 166, 205, 308, src="CineViewMLAPosterX (toggle poster_secondinfobar)", status=TECH_CLASSIC, poster=True),
	E("now_title", "text", 275, 166, 625, 82, text="21 Jump Street", size=36, role="text", lines=2, src="EventName Name (2 lines, RTL variant)", status=TECH_CLASSIC),
	E("now_meta", "text", 275, 266, 625, 30, text="111 min · Film · IMDb 7.2/10", size=23, role="muted", src="EventTime Duration + EventName Genre (EventInfo tokens), CineViewMLAIMDb", status=VERIFY),
	E("progress", "progress", 275, 306, 625, 6, value=0.42, src="EventTime Progress", status=TECH_CLASSIC),
	E("now_desc", "text", 275, 326, 625, 336, text="(SAD, 2012, film) Kad se policajci Schmidt i Jenko pridruže tajnoj jedinici Jump Street, iskoriste svoj mladenački izgled kako bi otišli na tajni zadatak prerušeni u srednjoškolce. Pištolje i značke zamijene ruksacima te krenu uništiti opasan lanac droge. Uloge: Jonah Hill, Channing Tatum, Brie Larson, Dave Franco, Rob Riggle.", size=24, role="text", lines=12, src="EventName FullDescription (12×28 px, swimming, RTL variant)", status=TECH_CLASSIC),
	E("next_label", "text", 966, 126, 200, 30, text="NEXT", size=23, role="accent", src="static", status=TECH_CLASSIC),
	E("next_time", "text", 1230, 126, 300, 30, text="21:01 – 22:51", size=24, role="muted", align="right", src="Event_Next EventTime", status=TECH_CLASSIC),
	E("poster_next", "poster", 966, 166, 140, 210, src="CineViewMLAPosterX nexts=1", status=TECH_CLASSIC, poster=True),
	E("next_title", "text", 1124, 166, 406, 72, text="22 Jump Street", size=32, role="text", lines=2, src="Event_Next EventName Name", status=TECH_CLASSIC),
	E("next_desc", "text", 966, 392, 564, 260, text="Nakon što su dvaput prošli kroz srednju školu, velike promjene čekaju policajce na tajnom zadatku Schmidta i Jenka kada moraju glumiti studente i razotkriti neuhvatljivoga dilera droge na kampusu.", size=23, role="muted", lines=10, src="Event_Next FullDescription (10×26 px, swimming)", status=TECH_CLASSIC),
	E("tech_label", "text", 1586, 126, 290, 30, text="SIGNAL & SERVICE", size=21, role="accent", src="static", status=TECH_CLASSIC),
	E("tech_snr", "text", 1586, 170, 290, 28, text="SNR 76%  ·  12.3 dB", size=21, role="text", src="FrontendInfo SNR/SNRdB", status=TECH_CLASSIC),
	E("tech_bar", "progress", 1586, 204, 290, 8, value=0.76, src="FrontendInfo SNR", status=TECH_CLASSIC),
	E("tech_agc", "text", 1586, 222, 290, 28, text="AGC 76%  ·  BER 0", size=21, role="muted", src="FrontendInfo AGC/BER", status=TECH_CLASSIC),
	E("tech_tp", "text", 1586, 266, 290, 72, text="DVB-S2 · 11636 H\n30000 · 5/6 · 8PSK\n16.0°E", size=21, role="muted", lines=3, src="CineViewMLATransponderInfo", status=TECH_CLASSIC),
	E("tech_cam", "text", 1586, 352, 290, 72, text="ncam-15.8\nReader: cccam", size=21, role="green", lines=3, src="CineViewMLACamInfo", status=TECH_CLASSIC),
	E("tech_video", "text", 1586, 474, 290, 28, text="1920x1080  HD  16:9", size=21, role="text", src="VideoSize, ServiceInfo", status=TECH_CLASSIC),
	E("tech_bitrate", "text", 1586, 508, 290, 28, text="4.76 Mbps", size=21, role="text", src="CineViewMLABitrate", status=TECH_CLASSIC),
	E("tech_cpu", "text", 1586, 542, 290, 28, text="CPU 57°C", size=21, role="muted", src="CineViewMLACPUTemp", status=TECH_CLASSIC),
	E("tech_weather", "text", 1586, 650, 290, 32, text="Hamburg 17°C", size=22, role="text", src="OAWeather", status=TECH_CLASSIC),
]
# SecondInfoBar Details keeps the Details InfoBar strip at the bottom (same as Classic keeps its InfoBar).
DETAILS_SIB_BOTTOM = True
DETAILS_SIB_OFF = {"hide": ["poster_now", "poster_next"], "grow_left": {"now_title": 225, "now_meta": 225, "progress": 225, "now_desc": 225, "next_title": 158},
	# posters off: the next description moves up under the (2-line) next title: 15 lines x 26 px
	"set": {"next_desc": {"y": 256, "h": 390}}}

DESIGNS = {
	"cinema": {"label": "Cinema", "infobar": (CINEMA_INFOBAR, CINEMA_INFOBAR_OFF), "secondinfobar": (CINEMA_SIB, CINEMA_SIB_OFF)},
	"details": {"label": "Details", "infobar": (DETAILS_INFOBAR, DETAILS_INFOBAR_OFF), "secondinfobar": (DETAILS_SIB, DETAILS_SIB_OFF)},
}


def variant(elements, off_rules, posters_on):
	"""Apply the posters-off rules -> list of elements actually shown."""
	if posters_on:
		return [dict(e) for e in elements]
	out = []
	for e in elements:
		if e["id"] in off_rules.get("hide", []):
			continue
		e = dict(e)
		if e["id"] in off_rules.get("shift", {}):
			e["x"] += off_rules["shift"][e["id"]]
		e.update(off_rules.get("set", {}).get(e["id"], {}))
		if e["id"] in off_rules.get("grow_left", {}):
			d = off_rules["grow_left"][e["id"]]
			e["x"] -= d
			e["w"] += d
		out.append(e)
	return out


def check(elements):
	"""Static design checks: inside 1920x1080 safe frame, no text box overlaps another text box."""
	problems = []
	texts = [e for e in elements if e["kind"] in ("text", "chip", "poster", "picon")]
	for e in elements:
		if e["x"] < 0 or e["y"] < 0 or e["x"] + e["w"] > W or e["y"] + e["h"] > H:
			problems.append("%s outside the screen" % e["id"])
	for i, a in enumerate(texts):
		for b in texts[i + 1:]:
			if a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]:
				problems.append("overlap %s / %s" % (a["id"], b["id"]))
	return problems
