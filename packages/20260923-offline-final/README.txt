CineView FHD 2.1 - Final Offline Packages - 2026-09-23 r3

PRIMARY:
cineview-fhd-universal-offline-final_2.1.20260923-r3_all.ipk
- One smart offline IPK containing all three final snapshots.
- Auto-detects OpenATV / OpenViX / OpenBH.
- Does not require GitHub after the IPK is copied to the receiver.

SEPARATE FALLBACKS:
cineview-fhd-openatv-offline-final_2.1.20260923-r3_all.ipk
cineview-fhd-openvix-offline-final_2.1.20260923-r3_all.ipk
cineview-fhd-openbh-offline-final_2.1.20260923-r3_all.ipk

r3 closure:
- OpenATV PluginBrowser/List/Grid: FHD and visible colored action bars.
- OpenATV PackageAction / PackageActionLog: FHD for install/remove/update plugin workflows.
- OpenATV PluginDownloadBrowser: FHD instead of the narrow PigTemplate layout.
- QuickMenu remains FHD and uses the CineView color-key footer handling.
- OpenATV GraphicalEPG remains true 1920x1080 and persists after activate.
- Persistent poster cache policy remains enabled on all three images:
  /media/hdd/poster first; other suitable local media next; /tmp fallback only.
- Multiboot media is excluded from poster cache.

Supported:
- OpenATV 7.4 / 7.5 / 7.6 / 8.0
- OpenViX 6.9 build 002
- OpenBH 6.0 build 001
