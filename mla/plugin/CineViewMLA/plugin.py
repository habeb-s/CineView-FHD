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
HEALTHY_AFTER_MS = 60000
TRIAL_CONFIRM_SECONDS = 20
_timer = None
_session = None


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
	try:
		j = json.load(open(os.path.join(STATE, "txn.json")))
	except Exception:
		j = {}
	if j.get("state") == "TRIAL" and _session is not None and mla_active():
		_session.openWithCallback(_trialAnswer, MessageBox,
			_("CineView: keep the new design?\nIt will be reverted automatically if you do not confirm."),
			MessageBox.TYPE_YESNO, timeout=TRIAL_CONFIRM_SECONDS, default=False)


def _trialAnswer(answer):
	try:
		eng = engine()
		if answer:
			eng.commit()
			print("[CineViewMLA] trial committed")
		else:
			eng.rollback()
			print("[CineViewMLA] trial reverted")
			from Screens.Standby import TryQuitMainloop
			_session.open(TryQuitMainloop, 3)
	except Exception as err:
		print("[CineViewMLA] trial handling failed: %s" % err)


def _clean_exit():
	_write("clean_exit", "1")


# ------------------------------------------------------------------ settings model
def _build_config():
	if not hasattr(config.plugins, "cineviewmla"):
		config.plugins.cineviewmla = ConfigSubsection()
	c = config.plugins.cineviewmla
	if not hasattr(c, "servermode"):
		c.servermode = ConfigSelection(default="profile", choices=[("full", _("Full server details")), ("profile", _("EMU + subscription only")), ("hide", _("Hide server information"))])
	return c


class CineViewMLASetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["CineViewMLASetup", "Setup"]
		self.setTitle(_("CineView Designs"))
		self.eng = engine()
		self.sel = self.eng.current_selection()
		self.layouts = self.eng.layouts()
		self.secs = self.eng.sections()
		rt = runtime()
		posters = rt.get("posters", {})
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
		self.cfgPosters = {}
		for sec in ("infobar", "secondinfobar", "channelselection", "epg", "eventview"):
			self.cfgPosters[sec] = ConfigYesNo(default=posters.get(sec, True))
		self.mla = _build_config()
		entries = [getConfigListEntry(_("Color theme"), self.cfgTheme, "theme", "")]
		for sec, spec in self.secs.items():
			entries.append(getConfigListEntry(_("Design") + " - " + _(spec.get("label", sec)), self.cfgLayouts[sec], "layout", sec))
		for sec, cfg in self.cfgPosters.items():
			entries.append(getConfigListEntry(_("Posters") + " - " + _(self.secs.get(sec, {}).get("label", sec)), cfg, "poster", sec))
		entries += [
			getConfigListEntry(_("Server / CAM information"), self.mla.servermode, "native", ""),
			getConfigListEntry(_("Second InfoBar mode"), config.usage.show_second_infobar, "native", ""),
			getConfigListEntry(_("Second InfoBar timeout"), config.usage.second_infobar_timeout, "native", ""),
		]
		ConfigListScreen.__init__(self, entries, session=session, on_change=self.updatePreview)
		self["preview"] = Pixmap()
		self["description"] = Label("")
		self["status"] = Label("")
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Apply (trial)"))
		self["key_yellow"] = StaticText(_("Preview"))
		self["key_blue"] = StaticText(_("Factory design"))
		self["mlaActions"] = ActionMap(["OkCancelActions", "ColorActions"], {
			"cancel": self.keyCancel, "red": self.keyCancel, "green": self.keyApply,
			"yellow": self.keyPreview, "blue": self.keyFactory, "ok": self.keyPreview,
		}, -2)
		self["config"].onSelectionChanged.append(self.updatePreview)
		self.onLayoutFinish.append(self.updatePreview)

	def _current(self):
		cur = self["config"].getCurrent()
		return cur if cur and len(cur) >= 4 else (None, None, None, None)

	def _preview_path(self):
		_, cfg, kind, sec = self._current()
		if kind == "layout":
			p = os.path.join(SKIN_DIR, "layouts", sec, cfg.value, "preview.png")
		elif kind == "theme":
			p = os.path.join(SKIN_DIR, "themes", cfg.value, "preview.png")
		elif kind == "poster" and sec in self.cfgLayouts:
			p = os.path.join(SKIN_DIR, "layouts", sec, self.cfgLayouts[sec].value, "preview.png")
		else:
			p = None
		return p if p and os.path.isfile(p) else None

	def updatePreview(self):
		_, cfg, kind, sec = self._current()
		p = self._preview_path()
		if p and self["preview"].instance:
			self["preview"].instance.setPixmap(LoadPixmap(p))
			self["preview"].show()
		else:
			self["preview"].hide()
		desc = ""
		if kind == "layout":
			m = self.layouts.get(sec, {}).get(cfg.value, {})
			desc = "%s\n%s %s" % (m.get("name", cfg.value), _("Version"), m.get("version", ""))
		elif kind == "poster":
			desc = _("Shown live without a restart.")
		self["description"].setText(desc)
		st = self.eng.status()
		self["status"].setText(_("Active generation: %s   Last known good: %s") % (st.get("active"), st.get("lkg")))

	def _selection(self):
		return {"theme": self.cfgTheme.value, "layouts": {s: c.value for s, c in self.cfgLayouts.items()}}

	def _save_runtime_and_native(self):
		save_runtime({"posters": {s: c.value for s, c in self.cfgPosters.items()}})
		for cfg in (self.mla.servermode, config.usage.show_second_infobar, config.usage.second_infobar_timeout):
			cfg.save()
		configfile.save()

	def keyApply(self):
		self._save_runtime_and_native()
		new = self._selection()
		if new == {"theme": self.sel.get("theme"), "layouts": self.sel.get("layouts")}:
			self.session.open(MessageBox, _("Settings saved. The design is unchanged."), MessageBox.TYPE_INFO, timeout=4)
			self.close()
			return
		try:
			gid = self.eng.apply(new, trial=True, components=self.eng.installed_components())
		except Exception as err:
			self.session.open(MessageBox, _("The design could not be applied:\n%s") % err, MessageBox.TYPE_ERROR)
			return
		self.session.openWithCallback(self._restart, MessageBox,
			_("Design %s prepared (trial).\nRestart the GUI now to try it? You will be asked to keep it.") % gid, MessageBox.TYPE_YESNO)

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

	def keyPreview(self):
		p = self._preview_path()
		if p:
			self.session.open(CineViewMLAPreview, p)

	def keyFactory(self):
		self.session.openWithCallback(self._factory, MessageBox, _("Return to the factory CineView Classic design?"), MessageBox.TYPE_YESNO, default=False)

	def _factory(self, answer):
		if answer:
			self.eng.rollback("factory")
			self._restart(True)

	def keyCancel(self):
		for c in [self.mla.servermode, config.usage.show_second_infobar, config.usage.second_infobar_timeout]:
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


def Plugins(**kwargs):
	return [
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart),
		PluginDescriptor(name=_("CineView Designs"), description=_("Choose and preview CineView designs, themes and options"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
	]
