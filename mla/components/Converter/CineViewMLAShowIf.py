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
		# ",poster0" / ",poster1": the posters-ON variant also needs a REAL poster on the screen's poster widget with
		# this toggle key and nexts 0/1 (CineViewMLAPosterState); otherwise the posters-OFF variant is shown.  No
		# placeholder: an event without a poster gets the No Poster layout (user decision 2026-10-05 22:03).
		self._pflag = None
		for p in parts[2:]:
			if p in ("poster0", "poster1"):
				self._pflag = int(p[-1])
		if self._pflag is not None:
			try:
				from Components.CineViewMLAPosterState import listen
				listen(self)
			except Exception as err:
				print("[CineViewMLAShowIf] poster state unavailable: %s" % err)
				self._pflag = None
		if self._key is None and not self._always:
			print("[CineViewMLAShowIf] invalid arguments '%s' (shown)" % args)
		self._debug = self._bool and os.path.exists(DEBUG_FLAG)

	def __getattr__(self, name):
		# Transparent like ConditionalShowHide; never recurse while the object is being built.
		if name.startswith("__") or name in ("source", "_key", "_value", "_invert", "_dir", "_always", "_bool", "_literal", "_up_visible", "_debug", "_pflag", "_mla_t"):
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
		match = value == self._value
		if match and self._pflag is not None and self._value == "True":
			try:
				from Components.CineViewMLAPosterState import get
				match = get(self._key, self._pflag)
			except Exception:
				pass
		return match ^ self._invert

	def poster_state_changed(self, key, nexts):
		"""CineViewMLAPosterState notification: re-evaluate the variant when its poster widget changed state.
		The poster widget may publish while its screen is still being built (renderer instances of later widgets do
		not exist yet, and a fresh screen only sends CHANGED_DEFAULT, which Picon ignores: device t68 / t82, Classic
		EventView strip without a picon).  So the refresh runs now AND once more when the event loop is back (the
		screen is complete then)."""
		if key == self._key and nexts == self._pflag and getattr(self, "source", None) is not None:
			self._refresh()
			self._schedule_refresh()

	def _refresh(self):
		try:
			if getattr(self, "source", None) is not None:
				self.changed((self.CHANGED_ALL,))
		except Exception as err:
			print("[CineViewMLAShowIf] poster state refresh: %s" % err)

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
			_set_visible(element, v)

	def changed(self, what):
		visible = self._visible() and getattr(self, "_up_visible", True)
		for element in self.downstream_elements:
			_set_visible(element, visible)
		if getattr(self, "_debug", False):
			self._log("changed %s" % (what,), visible)
		Converter.changed(self, what)
		if not visible:
			# native Picon (Renderer/Picon.py 57b7a51) calls instance.show() whenever it loads a file -- for a hidden
			# variant that is the default picon (its text is "").  Keep hidden variants hidden (device t57b / t82).
			for element in self.downstream_elements:
				try:
					_set_visible(element, False)
				except Exception:
					pass

	def connectDownstream(self, downstream):
		Converter.connectDownstream(self, downstream)
		downstream.visible = self._visible() and getattr(self, "_up_visible", True)
		if getattr(self, "_debug", False):
			self._log("connect", downstream.visible)
		if self._pflag is not None:
			# poster-following variants: one full update once the screen is built, so a Picon variant loads its picture
			# even when the poster state does not change (a fresh screen only sends CHANGED_DEFAULT)
			self._schedule_refresh()

	def _schedule_refresh(self):
		try:
			from enigma import eTimer
			t = getattr(self, "_mla_t", None)
			if t is None:
				t = self._mla_t = eTimer()
				t.callback.append(self._refresh)
			t.start(0, True)
		except Exception as err:
			print("[CineViewMLAShowIf] poster state timer: %s" % err)

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


def _set_visible(element, visible):
	"""GUIComponent.visible only acts when the flag changes.  A renderer that shows its widget instance itself
	(OpenBH Renderer/Picon.applySkin -> changed(CHANGED_DEFAULT) -> instance.show(), c06a87ef4c09 / 52dedddc314a)
	leaves the flag False while the widget is on screen, so a later 'visible = False' does nothing (OpenBH device
	2026-10-07: poster-on and poster-off channel logos both shown).  A hidden element's instance is therefore
	hidden explicitly as well; on OpenATV the instance is already hidden there (no visible change)."""
	element.visible = visible
	if not visible:
		inst = getattr(element, "instance", None)
		if inst is not None:
			inst.hide()


def _direction(text):
	for ch in text:
		cp = ord(ch)
		if any(a <= cp <= b for a, b in _RTL_RANGES):
			if ch.isalpha() or 0x0600 <= cp <= 0x06FF:
				return "rtl"
		elif ch.isalpha():
			return "ltr"
	return "ltr"
