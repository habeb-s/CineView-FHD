#!/usr/bin/env python3
"""Online updater: opkg runs with CINEVIEW_NO_RESTART=1 and Enigma2 is restarted only when nothing records.
Enigma2 modules are stubbed; the real updater source is loaded (updater/CineViewUpdater/plugin.py)."""
import importlib.util, os, sys, types

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "updater", "CineViewUpdater", "plugin.py")
calls = []


def mod(name, **attrs):
	m = types.ModuleType(name); m.__dict__.update(attrs); sys.modules[name] = m


class Widget(object):
	def __init__(self, *a): self.text = a[0] if a else ""
	def setText(self, t): self.text = t
	def setValue(self, v): pass
	def hide(self): pass
	def show(self): pass


class Screen(dict):
	def __init__(self, session): dict.__init__(self)
	def close(self, *a): pass


mod("enigma", eConsoleAppContainer=object, quitMainloop=lambda code: calls.append(("quitMainloop", code)))
for n in ("Plugins", "Screens", "Components"):
	mod(n)
mod("Plugins.Plugin", PluginDescriptor=lambda **k: k)
mod("Screens.Screen", Screen=Screen)
mod("Screens.MessageBox", MessageBox=type("MessageBox", (), {"TYPE_INFO": 0, "TYPE_ERROR": 1}))
mod("Components.ActionMap", ActionMap=lambda *a, **k: None)
mod("Components.Label", Label=Widget)
mod("Components.ProgressBar", ProgressBar=Widget)
spec = importlib.util.spec_from_file_location("cvupdater", SRC)
U = importlib.util.module_from_spec(spec); spec.loader.exec_module(U)


class Timer(object):
	def __init__(self, rec): self.rec = rec
	def isRecording(self):
		if isinstance(self.rec, Exception): raise self.rec
		return self.rec


class Nav(object):
	def __init__(self, rec, recs):
		self.RecordTimer = Timer(rec)
		self._recs = recs
	def getRecordings(self, simulate=False):
		if isinstance(self._recs, Exception): raise self._recs
		return self._recs


class Session(object):
	def __init__(self, nav): self.nav = nav
	def open(self, cls, text, *a, **k): calls.append(("open", text))
	def openWithCallback(self, cb, cls, text, *a, **k): calls.append(("openWithCallback", text)); self.cb = cb


def screen(nav):
	s = U.CineViewUpdater(Session(nav))
	s.remote = {"version": "9.9.9"}
	return s


res = []
def check(label, ok):
	res.append(ok); print("%s  %s" % ("PASS" if ok else "FAIL", label))

# opkg command
s = screen(Nav(False, []))
captured = []
s._run = lambda cmd, done, capture=False: captured.append(cmd)
U.os.path.exists = lambda p: True; U.os.path.getsize = lambda p: 4096
s._downloadDone(0)
check("opkg runs with CINEVIEW_NO_RESTART=1: %s" % captured[0], captured[0].startswith("CINEVIEW_NO_RESTART=1 opkg install --force-reinstall "))
U.os.remove = lambda p: None

scenarios = [
	("idle receiver -> restart", Nav(False, []), True),
	("RecordTimer.isRecording() True -> no restart", Nav(True, []), False),
	("getRecordings() not empty -> no restart", Nav(False, ["rec"]), False),
	("RecordTimer missing, getRecordings() empty -> restart", Nav(AttributeError(), []), True),
	("neither check possible -> no restart", Nav(AttributeError(), AttributeError()), False),
	("no session.nav -> no restart", None, False),
]
for label, nav, expect in scenarios:
	del calls[:]
	s = screen(nav)
	s._installDone(0)
	if calls and calls[-1][0] == "openWithCallback":
		s.session.cb()
	restarted = ("quitMainloop", 3) in calls
	msg = calls[0][1] if calls else ""
	check("%s (%s)" % (label, msg.replace("\n", " | ")[:95]), restarted == expect)

# recording starts while the "installed - restarting" message is on screen
del calls[:]
nav = Nav(False, [])
s = screen(nav); s._installDone(0)
nav.RecordTimer.rec = True
s.session.cb()
check("recording started during the message -> no restart", ("quitMainloop", 3) not in calls)
check("PLUGIN_VERSION = %s" % U.PLUGIN_VERSION, bool(U.PLUGIN_VERSION))
print("RESULT pass=%d fail=%d" % (sum(res), len(res) - sum(res)))
sys.exit(0 if all(res) else 1)
