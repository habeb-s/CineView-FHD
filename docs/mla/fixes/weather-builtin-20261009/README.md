# CineView MLA 1.0.5 — weather with or without OAWeather

## Report (real user, OpenBH, 2026-10-09)

Applying a design in CineView Designs failed:

```
The design could not be applied:
validation failed:
  EventView: converter OAWeather not installed
  EventView: renderer OAWeatherPixmap not installed
  InfoBar / SecondInfoBar / SecondInfoBarSimple: (same two lines)
```

**Reproduced on a real receiver** — Vu+ Duo 4K SE, OpenBH 6.0 (slot 1, as delivered, no OAWeather), published 1.0.3
installed with opkg: the same eight lines, in the CineView Designs GUI (`shots/rc_bh60_gui4.jpg`) and from the
composer (`logs/bh60_R.log`).

## Cause

- The Classic, Details and Cinema layout packs (and the factory generation) write their weather widgets with the
  components of the OAWeather plugin: `source="session.OAWeather"`, `<convert type="OAWeather">`,
  `render="OAWeatherPixmap"`. They are not part of Enigma2.
- **OpenBH 6.0's own feed does not offer OAWeather at all** (912 packages, no weather package —
  `logs/bh60_P.log`), so on that image the plugin cannot be installed from the feed either.
- 1.0.4 left the weather widgets out on such images: the design applied, but without the weather.

## Fix

### CineView's own weather components (own code and icons, CineView names — nothing of OAWeather is copied, replaced or changed)

| File (installed) | Source |
|---|---|
| `Components/Converter/CineViewMLAWeather.pyc` | `mla/components/Converter/CineViewMLAWeather.py` |
| `Components/Renderer/CineViewMLAWeatherPixmap.pyc` | `mla/components/Renderer/CineViewMLAWeatherPixmap.py` |
| `Components/CineViewMLAWeatherData.pyc` | `mla/components/_lib/CineViewMLAWeatherData.py` |
| `CineView_FHD_MLA/mla_assets/weather/*.png` (10 icons) | `tools/mla/mk_weather_icons.py` → `mla/assets/weather/` |

- The composer builds the weather widgets of every design with these components (same position, size, fonts,
  colours, options; only source / converter / renderer change). `features.json` of each generation records it
  (`{"omitted": [], "builtin": ["weather"]}`). If CineView's components were missing, the packs are used as they are
  when OAWeather is complete (`native`), else the widgets are left out (`omit`) — never a missing component.
- Source of the widget: `global.CurrentTime` (Enigma2's clock, on every image) only paces the refresh. The
  converter passes a value on only when it has changed (a RunningText restarts its scrolling on every change).
- **Location** — only one the user has set, never a guess (a time zone does not say where the receiver is):
  1. the location saved in OAWeather's settings (`config.plugins.OAWeather.weatherlocation`), unless OAWeather's
     weather is switched off there;
  2. otherwise the city chosen in **CineView Designs › Weather city** (OK → name in English or Arabic letters →
     Open-Meteo geocoding → choose from the list; saved in `/etc/enigma2/cineview_mla/runtime.json`, applied at once);
  3. neither: no weather is shown and nothing is looked up.
- **Data**: OAWeather running in the Enigma2 session with its saved location → OAWeather's own values as they are
  (city, temperature, icon of its icon set; CineView only reads its session source, never imports or starts it).
  Otherwise CineView looks the location up at Open-Meteo (free, no key; CC BY 4.0, "Weather data by
  Open-Meteo.com") once an hour in a background thread; cache `/etc/enigma2/cineview_mla/weather.json`.
- `/tmp/cineview_mla_weather.json` (RAM, only rewritten on change) shows the source, the location and what the
  widgets display — support and the device tests read it.
- Postinst runs `composer.py ensure`, so an upgrade with the factory design active is rebuilt at once.

### Smart Installer 1.3.5 (CineView-MLA-Install)

- OAWeather is checked: package state, all six modules, byte code for this image's Python (`.pyc` magic) or a
  compilable `.py`. Missing → installed from the image's own feed when offered; healthy → used as it is; incomplete /
  other Python → left as it is, CineView's own weather is used. Never removed or changed.
- When no weather location is set, the installer says where to choose the city.

## Tests

### Simulation (off the receiver — not a receiver test)

- `tools/mla/test_optional_weather.py`: **201/201** on the 10 published 1.0.4 packages (composer: reproduction with
  the 1.0.3 composer; 6 models × 6 themes with CineView's components with and without OAWeather; upgrade from 1.0.4
  and 1.0.3 generations; fallbacks; trial journal).
- `tools/mla/test_weather_components.py`: **39/39** (data module and converter with Enigma2 stand-ins: location
  order, OAWeather's default location ignored, chosen city, search in English / Arabic, refresh, back-off, grace,
  change filtering, status file).
- `tools/mla/test_engine.py`: **28/28** (fault injection) with the new composer.
- `verify105.py`: all 10 packages = 1.0.4 + exactly the planned changes; every new `.pyc` checked against the
  repository source with the package's Python.

### Device (Vu+ Duo 4K SE, real Enigma2) — see `logs/` and `shots/`

All runs: Vu+ Duo 4K SE (multiboot), real Enigma2, the final 1.0.5 packages (`logs/build105.log`,
`logs/verify105.log`). Each design: applied, Enigma2 restarted, InfoBar / Second InfoBar / Event View opened and
grabbed; PASS = Enigma2 up and stable, no new crash log, every renderer / converter / source of the active
generation installed, no OAWeather widget left, every weather value of the design shown from the expected source
(`/tmp/cineview_mla_weather.json`).

| Image (slot) | OAWeather | Result |
|---|---|---|
| **OpenBH 6.0** (1) | not installed — the feed does not offer it | 1.0.3 reproduces the report (GUI + composer); upgrade 1.0.3 → 1.0.5 with opkg rebuilds the factory with CineView's components; **7/7 designs** PASS; CineView Designs: Apply → GUI restart → "Keep?" → kept; another add-on on the pre-start hook next to it; Smart Installer: "feed does not offer OAWeather - CineView's own weather is used"; uninstaller with the add-on present; fresh install (`logs/bh60_*.log`) |
| OpenBH 6.0 (1) — location | not installed | fresh install of the final build: the installer says to choose the city; **no location → nothing shown, nothing looked up** (no time-zone guess); CineView Designs › Weather city: "Not set" → OK → typed `dammam` → list → *Dammam, Eastern Province, Saudi Arabia* → saved, weather at once (Dammam 33 °C, Open-Meteo 18:00); kept after a GUI restart; another city (`jeddah` → Jeddah 32 °C) → the row and the InfoBar follow at once; "Remove the weather city" → nothing shown; search on the receiver with Arabic letters (جدة → Jeddah) (`logs/bh60city*.log`, `shots/rc_bh60c_*`) |
| **OpenBH 5.6** (5) | 2.2, saved location Sayhāt; **Luka FHD 1.6 and AGlare FHD 8.4 depend on it** | `ROLLBACK=1` → 1.0.4, upgrade → 1.0.5 with the Smart Installer ("OAWeather installed and built for this image's Python - used as it is"); **7/7 designs** PASS with OAWeather's own data (Sayhāt, its icon set; 38 → 36 °C during the test); CineView's own weather (support switch): Sayhāt 35.3 °C (Open-Meteo 17:00); CineView Designs: Weather city row "Sayhāt (OAWeather)", design changed in the GUI → kept; **3489 files of OAWeather, Weatherinfo, Luka, AGlare and the other skins identical before / after** (`logs/bh56*.log`, `logs/fingerprints_summary.txt`) |
| **OpenViX 6.9** (4) | 2.4, saved location Sayhāt; Luka FHD and AGlare FHD depend on it | same steps: **7/7 designs** PASS; CineView's own weather 34.6 °C (17:30); GUI design change kept; **3592 files identical before / after** (`logs/vix69*.log`) |
| **OpenATV 8.0.1** (8) | 2.4, saved location Sayhāt | same steps: **7/7 designs** PASS; CineView's own weather 33.5 °C (18:15); GUI design change kept; **2500 files (OAWeather, Weatherinfo, MetrixHD) identical before / after** (`logs/atv801*.log`) |

The values follow the real weather: Open-Meteo for the same coordinates queried from the build PC at the same time
returned the same temperatures (Riyadh 38.3 °C at 16:15), and they fell through the evening on every receiver.
After the tests every slot was returned to its design, skin and settings from before (slot 1: CineView removed
again). OAWeather was never removed, reinstalled or changed anywhere.

## Remaining

- The weather location is the one saved in OAWeather, else the city chosen in CineView Designs; with neither, no
  weather is shown until a city is chosen (by design: a time zone does not say where the receiver is).
- While OAWeather supplies the data, its provider decides the values (OAWeather default: MSN); CineView's own
  lookup uses Open-Meteo — the two can differ by a degree or two.
- OpenATV 7.6 / 8.1+, OpenBH 5.7+, OpenViX 6.7 / 6.8 / 7.0+: the same files, compiled for that line's Python;
  verified statically, not run on a receiver in this round.
