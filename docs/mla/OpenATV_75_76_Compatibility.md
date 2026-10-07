# CineView MLA 1.0.0 — OpenATV 7.5 / 7.6 compatibility (static study)

Status: **study only — nothing here is runtime-verified.** 1.0.0 is declared for OpenATV 8.0 (Python 3.14) only.

## Method
- Package examined: the published `enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk`
  (SHA256 `4709881b66ae9e5b8cc8dfa7f5b7e3fafdfb57d779431709b8c5c1b48c4cb0a8`).
- Reference = the verified image: openatv/enigma2 `57b7a51` (OpenATV 8.0.1).
- Targets: openatv/enigma2 branch **7.6** @ `e42a0ff` (2026-09-11) and branch **7.5** @ `29c4150` (2025-11-07).
  These local trees are partial (no `lib/dvb`); C++ API checks used `lib/python/enigma_python.i`.
- Tools: `tools/mla/compat_image.py` (renderers, converter tokens, skin attributes, screen contracts) and an
  import / enigma-API scan of the 14 Python modules of the package (AST of the build94 sources).
- Static analysis is necessary, not a proof. Device behaviour (tuner data, EPG, PVR, posters) needs a real receiver.

## Results

| Check | 7.6 (e42a0ff) | 7.5 (29c4150) |
|---|---|---|
| Renderers / converters / converter tokens | same as 8.0 | `MovieInfo` token `FullDescription` **missing** (used by EventView, EPG, Channel Selection, Second InfoBar and PVR layouts — 26 layout files) |
| Skin attributes | same as 8.0 | `addon`, `connection`, `mode` **not parsed** — `Components/Addons` does not exist on 7.5 (`ColorButtonsSequence` ×39, `Pager` ×3, `ButtonSequence` ×1) |
| Screen contracts (skinName + widgets) | same as 8.0 | same as 8.0 |
| enigma API (`ePicLoad`, `loadPNG`, `savePNG`, `eEPGCache`, …) | present | present |
| Image modules / names imported (`PackageAction`, `SetupSummary`, `ServiceListLegacy`, `getTextBoundarySize`, …) | present | present |
| Newer skin features used by 1.0.0: `valueFont`, `cornerRadius`, `onLayoutFinish` applets, `Screens/Processing.py`, `PackageAction.setWaiting` | present | present |
| Python byte-code | **must be rebuilt** — the package ships sourceless `.pyc` for Python 3.14 (preinst refuses another version) | same |

## What 7.6 support would need (no design or feature change)
1. Read the Python version of a real 7.6 image (`python3 --version`); it is not assumed here.
2. Build the same 14 modules as `.pyc` with exactly that Python (`mkpyc.sh` with the 7.6 interpreter) and package a
   7.6 variant (same skin and data; only the `.pyc` and the preinst Python check differ).
3. Installer: allow 7.6 only when the matching package is offered (one package per Python version, chosen by the
   Python check — never by receiver model).
4. Full device QA on a real 7.6 receiver: all five models × six sections, posters on/off, six themes, CineView
   Designs (apply / keep / auto-revert / factory / profiles), package screens, Setup pages, MessageBox, EMC/PVR,
   live tuner data, install / upgrade / reinstall / bad SHA / reboot.
Estimate: packaging ½ day; QA 1–2 days on a 7.6 receiver. Until then 7.6 is **not** declared.

## What 7.5 support would need
7.5 lacks the `Components/Addons` widget system and the `MovieInfo FullDescription` token. Supporting it would mean
replacing the colour-button bars, pagers and full-description texts with older constructs — a visible change of the
approved design, or a CineView-owned copy of those components (new code to write and test). Both go against "no
feature or design reduction", so **7.5 is not recommended**. If required later: a separate 7.5 compatibility layer
(own converter for the full description + own button-bar/pager renderers), then the full 7.6-style QA above.

## Installer policy for 1.0.0
OpenATV 8.0 → installs (then Python 3.14, components, space and storage are checked). OpenATV 7.6 → stops
("not supported by 1.0.0 yet"; changed today — before, 7.6 went on to the Python check, which could have let an
untested image through). 7.5 and older → stops. Unknown image → stops. No receiver-model check anywhere.
