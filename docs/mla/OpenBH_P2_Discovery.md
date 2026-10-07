# OpenBH — P2.0/P2.1 discovery (static, read-only)

Status: **UNDER INVESTIGATION** — static evidence only; nothing installed or booted on OpenBH.

## Images found on the receiver's USB (read-only, no boot, no mount change)
| Folder | Image | enigma2 build → source commit | Python |
|---|---|---|---|
| `/media/usb/duo4kse/linuxrootfs5` | OpenBH 5.6 (= agreed floor) | 5.6+git37259 → `BlackHole/enigma2@52dedddc314a` "openbh: release 5.6.008" (2026-05-01) | 3.13 |
| `/media/usb/openbh-6003-test` | OpenBH 6.0.003 (test root copy) | 6.0+git37876 → `BlackHole/enigma2@c06a87ef4c09` (2026-09-11, branch Python3.14) | 3.14 |
| `/media/usb/duo4kse/linuxrootfs4` | OpenViX 6.9 (Phase 3) | `d3f089af4e` | 3.14 |
Note: linuxrootfs5 still has the OLD CineView FHD (OpenBH) installed — its files are not native and are ignored.
Both OpenBH images ship `.pyc` only; contracts were taken from the exact source commits above.

## Contract check of the published MLA 1.0.0 build (reference OpenATV 57b7a51)
OpenBH 5.6 and 6.0.003 give **identical** results → one OpenBH adapter for both; only the `.pyc` differ (3.13 / 3.14).

| Area | Finding | Consequence |
|---|---|---|
| Renderers / converters / tokens | same as OpenATV | shared |
| `Components/Addons` (ColorButtonsSequence, Pager, ButtonSequence…) | present | button bars and pagers shared |
| `Screens/Processing.py`, `enigma2_pre_start.sh` hook in enigma2.sh | present | Processing screen and boot guardian can be shared (runtime check needed) |
| skin attribute `valueFont` | **not parsed** (OpenBH has `secondfont`) | Setup value font needs an OpenBH override (`secondfont`, to verify) |
| skin attribute `backgroundColorMarked` | **not parsed** | OpenBH override / native equivalent |
| Graphical EPG (`GraphicalEPG`, `GraphicalEPGPIG`, `GraphicalInfoBarEPG`) | owned by `EpgSelectionGrid` / `EpgSelectionInfobarGrid`; `timeline0…5` not provided | EPG section needs `screens.openbh.xml` for the grid EPG (ViX-style EPG family) |
| `EPGvertical`, `EPGverticalPIG` | do not exist on OpenBH | the vertical EPG layout is OpenATV-only; OpenBH target omits it |
| `SecondInfoBarECM` | does not exist on OpenBH | not used on OpenBH (no loss) |
| Python `Components.ServiceList.ServiceListLegacy` | missing | name-clip patch already guarded (try/except) → off on OpenBH; OpenBH-native equivalent to study |
| Python `Screens.PluginBrowser.PackageAction` | missing | package-screen text fix already guarded → off; OpenBH package screens to study |

Not yet covered by the static check (next): OpenBH-only screens CineView must skin, ChannelSelection style mechanism,
skin reload sequence, EMC/PVR (OpenBH-native), Setup/ConfigList templates, MessageBox, Plugin Browser, Designs restart path.

## Next
P2.2 adapter seam with the OpenATV parity gate (0 diff), then OpenBH overrides for the rows above, then a test slot
decision before any install.
