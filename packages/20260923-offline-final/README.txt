CineView FHD 2.1 - Final Offline Packages - 2026-09-23 r2

PRIMARY:
cineview-fhd-universal-offline-final_2.1.20260923-r2_all.ipk
- One smart offline IPK containing all three final snapshots.
- Auto-detects OpenATV / OpenViX / OpenBH.
- Does not require GitHub after the IPK is copied to the receiver.

SEPARATE FALLBACKS:
cineview-fhd-openatv-offline-final_2.1.20260923-r2_all.ipk
cineview-fhd-openvix-offline-final_2.1.20260923-r2_all.ipk
cineview-fhd-openbh-offline-final_2.1.20260923-r2_all.ipk

Final r2 updates:
- OpenATV GraphicalEPG uses the accepted internal layout with a true 1920x1080 screen contract.
- OpenATV EPG generator and audit fix preserve that layout after activation.
- All three images use persistent poster storage when available:
  /media/hdd/poster first, then another local writable /media block storage mount.
- Multiboot storage is excluded from the poster cache.
- /tmp/CINEVIEW/poster is fallback only.
- OpenATV/OpenBH EMC uses the same CineView poster cache.

Supported:
- OpenATV 7.4 / 7.5 / 7.6 / 8.0
- OpenViX 6.9 build 002
- OpenBH 6.0 build 001

Safety:
- Wrong/unsupported images are rejected.
- Embedded snapshot SHA256 is checked before extraction.
- A rollback archive is created under /tmp before CineView files are changed.
