# CineView MLA: resume point (updated 2026-10-06 11:30 Riyadh)

Scope for 1.0.0 (user 06:13): Vu+ Duo 4K SE on OpenATV only. DM900 / other devices are out of the current release.

| Item | Value |
|---|---|
| Last build | **rc9 = build86 published** (SHA256 0d2336da…8ee8946, raw-verified, DRYRUN ok); installed on Slot 8 by t77 rc9 |
| Receiver | Slot 8, Vu+ Duo 4K SE, OpenATV 8.0.1; rc9 installed (t77 rc9: upgrade rc8→rc9 + five models, 0 errors), Classic navy |
| Queue on ai-agent | q94: t89 (25-min Modern on rc9, started 12:57) → report_rc9.html |

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
| 8 | 25-min performance run on rc9 | after QA |
| 9 | Report + video + release files | last |
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
