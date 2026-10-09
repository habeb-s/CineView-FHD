# -*- coding: utf-8 -*-
# CineView MLA - weather values for the CineView designs.  Design & Development by habeb-s (c) 2026.  Own code.
#
# The CineView MLA composer writes these widgets in place of the OAWeather widgets of the layout packs (same
# position, size, font, colours and options; only source / converter / renderer change), so a design never needs
# OAWeather's components to load - on an image without OAWeather, with a broken OAWeather or with a working one:
#   <widget source="global.CurrentTime" render="RunningText" ...><convert type="CineViewMLAWeather">city</convert></widget>
#   <widget source="global.CurrentTime" render="Label" ...><convert type="CineViewMLAWeather">temperature_current</convert></widget>
#   <widget source="global.CurrentTime" render="CineViewMLAWeatherPixmap" ...><convert type="CineViewMLAWeather">weathericon,current</convert></widget>
# Arguments as for the OAWeather converter: "<mode>[,<day>[,<icon folder>[,<extension>]]]"; modes city,
# temperature_current, weathericon / yahoocode; day: current.  Anything else shows nothing (never an error).
# The values come from Components.CineViewMLAWeatherData: OAWeather's own data while OAWeather runs, otherwise
# CineView's own lookup (Open-Meteo).
# global.CurrentTime (Enigma2's clock source, on every image) only paces the refresh: on each tick the values are
# read again and passed on ONLY when they have changed (a RunningText restarts its scrolling on every change it gets).
from Components.CineViewMLAWeatherData import weather
from Components.Converter.Converter import Converter
from Components.Element import cached

DAYS = {"current": 0}
MODES = ("city", "temperature_current", "weathericon", "yahoocode")


class CineViewMLAWeather(Converter):
	def __init__(self, arguments):
		Converter.__init__(self, arguments)
		self.args = (arguments or "").strip()
		parts = [p.strip() for p in self.args.split(",")]
		self.mode = parts[0]
		self.day = DAYS.get(parts[1], -1) if len(parts) > 1 and parts[1] else 0
		self.path = parts[2] if len(parts) > 2 and parts[2] else None
		self.ext = parts[3] if len(parts) > 3 and parts[3] else "png"
		self.last = None
		if self.mode not in MODES or self.day != 0:
			print("[CineViewMLAWeather] not supported: '%s' (shows nothing)" % arguments)

	def values(self):
		"""(text, picture file) of this widget now."""
		if self.mode not in MODES or self.day != 0:
			return "", ""
		try:
			if self.mode == "city":
				return weather.city(), ""
			if self.mode == "temperature_current":
				return weather.temperature(), ""
			return weather.code(), weather.icon(self.path, self.ext)
		except Exception as e:  # never an error in the GUI
			print("[CineViewMLAWeather] %s: %s" % (self.mode, e))
			return "", ""

	@cached
	def getText(self):
		return self.values()[0]

	text = property(getText)

	@cached
	def getIconFilename(self):
		return self.values()[1]

	iconfilename = property(getIconFilename)

	@cached
	def getBoolean(self):
		return bool(self.values()[0])

	boolean = property(getBoolean)

	def changed(self, what, *args, **kwargs):
		if what and what[0] == self.CHANGED_POLL:
			now = self.values()
			if now == self.last:
				return  # clock tick, nothing new to show
			self.last = now
		elif what and what[0] != self.CHANGED_CLEAR:
			self.last = self.values()
		else:
			self.last = None
		if self.last is not None:
			weather.note(self.args, self.last)
		Converter.changed(self, what, *args, **kwargs)
