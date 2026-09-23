# CineView FHD - OpenBH Final - 2026-09-23

Target: OpenBH 6.0.001 / OE-Alliance 6.0 / Python 3.14.6 / Vu+ Duo 4K SE.

## Porting rule
OpenBH native screen contracts are authoritative. OpenATV is only the visual/feature reference; OpenViX is a structural reference where useful.

## Final state
- Main InfoBar preserved.
- SecondInfoBar remains a separate current/next screen with poster frames.
- GraphicalEPG, GridEPG, GraphicalEPGPIG and GridEPGPIG are Full FHD CineView layouts.
- EPG keeps OpenBH-native widgets/contracts while presenting poster and event information above a full-width grid.
- Hotkey, Language, Skin Selection and MultiBootSelector are Full FHD.
- Movie/PVR keeps native OpenBH MiniTV/list behavior and adds poster/frame plus FILE/PATH.
- Long filename/path support and poster fallback are preserved.
- Poster cache remains under /tmp/cineview-emc-posters; no HDD data is used.

## Persistence validation
The final openbh_compat.py is the persistent source of OpenBH-specific contracts.
- 33 CineView skin/layout files patched by the helper.
- 34 CineView XML files parsed successfully.
- Python compile passed for openbh_compat.py, CineViewPosterX.py, LukaPosterXEMC.py and CineViewMoviePath.py.
- Semantic comparison against the final live OpenBH skin returned 0 differences across 17 target screens.
- This protects the final Hotkey/Language/MultiBoot/PVR/EPG/SecondInfoBar design after future CineView option changes.

## Runtime validation
- Enigma2 restart passed on the live OpenBH receiver.
- OpenWebif passed.
- Decoder returned 1920x1080.
- Live visual checks passed for Hotkey, Language, Skin Selection, MultiBoot, SecondInfoBar, Graphical EPG and Movie/PVR poster/fallback.
- An earlier aggressive EPG Stage 5 attempt was rolled back immediately; the final version keeps native OpenBH screen contracts.

## Safety
- No HDD data modified.
- Stage backups were created under /root/cineview-openbh-backups/.

## Final archive SHA256
- cineview-live-openbh-final-20260923.tar.gz
  9017ab3455632ef5f93d46def51a8d26738f6bd8ce24ddacedabaad31bcadf3c
- cineview-openbh-engineering-history-20260923.tar.gz
  6dbcf6bb0f9d4402f7a23e9243cec9df8c2cf90b8b0eacfac0a35653a20676d3

## Final smart-link end-to-end validation
Performed on the live Vu+ Duo 4K SE after booting MultiBoot Slot 1 (OpenBH 6.0.001):
- Public smart link detected OpenBH 6.0 build 001 correctly.
- Downloaded the pinned OpenBH final snapshot.
- SHA256 matched 9017ab3455632ef5f93d46def51a8d26738f6bd8ce24ddacedabaad31bcadf3c.
- Validated 34 CineView XML files.
- Created rollback backup under /tmp.
- Installed and activated the final OpenBH snapshot successfully.
- Enigma2 restart passed.
- OpenWebif returned normally after restart.
- AL Arabiya HD verified live at 1920x1080.
- SecondInfoBar and Full FHD EPG were visually revalidated after the smart-link install.
- No /media/hdd data was modified.
