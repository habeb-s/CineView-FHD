# -*- coding: utf-8 -*-
# CineView MLA runtime plugin (OpenATV 8.0.1).
#  - Guardian signals: "healthy" 60 s after session start; "clean_exit" on session shutdown.
#  - Design selector: theme + one layout per section (built dynamically from the engine registry),
#    live preview image, trial apply with automatic revert, runtime options (posters, info).
#  - Second InfoBar: mode and timeout are two separate NATIVE settings
#    (config.usage.show_second_infobar / config.usage.second_infobar_timeout) — fixes ISS-01.
import importlib.util
import json
import os
import time

from enigma import eTimer
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSelection, ConfigYesNo, configfile, getConfigListEntry, ConfigSubsection
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap

SKIN_DIR = "/usr/share/enigma2/CineView_FHD_MLA"
STATE = "/etc/enigma2/cineview_mla"
RUNTIME = os.path.join(STATE, "runtime.json")
PREVIEW_NONE = os.path.join(SKIN_DIR, "mla_assets", "preview_none.png")
PROFILES = os.path.join(STATE, "profiles")
POSTER_SECTIONS = ("infobar", "secondinfobar", "channelselection", "epg", "pvr", "eventview")
HEALTHY_AFTER_MS = 60000
TRIAL_CONFIRM_SECONDS = 20
TRIAL_GRACE_SECONDS = 40  # deadline = healthy (60 s) + prompt (20 s) + grace
_timer = None
_session = None
# version / build / commit written by the package (tools/mla/package_ipk.py); a development deploy has none
VERSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.json")
COPYRIGHT = "Design & Development by habeb-s \u00a9 2026"
PLUGIN_ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin.png")


def about():
	"""'CineView MLA 1.0.0 · build87 · d71db9d' + the rights line; never raises (missing file -> 'development')."""
	try:
		v = json.load(open(VERSION_FILE))
		ver = "CineView MLA %s \u00b7 %s \u00b7 %s" % (v.get("version", "?"), v.get("build", "?"), v.get("commit", "?"))
	except Exception:
		ver = "CineView MLA (development)"
	return "%s\n%s" % (ver, COPYRIGHT)


# ------------------------------------------------------------------ state helpers
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


def engine():
	spec = importlib.util.spec_from_file_location("cineview_mla_composer", os.path.join(SKIN_DIR, "mla", "engine", "composer.py"))
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


def runtime():
	try:
		return json.load(open(RUNTIME))
	except Exception:
		return {}


def save_runtime(data):
	cur = runtime()
	cur.update(data)
	_write("runtime.json", json.dumps(cur, indent=1, sort_keys=True))


def mla_active():
	return config.skin.primary_skin.value.startswith("CineView_FHD_MLA/")


# ------------------------------------------------------------------ guardian signals + trial confirm
def _dump_live_config():
	"""Diagnostics (tmpfs only): live values of settings other plugins may change at runtime."""
	try:
		live = {"time": int(time.time()), "primary_skin": config.skin.primary_skin.value}
		for key in ("show_second_infobar", "second_infobar_timeout", "infobar_timeout"):
			item = getattr(config.usage, key, None)
			if item is not None:
				live["usage." + key] = {"live": str(item.value), "saved": str(item.saved_value)}
		if not os.path.isdir("/tmp/CINEVIEW-MLA"):
			os.makedirs("/tmp/CINEVIEW-MLA")
		with open("/tmp/CINEVIEW-MLA/live_config.json", "w") as f:
			json.dump(live, f, indent=1, sort_keys=True)
	except Exception as err:
		print("[CineViewMLA] live config dump failed: %s" % err)


def _healthy():
	_write("boot.count", "0")
	_write("healthy", str(int(time.time())))
	print("[CineViewMLA] session healthy; guardian counter reset")
	_dump_live_config()
	if _trial.running and _session is not None and mla_active():
		_trial.prompt = _session.openWithCallback(_trialAnswer, MessageBox,
			_("Keep the %s design with %s theme?\nCineView returns to the previous design automatically if you do not confirm.") % _active_names(),
			MessageBox.TYPE_YESNO, timeout=TRIAL_CONFIRM_SECONDS, default=False)


class _TrialWatch:
	"""Trial safety that does NOT depend on the guardian (which only sees process restarts) nor on the
	confirmation dialog: while a trial design is unconfirmed, a Python crash handled in-process by
	OpenATV's bsod (Enigma2 keeps running), or a missing answer by the deadline, reverts to the
	last-known-good design and restarts the GUI.  If even this fails (process crash, power loss),
	composer.recover() reverts at the next start because the journal still says TRIAL_RUNNING."""

	def __init__(self):
		self.running = False
		self.since = 0
		self.done = False
		self.prompt = None
		self.timer = None

	def start(self):
		try:
			self.running = engine().mark_trial_running()
		except Exception as err:
			print("[CineViewMLA] trial state unavailable: %s" % err)
			self.running = False
		if not self.running:
			return
		self.since = time.time()
		self.timer = eTimer()
		self.timer.callback.append(self.check)
		self.timer.start(2000, False)
		print("[CineViewMLA] trial watch started")

	def crash_logs(self):
		dirs = {"/home/root/logs/"}
		try:
			path = config.crash.debug_path.value
			if path:
				dirs.add(path)
		except Exception:
			pass
		found = []
		for d in dirs:
			try:
				for f in os.listdir(d):
					if f.endswith("-enigma2-crash.log") and os.path.getmtime(os.path.join(d, f)) >= self.since - 1:
						found.append(f)
			except OSError:
				pass
		return found

	def check(self):
		if self.done or not self.running:
			return
		crashes = self.crash_logs()
		if crashes:
			self.revert("crash during trial: %s" % ", ".join(sorted(crashes)))
		elif time.time() - self.since > (HEALTHY_AFTER_MS / 1000.0) + TRIAL_CONFIRM_SECONDS + TRIAL_GRACE_SECONDS:
			self.revert("trial not confirmed in time")

	def commit(self):
		crashes = self.crash_logs()
		if crashes:
			self.revert("crash during trial: %s" % ", ".join(sorted(crashes)))
			return
		self.done = True
		self.timer and self.timer.stop()
		engine().commit()
		print("[CineViewMLA] trial committed")

	def revert(self, reason):
		if self.done:
			return
		self.done = True
		self.timer and self.timer.stop()
		print("[CineViewMLA] trial reverted: %s" % reason)
		try:
			eng = engine()
			eng._log("trial: revert (%s)" % reason)
			eng.rollback()
		except Exception as err:
			print("[CineViewMLA] rollback failed: %s (guardian/recover will retry at next start)" % err)
		try:
			if self.prompt is not None:
				self.prompt.close(False)
		except Exception:
			pass
		try:
			from Screens.Standby import TryQuitMainloop
			_session.open(TryQuitMainloop, 3)
		except Exception as err:
			print("[CineViewMLA] GUI restart failed: %s" % err)


_trial = _TrialWatch()


def _trialAnswer(answer):
	_trial.prompt = None
	try:
		if answer:
			_trial.commit()
		else:
			_trial.revert("declined by user / prompt timeout")
	except Exception as err:
		print("[CineViewMLA] trial handling failed: %s" % err)
		_trial.revert("trial handling failed: %s" % err)


def _clean_exit():
	_write("clean_exit", "1")


# ------------------------------------------------------------------ settings model
def _build_config():
	if not hasattr(config.plugins, "cineviewmla"):
		config.plugins.cineviewmla = ConfigSubsection()
	c = config.plugins.cineviewmla
	if not hasattr(c, "servermode"):
		c.servermode = ConfigSelection(default="profile", choices=[("full", _("Full server details")), ("profile", _("EMU + subscription only")), ("hide", _("Hide server information"))])
	# Live poster switches, read by the skin (ConfigEntryTest on the poster frames) and by the
	# CineViewMLAPosterX renderer (toggle="config.plugins.cineviewmla.poster_<section>").
	for sec in POSTER_SECTIONS:
		if not hasattr(c, "poster_" + sec):
			setattr(c, "poster_" + sec, ConfigYesNo(default=True))
	return c


# Defined at import: plugins are read (StartEnigma.runScreenTest -> readPluginList) before the
# InfoBar and the other skinned screens exist, so the skin sees the saved values from the start.
_build_config()


def theme_label(key):
	try:
		return json.load(open(os.path.join(SKIN_DIR, "themes", key, "theme.json")))["label"]
	except Exception:
		return key


def design_name(layouts):
	"""The design model whose layouts are selected in every section (EventView: Classic or Classic line by line),
	otherwise "Custom" - for the user-facing texts (no generation ids)."""
	for mid in MODEL_ORDER:
		want = dict(MODELS[mid]["layouts"])
		got = dict(layouts or {})
		if mid == "classic" and got.get("eventview") == "classic-lines":
			got["eventview"] = "classic"
		if all(got.get(s) == l for s, l in want.items()):
			return _(MODELS[mid]["label"])
	return _("Custom")


def _active_names():
	try:
		sel = engine().current_selection()
		return (design_name(sel.get("layouts")), theme_label(sel.get("theme", "navy")))
	except Exception:
		return (_("the new"), "")


def status_text(sel):
	"""What the user sees: product + version, design, theme, rights.  Generation / build / commit stay in the log
	and in version.json (user 2026-10-07)."""
	ver = "1.0.0"
	try:
		ver = json.load(open(VERSION_FILE)).get("version", ver)
	except Exception:
		pass
	return "CineView MLA %s\n%s: %s   %s: %s\n%s" % (ver, _("Design"), design_name(sel.get("layouts")), _("Theme"), theme_label(sel.get("theme", "navy")), COPYRIGHT)


class CineViewMLASetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["CineViewMLASetup", "Setup"]
		self.setTitle(_("CineView Designs"))
		self.eng = engine()
		self.sel = self.eng.current_selection()
		try:  # development details: log only (not on screen)
			st = self.eng.status()
			print("[CineViewMLA] CineView Designs: active %s, last known good %s; %s" % (st.get("active"), st.get("lkg"), about().replace("\n", " / ")))
		except Exception as err:
			print("[CineViewMLA] status: %s" % err)
		self.layouts = self.eng.layouts()
		self.secs = self.eng.sections()
		themes = self.eng.themes()
		theme_labels = []
		for t in themes:
			try:
				theme_labels.append((t, json.load(open(os.path.join(SKIN_DIR, "themes", t, "theme.json")))["label"]))
			except Exception:
				theme_labels.append((t, t))
		self.cfgTheme = ConfigSelection(default=self.sel.get("theme", "navy"), choices=theme_labels)
		self.cfgLayouts = {}
		for sec, spec in self.secs.items():
			choices = [(lid, m.get("name", lid)) for lid, m in sorted(self.layouts.get(sec, {}).items())]
			self.cfgLayouts[sec] = ConfigSelection(default=self.sel["layouts"].get(sec, "classic"), choices=choices)
		self.mla = _build_config()
		self.cfgPosters = {sec: getattr(self.mla, "poster_" + sec) for sec in POSTER_SECTIONS}
		entries = [getConfigListEntry(_("Color theme"), self.cfgTheme, "theme", "")]
		for sec, spec in self.secs.items():
			entries.append(getConfigListEntry(_("Design") + " - " + _(spec.get("label", sec)), self.cfgLayouts[sec], "layout", sec))
		for sec, cfg in self.cfgPosters.items():
			entries.append(getConfigListEntry(_("Posters") + " - " + _(self.secs.get(sec, {}).get("label", sec)), cfg, "poster", sec))
		# Row values are drawn in the list's value font: short labels; the details are in the description (t98).
		self.cfgEngine = ConfigSelection(default=runtime().get("poster_engine", "identity") if runtime().get("poster_engine", "identity") in ("identity", "legacy") else "identity",
			choices=[("identity", _("Unified (verified match)")), ("legacy", _("Legacy (title search)"))])
		entries += [
			getConfigListEntry(_("Poster engine"), self.cfgEngine, "engine", ""),
			getConfigListEntry(_("Server / CAM information"), self.mla.servermode, "native", "servermode"),
			getConfigListEntry(_("Second InfoBar mode"), config.usage.show_second_infobar, "native", "show_second_infobar"),
			getConfigListEntry(_("Second InfoBar timeout"), config.usage.second_infobar_timeout, "native", "second_infobar_timeout"),
		]
		ConfigListScreen.__init__(self, entries, session=session, on_change=self.updatePreview)
		self["preview"] = Pixmap()
		# CineView Info Card (user 2026-10-07): rows without a real visual preview show a card in the preview area -
		# CineView icon, option name, short explanation, current value, restart or not.  Never a placeholder image.
		for k in ("info_bg", "info_accent", "info_title", "info_text", "info_value", "info_restart"):
			self[k] = Label("")
		self["info_icon"] = Pixmap()
		self["description"] = Label("")
		self["status"] = Label("")
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Apply Design"))
		self["key_yellow"] = StaticText(_("Preview"))
		self["key_blue"] = StaticText(_("Restore Factory Design"))
		self["mlaActions"] = ActionMap(["OkCancelActions", "ColorActions", "MenuActions"], {
			"cancel": self.keyCancel, "red": self.keyCancel, "green": self.keyApply,
			"yellow": self.keyPreview, "blue": self.keyFactory, "ok": self.keyPreview,
			"menu": self.keyProfiles,
		}, -2)
		self["config"].onSelectionChanged.append(self.updatePreview)
		self.onLayoutFinish.append(self.updatePreview)

	def createSummary(self):
		# Screen.createSummary() (first in the MRO) returns None, so 57b7a51 falls back to ScreenSummary, which
		# picks the "SetupSummary" skin (skinName contains "Setup") without its "entry"/"value" sources
		# -> skin errors in the log (18:45:05).  Use the native SetupSummary like ConfigListScreen does.
		from Screens.Setup import SetupSummary
		return SetupSummary

	def _current(self):
		cur = self["config"].getCurrent()
		return cur if cur and len(cur) >= 4 else (None, None, None, None)

	def _preview_path(self):
		cfg, kind, sec = self._current()[1:]  # never bind "_": it is gettext here
		if kind == "layout":
			p = os.path.join(SKIN_DIR, "layouts", sec, cfg.value, "preview.png")
		elif kind == "theme":
			p = os.path.join(SKIN_DIR, "themes", cfg.value, "preview.png")
		elif kind == "poster" and sec in self.cfgLayouts:
			# Posters On / Off side by side, captured on the receiver for this section's selected design
			p = os.path.join(SKIN_DIR, "layouts", sec, self.cfgLayouts[sec].value, "preview_posters.png")
		else:
			p = None
		return p if p and os.path.isfile(p) else None

	def _card(self, kind, sec, cfg):
		"""(title, short explanation, restart text) of the Info Card for a row without a visual preview."""
		label = self._current()[0] or ""
		no_restart = _("No restart needed - saved with GREEN.")
		if kind == "poster":
			return (label, _("Shows or hides the poster in this section, in the designs that have a poster area here."), _("No restart needed - changes from the next channel or event."))
		if kind == "engine":
			return (label, _("How CineView finds posters: Unified shows a poster only when title, type and year match."), _("Restart needed - after the next GUI restart."))
		if kind == "native":
			return {
				"servermode": (label, _("What the InfoBar shows about the CAM / server."), no_restart),
				"show_second_infobar": (label, _("What the INFO key opens after the InfoBar (OpenATV setting)."), no_restart),
				"second_infobar_timeout": (label, _("How long the Second InfoBar stays on screen (OpenATV setting)."), no_restart),
			}.get(sec, (label, "", no_restart))
		if kind == "theme":
			return (label, _("The colours of every CineView screen."), _("The GUI restarts and asks you to keep the new design."))
		m = self.layouts.get(sec, {}).get(getattr(cfg, "value", None), {}) if kind == "layout" else {}
		return (label, m.get("name", ""), _("The GUI restarts and asks you to keep the new design."))

	def _show_card(self, show, kind=None, sec=None, cfg=None):
		names = ("info_bg", "info_accent", "info_title", "info_text", "info_value", "info_restart", "info_icon")
		if not show:
			for k in names:
				self[k].hide()
			return
		title, text, restart = self._card(kind, sec, cfg)
		self["info_title"].setText(title)
		self["info_text"].setText(text)
		self["info_value"].setText("%s: %s" % (_("Current value"), cfg.getText() if cfg is not None else ""))
		self["info_restart"].setText(restart)
		if self["info_icon"].instance and os.path.isfile(PLUGIN_ICON):
			self["info_icon"].instance.setPixmap(LoadPixmap(PLUGIN_ICON))
		for k in names:
			self[k].show()

	def updatePreview(self):
		cfg, kind, sec = self._current()[1:]  # never bind "_": it is gettext here
		p = self._preview_path()
		if self["preview"].instance:
			if p:
				self["preview"].instance.setPixmap(LoadPixmap(p))
				self["preview"].show()
			else:
				self["preview"].hide()
		self._show_card(not p and kind is not None, kind, sec, cfg)
		desc = ""
		applied = _("GREEN applies it: the GUI restarts and the new design is kept only after you confirm it.")
		if kind == "theme":
			desc = "%s\n%s\n\n%s" % (_("Colour theme"), cfg.getText(), _("The colours of every CineView screen.") + " " + applied)
		elif kind == "layout":
			m = self.layouts.get(sec, {}).get(cfg.value, {})
			desc = "%s\n\n%s" % (m.get("name", cfg.value), applied)
		elif kind == "poster":
			desc = _("The picture shows this section with posters on and with posters off - the other elements move to use the space.") if p else ""
			desc = (desc + "\n\n" if desc else "") + _("Applied without a restart, from the next channel or event change.")
		elif kind == "engine":
			desc = _("Unified: a poster only when title, type and year are confirmed, otherwise the CineView default image.\nLegacy: the original title search (may show posters of other works).\nTakes effect after the next GUI restart.")
		elif kind == "native":
			desc = {
				"servermode": _("Full server details, only the EMU and the subscription, or nothing."),
				"show_second_infobar": _("Second InfoBar, event information or nothing when INFO is pressed again."),
				"second_infobar_timeout": _("After this time the Second InfoBar closes by itself."),
			}.get(sec, "")
		self["description"].setText(desc)
		# YELLOW / OK only where they do something: the Preview key is shown only when this row has a preview
		self["key_yellow"].setText(_("Preview") if p else "")
		self["status"].setText(status_text(self.sel))

	def _selection(self):
		return {"theme": self.cfgTheme.value, "layouts": {s: c.value for s, c in self.cfgLayouts.items()}}

	def _save_runtime_and_native(self):
		for cfg in [self.mla.servermode, config.usage.show_second_infobar, config.usage.second_infobar_timeout] + list(self.cfgPosters.values()):
			cfg.save()
		configfile.save()
		self._engine_changed = runtime().get("poster_engine", "identity") != self.cfgEngine.value
		if self._engine_changed:
			save_runtime({"poster_engine": self.cfgEngine.value})

	def keyApply(self):
		self._save_runtime_and_native()
		new = self._selection()
		if new == {"theme": self.sel.get("theme"), "layouts": self.sel.get("layouts")}:
			msg = _("Settings saved. The design is unchanged.")
			if getattr(self, "_engine_changed", False):
				msg += "\n" + _("The poster engine changes after the next GUI restart.")
			self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=6)
			self.close()
			return
		try:
			gid = self.eng.apply(new, trial=True, components=self.eng.installed_components())
		except Exception as err:
			self.session.open(MessageBox, _("The design could not be applied:\n%s") % err, MessageBox.TYPE_ERROR)
			return
		self.session.openWithCallback(self._restart, MessageBox,
			_("Apply %s design with %s theme?\nThe GUI restarts and you will be asked to keep the new design.") % (design_name(new["layouts"]), theme_label(new["theme"])), MessageBox.TYPE_YESNO)
		print("[CineViewMLA] trial generation %s prepared" % gid)

	def _restart(self, answer):
		if answer:
			from Screens.Standby import TryQuitMainloop
			self.session.open(TryQuitMainloop, 3)
		else:
			try:
				self.eng.rollback()
			except Exception:
				pass
		self.close()

	# ---------------------------------------------------------------- profiles (Blueprint 2.7: JSON export/import)
	def _profile_names(self):
		try:
			return sorted(f[:-5] for f in os.listdir(PROFILES) if f.endswith(".json"))
		except OSError:
			return []

	def keyProfiles(self):
		from Screens.ChoiceBox import ChoiceBox
		choices = [(_("Apply a design model to every section"), "model"), (_("Save current settings as a profile"), "save")]
		if self._profile_names():
			choices += [(_("Load a profile"), "load"), (_("Delete a profile"), "delete")]
		self.session.openWithCallback(self._profileAction, ChoiceBox, text=_("CineView profiles"), choiceList=choices, windowTitle=_("CineView Designs"))

	def _profileAction(self, choice):
		from Screens.ChoiceBox import ChoiceBox
		if not choice:
			return
		if choice[1] == "model":
			models = [(_(MODELS[m]["label"]), m) for m in MODEL_ORDER]
			self.session.openWithCallback(self._modelLoad, ChoiceBox, text=_("Design model"), choiceList=models, windowTitle=_("CineView Designs"))
			return
		if choice[1] == "save":
			from Screens.VirtualKeyBoard import VirtualKeyBoard
			self.session.openWithCallback(self._profileSave, VirtualKeyBoard, title=_("Profile name"), text=_("My CineView"))
		else:
			names = [(n, n) for n in self._profile_names()]
			cb = self._profileLoad if choice[1] == "load" else self._profileDelete
			self.session.openWithCallback(cb, ChoiceBox, text=_("Select a profile"), choiceList=names, windowTitle=_("CineView Designs"))

	def _profile_data(self):
		return {"schema": 1, "theme": self.cfgTheme.value, "layouts": {s: c.value for s, c in self.cfgLayouts.items()},
			"posters": {s: bool(c.value) for s, c in self.cfgPosters.items()}, "servermode": self.mla.servermode.value,
			"show_second_infobar": config.usage.show_second_infobar.value, "second_infobar_timeout": config.usage.second_infobar_timeout.value,
			"poster_engine": self.cfgEngine.value}

	def _profileSave(self, name):
		import re as _re
		name = _re.sub(r"[^A-Za-z0-9 _.-]+", "", (name or "")).strip()[:40]
		if not name:
			return
		try:
			os.makedirs(PROFILES, exist_ok=True)
			path = os.path.join(PROFILES, name + ".json")
			with open(path + ".tmp", "w") as f:
				json.dump(self._profile_data(), f, indent=1, sort_keys=True)
				f.flush()
				os.fsync(f.fileno())
			os.replace(path + ".tmp", path)
			self.session.open(MessageBox, _("Profile '%s' saved.") % name, MessageBox.TYPE_INFO, timeout=4)
		except Exception as err:
			self.session.open(MessageBox, _("The profile could not be saved:\n%s") % err, MessageBox.TYPE_ERROR)

	def _profileLoad(self, choice):
		if not choice:
			return
		try:
			data = json.load(open(os.path.join(PROFILES, choice[1] + ".json")))
		except Exception as err:
			self.session.open(MessageBox, _("The profile could not be read:\n%s") % err, MessageBox.TYPE_ERROR)
			return
		skipped = []
		def setc(cfg, value, what):
			if value is None:
				return
			if hasattr(cfg, "choices") and value not in list(cfg.choices):  # choicesList iterates its keys (57b7a51)
				skipped.append(what)  # e.g. a design pack that is not installed: keep the current value
				return
			cfg.value = value
		setc(self.cfgTheme, data.get("theme"), "theme")
		for sec, lid in (data.get("layouts") or {}).items():
			if sec in self.cfgLayouts:
				setc(self.cfgLayouts[sec], lid, sec)
		for sec, v in (data.get("posters") or {}).items():
			if sec in self.cfgPosters:
				self.cfgPosters[sec].value = bool(v)
		setc(self.mla.servermode, data.get("servermode"), "servermode")
		setc(self.cfgEngine, data.get("poster_engine"), "poster engine")
		setc(config.usage.show_second_infobar, data.get("show_second_infobar"), "second infobar mode")
		setc(config.usage.second_infobar_timeout, data.get("second_infobar_timeout"), "second infobar timeout")
		self["config"].l.invalidate()
		self.updatePreview()
		msg = _("Profile '%s' loaded. Press GREEN to apply it.") % choice[1]
		if skipped:
			msg += "\n" + _("Not available here (kept as is): %s") % ", ".join(skipped)
		self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=6)

	def _modelLoad(self, choice):
		"""One model on every section at once (Five_Models_Plan.md: a profile applies one model to all sections).
		Only the selection in this screen changes; GREEN applies it through the engine (trial + automatic revert).
		A section whose design is not installed keeps its current design and is listed."""
		if not choice:
			return
		model = MODELS.get(choice[1], {})
		skipped = []
		for sec, lid in model.get("layouts", {}).items():
			cfg = self.cfgLayouts.get(sec)
			if cfg is None:
				continue
			if lid in list(cfg.choices):
				cfg.value = lid
			else:
				skipped.append(_(self.secs.get(sec, {}).get("label", sec)))
		self["config"].l.invalidate()
		self.updatePreview()
		msg = _("Model '%s' selected for every section. Press GREEN to apply it.") % _(model.get("label", choice[1]))
		if skipped:
			msg += "\n" + _("Not available yet (kept as is): %s") % ", ".join(skipped)
		self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=6)

	def _profileDelete(self, choice):
		if not choice:
			return
		self._to_delete = choice[1]
		self.session.openWithCallback(self._profileDeleteConfirmed, MessageBox, _("Delete the profile '%s'?") % choice[1], MessageBox.TYPE_YESNO, default=False)

	def _profileDeleteConfirmed(self, answer):
		if answer:
			try:
				os.remove(os.path.join(PROFILES, self._to_delete + ".json"))
			except OSError as err:
				self.session.open(MessageBox, _("The profile could not be deleted:\n%s") % err, MessageBox.TYPE_ERROR)

	def keyPreview(self):
		p = self._preview_path()
		if p:  # no preview: the key has no label and does nothing (no empty message window)
			self.session.open(CineViewMLAPreview, p)

	def keyFactory(self):
		self.session.openWithCallback(self._factory, MessageBox, _("Restore Factory Design?\nRestores Classic + Navy and the default CineView layout settings."), MessageBox.TYPE_YESNO, default=False)

	def _factory(self, answer):
		if answer:
			self.eng.rollback("factory")
			self._restart(True)

	def keyCancel(self):
		for c in [self.mla.servermode, config.usage.show_second_infobar, config.usage.second_infobar_timeout] + list(self.cfgPosters.values()):
			c.cancel()
		self.close()


class CineViewMLAPreview(Screen):
	def __init__(self, session, path):
		Screen.__init__(self, session)
		self.skinName = ["CineViewMLAPreview"]
		self.path = path
		self["image"] = Pixmap()
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.close, "cancel": self.close}, -1)
		self.onLayoutFinish.append(self._show)

	def _show(self):
		self["image"].instance.setPixmap(LoadPixmap(self.path))


# ------------------------------------------------------------------ plugin hooks
def main(session, **kwargs):
	session.open(CineViewMLASetup)


# Design models (Five_Models_Plan.md "Mapping proposal"; looks pending the user's approval except Classic).
MODEL_ORDER = ("classic", "details", "cinema", "modern", "minimal")
MODELS = {
	"classic": {"label": "Classic", "layouts": {"infobar": "classic", "secondinfobar": "classic", "channelselection": "classic", "epg": "classic", "pvr": "classic", "eventview": "classic"}},
	"details": {"label": "Details", "layouts": {"infobar": "details", "secondinfobar": "details", "channelselection": "posterlist", "epg": "graphicalplus", "pvr": "cover", "eventview": "detailscard"}},
	"cinema": {"label": "Cinema", "layouts": {"infobar": "cinema", "secondinfobar": "cinema", "channelselection": "videofirst", "epg": "graphicalplus", "pvr": "cinema", "eventview": "feature"}},
	"modern": {"label": "Modern", "layouts": {"infobar": "modern", "secondinfobar": "modern", "channelselection": "modern", "epg": "modern", "pvr": "modern", "eventview": "modern"}},
	"minimal": {"label": "Minimal", "layouts": {"infobar": "minimal", "secondinfobar": "minimal", "channelselection": "minimal", "epg": "minimal", "pvr": "minimal", "eventview": "minimal"}},
}

POSTER_OFF_SUFFIX = "_CVPosterOff"


def _event_has_poster(event):
	"""True when the poster engine already holds a reliable poster for this event (cache only, no network).
	Screens whose layout is fixed when they open (named-widget EventView designs) use their No Poster screen
	('<name>_CVPosterOff') for events without one, instead of a placeholder (user decision 2026-10-05 22:03).
	Unknown (engine not loaded, error) -> True: the normal screen, as before."""
	if event is None:
		return False
	try:
		import Components.Renderer.CineViewMLAPosterX as P
		name, short, ext, begin = P._mla_event_texts(event)
		if not name:
			return False
		ident = P._mla_identify(name, short, ext, now_year=time.localtime().tm_year + 1)
		if ident.get("generic"):
			return False
		return bool(P._mla_cached(ident))
	except Exception as err:
		print("[CineViewMLA] poster lookup: %s" % err)
		return True


def _poster_off(section, event=None, check_event=False):
	if configfile.getResolvedKey("config.plugins.cineviewmla.poster_%s" % section, silent=True) == "False":
		return True
	return check_event and not _event_has_poster(event)


def _install_poster_off_names():
	"""Posters OFF for screens whose texts are Python-owned named widgets (SecondInfoBarECM, EventViewSimple,
	InfoBarEventView).  The skin ships '<name>_CVPosterOff' screens with the wider geometry; here the screen's
	skinName list gets '<name>_CVPosterOff' in front of each name BEFORE the skin is applied (the session applies
	the skin after __init__), so the native skinName fallback uses it when it exists and otherwise the normal
	screen.  Only the in-memory classes are wrapped (no enigma2 file is touched); errors never reach the screen."""
	targets = []
	try:
		from Screens.InfoBarGenerics import SecondInfoBar
		targets.append((SecondInfoBar, "secondinfobar"))
	except Exception as err:
		print("[CineViewMLA] posters-off names: SecondInfoBar unavailable: %s" % err)
	try:
		from Screens.EventView import EventViewSimple
		targets.append((EventViewSimple, "eventview"))
	except Exception as err:
		print("[CineViewMLA] posters-off names: EventViewSimple unavailable: %s" % err)
	try:
		from Screens.EpgSelection import EPGSelection
		targets.append((EPGSelection, "epg"))  # GraphicalEPG_CVPosterOff (EPG pack "graphicalplus")
	except Exception as err:
		print("[CineViewMLA] posters-off names: EPGSelection unavailable: %s" % err)
	try:
		from Screens.MovieSelection import MovieSelection
		targets.append((MovieSelection, "pvr"))  # MovieSelection_CVPosterOff (PVR pack "cover")
	except Exception as err:
		print("[CineViewMLA] posters-off names: MovieSelection unavailable: %s" % err)
	try:
		# EnhancedMovieCenter (the PVR key on this receiver opens it): its EMCSelection screen; EMC's own skin
		# choice (config.EMC.use_orig_skin -> "EMCSelectionOwn") is left alone (see the name check below)
		from Plugins.Extensions.EnhancedMovieCenter.MovieSelection import EMCSelection
		targets.append((EMCSelection, "pvr"))
	except Exception as err:
		print("[CineViewMLA] posters-off names: EMCSelection unavailable: %s" % err)
	for cls, section in targets:
		orig = cls.__init__
		if getattr(orig, "_cvmla_poster_off", False):
			continue

		def wrapped(self, *args, _orig=orig, _section=section, **kw):
			_orig(self, *args, **kw)
			try:
				# EventViewSimple / InfoBarEventView (session, event, ref, ...): an event without a poster also gets the
				# No Poster screen
				ev = args[1] if _section == "eventview" and len(args) > 1 else kw.get("Event", kw.get("event"))
				if mla_active() and _poster_off(_section, ev, check_event=(_section == "eventview")):
					names = self.skinName if isinstance(self.skinName, list) else [self.skinName]
					if _section == "pvr" and names not in (["MovieSelection"], ["EMCSelectionExtended", "EMCSelection"]):
						names = []  # MovieSelectionSlim / EMCSelectionOwn (the user's own choices) keep their screens
					if names and not names[0].endswith(POSTER_OFF_SUFFIX):
						self.skinName = [n + POSTER_OFF_SUFFIX for n in names] + list(names)
			except Exception as err:
				print("[CineViewMLA] posters-off names: %s" % err)
		wrapped._cvmla_poster_off = True
		cls.__init__ = wrapped
		print("[CineViewMLA] posters-off names installed for %s" % cls.__name__)


def _install_epg_eventview_name():
	"""EventView opened from an EPG (EventViewEPGSelect, skinName ["EventView"]) shows the SELECTED event, but the
	Classic 'EventView' screen is a live-channel layout: its texts come from session.Event_Now / Event_Next /
	CurrentService and only its poster from 'Event' (device t42 2026-10-05: vertical EPG, INFO on HBO 2
	'Nevjesta!' -> titles/times of HBO HD 'Holland' with the poster of 'The Bride!').  The Classic
	'EventViewSimple' screen is built on the screen's own Event / Service sources and native widgets, so
	EventViewEPGSelect gets it in front of 'EventView' ('_CVPosterOff' first while EventView posters are off).
	Only the default name list is changed (a caller-supplied skinName is kept); nothing is changed while
	another skin is active; no enigma2 file is touched."""
	try:
		from Screens.EventView import EventViewEPGSelect
	except Exception as err:
		print("[CineViewMLA] EPG event view name: unavailable: %s" % err)
		return
	orig = EventViewEPGSelect.__init__
	if getattr(orig, "_cvmla_epg_ev", False):
		return

	def _not_live_now(session, args, kw):
		# EventViewEPGSelect(session, event, serviceRef, ...): the InfoBar also opens it for the playing service's
		# CURRENT event (device t47: live INFO); only there do the Classic dashboard's session sources (now / next
		# of the playing service) describe the shown event.  Any other service or any other event -> True.
		try:
			event = args[0] if args else kw.get("event")
			ref = args[1] if len(args) > 1 else kw.get("serviceRef")
			ref = getattr(ref, "ref", ref)
			playing = session.nav.getCurrentlyPlayingServiceOrGroup()
			if ref is None or playing is None or event is None:
				return False
			if ref.toCompareString() != playing.toCompareString():
				return True
			service = session.nav.getCurrentService()
			info = service and service.info()
			now = info and info.getEvent(0)
			return now is None or now.getEventId() != event.getEventId()
		except Exception:
			return False

	def wrapped(self, session, *args, **kw):
		orig(self, session, *args, **kw)
		try:
			event = args[0] if args else kw.get("event")
			if mla_active() and self.skinName == ["EventView"] and _not_live_now(session, args, kw):
				names = ["EventViewSimple", "EventView"]
				if _poster_off("eventview", event, check_event=True):
					names = ["EventViewSimple" + POSTER_OFF_SUFFIX] + names
				self.skinName = names
			elif mla_active() and self.skinName == ["EventView"] and _poster_off("eventview", event, check_event=True):
				# live event, posters off: a design built on the native named widgets ships 'EventView_CVPosterOff'
				# (Cinema Feature); designs without it (Classic dashboard) fall back to 'EventView' natively
				self.skinName = ["EventView" + POSTER_OFF_SUFFIX, "EventView"]
		except Exception as err:
			print("[CineViewMLA] EPG event view name: %s" % err)
	wrapped._cvmla_epg_ev = True
	EventViewEPGSelect.__init__ = wrapped
	print("[CineViewMLA] EPG event view name installed")


NAME_CLIP_LAYOUTS = ("posterlist", "videofirst", "videofirst-right", "modern", "minimal")  # narrow channel lists (D1, Modern 808 px, Minimal 744 px)


def _active_layout(section):
	try:
		return json.load(open(os.path.join(SKIN_DIR, "active", "selection.json")))["layouts"].get(section)
	except Exception:
		return None


def _clip_service_name_cell(lst, mode):
	"""enigma2 57b7a51 eListboxServiceContent (lib/service/listboxservice.cpp): the service-name text is laid out
	with the width of its cell and THEN moved right by the picon (xoffs += iconWidth + itemsDistances), so a long
	name runs that far past its cell — onto the progress bar on the right.  The cell itself is set from Python
	(ServiceListLegacy.setMode); here it is narrowed by exactly that offset so the name ends where the cell was
	meant to end.  Only the D1 channel-list designs, single-line rows, bar on the right, column mode 'Disable'
	(the defaults on this receiver).  The event text that follows the name ends the same amount earlier."""
	from enigma import eRect
	from Components.ServiceList import ServiceListLegacy
	cu = config.usage
	if getattr(lst, "instance", None) is None:
		return None  # setMode before the widget exists; postWidgetCreate calls it again
	if not mla_active() or _active_layout("channelselection") not in NAME_CLIP_LAYOUTS:
		return None
	# Only the TV channel list skinned by the D1 designs (screen class ChannelSelection).  The radio list and the
	# other channel pickers keep the Classic skin and its wide rows (user review 2026-10-04 22:06: the radio list
	# lost ~73 px of event text when the clip applied to every legacy list).
	if type(getattr(lst, "serviceList", None)).__name__ != "ChannelSelection":
		return None
	if cu.servicelist_twolines.value or cu.servicelist_column.value != "-1" or not cu.service_icon_enable.value:
		return None
	view = cu.show_event_progress_in_servicelist.value
	if view != "barright":
		return None
	if mode != ServiceListLegacy.MODE_BOUQUETS or not cu.show_channel_numbers_in_servicelist.value:
		num_w, num_space = 0, lst.listMarginLeft
	else:
		from Tools.TextBoundary import getTextBoundarySize  # same import as Components/ServiceList.py
		size = lst.instance.size()
		num_w = cu.alternative_number_mode.value and getTextBoundarySize(lst.instance, lst.ServiceNumberFont, size, "0" * cu.numberZapDigits.value).width() or getTextBoundarySize(lst.instance, lst.ServiceNumberFont, size, "00000").width()
		num_space = lst.fieldMargins + lst.listMarginLeft
	row_w = lst.instance.size().width() - lst.listMarginRight
	width = row_w - (num_w + num_space + lst.progressBarWidth + lst.fieldMargins)  # = ServiceListLegacy.setMode
	icon_w = int((lst.ItemHeight + int(cu.servicelist_picon_downsize.value) * 2) * (int(cu.servicelist_picon_ratio.value) * 0.01))
	shift = icon_w + lst.itemsDistances
	for mode_cfg, pic in ((cu.servicetype_icon_mode, lst.picDVB_S), (cu.crypto_icon_mode, lst.picCrypto)):
		if mode_cfg.value == "1" and pic:  # further icons left of the name move the text the same way
			shift += pic.size().width() + lst.itemsDistances
	if width - shift < 100:
		return None
	lst.l.setElementPosition(lst.l.celServiceName, eRect(num_w + num_space, 0, width - shift, lst.ItemHeight))
	return width, shift


def _install_service_name_clip():
	try:
		from Components.ServiceList import ServiceListLegacy
	except Exception as err:
		print("[CineViewMLA] name clip: ServiceListLegacy unavailable: %s" % err)
		return
	orig = ServiceListLegacy.setMode
	if getattr(orig, "_cvmla_name_clip", False):
		return

	def setMode(self, mode, _orig=orig):
		_orig(self, mode)
		try:
			r = _clip_service_name_cell(self, mode)
			if r:
				print("[CineViewMLA] name clip: name cell %d -> %d px (picon offset %d)" % (r[0], r[0] - r[1], r[1]))
		except Exception as err:
			print("[CineViewMLA] name clip: %s" % err)
	setMode._cvmla_name_clip = True
	ServiceListLegacy.setMode = setMode
	print("[CineViewMLA] name clip installed")


def _install_package_waiting():
	"""Plugin Browser -> Install / Remove / Update Plugins (device t96 2026-10-06, live stack): while opkg runs,
	PackageAction.setWaiting(text) shows the global Processing dialog with `text` AND the screen keeps the same text
	in its own 'description' label ("Downloading plugin information. Please wait..." twice on the TV).  While the
	Processing dialog is up, the screen's copy is cleared (and the HELP label, whose key opens help behind the busy
	dialog); both come back when setWaiting(None) ends the wait, unless the screen has set a new text meanwhile
	(the package count / an error message - those are kept).  Display only: the action maps, opkg and every key stay
	native.  Nothing changes while another skin is active; no enigma2 file is touched."""
	try:
		from Screens.PluginBrowser import PackageAction
	except Exception as err:
		print("[CineViewMLA] package waiting: unavailable: %s" % err)
		return
	orig = PackageAction.setWaiting
	if getattr(orig, "_cvmla_pkg_wait", False):
		return

	def setWaiting(self, text, _orig=orig):
		if not mla_active():
			return _orig(self, text)
		if text:
			try:
				if getattr(self, "_cvmla_wait", None) is None:
					self._cvmla_wait = (self["description"].getText(), self["key_help"].getText() if "key_help" in self else None)
			except Exception as err:
				print("[CineViewMLA] package waiting: %s" % err)
		_orig(self, text)
		try:
			saved = getattr(self, "_cvmla_wait", None)
			if text and saved is not None:
				self["description"].setText("")
				if saved[1] is not None:
					self["key_help"].setText("")
			elif not text and saved is not None:
				self._cvmla_wait = None
				if self["description"].getText() == "":
					self["description"].setText(saved[0])
				if saved[1] is not None:
					self["key_help"].setText(saved[1])
		except Exception as err:
			print("[CineViewMLA] package waiting: %s" % err)
	setWaiting._cvmla_pkg_wait = True
	PackageAction.setWaiting = setWaiting
	print("[CineViewMLA] package waiting installed")


def sessionstart(reason, session=None, **kwargs):
	global _timer, _session
	if reason != 0 or session is None:
		return
	_session = session
	_build_config()
	try:
		session.onShutdown.append(_clean_exit)
	except Exception as err:
		print("[CineViewMLA] onShutdown hook unavailable: %s" % err)
	_timer = eTimer()
	_timer.callback.append(_healthy)
	_timer.start(HEALTHY_AFTER_MS, True)
	if mla_active():
		_trial.start()
		_install_poster_off_names()
		_install_service_name_clip()
		_install_epg_eventview_name()
		_install_package_waiting()


def Plugins(**kwargs):
	return [
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart),
		PluginDescriptor(name=_("CineView Designs"), description=_("Choose and preview CineView designs, themes and options") + " \u00b7 by habeb-s", where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
	]
