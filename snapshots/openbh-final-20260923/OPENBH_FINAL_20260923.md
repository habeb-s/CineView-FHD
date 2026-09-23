# CineView FHD - OpenBH Final - 2026-09-23

Target: OpenBH 6.0.001 / OE-Alliance 6.0 / Python 3.14 / Vu+ Duo 4K SE.

## Porting rule
OpenBH native screen contracts are authoritative. OpenATV final is the visual/feature reference only.

## Final state
- Main InfoBar preserved.
- SecondInfoBar remains separate current/next with poster frames.
- GraphicalEPG, GridEPG, GraphicalEPGPIG and GridEPGPIG unified to Full FHD CineView layout.
- EPG uses poster and event information at top, full-width grid below, CineView footer.
- Hotkey, Language, Skin Selection and MultiBootSelector are Full FHD.
- Movie/PVR keeps native OpenBH layout and MiniTV; adds poster/frame plus FILE/PATH.
- Long filename/path scroll; poster cache stays in /tmp/cineview-emc-posters; fallback placeholder retained.

## Safety and validation
- No HDD data modified.
- Stage backups under /root/cineview-openbh-backups/.
- Initial Stage 5 EPG redesign was rolled back immediately after playback instability.
- Final EPG keeps native OpenBH widgets and changes layout only.
- XML parse passed.
- Python compile passed for CineViewPosterX.py, LukaPosterXEMC.py and CineViewMoviePath.py.
- Enigma2 restart and OpenWebif passed.
- Decoder returned to 1920x1080 after restart.
- Live visual checks passed for Hotkey, Language, Skin Selection, MultiBoot, SecondInfoBar, Graphical EPG and Movie/PVR poster/fallback.

## Archives
- cineview-live-openbh-final-20260923.tar.gz
- cineview-openbh-engineering-history-20260923.tar.gz
- SHA256SUMS
- validation/ screenshots
