# CineView Designs — checklist (night 2026-10-06/07)

Receiver: Vu+ Duo 4K SE, OpenATV 8.0.1 (enigma2 57b7a51), Slot 8, theme "black" (the user's choice).
Branch `dev/mla-openatv`. No checklist text with this title was found in the conversation, attachments or the
Project; this list is built from the Blueprint §2.7 (control UI), the earlier P6/P8 UI tests and the user's general
rules (keys only with a function, no empty areas, no clipped text, readable on a TV, nothing breaks native keys).

Status words: **PASS** = exercised on the receiver and correct; **FIXED** = defect found, fixed, re-tested on the
receiver; **DECISION** = works, a visual choice is waiting for the user (evidence prepared); **NOT TESTED** + reason.

| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | Opens from the plugin entry (plugin `main()`), title "CineView Designs", 17 rows, status lines (generation, version/build/commit, rights) | PASS | t98 D1 |
| 2 | Row values readable | **FIXED** — values were drawn at the image default (~18 px); CineView Designs now has its own list with value font 27 px | t98 p1 vs p1b |
| 3 | No half-drawn row at the bottom of the list | **FIXED** — list 832 px = 13 whole rows of 64 (was 855: a cut 14th row) | t98 p1 vs p1b |
| 4 | Every row has a useful description | **FIXED** — theme (was empty), Server/CAM, Second InfoBar mode/timeout (were "This option has no visual preview." only); layouts now also say how GREEN applies | t98 rows_*.txt |
| 5 | Long values fit | **FIXED** — poster engine "Unified (verified match)" / "Legacy (title search)"; details stay in the description | t98 p1b |
| 6 | Preview image for every design | **FIXED** — EventView "Classic (line by line)" had none ("No preview"); it now uses the Classic EventView still (same layout) | build92 log, t99 |
| 7 | YELLOW / OK Preview only where it does something | **FIXED** — the Preview key is shown only on rows with a preview; on other rows nothing opens (was an empty 960×520 message box) | t98 p1b, t99 |
| 8 | Full-screen preview opens / closes (EXIT) | PASS | t98 D3 |
| 9 | MENU: profiles menu, design models list (titles "CineView Designs" instead of "Choice Box") | PASS / **FIXED** (title) | t98 D4, t99 |
| 10 | Model "Details" fills the six sections, RED applies nothing | PASS | t98b E4 |
| 11 | Profile save (virtual keyboard) / load (RED: nothing applied) / delete (confirm) | PASS — JSON written atomically, deleted after the test | t98b E3 |
| 12 | Poster switch saved with GREEN, no restart; back to Yes | PASS (settings line written / removed) | t98b E1 |
| 13 | Second InfoBar timeout saved with GREEN (20 s → No timeout → 20 s) | PASS | t98b E2 |
| 14 | BLUE factory question, default No → nothing changes | PASS (the factory action itself was verified in P8 and its code is unchanged) | t98b E5 |
| 15 | Trial declined → automatic revert to the previous design, GUI restart | PASS (burgundy → black) | t98b E6, history.log |
| 16 | Trial kept → committed (lkg); original theme restored the same way | PASS | t98b E7 |
| 17 | Trial question text | **FIXED** — no internal generation id ("Design g000034 prepared") | t99 |
| 18 | RED cancel leaves everything unchanged | PASS (selection.json md5) | t98 D5 |
| 19 | 0 tracebacks / 0 skin errors / 0 crash logs in every run | PASS | all logs |
| 20 | Settings file after the tests = backup (except counters) | PASS | diff in t98b log |
| 21 | Message boxes of CineView Designs are fixed 960×520 boxes (one line of text in a large empty box) | **DECISION** — experiment `MLA_MSGBOX_FIT=1` sizes the CineView MessageBox to its text and answers; it changes every message box of the skin, so it is off until approved | t99 fit vs base |
| 22 | Values of all other Setup pages also ~18 px | **DECISION** — experiment `MLA_SETUP_VALUEFONT=1` (27 px in the shared ConfigTemplate); changes every Setup page | t99 fitfont |
| 23 | CineView Designs / Processing / MessageBox in the six themes (navy, black, graphite, purple, burgundy, green; engine apply + restart each) | PASS — same layout and readable text in all six; original selection restored | t100, evidence/designs/themes_*.jpg |
| 24 | Arabic UI language | NOT TESTED — changing the system language is a user setting; CineView Designs strings are English gettext ids (no Arabic catalogue in the package) |  |

## Observation (not changed, for the user)
- Burgundy theme: the red "Cancel" key text of the shared colour-key template has low contrast on the burgundy key
  bar (themes_designs.jpg). It is the same template on every Setup page; a change would be a theme-wide decision.

## Decisions waiting for the user (evidence: docs/mla/evidence/designs/decision_*.jpg, video)
1. **MessageBox fitted to its text** (`MLA_MSGBOX_FIT=1`): every message box of the skin becomes as tall as its text +
   answers (same width, same colours, centred). Device: info / yes-no / 9-line error / 4-answer list, 0 errors.
2. **Value font 27 px on every Setup page** (`MLA_SETUP_VALUEFONT=1`, shared ConfigTemplate). Device: OSD Settings, 0 errors.
Both are off in build92; switching one on = one build flag, then the package is rebuilt and the screens re-checked.

## Builds
- build91 (c3e1eba): first CineView Designs fixes - t98 p1b + t98b.
- build92 (b719a97): + EventView line-by-line preview, trial question text. Package 1.0.0 SHA256
  `b85220f59614a4287336560eec5091cb69dd4d7f55c96cd9f3608a2bac8ef978`, installed on Slot 8, theme black, devtool removed.
- build92x / build92y: experiments only (installed for the captures, then build92 installed again).

## Receiver state at the end (00:04)
1.0.0 build92 installed (`version.json` build92 / b719a97), active = lkg = g000047, theme black, every section Classic
(EventView line by line), journal COMMITTED, 0 tracebacks, 0 skin errors, 0 crash logs, development tool removed.
Backups: /media/usb/cineview-mla/state/backup-t98-20261006-231320, -232105, backup-t98b-20261006-232347.

---

# Round 2 — user review 2026-10-07 05:36 (decisions + open items A–G)

Decisions: **MessageBox fitted to its content — approved** (now default, min 180 / max 900 px; text taller than the room
under the maximum is cut at the bottom as the fixed box always did — MessageBox text is a plain Label in 57b7a51, there
is no native scrolling for it). **Setup value font 27 px — approved** (now default, shared ConfigTemplate).

| # | Item (user) | Change | Result |
|---|---|---|---|
| A | No development details on screen | status: "CineView MLA 1.0.0 / Design: <model or Custom>   Theme: <label> / Design & Development by habeb-s © 2026"; generation, last known good, build, commit only in the log ("[CineViewMLA] CineView Designs: active …") and version.json | t102 |
| B | "Apply (trial)" | GREEN "Apply Design"; question "Apply <Design> design with <Theme> theme?"; keep prompt "Keep the <Design> design with <Theme> theme? …"; no "trial", no g000xx anywhere on screen (trial / revert unchanged inside) | t102 |
| C | Preview / Info Card | rows without a visual preview show a CineView Info Card (icon, option name, short explanation, current value, restart or not); the "no image" placeholder is gone | t102 |
| D | EventView previews | every EventView design (Classic, line by line, Details Card, Feature, Modern, Minimal) has a real receiver picture | t101 |
| E | Posters On/Off | Posters rows show the selected design's section with posters ON and OFF side by side (real grabs); Classic PVR has no poster area (approved) → Info Card | t101 |
| F | Factory | BLUE "Restore Factory Design"; "Restores Classic + Navy and the default CineView layout settings." | t102 |
| G | Burgundy Cancel contrast | burgundy only: red key text #FF8585 (≈7:1 on the burgundy key bar) | t102 themes |
| + | Real previews for every design | found during the review: 19 of 32 design previews were a placeholder icon or a drawn mock-up, and the theme previews were colour swatches; all are now real receiver grabs (t101, t101b) | build log "without a preview: none" |
