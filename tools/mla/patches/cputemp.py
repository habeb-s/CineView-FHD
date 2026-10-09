# -*- coding: utf-8 -*-
# CineView MLA - receiver temperature (InfoBar / Second InfoBar / Event View "CPU: xx°C" label).
#
# Replaces the golden CineViewCPUTemp, which read only three fixed paths (thermal_zone0, /proc/stb/sensors/temp0,
# /proc/stb/fp/temp_sensor).  Receivers whose driver exposes the temperature elsewhere always showed "CPU: --°C" -
# e.g. Octagon SF8008 (HiSilicon Hi3798MV200, OpenATV 7.6): none of the three exists; the driver reports
# "Tsensor: temperature = 48 degree" in /proc/hisi/msp/pm_cpu (device evidence 2026-10-09).
#
# Every source is optional and probed by existence - nothing is assumed about a model or brand:
#   1. the three golden paths, in their original order (receivers that worked keep exactly the same reading);
#   2. any other kernel thermal zone (cpu/soc zones first);
#   3. /proc/stb/sensors/temp/value, /proc/stb/fp/temp_sensor_avs (other Enigma2 driver variants);
#   4. HiSilicon driver: /proc/hisi/msp/pm_cpu, /proc/hisi/msp/pm_temp ("temperature = <n>").
# A value is accepted only when it is a plausible temperature (0 < t < 150 °C; millidegrees and Fahrenheit
# converted).  No valid reading -> "CPU: N/A" (translated), never 0 or an invented number.  Polled every 5 s while
# the label is on screen; the source that answered is remembered and re-probed when it stops answering.
import glob
import os
import re

from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from Components.Element import cached

try:
	_
except NameError:  # outside Enigma2 (tests): no gettext installed
	def _(text):
		return text

_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_HISI = re.compile(r"temperature\s*[=:]\s*(-?\d+(?:\.\d+)?)", re.I)


def _plausible(value, unit=None):
	if unit and unit.strip().upper().startswith("F"):
		value = (value - 32.0) * 5.0 / 9.0
	if value > 1000:  # millidegrees (kernel thermal zones)
		value /= 1000.0
	return int(round(value)) if 0 < value < 150 else None


def _read_file(path):
	with open(path, "r") as f:
		return f.read()


def _plain(path):
	m = _NUM.search(_read_file(path))
	if not m:
		return None
	unit = None
	upath = os.path.join(os.path.dirname(path), "unit")  # /proc/stb/sensors/temp*/unit = C or F
	if os.path.basename(path) == "value" and os.path.exists(upath):
		try:
			unit = _read_file(upath)
		except Exception:
			unit = None
	return _plausible(float(m.group(0)), unit)


def _hisi(path):
	m = _HISI.search(_read_file(path))
	return _plausible(float(m.group(1))) if m else None


def _thermal_zones():
	zones = sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp"))
	def rank(p):
		try:
			kind = _read_file(os.path.join(os.path.dirname(p), "type")).strip().lower()
		except Exception:
			kind = ""
		return 0 if ("cpu" in kind or "soc" in kind) else 1
	return sorted(zones, key=rank)


class CineViewMLACPUTemp(Poll, Converter):
	GOLDEN = (
		"/sys/class/thermal/thermal_zone0/temp",
		"/proc/stb/sensors/temp0/value",
		"/proc/stb/fp/temp_sensor",
	)
	EXTRA = (
		"/proc/stb/sensors/temp/value",
		"/proc/stb/fp/temp_sensor_avs",
	)
	HISI = (
		"/proc/hisi/msp/pm_cpu",
		"/proc/hisi/msp/pm_temp",
	)

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		self.type = type
		self.poll_interval = 5000
		self.poll_enabled = True
		self._source = None  # (reader, path) that answered last time

	def _candidates(self):
		seen = set()
		for path in self.GOLDEN:
			seen.add(path)
			yield _plain, path
		for path in _thermal_zones():
			if path not in seen:
				seen.add(path)
				yield _plain, path
		for path in self.EXTRA:
			yield _plain, path
		for path in self.HISI:
			yield _hisi, path

	def _try(self, reader, path):
		try:
			if os.path.exists(path):
				return reader(path)
		except Exception:
			pass
		return None

	def _read(self):
		if self._source:
			value = self._try(*self._source)
			if value is not None:
				return value
			self._source = None
		for reader, path in self._candidates():
			value = self._try(reader, path)
			if value is not None:
				self._source = (reader, path)
				return value
		return None

	@cached
	def getText(self):
		value = self._read()
		if value is None:
			return "CPU: %s" % _("N/A")
		return "CPU: %d°C" % value

	text = property(getText)
