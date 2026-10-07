# OpenBH 5.6 — Clean Baseline + first compatibility run (2026-10-07)

Status: **UNDER INVESTIGATION** — first run with the golden core unchanged; no fix applied yet.
Evidence: `evidence/openbh_t105/` (logs per step, screenshots, summary), scripts `t105a.sh`, `t105b.sh`,
`cleanup_slot5_openbh.sh`.

## Environment (verified on the receiver, before any change)
Vu+ Duo 4K SE (vuduo4kse) · Slot 5 = `duo4kse/linuxrootfs5` (cmdline and STARTUP) · OpenBH 5.6.008, enigma2
5.6+git37259 (`BlackHole/enigma2@52dedddc314a`) · Python 3.13.12 (magic f30d0d0a) · armv7l / cortexa15hf-neon-vfpv4 ·
primary skin: image default (MX_Slim-Line_NP), display skin: old CineView · root `/dev/sdb1` (USB), 52 GB free.

## Clean baseline (old project removed from Slot 5 only)
Removed through opkg: `enigma2-plugin-cineview-mx-openbh` 2.0.0-openbh56-mx (meta), `enigma2-skin-mx-slim-line-se`
2.0.0-openbh56-mx (our MX build, maintainer habeb/openai, not in any OpenBH feed; image default MX_Slim-Line_NP
untouched), `enigma2-plugin-skins-cineview-fhd-openbh` 2.4.13. Removed by explicit path: CineViewControl compiled files,
6 converter + 1 renderer `.pyc`, `/etc/enigma2/CineView_FHD_skin_base.xml`, `/tmp/CineViewBitrate.log`, 3
`/usr/uninstall/*.del`; settings lines `config.plugins.cineview.theme`, CineView display skin. Rollback copy on the agent.
Not touched: `/var/volatile/tmp/GetImageliste_*` (live mount of the internal-flash multiboot partition = other slots),
other slots, STARTUP, HDD. After a full reboot: old packages 0, skin dirs 0, plugins 0, leftovers 0, broken links 0,
OpenBH default skin: 0 tracebacks, 0 skin errors.

## First run — golden core unchanged (package `1.0.0~openbh1`: build94 skin, .pyc by OpenBH Python 3.13)
| Component | Status | Evidence |
|---|---|---|
| Package install (preinst image/Python check, postinst factory) | PASS with adaptation | packaging target `openbh` + .pyc 3.13 |
| Skin load (skin.xml, theme, core, 6 section files) | PASS unchanged | all files loaded, GUI up |
| Picons (channel list, InfoBar) | PASS unchanged | screenshots |
| Multi EPG | PARTIAL | list OK; 5 missing elements |
| InfoBar | PARTIAL | frame, picon, tuner data OK; event texts empty; converter error |
| Second InfoBar | FAIL | both event panels empty; duplicate channel logo; converter error |
| Channel Selection | PARTIAL | list with events OK; info panel mostly empty |
| Grid EPG (GraphicalEPGPIG) / InfoBar grid EPG | PARTIAL | grid shown; OpenATV list attributes ignored; PiG black; missing elements |
| Single EPG | FAIL | list empty |
| Event View (InfoBar + EventViewSimple) | FAIL | entry point called, nothing displayed; cause not yet found |
| PVR (native MovieSelection) | PARTIAL | opens with CineView layout on an empty slot-local folder; rows not verifiable |
| EMC | NOT AVAILABLE | EnhancedMovieCenter not installed on this slot |
| Plugin Browser | FAIL | OpenBH contract differs; list empty |
| CineView Designs | FAIL | exception at open: `second_infobar_timeout` |
| Themes / Apply / Keep / Rollback / Profiles | NOT TESTED | blocked by Designs |
| Setup pages, MessageBox | NOT TESTED | test tool could not open them after the Designs failure (OpenBH modal rule) |
| Posters | PARTIAL | engine runs (2 files in pinned /tmp cache); no poster visible on InfoBar/SIB yet |
| ECM / CAM info, Arabic/RTL, reflow | NOT TESTED | next run |
| Name-clip patch, package-screen text fix | NOT AVAILABLE | OpenATV-only Python names, guarded off |
| Crashes | 0 new | only an old 2026-10-02 crash log from the old project |

## FAIL / PARTIAL analysis
1. **CineViewMLAServiceInfo** (InfoBar, SIB): `AttributeError ... 'interestingEvents'`. OpenBH's native `ServiceInfo`
   names it `interesting_events` (OpenATV: `interestingEvents`). Fix: name-agnostic access in the converter —
   **Common Core**. Likely cause of the empty event texts too (to be confirmed after the fix).
2. **CineView Designs**: reads `config.usage.second_infobar_timeout` (OpenATV). OpenBH has `show_second_infobar`
   (combined mode/timeout), `fix_second_infobar`, `second_infobar_simple`. Fix: native rows come from the image adapter
   — **OpenBH Adapter**.
3. **Plugin Browser**: OpenBH screen has no `description`, `quickselect`, `key_blue` and needs `list`; the OpenATV screen
   fails to build. Fix: `PluginBrowser` screen in `core/common.openbh.xml` — **OpenBH Adapter**.
4. **Single EPG / Grid EPG**: OpenBH uses the ViX EPG family (`EpgSelectionSingle/Grid`, widgets `bouquetlist`, `lab1`,
   `timeline`, `page`, `jump`, `primetime`…); OpenATV list attributes (`setEventItemFont`, `setColWidths`,
   `TimeBackgroundColor`…) are not implemented. Fix: EPG section `screens.openbh.xml` in the same design — **OpenBH Adapter**.
5. **Event View**: not displayed; needs the OpenBH EventView contract study (no `getEventViewInstance`; entry
   `openEventView`) — root cause **NOT YET IDENTIFIED**.
6. **Channel Selection info panel**, **SIB duplicate logo**, **posters not visible**: to re-check after fix 1 (shared
   converter) before classifying — **UNDER INVESTIGATION**.
7. Warnings: `ePixmap mode=` not implemented, missing `key_*` / `channel` / `epg_description` elements — cosmetic;
   OpenBH adapter screens can supply them.
8. `Session.onShutdown` missing, `ServiceListLegacy`, `PackageAction` missing — features stay off safely; OpenBH
   equivalents to study — **OpenBH Adapter**.

## Figures (estimate after one run; basis: 14 Python modules and 9 skin files of the package)
- OpenATV code reusable unchanged: **~70%** (12 of 14 modules; theme/base/infobar/SIB/PVR/MLA-UI skin files)
- OpenBH adaptation required (shared code made name-agnostic or adapter-driven): **~20%**
- OpenBH-specific code required (EPG, Plugin Browser, EventView screens, adapter module): **~10%**
- Open issues: **14** · Crashes: **0**
- Estimated work to full OpenBH compatibility: **4–6 working days** (fixes 2–3, full device QA 2–3).

## Proposed architecture (one CineView MLA for OpenATV + OpenBH)
- **Common Core** (one copy): layout packs and designs, themes, previews, composer engine, guardian, poster engine,
  converters/renderers (written against both native names), CineView Designs.
- **ImageAdapter** (`mla/adapters/openatv.py`, `openbh.py`, chosen by `/usr/lib/enigma.info distro`): native setting
  rows for Designs, EPG/EventView entry points, package-screen and name-clip hooks, shutdown hook, reload sequence.
- **Skin overrides only where contracts differ**: manifest `targets.<image>.file` defaults to the shared
  `screens.openatv.xml`; OpenBH gets `screens.openbh.xml` only for EPG (and EventView if needed) and
  `core/common.openbh.xml` for PluginBrowser and similar native screens.
- **Build/package**: `build.py --image`, packaging target per image (one package name, per-image preinst, .pyc per
  Python); OpenATV parity gate on every change (passed today).
- **Smart Installer**: picks the package for the detected image and Python; never by receiver model.
