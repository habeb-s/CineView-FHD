CineView FHD 2.1 - Offline Emergency Packages - Final 2026-09-23

PRIMARY / RECOMMENDED:
- cineview-fhd-universal-offline-final_2.1.20260923-r1_all.ipk
  One self-contained smart IPK for OpenATV, OpenViX and OpenBH.
  It auto-detects the active image and applies only its matching final snapshot.
  This exact file was live-tested on all three supported images.

SEPARATE FALLBACK PACKAGES:
- cineview-fhd-openatv-offline-final_2.1.20260923-r1_all.ipk
- cineview-fhd-openvix-offline-final_2.1.20260923-r1_all.ipk
- cineview-fhd-openbh-offline-final_2.1.20260923-r1_all.ipk

Supported/tested:
- OpenATV 8.0.0-beta build 20260922 (universal detector also allows 7.4/7.5/7.6/8.0)
- OpenViX 6.9 build 002
- OpenBH 6.0 build 001

Offline local installation:
  opkg install /tmp/cineview-fhd-universal-offline-final_2.1.20260923-r1_all.ipk
  init 4
  sleep 3
  init 3

Safety:
- Detects image/version before changing CineView.
- Rejects unsupported images.
- Verifies the embedded image-specific snapshot SHA256 before extraction.
- Creates rollback backup under /tmp.
- Validates CineView XML after installation.
- Does not use GitHub or the Internet.
- Does not modify /media/hdd.
