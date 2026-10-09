# CineView MLA 1.0.4 — optional weather (OAWeather)

## Report (real user, 2026-10-09)

Applying a design failed with:

```
The design could not be applied:
validation failed:
  EventView: converter OAWeather not installed
  EventView: renderer OAWeatherPixmap not installed
  InfoBar / SecondInfoBar / SecondInfoBarSimple: (same two lines)
```

## Cause

- The Classic, Details and Cinema layout packs and the factory generation `g000000` contain weather widgets:
  `source="session.OAWeather"` + `<convert type="OAWeather">` + `render="OAWeatherPixmap"`.
- These three components are not part of Enigma2. They belong to the separate oe-alliance plugin
  `enigma2-plugin-extensions-oaweather` (which depends on `enigma2-tools-weatherinfo`). The plugin is preinstalled
  on many OpenATV images but not on every OpenATV, OpenViX or OpenBH install.
- Nothing provided the plugin. The MLA Smart Installer did not install it, and the packages did not declare it.
- The composer's validation correctly refused any selection that contained the widgets. The same widgets in the
  factory generation would also have reached Enigma2 unvalidated on such an image.
- Audit of all 10 published 1.0.3 packages: every `render=`, `<convert type=>` and `session.*` source of every
  screen file was checked against the OpenATV, OpenBH and OpenViX Enigma2 trees plus the modules the package ships.
  The OAWeather trio is the only set of components a screen uses that an image may lack. The audit script is
  `audit.py` on the build PC.

## Fix (mla/engine/composer.py only; every other file in the packages is byte for byte unchanged)

- **`OPTIONAL_FEATURES["weather"]`** names the plugin's components: the session source, the converter, the
  renderer and `Sources/OAWeather`. `installed_components()` now also reads `Components/Sources`.
- **Missing plugin:**
  - Exactly those widgets are left out when the generation is built.
  - Validation runs on that pruned generation, which is the one Enigma2 loads.
  - Every other missing renderer or converter still blocks.
- **`features.json`** in each generation records which features were left out.
- **`ensure_components()`** runs in the guardian's pre-start `recover` and after `rollback`. It rebuilds the
  active generation, keeping the same selection, when the installed plugins change:
  - The factory without OAWeather is rebuilt before Enigma2 loads it.
  - When OAWeather is installed later, the weather returns at the next start.
  - The last-known-good marker and the trial journal follow the rebuilt generation.
- **With OAWeather installed nothing changes:** the packs are copied byte for byte and the factory stays `g000000`.
- **Smart Installer 1.3.4** (CineView-MLA-Install) installs `enigma2-plugin-extensions-oaweather` from the image's
  own feed when that feed offers it. This step is optional and never fatal. The installer also no longer restarts
  the GUI while a recording is running.

## Tests

- **`tools/mla/test_optional_weather.py`: 170/170 on the 10 published 1.0.3 packages (17 checks each).**
  - The 1.0.3 composer reproduces the error.
  - With the new composer and no OAWeather:
    - A first install rebuilds the factory without weather. That generation has zero missing components, is
      identical to the factory apart from the weather widgets, and is stable at the next start.
    - All 6 models × 6 themes apply, and every generation passes a strict component check.
    - A missing non-optional converter still blocks.
  - If OAWeather is installed later, the generation is rebuilt with weather and is byte-identical to the packs.
  - If OAWeather is installed from the start, nothing is rebuilt.
  - If OAWeather is removed later, the pre-start recover drops the weather and keeps the user's selection.
  - A trial journal follows a rebuilt generation.
- **`tools/mla/test_engine.py`: 28/28**, the same as 1.0.3.
- **`verify104.py`:** each 1.0.4 package equals its 1.0.3 package except `composer.py` and `version.json`, and
  `control` differs only in Version/Source. Result: PASS for all 10.
- **Device: Vu+ Duo 4K SE, OpenATV 8.0.1, Python 3.14, not recording.** Steps in order:
  1. 1.0.3 installed, OAWeather removed (`opkg remove`). Validating Classic gives exactly the user's 8 errors (rc=1).
  2. 1.0.4 installed, still without OAWeather. Classic, Details (purple) and Cinema (burgundy) applied. Each time
     the GUI was restarted and the InfoBar, Second InfoBar and Event View were opened. Result: no crash log, the
     Enigma2 process unchanged after the screens, and no weather fields
     (`noweather_classic_*`, `nw_classic_*`, `nw_details_*`, `nw_cinema_*`).
  3. Factory design restored without OAWeather: `ensure g000000 -> g000055 omitted=['weather']`, then the GUI
     restarted (`nw_factory_*`).
  4. OAWeather reinstalled from the official feed (feeds2.mynonpublic.com) and the GUI restarted. The guardian
     logged `ensure: g000055 -> g000056 omitted=[]` and the weather is back (`w_factory_infobar.jpg`).
  5. Smart Installer 1.3.4 (`PKG_DIR`, `RESTART=1`) run after removing OAWeather. It installed OAWeather from the
     feed, then upgraded to 1.0.4 with the design kept, restarted the GUI and passed verification
     (`installer_1.3.4.log`).
  6. The receiver was returned to its previous design (Black, Modern / Posterlist) and to standby. OAWeather is
     installed and CineView MLA 1.0.4 is active.
