# -*- coding: utf-8 -*-
# DEVELOPMENT-ONLY test tool (Slot 8).  Not part of the MLA package; removed after testing.
#
# Renders the LIVE SecondInfoBar panel widgets of the active MLA generation (same XML attributes,
# same RunningText options, narrow = posters-on or wide = posters-off variant) with arbitrary texts,
# e.g. long Arabic titles/descriptions, WITHOUT touching the EPG cache or any disk.
#
# Trigger: write /tmp/cvmla/texttest.json  {"mode": "narrow"|"wide", "seconds": 20,
#          "title_now": "...", "desc_now": "...", "title_next": "...", "desc_next": "..."}
# The file is consumed (deleted) and the test screen is shown for "seconds".
import json
import os
import xml.etree.ElementTree as ET

from enigma import eTimer
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen

TRIGGER = "/tmp/cvmla/texttest.json"
ACTIVE = "/usr/share/enigma2/CineView_FHD_MLA/active/secondinfobar.xml"
KEYS = {("session.Event_Now", "Name"): "title_now", ("session.Event_Now", "FullDescription"): "desc_now",
	("session.Event_Next", "Name"): "title_next", ("session.Event_Next", "FullDescription"): "desc_next"}
_session = None
_timer = None


def build_skin(mode):
	root = ET.parse(ACTIVE).getroot()
	sib = [s for s in root.iter("screen") if s.get("name") == "SecondInfoBar"][0]
	out = ['<screen name="CineViewMLATextTest" position="fill" flags="wfNoBorder" backgroundColor="transparent">']
	for el in sib:
		if el.tag == "eLabel" and el.get("backgroundColor") == "steSecondInfoBG" and int(el.get("position").split(",")[1]) < 300:
			out.append(ET.tostring(el, encoding="unicode").strip())  # the two event panels
		elif el.tag == "widget" and el.get("render") == "Pixmap" and "frame_" in (el.get("pixmap") or "") and el.get("position", "").endswith(",177") and mode == "narrow":
			out.append('<ePixmap pixmap="%s" position="%s" size="%s" zPosition="%s" />' % (el.get("pixmap"), el.get("position"), el.get("size"), el.get("zPosition")))
		elif el.tag == "widget" and el.get("render") == "RunningText":
			convs = el.findall("convert")
			name = convs[0].text.strip() if convs else ""
			key = KEYS.get((el.get("source"), name))
			show = [c.text for c in convs if c.get("type") == "CineViewMLAShowIf"]
			if not key or not show:
				continue
			is_wide = show[0].strip().endswith(",Invert")
			if is_wide != (mode == "wide"):
				continue
			attrs = " ".join('%s="%s"' % (k, v.replace('"', "&quot;")) for k, v in el.attrib.items() if k != "source")
			out.append('<widget source="%s" %s />' % (key, attrs))
	out.append("</screen>")
	return "\n".join(out)


class CineViewMLATextTest(Screen):
	def __init__(self, session, data):
		self.skin = build_skin(data.get("mode", "narrow"))
		Screen.__init__(self, session)
		for k in ("title_now", "desc_now", "title_next", "desc_next"):
			self[k] = StaticText(data.get(k, ""))
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.close, "cancel": self.close}, -1)
		self.t = eTimer()
		self.t.callback.append(self.close)
		self.t.start(int(data.get("seconds", 20)) * 1000, True)


def _poll():
	try:
		if os.path.isfile(TRIGGER) and _session is not None:
			data = json.load(open(TRIGGER, encoding="utf-8"))
			os.remove(TRIGGER)
			print("[CineViewMLATextTest] opening (%s)" % data.get("mode"))
			_session.open(CineViewMLATextTest, data)
	except Exception as err:
		print("[CineViewMLATextTest] error: %s" % err)
	_timer.start(1000, True)


def sessionstart(reason, session=None, **kwargs):
	global _session, _timer
	if reason == 0 and session is not None:
		_session = session
		_timer = eTimer()
		_timer.callback.append(_poll)
		_timer.start(5000, True)


def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False)]
