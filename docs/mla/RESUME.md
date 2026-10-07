# CineView MLA: resume point (updated 2026-10-06 20:00 Riyadh)

Scope for 1.0.0 (user 06:13): Vu+ Duo 4K SE on OpenATV only. DM900 / other devices are out of the current release.

| Item | Value |
|---|---|
| Last build | **rc10 = build87 published** (SHA256 d90ea535…ee86387c), installed on Slot 8 (t86_rc10 / t77_rc10) |
| Receiver | Slot 8 (linuxrootfs8), rc10 installed, Classic navy, posters ON, cache pinned to USB dev cache |
| Queue on ai-agent | empty |

## Task list to the final RC (user report 06:13)
| # | Task | Status |
|---|---|---|
| 1 | Static audit of placeholders / picon pairs (`tools/mla/audit_np.py`) | DONE: build77 had 11 + 6 screens with placeholders → build79: 0 |
| 2 | t85 picon pairs + Classic No Poster grabs, five models; t85b named EventView | DONE: one picon per place, no placeholder, 0 errors |
| 3 | SecondInfoBarECM (only with show_second_infobar=ECM) | build79: no placeholder (underlay). Moving its text into the poster area needs Python resizing of named widgets → user decision |
| 4 | Named EventView screens when the poster fails | DONE in build78/79 (placeholder removed, underlay, frames follow the real poster) |
| 5 | rc8 (build79) + t77 install test | DONE, published |
| 6 | t86 package lifecycle | DONE on rc8 (run 1: harness fault in step 4, /tmp cleared by reboot, repaired; rc8b steps 3-6 pass) |
| 7 | Final QA: 5 models × 6 sections × ON/OFF × 6 themes | DONE on installed rc9 (t68_rc9): 145 grabs, 0 errors |
| 8 | 25-min performance run on rc9 | DONE (t89): RSS flat, 0 errors, 4 accel incl. start-up |
| 9 | Report + video + release files | DONE for rc9 (report republished, video, release/rc rc9) |
| 11 | Opaque information areas on the InfoBar family (user 06:42): infoplate.py; build86 = rc9. Device t87e (build85, 5 models × 6 themes) + t87f (build86 Modern × 6): 0 REAL not-opaque, 0 errors; scrims kept; PVRState black box and Modern SIB band fixed; t88: one Minimal/Purple capture not reproducible (24/24 opaque). Sheets: docs/mla/evidence/opaque_*.jpg | RUNTIME TESTED — visual approval by the user pending |
| 10 | Explicit poster-cache delete option | DONE (`uninstall-mla.sh cache`, CONFIRM=yes; only MLA's id/ and sz*/), tested on /tmp |

## Harness fault 2026-10-06 (fixed)
- Also gone from /tmp after the reboot: `/tmp/cvmla/setcfg.py`. Effect checked: t87 only re-set the movie folder to
  its own value (no change; the receiver has no folder override). Scripts now push setcfg.py themselves.
- The t86 reboot cleared `/tmp/cvmla` on the receiver; `deploy.sh` (set -e) writes there first, so every deploy
  after the reboot aborted silently until 09:00. Affected: the t87 "build81" run (measured build79) and the first
  t87c start. Not affected: t77 rc8 / t86 (package installs), t87a (build79 was installed anyway).
- Fixed: deploy.sh and t87 `op()` create the directory; t87 aborts when the deployed layout md5 differs from the build.

## Observations (not blocking)
- "Kraljica ringa (2024)": negative identity cache (`.none`), the reliable-only policy refused the Croatian
  title. Better coverage of translated titles is a possible later improvement.

## Rules (unchanged)
- Slot 8 and dev/mla-openatv only.
- No main, no HDD writes, no other slots, no Multiboot or tuner changes.
- No final release without the user's approval.

## Waiting for the user (no final release without approval)
- Visual approval: opaque information areas (docs/mla/evidence/opaque_*.jpg, report section), No Poster
  arrangements, PIL poster sharpness, final look of the five models.
- Decisions: installer HDD cache default (HDD_CACHE); dedicated HDD cache test only after the user's OK;
  SecondInfoBarECM (no placeholder now; moving its text needs Python resizing of named widgets).

## User list 2026-10-06 14:31 - all items closed on rc10
1. Minimal/Purple SIB leak: reproduced (t90), fixed (build87 scroll-fill), t90b 0/216, t93 0/75 (rare event; see evidence 15).
2. SecondInfoBarECM: no placeholder / no frame without a poster, five models (t91); no runtime resizing.
3. Poster cache: HDD real mount -> USB -> /tmp in runtime + rc10 installer; t92 dedicated HDD test PASS.
4. Classic No Poster: InfoBar / EPG / EMC / MovieSelection pairs (t91).
5. Picons: one per place under fast zapping (t91).
Final: rc10 built from the tested build87; t86 lifecycle + t77 short QA pass; 1.0.0 review report published.
Waiting: the user's approval for 1.0.0 (no final release / no main without it).

## Decisions 19:25 / 19:54 (final, do not reopen)
- Approved: scrolling-text fill (rc10), SecondInfoBarECM without a poster, Classic PVR/EMC as is (live preview, no poster box).
## Plan (status 19:54)
- Stage A docs/report (no receiver) -> Stage B 1.0.0 package = build87 files, version only; upgrade rc10->1.0.0, reboot,
  quick 5-model check, receiver-captured video -> Stage C release (publish, installer, main) ONLY after explicit approval.

## 2026-10-06 22:00 request - package management screens: DONE (RUNTIME TESTED, build90)
- Root cause / fix / tests: evidence section 18; video docs/mla/evidence/video/CineView_MLA_package_screens_2026-10-06.mp4.
- Final 1.0.0 re-packaged from build90 (commit ac29f6f): agent ~/cineview-mla/final100d, SHA256 8fb44a69...242516,
  installed on Slot 8 (theme black kept); development screen-open tool removed from the receiver.
- NOT published. Stage C (release/rc + installer + main) waits for the user's approval.

## Night 2026-10-06/07 - CineView Designs checklist (docs/mla/CineView_Designs_Checklist.md)
- build92 (b719a97) installed on Slot 8 (package SHA256 b85220f5...ef978); 24 items: 13 PASS, 8 FIXED + re-tested (item 9 both),
  2 DECISIONS (MessageBox fit, Setup value font: build flags, off), Arabic UI not tested (system language).
- Next: the user's two decisions -> (flags on/off) -> final package -> approval -> Stage C (publish, installer, main).

## 2026-10-07 07:25 - CineView Designs round 2 closed on the receiver (build94, 9e68174)
- Items A-G + MessageBox fit + Setup 27 px: implemented and RUNTIME TESTED (checklist round 2 results).
- Package 1.0.0 SHA256 273f9dfb...76eb on Slot 8; theme Black / Classic; devtool removed. NOT published.
- Next: the user's final approval -> Stage C (release/rc ipk + SHA256SUMS + installer -> 1.0.0, merge to main).

## 2026-10-07 08:05 - closing / publication requirements (user)
- Prepared (dev branch, nothing public beyond the dev branch that was already public): product/README.md,
  product/RELEASE_NOTES.md, product/images (real receiver grabs), product/install/cineview-install.sh (Smart Installer),
  product/install/cineview-uninstall.sh.  Placeholders @INSTALLER_URL@ / @UNINSTALLER_URL@ / @PKG_URL@ / @PKG_SHA@ are
  filled when the final repository is chosen.
- Smart Installer RUNTIME TESTED (t103, Slot 8): check-only, same version (verify only), SHA mismatch (stops, nothing
  changed), upgrade 1.0.0~rc10 -> 1.0.0 with restart; no temporary files or installer left; 0 errors.
- Final package candidate (build94 + clean maintainer texts): agent ~/cineview-mla/pkg_final, SHA256 bdae6fca...0775,
  NOT pushed anywhere public.  Repackaged once more after the repository decision (homepage + URLs).
- Waiting for the user: (1) repository: new private habeb-s/CineView-MLA (recommended) or CineView-FHD main;
  (2) compatibility wording (evidence: OpenATV 8.0 only; 7.5 lacks skin features; 7.6 needs its own Python build);
  (3) LICENSE text; (4) final approval -> repo public, Release 1.0.0, tag v1.0.0, main, installer link live.
