# -*- coding: utf-8 -*-
# DEVELOPMENT-ONLY test tool (Slot 8), generic version for any active layout pack (Classic, Details, ...).
# Renders the LIVE screen of the active MLA generation with arbitrary EPG texts (e.g. long Arabic), without
# touching the EPG cache: every widget fed by EventName Name / ShortDescription / FullDescription keeps its
# exact geometry, font, options and CineViewMLAShowIf converter (poster narrow/wide + ltr/rtl variants,
# driven by the REAL settings); its source becomes a StaticText.  Other event widgets (times, posters,
# progress, IMDb, genre) are dropped; panels, separators and static texts stay.
# Trigger: /tmp/cvmla/texttest2.json {"screen": "SecondInfoBar"|"InfoBar", "file": "secondinfobar.xml",
#          "seconds": 25, "title_now": "...", "desc_now": "...", "short_now": "...", "title_next": "...",
#          "desc_next": "...", "short_next": "..."}
import json
import os
import xml.etree.ElementTree as ET

from enigma import eTimer
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen

TRIGGER = "/tmp/cvmla/texttest2.json"
ACTIVE = "/usr/share/enigma2/CineView_FHD_MLA/active/"
MAP = {("session.Event_Now", "Name"): "title_now", ("session.Event_Now", "FullDescription"): "desc_now",
	("session.Event_Now", "ShortDescription"): "short_now", ("session.Event_Next", "Name"): "title_next",
	("session.Event_Next", "FullDescription"): "desc_next", ("session.Event_Next", "ShortDescription"): "short_next"}
EVENT_SOURCES = ("session.Event_Now", "session.Event_Next", "Event")
_session = None
_timer = None


def build_skin(fname, scrname):
	root = ET.parse(os.path.join(ACTIVE, fname)).getroot()
	scr = [s for s in root.iter("screen") if s.get("name") == scrname][0]
	out = ['<screen name="CineViewMLATextTest2" position="fill" flags="wfNoBorder" backgroundColor="transparent">']
	for el in scr:
		src = el.get("source")
		if el.tag == "widget" and src in EVENT_SOURCES:
			convs = el.findall("convert")
			first = convs[0] if convs else None
			key = MAP.get((src, (first.text or "").strip())) if first is not None and first.get("type") == "EventName" else None
			if not key:
				continue
			el.set("source", key)
			el.remove(first)
		elif el.tag == "widget" and src and src.startswith("session.") and el.get("render") != "Pixmap":
			continue  # live service/tuner widgets are not needed for a text test
		out.append(ET.tostring(el, encoding="unicode").strip())
	out.append("</screen>")
	return "\n".join(out)


class CineViewMLATextTest2(Screen):
	def __init__(self, session, data):
		self.skin = build_skin(data.get("file", "secondinfobar.xml"), data.get("screen", "SecondInfoBar"))
		Screen.__init__(self, session)
		for k in set(MAP.values()):
			self[k] = StaticText(data.get(k, ""))
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.close, "cancel": self.close}, -1)
		self.t = eTimer()
		self.t.callback.append(self.close)
		self.t.start(int(data.get("seconds", 25)) * 1000, True)


def _poll():
	try:
		if os.path.isfile(TRIGGER) and _session is not None:
			data = json.load(open(TRIGGER, encoding="utf-8"))
			os.remove(TRIGGER)
			print("[CineViewMLATextTest2] opening %s/%s" % (data.get("file"), data.get("screen")))
			_session.open(CineViewMLATextTest2, data)
	except Exception as err:
		print("[CineViewMLATextTest2] error: %s" % err)
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
