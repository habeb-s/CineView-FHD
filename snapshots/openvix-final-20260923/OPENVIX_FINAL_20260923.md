# CineView FHD - OpenViX Final - 2026-09-23

Target: OpenViX 6.9 build 002 / OE-Alliance 6.0 / Python 3.14.7 / Vu+ Duo 4K SE.

## Final state
- Existing OpenViX-native CineView screen contracts preserved.
- Main InfoBar preserved with the accepted final visual spacing.
- SecondInfoBar remains separate current/next with the accepted poster-frame treatment.
- Hotkey, Language, Skin, Movie/PVR, EPGSelection and PluginBrowser remain native OpenViX contracts.
- activate.sh no longer runs the OpenATV post-processor on OpenViX.
- New openvix_final.py reapplies only the accepted OpenViX visual refinements after CineView option changes.
- No OpenATV screen contracts are imported into OpenViX.

## Persistence validation
A real activate.sh run was executed after the fix. Semantic comparison of the active skin before and after activation returned 0 differences for:
- InfoBar
- SecondInfoBar
- SecondInfoBarSimple
- HotkeySetup
- HotkeySetupSelect
- LanguageSelection
- SkinSelector
- MovieSelection
- EPGSelection
- EPGSelectionMulti
- PluginBrowser

## Runtime validation
- 34 CineView XML files parse successfully.
- Python compile passed for CineViewPosterX and the new OpenViX final compatibility helper.
- Enigma2 restart passed.
- OpenWebif passed after restart.
- Video decoder returned 1920x1080.
- Live visual checks passed for SecondInfoBar and EPG.

## Safety
- No HDD data modified.
- Pre-change backup stored under /root/cineview-openvix-backups/.

## Archives
- cineview-live-openvix-final-20260923.tar.gz
- cineview-openvix-engineering-history-20260923.tar.gz
- SHA256SUMS.txt
- validation/ screenshots

## 2026-09-23 poster-cache update
- Poster cache now prefers persistent writable storage: /media/hdd/poster first, then another local writable /media block mount; multiboot media is skipped; /tmp/CINEVIEW/poster is fallback only.
