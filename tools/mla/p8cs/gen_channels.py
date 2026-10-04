#!/usr/bin/env python3
"""Generate the Channel Selection layout packs "posterlist", "videofirst" and "videofirst-right" from
spec_cs.py (user-approved 2026-10-04 17:01).  Geometry comes only from the spec; widgets are the ones
verified in enigma2 57b7a51 (see spec_cs.py) plus the tested CineView components.

* every event field follows the HIGHLIGHTED service: source "ServiceEvent" (+ EventName Next* tokens, and
  CineViewMLAPosterX nexts=0/1 on ServiceEvent);
* posters off -> poster/frame/default image hidden and every text that sat beside a poster switches to its
  wider variant (CineViewMLAShowIf config.plugins.cineviewmla.poster_channelselection,True[,Invert]);
* right-to-left texts -> right-aligned variants (dir=rtl), titles page line by line (proven method);
* the native list keeps the Classic list attributes (fonts/heights adapted to the row height).
usage (from build.py): generate(skin_dir) -> list of created pack dirs
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "p7"))
import spec_cs as C  # noqa: E402
import gen_details as G  # noqa: E402

KEY = "config.plugins.cineviewmla.poster_channelselection"
SRC = "ServiceEvent"


def E(t):
	return {"x": t[0], "y": t[1], "w": t[2], "h": t[3]}


def mirror(e):
	return dict(e, x=1920 - e["x"] - e["w"])


def list_widget(e, row_h, name_font, info_font, num_font):
	# Classic's list attributes (device-proven on 57b7a51), sizes adapted to the row height
	return ('\t\t<widget name="list" %s itemHeight="%d" zPosition="12" backgroundColor="steThemeOverlay" transparent="1" foregroundColor="foreground" '
		'serviceNumberFont="Regular;%d" scrollbarMode="showOnDemand" serviceInfoFont="Regular;%d" serviceNameFont="Regular;%d" serviceItemHeight="%d" '
		'picServiceEventProgressbar="window/progress.png" progressbarHeight="10" progressBarWidth="70" colorEventProgressbarBorder="un33333a" fieldMargins="12" '
		'nonplayableMargins="12" colorEventProgressbarBorderSelected="darkgrey" colorServiceDescription="yellowsoft" progressbarBorderWidth="0" '
		'foregroundColorServiceNotAvail="#656565" backgroundColorMarked="#656565" colorServiceDescriptionFallback="yellowsoft" '
		'colorServiceDescriptionSelectedFallback="yellowsoft" colorFallbackItem="#aaaaaa" colorServiceSelectedFallback="yellowsoft" />'
		% (G.pos(e), row_h, num_font, info_font, name_font, row_h))


def clock(e_time, e_date, tfont, dfont):
	return [G.label("global.CurrentTime", e_time, [("ClockToText", "Format:%H:%M")], tfont, "foreground", ' halign="right"', 14),
		G.label("global.CurrentTime", e_date, [("ClockToText", "Date")], dfont, "grey", ' halign="right"', 14)]


def shown(line, inv=""):
	assert line.rstrip().endswith("</widget>"), line
	return line.replace("</widget>", "\t<convert type=\"CineViewMLAShowIf\">%s,True%s</convert>\n\t\t</widget>" % (KEY, inv))


def times_left(src, e, font, color, start="StartTime", end="EndTime"):
	"""'HH:MM – HH:MM' left-aligned (start | dash from the event | end)."""
	cw = int(font * 2.9)
	return [G.label(src, dict(e, w=cw), [("EventTime", start), ("ClockToText", "Format:%H:%M")], font, color),
		G.label(src, dict(e, x=e["x"] + cw, w=int(font * 1.1)), [("EventTime", start), ("ClockToText", "Format:–")], font, color, ' halign="center"'),
		G.label(src, dict(e, x=e["x"] + cw + int(font * 1.1), w=cw), [("EventTime", end), ("ClockToText", "Format:%H:%M")], font, color)]


def poster_slot(skin, e, nexts):
	return G.poster(skin, SRC, e, KEY, nexts)


def colour_keys(e, font=23):
	x, y, w, h = e["x"], e["y"], e["w"], e["h"]
	cw, ch = w // 2, h // 2
	out = []
	for i, (k, col) in enumerate((("key_red", "#00a00000"), ("key_green", "#00008000"), ("key_yellow", "#00a08000"), ("key_blue", "#000040a0"))):
		cx, cy = x + (i % 2) * cw, y + (i // 2) * ch
		out.append('\t\t<eLabel position="%d,%d" size="8,%d" backgroundColor="%s" zPosition="14" />' % (cx, cy + 8, ch - 16, col))
		out.append('\t\t<widget source="%s" render="Label" position="%d,%d" size="%d,%d" transparent="1" zPosition="14" foregroundColor="foreground" font="Regular;%d" valign="center" noWrap="1" />' % (k, cx + 20, cy, cw - 28, ch, font))
	return out


def posterlist(skin):
	s = C.POSTER_LIST
	b = {k: E(v) for k, v in s["boxes"].items()}
	on = {k: E(v) for k, v in s["posters_on"].items()}
	off = {k: E(v) for k, v in s["posters_off"].items()}
	fs = {k: v[4] for k, v in s["posters_on"].items() if len(v) > 4}
	x = ['\t\t<eLabel position="0,0" size="1920,1080" backgroundColor="#40000000" zPosition="0" />']
	x.append(G.box(b["list_panel"], "steThemeOverlay", 1))
	x.append(G.box(b["detail_panel"], "steThemeOverlay", 1))
	h = b["header"]
	x.append('\t\t<widget source="Title" render="Label" position="%d,%d" size="1000,48" transparent="1" zPosition="12" foregroundColor="foreground" font="Regular;34" noWrap="1" />' % (h["x"] + 16, h["y"] + 6))
	x += clock(dict(x=h["x"] + h["w"] - 216, y=h["y"], w=200, h=58), dict(x=h["x"] + h["w"] - 560, y=h["y"] + 20, w=320, h=30), 46, 21)
	x.append(list_widget(b["list"], s["row_h"], 30, 26, 30))
	# selected service
	x.append('\t\t<widget source="%s" render="Picon" %s alphatest="blend" scale="aspect" transparent="1" zPosition="14">\n\t\t\t<convert type="ServiceName">Reference</convert>\n\t\t</widget>' % (SRC, G.pos(on["svc_picon"])))
	x.append('\t\t<widget source="%s" render="RunningText" %s transparent="1" zPosition="14" foregroundColor="foreground" font="Regular;%d" noWrap="1" options="%s">\n\t\t\t<convert type="ServiceName">Name</convert>\n\t\t</widget>' % (SRC, G.pos(on["svc_name"]), fs["svc_name"], G.RUN_OPTS))
	t = on["svc_tech"]
	x.append(G.label(SRC, dict(t, w=110), [("ServiceOrbitalPosition", None)], fs["svc_tech"], "secondFG", "", 14))
	x.append('\t\t<widget source="%s" render="RunningText" %s transparent="1" zPosition="14" foregroundColor="grey" font="Regular;%d" noWrap="1" options="%s">\n\t\t\t<convert type="TransponderInfo" />\n\t\t</widget>' % (SRC, G.pos(dict(t, x=t["x"] + 118, w=t["w"] - 118)), fs["svc_tech"], G.RUN_OPTS))
	x.append(G.box(on["div1"], "steThemePanelAlt", 10))
	x.append(G.box(on["div2"], "steThemePanelAlt", 10))
	# NOW
	x += poster_slot(skin, on["now_poster"], 0)
	for g, inv in ((on["now_eyebrow"], ""), (off["now_eyebrow"], ",Invert")):
		x.append(shown(G.label(SRC, g, [("EventName", "Name"), ("CineViewMLAShowIf", "always,True,text=NOW")], fs["now_eyebrow"], "secondFG"), inv))
	x += G.text_variants(SRC, [("EventName", "Name")], on["now_title"], off["now_title"], fs["now_title"], "foreground", G.T_OPTS, KEY)
	for g, inv in ((on["now_times"], ""), (off["now_times"], ",Invert")):
		x += [shown(l, inv) for l in times_left(SRC, g, fs["now_times"], "foreground")]
		x.append(shown(G.label(SRC, dict(g, x=g["x"] + 190, w=200), [("EventTime", "Duration"), ("ClockToText", "InMinutes")], fs["now_times"], "grey"), inv))
	x += G.progress(SRC, [("EventTime", "Progress")], on["now_progress"], off["now_progress"], KEY)
	for g, inv in ((on["now_genre"], ""), (off["now_genre"], ",Invert")):
		x.append(shown(G.label(SRC, g, [("EventName", "Genre")], fs["now_genre"], "grey", ' noWrap="1"'), inv))
	x += G.text_variants(SRC, [("EventName", "FullDescription")], on["now_desc"], off["now_desc"], fs["now_desc"], "foreground", G.D_OPTS, KEY)
	# NEXT
	x += poster_slot(skin, on["next_poster"], 1)
	for g, inv in ((on["next_eyebrow"], ""), (off["next_eyebrow"], ",Invert")):
		f = fs["next_eyebrow"]
		x.append(shown(G.label(SRC, dict(g, w=80), [("EventName", "NextName"), ("CineViewMLAShowIf", "always,True,text=NEXT")], f, "secondFG"), inv))
		x += [shown(l, inv) for l in times_left(SRC, dict(g, x=g["x"] + 86, w=g["w"] - 86), f, "secondFG", "NextStartTime", "NextEndTime")]
	x += G.text_variants(SRC, [("EventName", "NextNameOnly")], on["next_title"], off["next_title"], fs["next_title"], "foreground", G.T_OPTS, KEY)
	x += G.text_variants(SRC, [("EventName", "NextDescription")], on["next_desc"], off["next_desc"], fs["next_desc"], "grey", G.D_OPTS, KEY)
	x.append('\t\t<panel name="ButtonTemplate" />')
	return x


def videofirst(skin, right=False):
	s = C.VIDEO_FIRST
	b = {k: E(v) for k, v in s["boxes"].items()}
	on = {k: E(v) for k, v in s["posters_on"].items()}
	off = {k: E(v) for k, v in s["posters_off"].items()}
	fs = {k: v[4] for k, v in s["posters_on"].items() if len(v) > 4}
	fs.update({k: v[4] for k, v in s["boxes"].items() if len(v) > 4})
	if right:
		b = {k: mirror(v) for k, v in b.items()}
		dx = b["card"]["x"] - E(s["boxes"]["card"])["x"]
		on = {k: dict(v, x=v["x"] + dx) for k, v in on.items()}
		off = {k: dict(v, x=v["x"] + dx) for k, v in off.items()}
	x = [G.box(b["list_panel"], "steThemeOverlay", 1), G.box(b["card"], "steThemeOverlay", 1), G.box(b["clock"], "steThemeOverlay", 1)]
	x.append('\t\t<widget source="Title" render="Label" %s transparent="1" zPosition="12" foregroundColor="foreground" font="Regular;%d" noWrap="1" />' % (G.pos(b["title"]), fs["title"]))
	x.append(list_widget(b["list"], s["row_h"], 26, 22, 26))
	x += colour_keys(b["keys"])
	c = b["clock"]
	x += clock(dict(x=c["x"] + 12, y=c["y"] + 4, w=c["w"] - 24, h=48), dict(x=c["x"] + 12, y=c["y"] + 48, w=c["w"] - 24, h=22), 40, 17)
	# card: highlighted service
	x += poster_slot(skin, on["poster"], 0)
	for g, inv in ((on["svc_line"], ""), (off["svc_line"], ",Invert")):
		f = fs["svc_line"]
		x.append(shown(G.label(SRC, dict(g, w=300), [("ServiceName", "Name")], f, "foreground", ' noWrap="1"'), inv))
		x.append(shown(G.label(SRC, dict(g, x=g["x"] + 310, w=110), [("ServiceOrbitalPosition", None)], f, "secondFG"), inv))
		x.append(shown('\t\t<widget source="%s" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="grey" font="Regular;%d" noWrap="1" options="%s">\n\t\t\t<convert type="TransponderInfo" />\n\t\t</widget>' % (SRC, G.pos(dict(g, x=g["x"] + 428, w=g["w"] - 428)), f, G.RUN_OPTS), inv))
	x += G.text_variants(SRC, [("EventName", "Name")], on["now_title"], off["now_title"], fs["now_title"], "foreground", G.T_OPTS, KEY)
	x += G.times(SRC, on["now_times"], fs["now_times"], "foreground")
	x += G.progress(SRC, [("EventTime", "Progress")], on["now_progress"], off["now_progress"], KEY)
	x += G.text_variants(SRC, [("EventName", "FullDescription")], on["now_desc"], off["now_desc"], fs["now_desc"], "foreground", G.D_OPTS, KEY)
	for g, inv in ((on["next_line"], ""), (off["next_line"], ",Invert")):
		f = fs["next_line"]
		x.append(shown(G.label(SRC, dict(g, w=70), [("EventName", "NextName"), ("CineViewMLAShowIf", "always,True,text=NEXT")], f, "secondFG"), inv))
		x.append(shown(G.label(SRC, dict(g, x=g["x"] + 76, w=74), [("EventTime", "NextStartTime"), ("ClockToText", "Format:%H:%M")], f, "secondFG"), inv))
		x.append(shown('\t\t<widget source="%s" render="RunningText" %s transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;%d" noWrap="1" options="%s">\n\t\t\t<convert type="EventName">NextNameOnly</convert>\n\t\t</widget>' % (SRC, G.pos(dict(g, x=g["x"] + 156, w=g["w"] - 156)), f, G.H_OPTS), inv))
	for g, inv in ((on["tech_line"], ""), (off["tech_line"], ",Invert")):
		f = fs["tech_line"]
		parts = [(0, 60, None, "LIVE", "secondFG"), (64, 60, ("FrontendInfo", "SNR"), None, "foreground"), (128, 110, ("FrontendInfo", "SNRdB"), None, "secondFG"),
			(244, 50, None, "AGC", "grey"), (296, 64, ("FrontendInfo", "AGC"), None, "foreground")]
		for px, pw, conv, txt, col in parts:
			gg = dict(g, x=g["x"] + px, w=pw)
			if conv:
				x.append(shown(G.label("session.FrontendStatus", gg, [conv], f, col), inv))
			else:
				x.append(shown(G.label("session.CurrentService", gg, [("CineViewMLAShowIf", "always,True,text=%s" % txt)], f, col), inv))
		x.append(shown('\t\t<widget render="VideoSize" source="session.CurrentService" %s font="Regular;%d" foregroundColor="grey" transparent="1" zPosition="20"></widget>' % (G.pos(dict(g, x=g["x"] + 372, w=150)), f), inv))
		x.append(shown(G.label("session.CurrentService", dict(g, x=g["x"] + 530, w=170), [("CineViewMLABitrate", "Mbps")], f, "grey"), inv))
	return x


def _classic_screens(skin, keep):
	src = open(os.path.join(skin, "layouts", "channelselection", "classic", "screens.openatv.xml"), encoding="utf-8").read()
	out = []
	for name in keep:
		m = re.search(r'\t?<screen name="%s".*?</screen>' % re.escape(name), src, re.S)
		if m:
			out.append((name, m.group(0)))
	return out


def _write(skin, pid, name, body):
	d = os.path.join(skin, "layouts", "channelselection", pid)
	os.makedirs(d, exist_ok=True)
	parts = ['\t<screen name="ChannelSelection" title="Channel Selection" position="fill" backgroundColor="transparent" flags="wfNoBorder">\n%s\n\t</screen>' % "\n".join(l for l in body if l)]
	keep = _classic_screens(skin, ("ChannelSelectionRadio", "SimpleChannelSelection", "SlimChannelSelection"))
	parts += [p.strip("\n") if p.startswith("\t") else "\t" + p.strip() for _, p in keep]
	xml = '<?xml version="1.0" encoding="utf-8"?>\n<!-- CineView %s (Channel Selection) — generated by tools/mla/p8cs/gen_channels.py from spec_cs.py. Do not edit by hand. -->\n<skin>\n%s\n</skin>\n' % (name, "\n".join(parts))
	open(os.path.join(d, "screens.openatv.xml"), "w", encoding="utf-8").write(xml)
	json.dump({"schema": 1, "id": pid, "section": "channelselection", "name": "CineView " + name, "version": "0.1.0", "author": "habeb-s",
		"license": "CineView-Proprietary", "origin": "tools/mla/p8cs/spec_cs.py (user-approved 2026-10-04 17:01)",
		"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}},
		"provides_screens": ["ChannelSelection"] + [n for n, _ in keep], "options": [], "preview": "preview.png"},
		open(os.path.join(d, "manifest.json"), "w"), indent=1)
	return d


def generate(skin):
	made = [_write(skin, "posterlist", "Poster List", posterlist(skin)),
		_write(skin, "videofirst", "Video First", videofirst(skin)),
		_write(skin, "videofirst-right", "Video First (list right)", videofirst(skin, right=True))]
	import xml.etree.ElementTree as ET
	for d in made:
		r = ET.parse(os.path.join(d, "screens.openatv.xml")).getroot()
		for el in r.iter():
			p, s = el.get("position"), el.get("size")
			if p and s and "," in p and not p.startswith(("c", "e")):
				x, y = (int(v) for v in p.split(","))
				w, h = (int(v) for v in s.split(","))
				assert 0 <= x and x + w <= 1920 and 0 <= y and y + h <= 1080, (d, el.attrib)
	return made


if __name__ == "__main__":
	print(generate(sys.argv[1]))
