# CineView MLA — OpenATV Slot 8: static verification without booting it

**Date:** 2026-10-08.

**Method:** Slot 5 (OpenBH) stayed booted. Slot 8's root (`/linuxrootfs8` on the USB disk `sdb1`) was read through
`e4ro.py`, a small read-only ext4 reader. It opens the block device `O_RDONLY` and does not mount or write.
- Before use, the reader was checked against a live Slot 5 file: identical md5.
- No mount of Slot 8 exists; a mount attempt was refused by the permission system and nothing was mounted.
- Analysis ran on copies on the agent PC, with Python 3.14.8 (same bytecode magic `2b0e0d0a` as Slot 8's 3.14.7).

**Untouched:** STARTUP / multiboot, HDD and Slot 8 files.

**Status:** static checks only. Nothing below is a runtime result. Evidence: `docs/mla/evidence/openatv_slot8_static/`.

## Proven without booting

| # | Check | Result |
|---|---|---|
| 1 | Slot 8 image | OpenATV 8.0.1, build 20261003, Vu+ Duo4K SE, Python 3.14.7. This is the image 1.0.0 was runtime-verified on |
| 2 | Slot 8 enigma2 Python = which source? | Slot 8 ships hash-based `.pyc`: 428 of 428 enigma2 modules are byte-identical to openatv/enigma2 **`57b7a5127d`**, with 0 differing. The other 375 `.pyc` belong to other packages or plugins |
| 3 | CineView on Slot 8 = published 1.0.0? | 615/615 package files identical (incl. `enigma2_pre_start.sh`); `control` / preinst / postinst / prerm / postrm identical. opkg status `1.0.0 install ok installed` |
| 4 | Published 1.0.0 `.pyc` = golden sources | 14/14 match build94 sources by source hash |
| 5 | Candidate OpenATV build (current dev branch) vs golden | Parity **PASS**. 25 files differ, all allowed: CamInfo / ServiceInfo / ShowIf converters, plugin + image_adapter, composer, guardian, 8 layout files and 10 generated / active files |
| 6 | Python 3.14 compile of every candidate `.py` | 16 files, 0 errors |
| 7 | XML parse of candidate skin files | 49 files, 0 errors |
| 8 | Screen contracts (skinName + `self[...]`) of `57b7a5127d` vs skin | Candidate findings **identical to golden**. The only finding is the known `xpowerHelp`, also present in golden |
| 9 | Design engine on Slot 8's `enigma.info` | Golden vs candidate composer, every layout of every section and every theme (38 applies): 206 files identical, 60 differ only by the approved PVR-icon positions or CAM `wrap`, **0 other differences** |
| 10 | Guardian crash-loop tests | Golden 11/11, candidate 11/11 PASS (incl. MetrixHD fallback on OpenATV) |
| 11 | ImageAdapter with Slot 8's `enigma.info` | `openatv`. Second-InfoBar rows, `session.onShutdown`, `choiceList=`, PackageAction wait, ServiceListLegacy clip, no label override — all identical to 1.0.0 |
| 12 | OpenBH-only code on OpenATV | Not installed. Shortened names, PluginDownloadBrowser and Arabic override need `name_clip=complexcolumn`, `package_wait=plugindownloadbrowser` and OpenBH label rules, which the adapter does not return on OpenATV |
| 13 | Native contracts used by the changes, in `57b7a5127d` source | `Element.changed` → `RunningText.changed` restarts scrolling (the CamInfo fix applies), RunningText `wrap` option, `ServiceInfo.interestingEvents`, `GUIComponent.setVisible(False)` → `instance.hide()` (ShowIf's extra `hide()` is a no-op on OpenATV), `ServiceListLegacy`, `PackageAction.setWaiting`, `ChoiceBox(choiceList=)`, `session.onShutdown` — all present |
| 14 | Candidate OpenATV package (structure, **not a release**) | Maintainer scripts identical to 1.0.0. Content differs only in the 25 changed files plus `version.json`. One new module: `image_adapter.pyc` |
| 15 | Smart Installer (dev/openbh-installer) detection on Slot 8's files | "OpenATV 8.0.1 detected / supported", published 1.0.0 URL + SHA, Python 3.14. Same decision as the public installer |
| 16 | PVR header icons | New positions inside 1920×1080 and no overlapping widget rectangle. Not conclusive: the original defect was text drawn over the date, which a rectangle check does not show |

## Needs a Runtime Test on Slot 8 (cannot be proven statically)
1. Every screen loads the candidate skin: InfoBar, SIB, ChannelSelection, EPG ×4, EventView, PVR, Plugin Browser, Setup, MessageBox, with 0 traceback and 0 skin error.
2. **CAM field:** text really scrolls in Details / Cinema and all lines appear without clipping, in Full / Profile / Hide.
3. **PVR Classic / Cover:** icons on the clock line, date clean, English and Arabic; icons switch with sort / view.
4. **ShowIf:** one channel logo, posters on / off.
5. **ServiceInfo:** HD / 16:9 / resolution change with HD↔SD zap.
6. **Long channel names on OpenATV** (ServiceListLegacy hook, unchanged since 1.0.0): six designs × bar left / right.
7. **Plugin Browser Install / Remove:** one wait message (PackageAction hook).
8. **CineView Designs:** profiles, design model, Apply / Keep / auto-rollback, Factory, guardian on a real crash loop, clean exit through `session.onShutdown`.
9. **Package install / upgrade 1.0.0 → candidate** on the receiver (preinst / postinst with the user's selection), then rollback to 1.0.0.
10. **Smart Installer** real run (`DRYRUN=1`, then install) on the receiver.
