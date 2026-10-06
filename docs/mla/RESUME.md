# CineView MLA: resume point (updated 2026-10-06 08:25 Riyadh)

Scope for 1.0.0 (user 06:13): Vu+ Duo 4K SE on OpenATV only. DM900 / other devices are out of the current release.

| Item | Value |
|---|---|
| Last build | build81 (opaque info areas, not device-verified yet); **rc8 = build79 published** (SHA256 cd3bfbe5…59bc1), installed on Slot 8 |
| Receiver | Slot 8, Vu+ Duo 4K SE, OpenATV 8.0.1; rc8 installed (t86 + t77), Classic navy |
| Queue on ai-agent | q88: t87a (build79 navy, before) → t87 (build81, 5 models × 6 themes) |

## Task list to the final RC (user report 06:13)
| # | Task | Status |
|---|---|---|
| 1 | Static audit of placeholders / picon pairs (`tools/mla/audit_np.py`) | DONE: build77 had 11 + 6 screens with placeholders → build79: 0 |
| 2 | t85 picon pairs + Classic No Poster grabs, five models; t85b named EventView | DONE: one picon per place, no placeholder, 0 errors |
| 3 | SecondInfoBarECM (only with show_second_infobar=ECM) | build79: no placeholder (underlay). Moving its text into the poster area needs Python resizing of named widgets → user decision |
| 4 | Named EventView screens when the poster fails | DONE in build78/79 (placeholder removed, underlay, frames follow the real poster) |
| 5 | rc8 (build79) + t77 install test | DONE, published |
| 6 | t86 package lifecycle | DONE on rc8 (run 1: harness fault in step 4, /tmp cleared by reboot, repaired; rc8b steps 3-6 pass) |
| 7 | Final QA: 5 models × 6 sections × ON/OFF × 6 themes | after rc8 |
| 8 | 25-min performance run on rc8 | after QA |
| 9 | Report + video + release files | last |
| 11 | Opaque information areas on the InfoBar family (user 06:42): `infoplate.py` + `<token>Solid` theme twins; build81. Static audit 0 non-opaque. Device: t87a (build79 before) → t87 (build81, 5 models × 6 themes, real OSD alpha + red/yellow/white/dark composites) | IMPLEMENTED — NOT RUNTIME VERIFIED (q87 queued) |
| 10 | Explicit poster-cache delete option | DONE (`uninstall-mla.sh cache`, CONFIRM=yes; only MLA's id/ and sz*/), tested on /tmp |

## Observations (not blocking)
- "Kraljica ringa (2024)": negative identity cache (`.none`), the reliable-only policy refused the Croatian
  title. Better coverage of translated titles is a possible later improvement.

## Rules (unchanged)
- Slot 8 and dev/mla-openatv only.
- No main, no HDD writes, no other slots, no Multiboot or tuner changes.
- No final release without the user's approval.
