# CineView FHD — Handoff to Claude

## Mission
Take over CineView FHD as an evidence-driven Enigma2 engineering project. The goal is not to make XML/code look valid; the goal is to make the real target Enigma2 system demonstrably behave correctly without damaging unrelated functionality.

## Repository
Canonical remote configured in this checkout: habeb-s/CineView-FHD on GitHub. Main branch is the working release branch at handoff time.

## Current supported families
The repository contains work for OpenATV, OpenViX and OpenBH. Treat each image as a separate native contract. Never assume a screen definition or Python component is portable merely because it has the same visible purpose.

## Known project requirements
- Maintain the accepted CineView FHD visual identity across supported images while honoring each image's native contracts.
- Full-screen/FHD treatment is required for project screens intentionally unified, including EPG and relevant settings/plugin pages.
- Main InfoBar must not be changed when already correct.
- SecondInfoBar must remain a distinct current/next design.
- Poster/EPG integration and poster frame are part of the design.
- Plugin lists and skin/settings pages must not regress to small/non-FHD layouts; required colored actions must remain visible/functioning.
- OpenBH EMC/PVR must retain native OpenBH behavior unless a specific enhancement is required.
- OpenBH compatibility floor is 5.6. OpenViX policy includes 6/7 and newer subject to verified runtime compatibility.
- Poster cache should use persistent HDD storage when available (/media/hdd/poster) and /tmp only as fallback; never delete unrelated HDD data.

## Critical engineering warning
There has been recent active debugging around OpenATV/OpenBH layouts and live receiver behavior. Do NOT infer that every file or historical snapshot is currently correct. Establish a fresh baseline from the target device before modifying production.

## Repository landmarks
- snapshots/: historical/finalized image-specific captures and engineering notes; references, not universal truth.
- installer/: compatibility/install-time helpers.
- tools/: validation and targeted engineering utilities.
- packages/: release/hotfix package material.
- dist/: locally generated packages may be untracked; inspect before using.
- lab/: experimental/live-fix material may be untracked and must never be promoted without review and real validation.
- updater/: CineView updater plugin work.

## First-session procedure for Claude
1. Read CLAUDE.md completely.
2. Run git status, inspect recent commits and identify untracked lab/dist material. Do not delete it.
3. Read current README and relevant snapshot notes.
4. Determine the exact requested target image/device before changing code.
5. Inspect the target's native Python/XML contracts and current live CineView files.
6. Create a read-only baseline report before editing.
7. Back up exact production files before any write.
8. Make only evidence-supported changes.
9. Perform real Enigma2 runtime + visual + functional + regression validation before claiming completion.

## Do not do
- No speculative bulk XML rewrites.
- No blind cross-image copying.
- No editing satellites.xml or tuner/service databases for a skin defect.
- No fake/mock acceptance claims.
- No destructive cleanup of lab/history/backups without explicit approval.
- No changing approved CineView design merely to fit a convenient implementation.

## Reporting format
For each completed engineering task report: Environment; Requirement; Root Cause; Changed files/components; Technical rationale; Static validation; Runtime/device evidence; Visual evidence; Regression checks; Remaining unknowns; Completion state.
