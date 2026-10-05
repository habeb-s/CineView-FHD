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
# args:   <config key>|always,<value>[,Invert][,dir=rtl|dir=ltr][,bool][,text=<literal>]
#         The key is resolved live (configfile.getResolvedKey); a missing key resolves to the
#         converter's default "True", so posters-on layouts are shown when nothing is configured.
#         dir=: additionally require the direction of the source text (first strong character:
#         Arabic/Hebrew/Syriac/Thaana/N'Ko or their presentation forms = rtl, any other letter = ltr).
#         Used to give right-to-left texts a right-aligned variant: on OpenATV 57b7a51 eLabel treats
#         "bidi" alignment as left and wraps RTL paragraphs with the short line on top.
import os

from Components.config import configfile
from Components.Converter.Converter import Converter

# Diagnostics (off by default): with this file present, every widget using ",bool" logs each update with the raw
# video info of the playing service (device investigation of the Modern HD / 16:9 chips, 2026-10-05).
DEBUG_FLAG = "/etc/enigma2/cineview_mla/debug_showif"


class CineViewMLAShowIf(Converter):
	def __init__(self, args):
		Converter.__init__(self, args)
		parts = [x.strip() for x in (args or "").split(",")]
		self._key = parts[0] if parts and parts[0].startswith("config.") else None
		self._always = bool(parts) and parts[0] == "always"  # "always,True,dir=rtl": direction-only switch
		self._value = parts[1] if len(parts) > 1 else "True"
		self._invert = "Invert" in parts[2:]
		self._dir = None
		self._bool = "bool" in parts[2:]  # AND the source's boolean (e.g. ServiceInfo IsHD) -> icons that move
		self._literal = None  # text=<literal>: a static caption that follows the switch (e.g. "NEXT")
		for p in parts[2:]:
			if p in ("dir=rtl", "dir=ltr"):
				self._dir = p[4:]
			elif p.startswith("text="):
				self._literal = p[5:]
		if self._key is None and not self._always:
			print("[CineViewMLAShowIf] invalid arguments '%s' (shown)" % args)
		self._debug = self._bool and os.path.exists(DEBUG_FLAG)

	def __getattr__(self, name):
		# Transparent like ConditionalShowHide; never recurse while the object is being built.
		if name.startswith("__") or name in ("source", "_key", "_value", "_invert", "_dir", "_always", "_bool", "_literal", "_up_visible", "_debug"):
			raise AttributeError(name)
		return getattr(self.source, name)

	def _visible(self):
		if self._dir is not None and _direction(self._text()) != self._dir:
			return False
		if self._bool:
			try:
				if not self.source.boolean:
					return False
			except Exception:
				return False
		if self._key is None:
			return True
		value = configfile.getResolvedKey(self._key, silent=True)
		if value is None:
			value = "True"
		return (value == self._value) ^ self._invert

	@property
	def text(self):
		# Hidden variants get NO text: a hidden RunningText then has nothing to animate.  Without this,
		# the 3 hidden variants of every SecondInfoBar/EventView text kept swimming (moving their labels)
		# behind the visible one; device-observed as an intermittent blank band above the visible
		# description when the swim started (EventView fast-zap test 2026-10-03 21:4x).
		if not self._visible():
			return ""
		return self._literal if self._literal is not None else self._text()

	def _text(self):
		try:
			return self.source.text or ""
		except Exception:
			return ""

	# Upstream converters may drive the visibility of their first downstream element themselves
	# (57b7a51 EventInfo Progress: downstream_elements[0].visible = bool(event)).  Behind ShowIf that
	# element is this converter: keep the upstream wish and AND it with our own condition.
	# (device crash 2026-10-03 21:51: AttributeError 'EventTime' object has no attribute 'visible')
	@property
	def visible(self):
		return getattr(self, "_up_visible", True)

	@visible.setter
	def visible(self, value):
		self._up_visible = bool(value)
		v = self._up_visible and self._visible()
		for element in self.downstream_elements:
			element.visible = v

	def changed(self, what):
		visible = self._visible() and getattr(self, "_up_visible", True)
		for element in self.downstream_elements:
			element.visible = visible
		if getattr(self, "_debug", False):
			self._log("changed %s" % (what,), visible)
		Converter.changed(self, what)

	def connectDownstream(self, downstream):
		Converter.connectDownstream(self, downstream)
		downstream.visible = self._visible() and getattr(self, "_up_visible", True)
		if getattr(self, "_debug", False):
			self._log("connect", downstream.visible)

	def _log(self, event, visible):
		try:
			from enigma import iServiceInformation
			up = self.source
			arg = getattr(up, "type", None) or getattr(up, "token", None)
			svc = getattr(getattr(up, "source", None), "service", None)
			info = svc and svc.info()
			vi = info and info.getInfoString(iServiceInformation.sVideoInfo)
			try:
				b = up.boolean
			except Exception as err:
				b = "err:%s" % err
			print("[CineViewMLAShowIf] dbg %x %s token=%s literal=%s boolean=%s visible=%s videoinfo=%s" % (id(self) & 0xffffff, event, arg, self._literal, b, visible, vi))
		except Exception as err:
			print("[CineViewMLAShowIf] dbg error %s" % err)


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
