# Vu+ Duo 4K SE — multiboot slots, read-only survey

**Date:** 2026-10-08, with Slot 5 (OpenBH 5.6) booted.

**Method:** nothing was mounted and nothing was written.
- STARTUP_1..15 were read with `cat`.
- eMMC slots were read directly under `/boot/linuxrootfsN`.
- USB slots were read from `/dev/sdb1` with the read-only ext4 reader `e4ro.py`.
- HDD, STARTUP and multiboot were not changed.

| Slot | Storage | Image | Build / date | Python | enigma2 | CineView installed | Kernel + rootfs |
|---|---|---|---|---|---|---|---|
| 1 | eMMC | OpenBH 6.0 | 003 / 2026-09-13 | 3.14 | c06a87ef4c | – | present |
| 2 | eMMC | OpenATV 7.6.0 | 20260925 | 3.13 | e42a0ffb00 | CineView FHD 2.3.4 | present |
| 3 | eMMC | OpenATV 8.0.0-beta | 20260925 | 3.14 | 3b21864bdc | CineView FHD 2.1.20260923-r1 | present |
| **4** | USB | **OpenViX 6.9** | build 002, dev 036 / 2026-09-02 | **3.14.7** | d3f089af4e | CineView FHD universal-offline 2.1.20260923-r1 (selected skin `CineView_FHD/skin.xml`) | present |
| 5 | USB | OpenBH 5.6.008 | 2026-05-01 | 3.13 | 52dedddc31 | CineView MLA 1.0.0~openbh17 | present (running) |
| 6 | USB | OpenPLi 9.2 | 2026-09-06 | 3.9.9 | b96a317 | – | present |
| 7 | USB | openDroid 8.1.2 | 20260910 | 3.14 | d8413a7a25 | – | present |
| 8 | USB | OpenATV 8.0.1 | 20261003 | 3.14.7 | 57b7a5127d | CineView MLA 1.0.0 | present |
| 9–15 | USB | empty (no kernel, no rootfs) | | | | | |

## OpenViX = Slot 4
`STARTUP_4`: `kernel=duo4kse/linuxrootfs4/zImage root=UUID=3cfb20d7-… rootsubdir=duo4kse/linuxrootfs4 rootwait=35`.

Read-only readiness checks:

| Check | Result |
|---|---|
| zImage | present (4,528,248 bytes) |
| Kernel version | 4.1.45, same as the other slots |
| Boot files | `/sbin/init` and `/usr/bin/enigma2` present |
| Image info | `/usr/lib/enigma.info`: `distro=openvix`, `imageversion=6.9` |
| Selected skin | `CineView_FHD/skin.xml` (old CineView FHD 2.1 universal-offline); the directory exists |
| Crash logs | none in `/home/root/logs` |
| MLA pre-start hook | `enigma2_pre_start.sh` absent: no MLA installed yet |

What cannot be proven without booting: that the image starts cleanly, the state of its settings, and network / feed access.
