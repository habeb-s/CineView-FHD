#!/usr/bin/env python3
"""Off-receiver tests of CineView's weather components (SIMULATION: Enigma2's Element/Converter base classes and the
network are replaced by stand-ins here; the real behaviour is checked on receivers).
usage: test_weather_components.py
Covers: OAWeather used as it is while it runs with data; CineView's own lookup otherwise (location from OAWeather's
saved setting or the time zone, unit, cache, refresh, failure back-off, grace period while OAWeather fetches);
weather_source off/builtin; change filtering of the 1-second clock ticks; status file; converter arguments."""
import importlib.util, json, os, shutil, sys, tempfile, time, types

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
fails = []


def check(name, cond, detail=""):
	print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  [%s]" % (detail,)))
	if not cond:
		fails.append(name)


# ---- stand-ins for Enigma2's Components.Element / Converter (same contract: changed() pushes downstream)
class Element:
	CHANGED_DEFAULT, CHANGED_ALL, CHANGED_CLEAR, CHANGED_SPECIFIC, CHANGED_POLL = 0, 1, 2, 3, 4

	def __init__(self):
		self.downstream = []
		self.cache = None

	def changed(self, *args, **kwargs):
		self.cache = {}
		for d in self.downstream:
			d.changed(*args, **kwargs)
		self.cache = None


def cached(f):
	name = f.__name__

	def wrapper(self):
		if self.cache is None:
			return f(self)
		if name not in self.cache:
			self.cache[name] = f(self)
		return self.cache[name]
	return wrapper


class Converter(Element):
	def __init__(self, arguments):
		Element.__init__(self)
		self.converter_arguments = arguments


class Renderer:  # records what a Label / RunningText would get
	def __init__(self, src):
		self.src, self.texts, self.calls = src, [], 0
		src.downstream.append(self)

	def changed(self, what):
		self.calls += 1
		self.texts.append(self.src.text)


comps = types.ModuleType("Components")
comps.__path__ = []
el = types.ModuleType("Components.Element"); el.cached = cached; el.Element = Element
cv = types.ModuleType("Components.Converter"); cv.__path__ = []
cvc = types.ModuleType("Components.Converter.Converter"); cvc.Converter = Converter
sys.modules.update({"Components": comps, "Components.Element": el, "Components.Converter": cv, "Components.Converter.Converter": cvc})


def load(name, path):
	spec = importlib.util.spec_from_file_location(name, path)
	m = importlib.util.module_from_spec(spec)
	sys.modules[name] = m
	spec.loader.exec_module(m)
	return m


T = tempfile.mkdtemp(prefix="wxc_")
data = load("Components.CineViewMLAWeatherData", os.path.join(REPO, "mla/components/_lib/CineViewMLAWeatherData.py"))
conv = load("Components.Converter.CineViewMLAWeather", os.path.join(REPO, "mla/components/Converter/CineViewMLAWeather.py"))
os.makedirs(T + "/state"); os.makedirs(T + "/icons"); os.makedirs(T + "/oaw_icons")
for n in ("clear_day", "partly_night", "rain", "cloudy"):
	open(T + "/icons/%s.png" % n, "w").close()
open(T + "/oaw_icons/32.png", "w").close()
data.STATE, data.CACHE, data.RUNTIME = T + "/state", T + "/state/weather.json", T + "/state/runtime.json"
data.SETTINGS, data.ICONS, data.STATUS = T + "/settings", T + "/icons", T + "/status.json"
calls = []
REPLY = {"geo": {"results": [{"name": "Riyadh", "latitude": 24.68773, "longitude": 46.72185}]},
	"wx": {"current": {"temperature_2m": 31.6, "weather_code": 2, "is_day": 0}}, "fail": False}


def fake_http(url, params):
	calls.append((url, dict(params)))
	time.sleep(REPLY.get("delay", 0))
	if REPLY["fail"]:
		raise OSError("network down")
	return REPLY["geo"] if "geocoding" in url else REPLY["wx"]


data._http_json = fake_http
OAW_LOC = "config.plugins.OAWeather.weatherlocation=('Sayhāt, Eastern Province, SAUDI ARABIA', 50.04849, 26.48345)\n"
CITY = {"weather_city": {"name": "Jeddah", "label": "Jeddah, Mecca Region, Saudi Arabia", "lat": 21.49012, "lon": 39.18624}}


def fresh(settings="", runtime=None):
	open(data.SETTINGS, "w", encoding="utf-8").write(settings)
	if runtime is None:
		if os.path.exists(data.RUNTIME):
			os.remove(data.RUNTIME)
	else:
		json.dump(runtime, open(data.RUNTIME, "w"))
	for f in (data.CACHE, data.STATUS):
		if os.path.exists(f):
			os.remove(f)
	sys.modules.pop(data.OAW_MODULE, None)
	w = data.CineViewWeather()
	data.weather = w
	conv.weather = w
	calls.clear()
	return w


def settle(w):
	for _ in range(100):
		if w.thread is None:
			return
		time.sleep(0.02)


class FakeSource:
	def __init__(self, data_):
		self.data = data_
		self.iconpath = T + "/oaw_icons"

	def getCity(self):
		return self.data.get("name", "n/a")

	def getTemperature(self):
		return "%s %s" % (self.data.get("current", {}).get("temp", "n/a"), "°C")

	def getYahooCode(self, day):
		return self.data.get("current", {}).get("yahooCode", "")


def oaweather(src):
	mod = types.ModuleType(data.OAW_MODULE)
	session = types.SimpleNamespace(screen={"OAWeather": src})
	mod.weatherhandler = types.SimpleNamespace(session=session)
	sys.modules[data.OAW_MODULE] = mod


HAMBURG = {"name": "Hamburg", "current": {"temp": "12", "yahooCode": "32"}}  # OAWeather's own default location

# ---------------- no location set anywhere: nothing is guessed (no time zone, no geocoding), nothing is shown
w = fresh()
v = (w.city(), w.temperature(), w.icon()); settle(w)
check("no OAWeather location, no city chosen: nothing shown, nothing looked up", v == ("", "", "") and not calls and w.source_name() == "none", (v, calls))
w = fresh(); oaweather(FakeSource(HAMBURG))
v = (w.city(), w.temperature(), w.icon()); settle(w)
check("OAWeather running on its DEFAULT location (none saved): its data is not shown as the user's weather", v == ("", "", "") and not calls and w.source_name() == "none", v)

# ---------------- the city chosen in CineView Designs (runtime.json)
w = fresh(runtime=CITY); REPLY["delay"] = 0.3
check("city chosen in CineView: lookup started in the background, nothing shown yet", w.city() == "" and w.temperature() == "" and w.thread is not None)
settle(w); time.sleep(0.8); settle(w); REPLY["delay"] = 0
check("   forecast asked for its coordinates (Celsius), no geocoding", [c[0] for c in calls] == [data.WX_URL] and calls[0][1]["latitude"] == 21.49012 and calls[0][1]["longitude"] == 39.18624 and calls[0][1]["temperature_unit"] == "celsius", calls)
check("   values: chosen city, rounded temperature with unit, night icon", w.city() == "Jeddah" and w.temperature() == "32 °C" and w.icon() == T + "/icons/partly_night.png", (w.city(), w.temperature(), w.icon()))
c = json.load(open(data.CACHE, encoding="utf-8"))
check("   cache written", c["weather"]["icon"] == "partly_night" and c["weather"]["location_from"] == "cineview")
n = len(calls); w.city(); w.temperature(); settle(w)
check("   no new lookup before the refresh time", len(calls) == n)
w = data.CineViewWeather(); data.weather = conv.weather = w; calls.clear()
check("   after a restart: cached values at once, no network", w.city() == "Jeddah" and w.temperature() == "32 °C" and not calls, calls)
check("   location() for CineView Designs", w.location() == ("cineview", "Jeddah, Mecca Region, Saudi Arabia"), w.location())
w = fresh(runtime=CITY); oaweather(FakeSource(HAMBURG)); w.city(); settle(w)
check("   OAWeather running on its default location: the chosen city is shown, not OAWeather's", w.city() == "Jeddah" and w.source_name() == "cineview", w.city())
# another city chosen: reload() -> old values dropped, new lookup at once
REPLY["wx"] = {"current": {"temperature_2m": 26.4, "weather_code": 3, "is_day": 1}}
json.dump({"weather_city": {"name": "Dammam", "label": "Dammam, Eastern Province, Saudi Arabia", "lat": 26.43442, "lon": 50.10326}}, open(data.RUNTIME, "w"))
calls.clear(); REPLY["delay"] = 0.3; w.reload(); v = w.city(); settle(w); time.sleep(0.5); settle(w); REPLY["delay"] = 0
check("another city chosen (CineView Designs calls reload): old values dropped, new lookup at once", v == "" and calls and calls[0][1]["latitude"] == 26.43442 and w.city() == "Dammam" and w.temperature() == "26 °C", (v, calls, w.city()))
REPLY["wx"] = {"current": {"temperature_2m": -3.2, "weather_code": 71, "is_day": 1}}
w = fresh(runtime=CITY); w.city(); settle(w)
check("snow icon missing in the folder -> no picture (no error); negative temperature", w.icon() == "" and w.temperature() == "-3 °C", (w.icon(), w.temperature()))
os.remove(data.RUNTIME); w.reload(); settle(w)
check("city removed again: nothing shown", w.city() == "" and w.source_name() == "none")

# ---------------- OAWeather's saved location comes first (real line from OpenViX 6.9)
REPLY["wx"] = {"current": {"temperature_2m": 88.2, "weather_code": 61, "is_day": 1}}
w = fresh(OAW_LOC + "config.plugins.OAWeather.tempUnit=Fahrenheit\n", runtime=CITY); w.city(); settle(w)
check("OAWeather location saved (and a CineView city too): OAWeather's location used, lat/lon in the right order, Fahrenheit",
	len(calls) == 1 and calls[0][1]["latitude"] == 26.48345 and calls[0][1]["longitude"] == 50.04849 and calls[0][1]["temperature_unit"] == "fahrenheit", calls)
check("   values: city from OAWeather's setting, °F, rain icon", w.city() == "Sayhāt" and w.temperature() == "88 °F" and w.icon() == T + "/icons/rain.png", (w.city(), w.temperature(), w.icon()))
check("   location() for CineView Designs", w.location() == ("oaweather", "Sayhāt, Eastern Province, SAUDI ARABIA"), w.location())
open(data.SETTINGS, "w").write("config.plugins.OAWeather.weatherlocation=('Jeddah, Makkah, SAUDI ARABIA', 39.19797, 21.54238)\n")
w.conf["time"] = 0; calls.clear(); REPLY["delay"] = 0.3
city_now = w.city(); settle(w); time.sleep(0.5); settle(w); REPLY["delay"] = 0
check("   OAWeather location changed in its settings: old values dropped, new lookup", city_now == "" and calls and calls[0][1]["latitude"] == 21.54238 and w.city() == "Jeddah", (city_now, calls))
w = fresh(OAW_LOC + "config.plugins.OAWeather.enabled=False\n", runtime=CITY); w.city(); settle(w)
check("OAWeather's weather switched off: its location is not used, the CineView city is", w.city() == "Jeddah", w.city())
w = fresh(OAW_LOC + "config.plugins.OAWeather.enabled=False\n"); w.city(); settle(w)
check("   ... and without a CineView city: nothing shown", w.city() == "" and not calls)

# ---------------- failures: back-off, never an exception
REPLY["fail"] = True
w = fresh(runtime=CITY); t0 = time.time()
v = w.city(); settle(w)
check("network down: empty values, no exception, retry later (not at once)", v == "" and w.next_lookup >= t0 + data.RETRY - 1)
n = len(calls); w.city(); w.city(); settle(w)
check("   no hammering while the retry time has not come", len(calls) == n)
REPLY["fail"] = False

# ---------------- OAWeather running with its SAVED location: its own data is used as it is
REPLY["wx"] = {"current": {"temperature_2m": 30.0, "weather_code": 0, "is_day": 1}}
w = fresh(OAW_LOC); oaweather(FakeSource({"name": "Sayhat", "current": {"temp": "29", "yahooCode": "32"}}))
check("OAWeather running with data (location saved): its city / temperature / icon of its icon set", w.city() == "Sayhat" and w.temperature() == "29 °C" and w.icon() == T + "/oaw_icons/32.png" and w.source_name() == "oaweather", (w.city(), w.temperature(), w.icon()))
settle(w)
check("   no own lookup while OAWeather delivers", not calls, calls)
check("   an icon path given in the skin is used for OAWeather's icons", w.icon(T + "/icons", "png") == "")
w = fresh(OAW_LOC); src = FakeSource({}); oaweather(src)
v = w.city(); settle(w)
check("OAWeather running without data yet: CineView waits (grace), shows nothing", v == "" and not calls and w.source_name() == "cineview", calls)
w.oaw_waiting = time.time() - data.GRACE - 1
w.city(); settle(w)
check("   after the grace period: CineView's own lookup at OAWeather's location", [c[0] for c in calls] == [data.WX_URL] and w.city() == "Sayhāt", calls)
src.data = {"name": "Sayhat", "current": {"temp": "29", "yahooCode": "32"}}
check("   OAWeather gets its data: back to OAWeather's values", w.city() == "Sayhat" and w.source_name() == "oaweather")
w = fresh(OAW_LOC); mod = types.ModuleType(data.OAW_MODULE); sys.modules[data.OAW_MODULE] = mod
v = w.city(); settle(w)
check("OAWeather module without a session: CineView's own data, no exception", w.city() == "Sayhāt" and w.source_name() == "cineview")


class Broken(FakeSource):
	def getCity(self):
		raise RuntimeError("broken")


w = fresh(OAW_LOC); oaweather(Broken({"name": "x", "current": {"temp": "1"}}))
check("OAWeather source raising: empty value, no exception", w.city() == "" and w.temperature() == "1 °C")

# ---------------- weather_source switch
w = fresh(OAW_LOC, runtime={"weather_source": "builtin", "poster_cache": "/media/hdd/poster"}); oaweather(FakeSource({"name": "Sayhat", "current": {"temp": "29", "yahooCode": "32"}}))
w.city(); settle(w)
check("weather_source=builtin: CineView's own data even while OAWeather runs", w.city() == "Sayhāt" and w.source_name() == "cineview")
w = fresh(OAW_LOC, runtime={"weather_source": "off"}); w.city(); settle(w)
check("weather_source=off: nothing shown, no lookup", w.city() == "" and w.temperature() == "" and w.icon() == "" and not calls and w.source_name() == "off")

# ---------------- city search (CineView Designs)
REPLY["geo"] = {"results": [{"name": "Jeddah", "admin1": "Mecca Region", "country": "Saudi Arabia", "latitude": 21.49012, "longitude": 39.18624},
	{"name": "Jiddah", "admin1": "Northern Governorate", "country": "Bahrain", "latitude": 26.19372, "longitude": 50.4049}, {"name": "broken"}]}
calls.clear(); res = data.search("Jeddah")
check("search: English letters -> language en; label name, region, country; broken entries skipped",
	calls[0][1]["language"] == "en" and calls[0][1]["name"] == "Jeddah" and [r["label"] for r in res] == ["Jeddah, Mecca Region, Saudi Arabia", "Jiddah, Northern Governorate, Bahrain"] and res[0]["lat"] == 21.49012, (calls, res))
calls.clear(); data.search("جدة")
check("search: Arabic letters -> language ar", calls[0][1]["language"] == "ar", calls)

# ---------------- converter: arguments, values, change filtering of the clock ticks, status file
REPLY["wx"] = {"current": {"temperature_2m": 21.0, "weather_code": 3, "is_day": 1}}
w = fresh(runtime=CITY); w.city(); settle(w)
c_city = conv.CineViewMLAWeather("city"); c_temp = conv.CineViewMLAWeather("temperature_current"); c_icon = conv.CineViewMLAWeather("weathericon,current")
c_bad = conv.CineViewMLAWeather("windspeed"); c_day = conv.CineViewMLAWeather("weathericon,day1")
for x in (c_city, c_temp, c_icon, c_bad, c_day):
	x.changed((Element.CHANGED_DEFAULT,))
check("converter values: city / temperature / icon file; unsupported mode or day -> empty",
	c_city.text == "Jeddah" and c_temp.text == "21 °C" and c_icon.iconfilename == T + "/icons/cloudy.png" and c_bad.text == "" and c_day.iconfilename == "", (c_city.text, c_temp.text, c_icon.iconfilename))
r = Renderer(c_city)
for _ in range(5):
	c_city.changed((Element.CHANGED_POLL,))
check("clock ticks with unchanged values are not passed on (RunningText keeps scrolling)", r.calls == 0, r.calls)
w.data = dict(w.data, city="Jiddah")
c_city.changed((Element.CHANGED_POLL,)); c_city.changed((Element.CHANGED_POLL,))
check("a changed value is passed on once", r.calls == 1 and r.texts == ["Jiddah"], r.texts)
c_city.changed((Element.CHANGED_CLEAR,)); c_city.changed((Element.CHANGED_DEFAULT,))
check("CLEAR / DEFAULT are always passed on", r.calls == 3)
st = json.load(open(data.STATUS, encoding="utf-8"))
check("status file: source, location and what the widgets show", st["source"] == "cineview" and st["location"]["from"] == "cineview" and st["shown"]["city"]["text"] == "Jiddah"
	and st["shown"]["weathericon,current"]["file"].endswith("cloudy.png") and st["shown"]["weathericon,day1"]["file"] == "", st)
check("getBoolean", c_city.boolean is True and c_bad.boolean is False)

shutil.rmtree(T, ignore_errors=True)
print("\nRESULT: %s (%d failures)" % ("PASS" if not fails else "FAIL", len(fails)))
sys.exit(1 if fails else 0)
