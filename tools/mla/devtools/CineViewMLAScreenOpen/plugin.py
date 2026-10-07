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
#   radio      -> InfoBar.showRadio()          (radio channel list, native RADIO key path)
#   vertical   -> InfoBar.openVerticalEPG()   (EPGvertical — contract check for the Columns proposal)
#   graph      -> InfoBar.openGraphEPG()      (GraphicalEPG)
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
# PVR test folder: the USB test folder on Slot 8 (OpenATV); on other slots a folder on the slot's own filesystem.
# Never the HDD.
TESTMEDIA = "/media/usb/cineview-mla/testmedia/" if os.path.isdir("/media/usb/cineview-mla/testmedia") else "/home/root/cvmla-testmedia/"
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
	elif what == "radio":
		ib.showRadio()  # native RADIO key path (ChannelSelectionRadio, or ChannelSelection in e1-like mode)
	elif what == "nativemovies":
		# the native MovieSelection, opened on the USB test folder (never the HDD); the previous folder value is
		# kept in /tmp/cvmla/last_videodir for the test's restore step
		from Screens.MovieSelection import MovieSelection
		old = config.movielist.last_videodir.value
		open("/tmp/cvmla/last_videodir", "w").write(old)
		config.movielist.last_videodir.value = TESTMEDIA
		_session.open(MovieSelection, None)  # the value stays on USB until the test restores it (MovieSelection may
		# read it after __init__); the test restarts Enigma2 with the saved value
	elif what == "play":
		# the native MoviePlayer on the USB test clip, opened exactly as InfoBar.movieSelected opens it (t87: the
		# playback InfoBar of the skin).  USB test media only; STOP returns (config.usage.on_movie_stop default).
		import glob
		from enigma import eServiceReference
		from Screens.InfoBar import MoviePlayer
		clips = sorted(glob.glob(TESTMEDIA + "*CineView MLA test clip.ts"))
		if clips:
			ref = eServiceReference(1, 0, clips[0])
			_session.open(MoviePlayer, ref, slist=ib.servicelist, lastservice=_session.nav.getCurrentlyPlayingServiceOrGroup())
	elif what == "movies":
		ib.showMovies()  # native PVR key path (MovieSelection; listing only, nothing is played)
	elif what == "vertical":
		ib.openVerticalEPG()
	elif what == "graph":
		(getattr(ib, "openGraphEPG", None) or ib.openGridEPG)()  # OpenATV GraphicalEPG / OpenBH-ViX grid EPG
	elif what == "single":
		ib.openSingleServiceEPG()
	elif what == "eventview":
		ib.openEventView()
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
	elif what == "stack":
		# the LIVE dialog stack (2026-10-06 22:00, plugin-download screen): class, module, skinName actually used,
		# parent, every widget / source with its type and text -> /tmp/cvmla/stack.txt (read-only; nothing changes)
		out = []
		stack = [(s, "dialog_stack") for s, shown in getattr(_session, "dialog_stack", [])] + [(_session.current_dialog, "current")]
		for dlg, tag in stack:
			if dlg is None:
				continue
			sk = getattr(dlg, "skinName", None)
			out.append("== %s %s.%s skinName=%r applied=%r parent=%r shown=%r" % (tag, dlg.__class__.__module__, dlg.__class__.__name__,
				sk, getattr(dlg, "skinAttributes", None) and "yes", getattr(getattr(dlg, "parent", None), "__class__", type(None)).__name__, getattr(dlg, "shown", None)))
			try:
				for k in sorted(dlg.keys()):
					w = dlg[k]
					txt = ""
					for attr in ("getText", "text"):
						v = getattr(w, attr, None)
						try:
							txt = v() if callable(v) else (v or "")
						except Exception:
							pass
						if txt:
							break
					out.append("   %-24s %-28s %r" % (k, w.__class__.__name__, (str(txt) or "")[:90]))
			except Exception as err:
				out.append("   (widgets: %s)" % err)
			for r in getattr(dlg, "renderer", []):
				out.append("   renderer %-20s source=%s" % (r.__class__.__name__, getattr(getattr(r, "source", None), "__class__", type(None)).__name__))
		open("/tmp/cvmla/stack.txt", "w").write("\n".join(out) + "\n")
	elif what == "designs":
		# CineView Designs exactly as the Plugin Browser entry opens it (plugin main())
		from Plugins.Extensions.CineViewMLA.plugin import main as designs_main
		designs_main(_session)
	elif what in ("msg_info", "msg_yesno", "msg_long", "msg_list"):
		# sample MessageBoxes (display only; closed by the test with EXIT) - texts of CineView Designs / OpenATV
		from Screens.MessageBox import MessageBox
		if what == "msg_info":
			_session.open(MessageBox, _("Settings saved. The design is unchanged."), MessageBox.TYPE_INFO)
		elif what == "msg_yesno":
			_session.open(MessageBox, "Apply Classic design with Black theme?\nThe GUI restarts and you will be asked to keep the new design.", MessageBox.TYPE_YESNO)
		elif what == "msg_long":
			_session.open(MessageBox, "\n".join(["CineView MLA display test (nothing is changed)."] + ["Line %d of a long message: the window must grow with the text and stay centred." % i for i in range(1, 9)]), MessageBox.TYPE_ERROR)
		else:
			_session.open(MessageBox, _("What do you want to do?"), MessageBox.TYPE_YESNO, list=[("Option %d" % i, i) for i in range(1, 5)])
	elif what == "setup" or what.startswith("setup:"):
		# a native OpenATV Setup page (display only, nothing is saved: closed with EXIT) - shared Setup look check
		from Screens.Setup import Setup
		_session.open(Setup, what.split(":", 1)[1] if ":" in what else "UserInterface")
	elif what == "rows":
		# CineView Designs rows: label, shown value, current-row marker, description / status texts -> /tmp/cvmla/rows.txt
		dlg = _session.current_dialog
		out = ["screen %s.%s" % (dlg.__class__.__module__, dlg.__class__.__name__)]
		try:
			lst = dlg["config"].list
			cur = dlg["config"].getCurrentIndex()
			for i, e in enumerate(lst):
				try:
					val = e[1].getText()
				except Exception as err:
					val = "?(%s)" % err
				out.append("%s%2d  %-40s | %s" % (">" if i == cur else " ", i, e[0], val))
		except Exception as err:
			out.append("(no config list: %s)" % err)
		for k in ("description", "status", "key_red", "key_green", "key_yellow", "key_blue", "key_menu", "key_help", "Title"):
			if k in dlg:
				try:
					out.append("%-12s %r" % (k, dlg[k].getText()))
				except Exception:
					pass
		open("/tmp/cvmla/rows.txt", "w").write("\n".join(out) + "\n")
	elif what in ("processing", "processing2"):
		# display only (2026-10-06): the global Processing dialog with the native texts of the feed update
		# (one line) / feed reset (several lines - the window grows with the text), shown 6 s then hidden.
		# No opkg command runs, no feed is touched.
		from Screens.Processing import Processing
		text = _("Please wait while feeds are updated...") if what == "processing" else \
			"%s\n\n%s" % (_("Please wait while the feeds are reset (cleared and reloaded)..."), _("Warning: Canceling this process will leave the feeds in an incomplete and unusable state!"))
		Processing.instance.setDescription(text)
		Processing.instance.showProgress(endless=True)
		t = eTimer()

		def hide_processing():
			Processing.instance.hideProgress()
			_keep[:] = []
		t.callback.append(hide_processing)
		t.start(6000, True)
		_keep[:] = [t]
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
