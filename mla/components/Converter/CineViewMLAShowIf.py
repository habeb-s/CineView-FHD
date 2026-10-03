# -*- coding: utf-8 -*-
# CineView MLA — show a renderer only while a config value matches, WITHOUT replacing its data.
#
# Native ConditionalShowHide needs a boolean source (e.g. ConfigEntryTest), which would replace the
# text of a Label/RunningText.  This converter is placed at the END of a normal chain, passes every
# attribute of its source through unchanged (text, event, ...), and sets the visibility of its
# renderers the same way ConditionalShowHide does (changed() and connectDownstream()).
#
# usage:  <convert type="EventName">Name</convert>
#         <convert type="CineViewMLAShowIf">config.plugins.cineviewmla.poster_secondinfobar,True</convert>
# args:   <config key>,<value>[,Invert]
#         The key is resolved live (configfile.getResolvedKey); a missing key resolves to the
#         converter's default "True", so posters-on layouts are shown when nothing is configured.
from Components.config import configfile
from Components.Converter.Converter import Converter


class CineViewMLAShowIf(Converter):
	def __init__(self, args):
		Converter.__init__(self, args)
		parts = [x.strip() for x in (args or "").split(",")]
		self._key = parts[0] if parts and parts[0].startswith("config.") else None
		self._value = parts[1] if len(parts) > 1 else "True"
		self._invert = "Invert" in parts[2:]
		if self._key is None:
			print("[CineViewMLAShowIf] invalid arguments '%s' (shown)" % args)

	def __getattr__(self, name):
		# Transparent like ConditionalShowHide; never recurse while the object is being built.
		if name.startswith("__") or name in ("source", "_key", "_value", "_invert"):
			raise AttributeError(name)
		return getattr(self.source, name)

	def _visible(self):
		if self._key is None:
			return True
		value = configfile.getResolvedKey(self._key, silent=True)
		if value is None:
			value = "True"
		return (value == self._value) ^ self._invert

	def changed(self, what):
		visible = self._visible()
		for element in self.downstream_elements:
			element.visible = visible
		Converter.changed(self, what)

	def connectDownstream(self, downstream):
		Converter.connectDownstream(self, downstream)
		downstream.visible = self._visible()
