# CineView MLA: resume point (updated 2026-10-06 06:45 Riyadh)

Scope for 1.0.0 (user 06:13): Vu+ Duo 4K SE on OpenATV only. DM900 / other devices are out of the current release.

| Item | Value |
|---|---|
| Last build | build79 (placeholder audit: 0 screens); rc7 = build77 is published and installed |
| Receiver | Slot 8, Vu+ Duo 4K SE, OpenATV 8.0.1; rc7 package + build79 deployed by t85 |
| Queue on ai-agent | t85 (build79 picons + placeholders, 5 models) → q85b: t85b (named EventView from the EPG, later event) |

## Task list to the final RC (user report 06:13)
| # | Task | Status |
|---|---|---|
| 1 | Static audit of placeholders / picon pairs (`tools/mla/audit_np.py`) | DONE: build77 had 11 + 6 screens with placeholders → build79: 0 |
| 2 | t85 picon pairs + Classic No Poster grabs, five models; t85b named EventView | RUNNING |
| 3 | SecondInfoBarECM | build79: no placeholder (underlay). Moving its text into the poster area needs Python resizing of named widgets → user decision |
| 4 | Named EventView screens when the poster fails | DONE in build78/79 (placeholder removed, underlay, frames follow the real poster) |
| 5 | rc8 (build79+) + t77 install test | after t85/t85b |
| 6 | t86 package lifecycle (upgrade with GUI running, reboot, uninstall, fresh install, purge, restore) | script ready |
| 7 | Final QA: 5 models × 6 sections × ON/OFF × 6 themes | after rc8 |
| 8 | 25-min performance run on rc8 | after QA |
| 9 | Report + video + release files | last |
| 10 | Explicit poster-cache delete option | DONE (`uninstall-mla.sh cache`, CONFIRM=yes; only MLA's id/ and sz*/), tested on /tmp |

## Observations (not blocking)
- "Kraljica ringa (2024)": negative identity cache (`.none`), the reliable-only policy refused the Croatian
  title. Better coverage of translated titles is a possible later improvement.

## Rules (unchanged)
- Slot 8 and dev/mla-openatv only.
- No main, no HDD writes, no other slots, no Multiboot or tuner changes.
- No final release without the user's approval.
