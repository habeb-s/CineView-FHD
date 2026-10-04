# -*- coding: utf-8 -*-
# DEVELOPMENT-ONLY test tool (Slot 8).  Not part of the MLA package; removed after testing.
#
# Opens native OpenATV screens through their NATIVE entry points so the skin can be checked on screens that
# are hard to reach with remote-control keys on this receiver (EMC replaces MovieSelection on PVR, QuickEPG
# needs config.epgselection.infobar_type_mode == "single").  Nothing is saved: the only config value touched
# (infobar_type_mode) is changed in memory for the call and restored right after.
#
# Trigger: write /tmp/cvmla/open.txt with one word:
#   multi      -> InfoBar.openMultiServiceEPG()            (EPGSelectionMulti)
#   infobarepg -> InfoBar.openInfoBarEPG()                 (default "text" mode; INFO there opens InfoBarEventView)
#   quick      -> InfoBar.openInfoBarEPG() in "single"     (QuickEPG)
#   evsimple   -> session.open(EventViewSimple, event, ServiceReference)  -- the same call MovieSelection.showEventInformation
#                 makes, with the current event of the playing service
#   ibeventview-> getEventViewInstance(..., skinName="InfoBarEventView") shown for 20 s (same call as EpgSelection.infoKeyPressed)
#   pluginbrowser -> session.open(PluginBrowser)            (PluginBrowserList / PluginBrowserGrid by the user's layout setting)
#   quickmenu  -> session.open(QuickMenu)
#   pkgremove  -> session.open(PackageAction, MODE_REMOVE)  (only lists installed plugins; nothing is removed unless confirmed)
#   pkglog     -> session.open(PackageActionLog, <fixed sample text>)  (display only; no opkg command runs)
#   accel_on / accel_off -> enigma.setACCELDebug(1/0): gAccel logs every accel allocation and the pool map
#                 (native SWIG function of 57b7a51, logging only).  /tmp/cvmla/acceldebug present at session start
#                 switches it on from the start.
import os

from enigma import eTimer, eEPGCache
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from ServiceReference import ServiceReference

TRIGGER = "/tmp/cvmla/open.txt"
_session = None
_timer = None
_keep = []


def _now_event(session):
	ref = session.nav.getCurrentlyPlayingServiceOrGroup()
	info = session.nav.getCurrentService() and session.nav.getCurrentService().info()
	evt = info and info.getEvent(0)
	if evt is None and ref is not None:
		evt = eEPGCache.getInstance().lookupEventTime(ref, -1)
	return evt, ref


def _open(what):
	from Screens.InfoBar import InfoBar
	ib = InfoBar.instance
	if what == "multi":
		ib.openMultiServiceEPG()
	elif what == "infobarepg":
		ib.openInfoBarEPG()
	elif what == "quick":
		old = config.epgselection.infobar_type_mode.value
		config.epgselection.infobar_type_mode.value = "single"
		try:
			ib.openInfoBarEPG()
		finally:
			config.epgselection.infobar_type_mode.value = old
	elif what == "evsimple":
		from Screens.EventView import EventViewSimple
		evt, ref = _now_event(_session)
		if evt is not None:
			_session.open(EventViewSimple, evt, ServiceReference(ref))
	elif what == "ibeventview":
		from Screens.EventView import getEventViewInstance
		evt, ref = _now_event(_session)
		if evt is not None:
			dlg = getEventViewInstance(_session, evt, ServiceReference(ref), skinName="InfoBarEventView")
			dlg.show()
			t = eTimer()

			def done():
				dlg.hide()
				_session.deleteDialog(dlg)
				_keep[:] = []
			t.callback.append(done)
			t.start(20000, True)
			_keep[:] = [dlg, t]
	elif what == "pluginbrowser":
		from Screens.PluginBrowser import PluginBrowser
		_session.open(PluginBrowser)
	elif what == "quickmenu":
		from Screens.QuickMenu import QuickMenu
		_session.open(QuickMenu)
	elif what == "pkgremove":
		from Screens.PluginBrowser import PackageAction
		_session.open(PackageAction, PackageAction.MODE_REMOVE)
	elif what == "pkglog":
		from Screens.PluginBrowser import PackageActionLog
		_session.open(PackageActionLog, "\n".join(["CineView MLA display test (no opkg command was run)"] + ["Line %02d: Removing package enigma2-plugin-example-%02d from root..." % (i, i) for i in range(1, 31)]))
	elif what in ("accel_on", "accel_off"):
		from enigma import setACCELDebug
		setACCELDebug(1 if what == "accel_on" else 0)
	print("[CineViewMLAScreenOpen] opened %s" % what)


def _poll():
	try:
		if os.path.isfile(TRIGGER) and _session is not None:
			what = open(TRIGGER).read().strip()
			os.remove(TRIGGER)
			_open(what)
	except Exception as err:
		print("[CineViewMLAScreenOpen] error: %s" % err)
	_timer.start(700, True)


def sessionstart(reason, session=None, **kwargs):
	global _session, _timer
	if reason == 0 and session is not None:
		_session = session
		if os.path.isfile("/tmp/cvmla/acceldebug"):
			from enigma import setACCELDebug
			setACCELDebug(1)
			print("[CineViewMLAScreenOpen] accel debug on from session start")
		_timer = eTimer()
		_timer.callback.append(_poll)
		_timer.start(5000, True)


def Plugins(**kwargs):
	return [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False)]
