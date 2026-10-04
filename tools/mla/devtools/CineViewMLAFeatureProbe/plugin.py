# -*- coding: utf-8 -*-
# DEVELOPMENT-ONLY probe (Slot 8): opens an arbitrary skin snippet over the live picture so a skin feature can be
# checked on the real receiver before a layout pack depends on it (Modern model: cornerRadius, borders, gradients
# with alpha blending, rounded pixmaps).  Nothing in the active skin is changed.
# Trigger: /tmp/cvmla/probe.json {"skin": "<screen ...>...</screen>", "seconds": 30, "texts": {"name": "text", ...}}
# Every key of "texts" becomes a StaticText source.  OK / EXIT closes.
import json
import os

from enigma import eTimer
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen

TRIGGER = "/tmp/cvmla/probe.json"
_session = None
_timer = None


class CineViewMLAFeatureProbe(Screen):
	def __init__(self, session, data):
		self.skin = data["skin"]
		Screen.__init__(self, session)
		for k, v in data.get("texts", {}).items():
			self[k] = StaticText(v)
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.close, "cancel": self.close}, -1)
		self.t = eTimer()
		self.t.callback.append(self.close)
		self.t.start(int(data.get("seconds", 30)) * 1000, True)


def _poll():
	try:
		if os.path.isfile(TRIGGER) and _session is not None:
			data = json.load(open(TRIGGER, encoding="utf-8"))
			os.remove(TRIGGER)
			print("[CineViewMLAFeatureProbe] opening probe screen")
			_session.open(CineViewMLAFeatureProbe, data)
	except Exception as err:
		print("[CineViewMLAFeatureProbe] error: %s" % err)
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
