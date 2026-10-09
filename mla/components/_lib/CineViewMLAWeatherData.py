# -*- coding: utf-8 -*-
# CineView MLA - weather data for the CineView designs.  Design & Development by habeb-s (c) 2026.
# Own code: no OAWeather or Weatherinfo code is copied or imported.
#
# The CineView designs show three weather values: city, current temperature, current weather icon (Converter
# CineViewMLAWeather + Renderer CineViewMLAWeatherPixmap; the composer writes them in place of the OAWeather widgets
# of the layout packs, so a design never needs OAWeather's components to load).
#
# Location - only one the user has set, never a guess (a time zone does not say where the receiver is):
#   1. the location saved in OAWeather's settings (config.plugins.OAWeather.weatherlocation), when OAWeather's weather
#      is not switched off there;
#   2. otherwise the city chosen in CineView Designs > Weather city (runtime.json "weather_city");
#   3. neither: no weather is shown and nothing is looked up until a city is chosen.
# Values:
#   - OAWeather's saved location in use, and OAWeather running in this Enigma2 session (its plugin module already
#     loaded by Enigma2, its session source present) with weather data: OAWeather's own values as they are - city,
#     temperature with its unit, icon of its configured icon set.  CineView never imports, starts, configures or
#     changes OAWeather.
#   - otherwise CineView's own lookup at Open-Meteo for that location (https://open-meteo.com - free, no key; weather
#     data CC BY 4.0, "Weather data by Open-Meteo.com"), every REFRESH seconds; unit = OAWeather's unit setting when
#     there is one, else Celsius.  While OAWeather runs but has no data yet (its first lookup after a start),
#     CineView waits GRACE seconds before its own lookup.
# "weather_source" in runtime.json: "off" = no weather at all; "builtin" = never OAWeather's values (support / tests).
# Network work runs in a background thread; the GUI only reads the last result (also kept in
# /etc/enigma2/cineview_mla/weather.json, so it shows at once after a restart).  Nothing here raises into Enigma2.
# /tmp/cineview_mla_weather.json (RAM, rewritten only when something changes) tells which location and source are in
# use and what the weather widgets show - for support and tests.
import ast
import json
import os
import sys
import threading
import time

STATE = "/etc/enigma2/cineview_mla"
CACHE = os.path.join(STATE, "weather.json")
RUNTIME = os.path.join(STATE, "runtime.json")
STATUS = "/tmp/cineview_mla_weather.json"
SETTINGS = "/etc/enigma2/settings"
ICONS = "/usr/share/enigma2/CineView_FHD_MLA/mla_assets/weather"
REFRESH = 3600   # seconds between two lookups
RETRY = 600      # after a failed lookup
GRACE = 120      # OAWeather runs without data: CineView's own lookup only after this many seconds
RECHECK = 30     # settings, runtime.json and icon files are looked at again after this many seconds
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL = "https://api.open-meteo.com/v1/forecast"
UA = {"User-Agent": "CineView-MLA (Enigma2 skin)"}
OAW_MODULE = "Plugins.Extensions.OAWeather.plugin"

# WMO weather interpretation codes (Open-Meteo "weather_code") -> CineView icon names (mla_assets/weather/<name>.png)
WMO = {0: "clear", 1: "partly", 2: "partly", 3: "cloudy", 45: "fog", 48: "fog"}
WMO.update((c, "drizzle") for c in (51, 53, 55, 56, 57))
WMO.update((c, "rain") for c in (61, 63, 65, 66, 67, 80, 81, 82))
WMO.update((c, "snow") for c in (71, 73, 75, 77, 85, 86))
WMO.update((c, "thunder") for c in (95, 96, 99))


def _log(msg):
	print("[CineViewMLA] weather: %s" % msg)


def _http_json(url, params):
	try:
		from requests import get
	except ImportError:
		get = None
	if get is not None:
		r = get(url, params=params, timeout=15, headers=UA)
		r.raise_for_status()
		return r.json()
	from urllib.parse import urlencode
	from urllib.request import Request, urlopen
	with urlopen(Request(url + "?" + urlencode(params), headers=UA), timeout=15) as f:
		return json.loads(f.read().decode("utf-8"))


def _mtime(path):
	try:
		st = os.stat(path)
		return (st.st_mtime, st.st_size)
	except OSError:
		return None


def search(text, count=10):
	"""Cities for a name typed in CineView Designs (Open-Meteo geocoding; Arabic or Latin letters, at least 3).
	Returns [{"name", "label", "lat", "lon"}]; network errors are raised to the caller (run it in a thread)."""
	text = (text or "").strip()
	lang = "ar" if any("؀" <= ch <= "ۿ" for ch in text) else "en"
	res = _http_json(GEO_URL, {"name": text, "count": count, "language": lang, "format": "json"}).get("results") or []
	out = []
	for r in res:
		try:
			parts = []
			for p in (r.get("name"), r.get("admin1"), r.get("country")):
				if p and p not in parts:
					parts.append(p)
			out.append({"name": str(r["name"]), "label": ", ".join(parts), "lat": round(float(r["latitude"]), 5), "lon": round(float(r["longitude"]), 5)})
		except Exception:
			pass
	return out


class CineViewWeather:
	def __init__(self):
		self.lock = threading.Lock()
		self.data = {}            # CineView's own: {"city", "temp", "unit", "icon", "code", "time", "key", ...}
		self.thread = None
		self.next_lookup = 0
		self.loaded = False
		self.oaw_waiting = None   # when OAWeather was first seen running without data
		self.conf = None
		self.files = {}           # icon file -> (exists, checked at)
		self.kind = None          # last source used (logged when it changes)
		self.shown = {}           # converter arguments -> (text, picture file) the widgets show

	# ------------------------------------------------------------ configuration (read at most every RECHECK s)
	def _config(self):
		now = time.time()
		c = self.conf
		if c is not None and 0 <= now - c["time"] < RECHECK:
			return c
		stamp = (_mtime(RUNTIME), _mtime(SETTINGS))
		if c is not None and c["stamp"] == stamp:
			c["time"] = now  # nothing changed: the files are not read again
			return c
		c = {"time": now, "stamp": stamp, "mode": "auto", "enabled": True, "oaw_loc": None, "city": None, "unit": "celsius"}
		try:
			with open(RUNTIME, encoding="utf-8") as f:
				rt = json.load(f)
			m = rt.get("weather_source", "auto")
			if m in ("auto", "builtin", "off"):
				c["mode"] = m
			wc = rt.get("weather_city")
			if isinstance(wc, dict) and wc.get("name"):
				c["city"] = (str(wc["name"]), float(wc["lat"]), float(wc["lon"]))
				c["city_label"] = str(wc.get("label") or wc["name"])
		except Exception:
			pass
		try:
			with open(SETTINGS, encoding="utf-8", errors="replace") as f:
				for line in f:
					if not line.startswith("config.plugins.OAWeather."):
						continue
					key, _, val = line.rstrip("\r\n").partition("=")
					val = val.strip()
					try:
						if key == "config.plugins.OAWeather.weatherlocation":
							v = ast.literal_eval(val)  # OAWeather stores (name, longitude, latitude)
							c["oaw_loc"] = (str(v[0]).split(",")[0].strip(), float(v[2]), float(v[1]))
							c["oaw_label"] = str(v[0])
						elif key == "config.plugins.OAWeather.tempUnit":
							c["unit"] = "fahrenheit" if val == "Fahrenheit" else "celsius"
						elif key == "config.plugins.OAWeather.enabled":
							c["enabled"] = val.lower() not in ("false", "0", "no")
					except Exception:
						pass
		except Exception:
			pass
		# OAWeather's saved location first (unless its weather is switched off), then the city chosen in CineView
		if c["oaw_loc"] and c["enabled"]:
			c["loc"], c["loc_from"] = c["oaw_loc"], "oaweather"
		elif c["city"]:
			c["loc"], c["loc_from"] = c["city"], "cineview"
		else:
			c["loc"], c["loc_from"] = None, None
		c["key"] = "%s|%.4f,%.4f" % (c["unit"], c["loc"][1], c["loc"][2]) if c["loc"] else c["unit"] + "|none"
		self.conf = c
		return c

	def reload(self):
		"""Read the settings again now (CineView Designs calls this after the weather city has changed)."""
		self.conf = None
		self._source()

	def location(self):
		"""For CineView Designs: (where the location comes from: "oaweather" | "cineview" | None, its text)."""
		c = self._config()
		if c["loc_from"] == "oaweather":
			return "oaweather", c.get("oaw_label") or c["oaw_loc"][0]
		if c["loc_from"] == "cineview":
			return "cineview", c.get("city_label") or c["city"][0]
		return None, ""

	# ------------------------------------------------------------ OAWeather (used as it is, while it runs)
	def _oaweather(self):
		"""OAWeather's session source while OAWeather runs in this session and has data, else None."""
		mod = sys.modules.get(OAW_MODULE)  # only a module Enigma2 itself has loaded - never imported from here
		if mod is None:
			return None
		try:
			session = getattr(getattr(mod, "weatherhandler", None), "session", None)
			src = session.screen["OAWeather"] if session is not None else None
		except Exception:
			src = None
		if src is None:
			return None
		if getattr(src, "data", None):
			self.oaw_waiting = None
			return src
		if self.oaw_waiting is None:
			self.oaw_waiting = time.time()
		return None

	def _source(self):
		"""("oaweather", source) | ("cineview", None) | ("none", None) no location set | ("off", None)"""
		c = self._config()
		src = None
		if c["mode"] == "off":
			kind = "off"
		elif not c["loc"]:
			kind = "none"
		else:
			src = self._oaweather() if c["mode"] == "auto" and c["loc_from"] == "oaweather" else None
			kind = "oaweather" if src is not None else "cineview"
		if kind != self.kind:
			_log("source %s -> %s (location: %s)" % (self.kind, kind, c["loc_from"]))
			self.kind = kind
			self._status()
		if kind == "cineview":
			self.start(c)
		return kind, src

	def source_name(self):
		return self._source()[0]

	def note(self, args, values):
		"""Called by the converter (with its arguments) when what its widgets show has changed."""
		if self.shown.get(args) != values:
			self.shown[args] = values
			self._status()

	def _status(self):
		try:
			c = self.conf or {}
			d = self.data
			st = {"source": self.kind, "location": {"from": c.get("loc_from"), "name": c["loc"][0], "lat": c["loc"][1], "lon": c["loc"][2]} if c.get("loc") else None,
				"time": time.time(), "shown": {m: {"text": v[0], "file": v[1]} for m, v in sorted(self.shown.items())},
				"cineview_data": {k: d.get(k) for k in ("city", "temp", "unit", "icon", "time", "source")} if d else None}
			tmp = STATUS + ".tmp"
			with open(tmp, "w", encoding="utf-8") as f:
				json.dump(st, f, ensure_ascii=False)
			os.replace(tmp, STATUS)
		except Exception:
			pass

	# ------------------------------------------------------------ values for the converter
	def city(self):
		kind, src = self._source()
		if kind == "oaweather":
			try:
				return str(src.getCity())
			except Exception:
				return ""
		return str(self.data.get("city", "")) if kind == "cineview" else ""  # self.data is replaced, never changed in place

	def temperature(self):
		kind, src = self._source()
		if kind == "oaweather":
			try:
				return str(src.getTemperature())
			except Exception:
				return ""
		d = self.data if kind == "cineview" else {}
		try:
			return "" if d.get("temp") is None else "%d %s" % (round(float(d["temp"])), d.get("unit", "°C"))
		except Exception:
			return ""

	def code(self):
		kind, src = self._source()
		if kind == "oaweather":
			try:
				return str(src.getYahooCode(0))
			except Exception:
				return ""
		return str(self.data.get("icon", "")) if kind == "cineview" else ""

	def icon(self, path=None, ext="png"):
		"""Picture file of the current weather, "" when there is none."""
		kind, src = self._source()
		if kind == "oaweather":
			try:
				code = src.getYahooCode(0)
				base = path or getattr(src, "iconpath", None)
			except Exception:
				return ""
			return self._file(base, "%s.%s" % (code, ext)) if code and base else ""
		name = self.data.get("icon") if kind == "cineview" else None
		return self._file(ICONS, "%s.png" % name) if name else ""  # CineView's own icons (named by weather type)

	def _file(self, base, name):
		f = os.path.join(base, name)
		now = time.time()
		hit = self.files.get(f)
		if hit is None or not (0 <= now - hit[1] < RECHECK):
			if len(self.files) > 64:
				self.files.clear()
			hit = (os.path.isfile(f), now)
			self.files[f] = hit
		return f if hit[0] else ""

	# ------------------------------------------------------------ CineView's own lookup
	def start(self, c=None):
		"""Load the cache once; start a lookup in the background when one is due (never blocks the GUI)."""
		c = c or self._config()
		if not c["loc"]:
			return
		now = time.time()
		if not self.loaded:
			self.loaded = True
			try:
				with open(CACHE, encoding="utf-8") as f:
					cached = json.load(f)
				w = cached.get("weather") if isinstance(cached, dict) else None
				if isinstance(w, dict) and w.get("key") == c["key"]:
					with self.lock:
						self.data = w
					age = now - float(w.get("time", 0))
					self.next_lookup = now + (REFRESH - age) if 0 <= age < REFRESH else 0
			except Exception:
				pass
		if self.thread is not None:
			return
		if self.data and self.data.get("key") != c["key"]:
			with self.lock:  # location or unit changed in the settings: the old values are not shown any more
				self.data = {}
			self.next_lookup = 0
		if now < self.next_lookup:
			return
		if self.oaw_waiting is not None and 0 <= now - self.oaw_waiting < GRACE and c["loc_from"] == "oaweather":
			return  # OAWeather is running and fetching its first data
		self.next_lookup = now + RETRY  # until this lookup has finished
		t = threading.Thread(target=self._lookup, args=(dict(c),), name="CineViewMLAWeather")
		t.daemon = True
		self.thread = t
		try:
			t.start()
		except Exception as e:
			self.thread = None
			_log("lookup not started: %s" % e)

	def _lookup(self, c):
		try:
			name, lat, lon = c["loc"]
			cur = _http_json(WX_URL, {"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code,is_day",
				"temperature_unit": c["unit"], "timezone": "auto"}).get("current") or {}
			code = int(cur.get("weather_code", -1))
			icon = WMO.get(code, "cloudy")
			if icon in ("clear", "partly"):
				icon += "_day" if int(cur.get("is_day", 1)) else "_night"
			data = {"city": name, "temp": float(cur["temperature_2m"]), "unit": "°F" if c["unit"] == "fahrenheit" else "°C",
				"icon": icon, "code": code, "time": time.time(), "key": c["key"], "lat": lat, "lon": lon,
				"location_from": c["loc_from"], "observed": cur.get("time"), "source": "Open-Meteo.com (CC BY 4.0)"}
			with self.lock:
				self.data = data
			os.makedirs(STATE, exist_ok=True)
			tmp = CACHE + ".tmp"
			with open(tmp, "w", encoding="utf-8") as f:
				json.dump({"weather": data}, f, ensure_ascii=False)
			os.replace(tmp, CACHE)
			self.next_lookup = time.time() + REFRESH
			_log("%s (%s) %s %s (%s)" % (name, c["loc_from"], data["temp"], data["unit"], icon))
		except Exception as e:  # network down, service changed, ... -> try again later, never raise
			_log("lookup failed: %s" % e)
			self.next_lookup = time.time() + RETRY
		finally:
			self.thread = None


weather = CineViewWeather()
