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
# args:   <config key>|always,<value>[,Invert][,dir=rtl|dir=ltr]
#         The key is resolved live (configfile.getResolvedKey); a missing key resolves to the
#         converter's default "True", so posters-on layouts are shown when nothing is configured.
#         dir=: additionally require the direction of the source text (first strong character:
#         Arabic/Hebrew/Syriac/Thaana/N'Ko or their presentation forms = rtl, any other letter = ltr).
#         Used to give right-to-left texts a right-aligned variant: on OpenATV 57b7a51 eLabel treats
#         "bidi" alignment as left and wraps RTL paragraphs with the short line on top.
from Components.config import configfile
from Components.Converter.Converter import Converter


class CineViewMLAShowIf(Converter):
	def __init__(self, args):
		Converter.__init__(self, args)
		parts = [x.strip() for x in (args or "").split(",")]
		self._key = parts[0] if parts and parts[0].startswith("config.") else None
		self._always = bool(parts) and parts[0] == "always"  # "always,True,dir=rtl": direction-only switch
		self._value = parts[1] if len(parts) > 1 else "True"
		self._invert = "Invert" in parts[2:]
		self._dir = None
		for p in parts[2:]:
			if p in ("dir=rtl", "dir=ltr"):
				self._dir = p[4:]
		if self._key is None and not self._always:
			print("[CineViewMLAShowIf] invalid arguments '%s' (shown)" % args)

	def __getattr__(self, name):
		# Transparent like ConditionalShowHide; never recurse while the object is being built.
		if name.startswith("__") or name in ("source", "_key", "_value", "_invert", "_dir", "_always"):
			raise AttributeError(name)
		return getattr(self.source, name)

	def _visible(self):
		if self._dir is not None and _direction(self._text()) != self._dir:
			return False
		if self._key is None:
			return True
		value = configfile.getResolvedKey(self._key, silent=True)
		if value is None:
			value = "True"
		return (value == self._value) ^ self._invert

	def _text(self):
		try:
			return self.source.text or ""
		except Exception:
			return ""

	def changed(self, what):
		visible = self._visible()
		for element in self.downstream_elements:
			element.visible = visible
		Converter.changed(self, what)

	def connectDownstream(self, downstream):
		Converter.connectDownstream(self, downstream)
		downstream.visible = self._visible()


_RTL_RANGES = ((0x0590, 0x08FF), (0xFB1D, 0xFDFF), (0xFE70, 0xFEFF), (0x10800, 0x10FFF), (0x1E800, 0x1EFFF))


def _direction(text):
	for ch in text:
		cp = ord(ch)
		if any(a <= cp <= b for a, b in _RTL_RANGES):
			if ch.isalpha() or 0x0600 <= cp <= 0x06FF:
				return "rtl"
		elif ch.isalpha():
			return "ltr"
	return "ltr"
