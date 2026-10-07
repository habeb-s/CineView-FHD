# CineView MLA — Multi-Image Compatibility (Phase 2: OpenBH, Phase 3: OpenViX)

Status: **UNDER INVESTIGATION** (2026-10-07). Branch `dev/mla-multiimage`.

## Baseline (frozen)
- Golden baseline: tag `mla-openatv-1.0.0-golden` → `1c24d6a` (build94 code; published package
  `enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk`, SHA256 `4709881b…c4cb0a8`, repo habeb-s/CineView-MLA).
- Rule: nothing on this branch may change the OpenATV output. Every change is checked by an **OpenATV parity gate**:
  build the OpenATV target from this branch and compare the skin tree file by file with the golden build (0 differences
  outside files that carry an image suffix for another image).

## Principles
1. **One core, one design.** Layout packs, themes, previews, the composer engine, CineView Designs, the poster engine and
   the installer are shared. No second copy of the project per image.
2. **Differences live in adapters only.** An image adds:
   - `targets.<image>` entries in each layout manifest (the seam already used by `composer.py`: `targets.openatv.file`);
   - a per-image screen file **only where the native contract differs** (`screens.openbh.xml` next to
     `screens.openatv.xml`); otherwise the target points at the shared file;
   - `core/*.<image>.xml` for image-specific core screens;
   - an `ImageAdapter` in Python (detect, contracts, reload sequence, ChannelSelection mode, boot hook, package screens);
   - installer rules (image, version floor, Python).
3. **Evidence first.** Every screen name, widget, source, converter token and Python API used on OpenBH is checked
   against the real OpenBH image (its own Python/XML on the receiver), not against OpenATV and not against the old
   CineView FHD OpenBH snapshot.
4. Same safety rules as Phase 1: no HDD writes, no tuner/dish/CA changes, backups before changes, rollback kept.

## Work plan — Phase 2 (OpenBH)
| Step | What | Output |
|---|---|---|
| P2.0 | Discovery on the real OpenBH image: version/build, Python, enigma2 commit, skin.py features (valueFont, cornerRadius, applets, Addons, `<include conditional>`), boot pre-start hook, package/Processing screens, ChannelSelection style mechanism | `contracts/openbh-<ver>-<commit>.json` + discovery report |
| P2.1 | Contract diff OpenATV 8.0.1 ↔ OpenBH for every screen/widget/source/converter/renderer the MLA skin uses (`compat_image.py`, `contracts.py`) | difference list per section |
| P2.2 | Adapter seam in code: `ImageAdapter` (openatv = current behaviour), image key passed to composer/build/plugin/installer | OpenATV parity gate = 0 diff |
| P2.3 | OpenBH overrides only for real differences (screens, core, package screens, CineView Designs reload/restart path) | `*.openbh.xml` files, adapter code |
| P2.4 | Build + .pyc with the OpenBH Python; package (same package name, image-checked preinst, or one package with per-image targets — decided after P2.1) | OpenBH package |
| P2.5 | Device QA on OpenBH: all models × sections, posters on/off, themes, Designs (apply/keep/revert/factory/profiles), EMC/PVR (OpenBH-native logic kept), live tuner data, installer scenarios | evidence |
| P2.6 | OpenATV regression with the unified build (same tests as 1.0.0) | evidence |

## Decisions needed from the user
- Which multiboot slot may be used for OpenBH (earlier evidence: Slot 1 = OpenBH 6.0.001, Python 3.14.6), and whether
  reading its files and installing test builds there is allowed.
- OpenBH minimum version for MLA (earlier CineView FHD policy: 5.6) — to be confirmed by the contracts found in P2.0.
