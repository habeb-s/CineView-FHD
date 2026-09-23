CineView FHD 2.1 - Offline Emergency IPKs - Final 2026-09-23

These IPKs are fully self-contained. They do not download CineView from GitHub.
Each package embeds the final tested image-specific snapshot and verifies its
original snapshot SHA256 before installing it.

Files:
- cineview-fhd-openatv-offline-final_2.1.20260923-r1_all.ipk
  Target: OpenATV 7.4 / 7.5 / 7.6 / 8.0
  Live install test: OpenATV 8.0.0-beta, build 20260922

- cineview-fhd-openvix-offline-final_2.1.20260923-r1_all.ipk
  Target: OpenViX 6.9 build 002
  Live install test: OpenViX 6.9 build 002

- cineview-fhd-openbh-offline-final_2.1.20260923-r1_all.ipk
  Target: OpenBH 6.0 build 001
  Live install test: OpenBH 6.0 build 001

Local installation:
  opkg install /tmp/<correct-image-file>.ipk
  init 4
  sleep 3
  init 3

Safety:
- The preinst checks the receiver image and refuses the wrong image package.
- A rollback archive is created under /tmp before CineView files are changed.
- The embedded snapshot SHA256 is verified before extraction.
- CineView XML is validated during post-install.
- No /media/hdd data is modified.
- The package owns only its private embedded archive. CineView files are
  overlaid by postinst, avoiding opkg file-ownership clashes with image packages.
