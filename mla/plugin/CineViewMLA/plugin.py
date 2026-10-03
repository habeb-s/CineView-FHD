# -*- coding: utf-8 -*-
# CineView MLA runtime plugin (OpenATV).  Phase: guardian signals only.
#  - healthy: 60 s after the session starts without crashing -> boot.count = 0
#  - clean exit: session.onShutdown -> clean_exit marker (guardian then does not count a crash)
# The settings / preview UI is added in the P6 phase.
import os

from enigma import eTimer
from Plugins.Plugin import PluginDescriptor

STATE = "/etc/enigma2/cineview_mla"
HEALTHY_AFTER_MS = 60000
_timer = None


def _write(name, data):
	try:
		if not os.path.isdir(STATE):
			os.makedirs(STATE)
		tmp = os.path.join(STATE, name + ".tmp")
		with open(tmp, "w") as f:
			f.write(data)
			f.flush()
			os.fsync(f.fileno())
		os.rename(tmp, os.path.join(STATE, name))
	except Exception as err:
		print("[CineViewMLA] state write failed: %s" % err)


def _healthy():
	_write("boot.count", "0")
	_write("healthy", str(int(__import__("time").time())))
	print("[CineViewMLA] session healthy; guardian counter reset")


def _clean_exit():
	_write("clean_exit", "1")


def sessionstart(reason, session=None, **kwargs):
	global _timer
	if reason != 0 or session is None:
		return
	try:
		session.onShutdown.append(_clean_exit)
	except Exception as err:
		print("[CineViewMLA] onShutdown hook unavailable: %s" % err)
	_timer = eTimer()
	_timer.callback.append(_healthy)
	_timer.start(HEALTHY_AFTER_MS, True)


def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart)]
