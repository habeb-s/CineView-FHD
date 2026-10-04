# CineView MLA — autonomous night run (order 2026-10-04 22:06): device evidence

**Receiver:** Vu+ Duo 4K SE · OpenATV 8.0.1 · enigma2 57b7a51 · Python 3.14.7 · Slot 8 (USB) only.
**Branch:** `dev/mla-openatv`. No change to main, HDD, other slots, Multiboot, tuner or CA.
**Builds:** build35 → build41. Every deploy keeps `backup-buildN` on USB.

Status words:
- **RUNTIME TESTED** = exercised on the receiver, with evidence.
- **IMPLEMENTED — NOT RUNTIME VERIFIED** = built and checked statically only.

Evidence files are in `~/cineview-mla/shots/t37 … t48` on ai-agent. The selected images are copied to
`docs/mla/evidence/night_1005/`.

## 1. Graphical Plus (EPG, Details) — RUNTIME TESTED, look pending approval
- **build35 (t37):**
  - Opens in all six themes.
  - The details panel follows the highlighted cell: Bajkeri → Holland → Kaskader.
  - Posters OFF selects `GraphicalEPG_CVPosterOff`: the grid widens from 1290 to 1540 px (about 3 h at the
    user's 180-min setting), with no reserved poster space.
- **SkinError `'date' not found` (build35).** EPGSelection creates `self["date"]` only for some EPG types.
  build36 takes the date from the clock source instead. t40: 0 tracebacks and 0 skin errors in both ON and OFF;
  the header shows "Sun 04 Oct".
- **OFF panel (240 px column).** Justified text left wide gaps, and a 3-line title box left a hole under short
  titles. build36 uses a 2-line title and a left-aligned description.

## 2. IMDb ratings only for reliable identities — RUNTIME TESTED (build36, t40)

| Channel / event | Identity (meta json) | Shown |
|---|---|---|
| HBO "Bajkeri" | no reliable match (The Bikeriders 0.74, no cast confirmation) | no poster, **no rating** (was 4.7 before) |
| HBO 2 "Kaskader" | imdb tt1684562 The Fall Guy 2024, 0.95 | poster + **6.8/10** |
| Cinemax "Misija: Bijela kuća" | imdb tt2334879 White House Down 2013, 0.95 | poster + **6.3/10** |
| HRT1 "Majstori iluzije…(2013.)" | no reliable match (Now You See Me 0.28) | placeholder, no rating |

An independent check of the two shown values against IMDb was not possible: ai-agent and the receiver both
received 403 from IMDb. The values come from the exact tt id.

## 3. Vertical EPG (Columns study) — root cause fixed, RUNTIME TESTED (build37, t42)
- **Symptom (t37).** The screen showed only a numbered channel list.
- **Cause.** The inherited CineView screen draws `self["list"]` at 1730x700, z=19, over the five columns.
  EpgSelection.py uses that MenuList only as the page index. The defect already exists in the golden skin.
- **Fix.** The native contract: receiver `skin_default.xml` ("DO NOT CHANGE THIS LINE") and MetrixHD both use
  zero width, z=-10, and height = itemHeight × (Fields−1).
- **t42.**
  - Five channel columns are visible.
  - RIGHT moves the active column; DOWN moves the event.
  - 0 tracebacks.
- **Columns verdict.** The native vertical EPG works with CineView once the index is hidden. A "Columns" design
  can therefore be built on this native screen (list1..list5, piconCh/currCh/Active) without new widgets.

## 4. EventView opened from an EPG showed two programmes — fixed (build40 → build42), tests t47 / t50
- **Symptom (t42).** INFO in the vertical EPG on HBO 2 "Nevjesta!" showed HBO HD "Holland" titles and times
  together with the "The Bride!" poster.
- **Cause.** `EventViewEPGSelect` uses skinName `["EventView"]`. The Classic `EventView` screen is a
  live-channel dashboard: its texts come from `session.Event_Now/Next/CurrentService`, and only the poster comes
  from `Event`. This is pre-existing.
- **Fix.** The CineView MLA plugin puts the Classic `EventViewSimple` screen in front of `EventView`, plus
  `_CVPosterOff` when posters are OFF. That screen is built on the screen's own `Event`/`Service` sources and
  native widgets. A caller-supplied skinName is kept, and the hook is inactive under other skins.
- **t47 (build40).**
  - Vertical EPG and Graphical EPG on HBO 2 "Opaki Radnik" now show that event: 02:58–04:50, matching
    OpenWebif, with its own poster (A Working Man). Posters OFF selects `EventViewSimple_CVPosterOff`.
  - **Regression found:** the InfoBar's INFO opens the same class (`EventViewEPGSelect`), so live INFO lost the
    approved Classic dashboard.
- **build42.** The dashboard stays when the event is the playing service's CURRENT event; every other event
  (another channel, or a later event of the playing channel) gets the simple screen.
- **t50.**

  | Case | Screen used |
  |---|---|
  | vertical EPG, other channel | `EventViewSimple` |
  | Graphical EPG, other channel | `EventViewSimple` |
  | live INFO | Classic `EventView` dashboard (unchanged) |
  | Graphical EPG, later event on the playing channel ("Nasljednik Green Lanterna" 04:03–05:05) | `EventViewSimple` |
  | posters OFF | `EventViewSimple_CVPosterOff` |

  0 tracebacks. **RUNTIME TESTED.**
- **EPG text.** Some descriptions show garbled letters ("Ïzivio", "kÂcer"). OpenWebif shows exactly the same
  text, so this is the broadcast's encoding as decoded by Enigma2, not CineView.
- **Open, not changed.** Neither Classic screen shows the coloured-key captions (Add Timer / Single EPG /
  Multi EPG). The keys still work.

## 5. EventView "line by line" — defect found and fixed (build39), test t46
- **t39 (build35).**
  - Arabic: 26 and 25 moves, 0 bad.
  - English: 30 moves with 0 bad, then 31 moves with **2 bad**.
- **Bad frames.** At the end of the text, native `swimming` reverses and moves back one line per step. Each
  downward 29-px move left two overlapping lines, or half a box blank, for a whole step: frames 261–269 at 52 s.
  Upward moves were always clean.
- **Fix.** `CineViewMLALineText`, CineView's own RunningText subclass; Enigma2 is untouched. At the end of a
  long text it holds for `pause`, then restarts from the first line with a full redraw. Short texts and all
  other modes behave natively. The continuous Classic motion is unchanged.
- **Measurement.** jumpcheck now also accepts a pixel-exact "restart-to-top".
- **Continuous mode (t39).** swim AR/EN shows smooth 1–5 px steps, with no change.
- **t46 (build39), 3 rounds × AR/EN.**
  - Rounds 1–2: 135 moves, **0 bad**, 10 pixel-exact restarts-to-top.
  - Round 3 English: **2 bad moves in the middle of the text**, both forward (upward) moves. One frame is half
    blank, then two lines stay drawn over each other for 1.6 s.
  - So the wrong paint is not limited to the reverse. eWidget::move() invalidates the old and the new area (the
    desktop is not buffered), so the fault is in the paint itself, inside enigma2 graphics or the driver. The
    cause is not proven.
- **build43 mitigation.** One more full repaint of the label 150 ms after every line move, so a wrong paint
  lasts at most one frame.
- **t51 (build43), 4 rounds × AR/EN.** 8 runs, 290 moves, **0 bad**, 21 pixel-exact restarts-to-top. No
  "repaint unavailable" message, so `invalidate()` works from Python. **RUNTIME TESTED.**
  - Limit of the measurement: jumpcheck ignores single-frame states. A wrong paint corrected within 150 ms would
    not be counted. The requirement, no lasting duplicated or overlapping lines, is what is measured.
- **Measurement.** jumpcheck now also tries 3–4 line shifts: a 4.8-s gap in a recording had hidden several
  steps. Re-scored: t39 (native) 2 bad of 112; t46 rounds 1–2 0 bad of 135.

## 6. Modern model — skin features and InfoBar on the receiver
- **t41 probe** (CineViewMLAFeatureProbe over HRT1, OSD alpha measured):
  - These work: `cornerRadius` on eLabel / Label / ePixmap, `"r;top"`, the translucent card (alpha 204), and the
    gradient scrim with alpha blending (alpha 1 → 203).
  - `borderWidth` on a rounded translucent eLabel is **not drawn**. Modern does not use borders.
- **Modern InfoBar (build38, t43): RUNTIME TESTED, look NOT approved.**
  - Rounded card, pill chips, rounded poster, bold face `CVModernBold` (LiberationSans-Bold), loaded from the
    pack's `<fonts>`.
  - Posters OFF reflows the content to the card's left edge.
  - IMDb is shown only for Kaskader (6.8).
  - Six themes OK.
  - Long Arabic and English titles fit; Arabic is right-aligned.
  - Live values vs OpenWebif: HRT1 72 % / 11.5 dB vs 71 / 11.61; HBO 2 73 % / 11.6 dB vs 73 / 11.65.
  - 0 tracebacks, 0 skin errors.
  - **Open:** the HD and 16:9 chips were missing in 2 of 6 theme runs. Those runs restarted on the same
    channel, so Enigma2 timing is suspected.
  - **t48 (identical sequence, Classic vs Modern).** All samples show HD and 16:9 for both designs. The script's
    loop variable was overwritten by a helper, so only 1 restart sample per design survived. t48b repeats the
    test with 4 restarts per design.

## 7. Performance / memory soak — RUNTIME TESTED (build36, t38)
Poster List, posters ON, 33 navigation rounds (30.6 min, about 33 key presses per round + EventView):

| | start | end / range | note |
|---|---|---|---|
| RSS | 153.6 MB | 154.3–155.1 MB after round 5 | flat |
| threads / fds | 15 / 105 | 15 / 105 | constant |
| poster cache | 224 files | 241 files | only new events |
| CPU per 4 rounds | — | 20.1–21.8 s | no degradation |
| lag (start vs end recording) | p90 0.15 s, max 0.21 s | p90 0.14 s, max 0.16 s | no degradation |
| tracebacks | 0 | 0 | |

Baselines, same 10-min navigation:

| | accelAlloc failed | CPU / round | RSS |
|---|---|---|---|
| Poster List posters ON | ~22 per round | ~5.4 s | 155 MB |
| Poster List posters OFF | 1 (the zap surface, Enigma2) | ~3.9 s | 150 MB |
| Classic posters ON | 1 | ~6.2 s | 152.7 MB |

The per-key-press accel failures come with the **CineView Poster List posters**.
**t45 (gAccel debug, build38, 15 DOWN presses)** shows the mechanism:
- **Per DOWN press:** exactly two allocations, the now poster 240x360 (338 kB) and the next poster 160x240.
- **When the list opens:** a burst of 220x132 surfaces. These are the native picon files of the visible rows,
  and Enigma2's service list keeps them: 23 surfaces, **2.6 MB of the 5.4 MB pool**.
- **At zap:** the InfoBar / SecondInfoBar posters (105x158, 205x308). They are not re-decoded per key press.
- **At the failures:** the largest free block was 26–150 kB, so a 338 kB poster or a 118 kB picon finds no
  contiguous space, and gSurface falls back to RAM by design.
- **Failures in t45:** 11 picons, 4 now posters, 2 SIB posters, 1 zap surface (1536x1024, Enigma2).

**Verdict.** This is pool pressure: Enigma2's picon cache plus CineView's two posters. It is not a leak. Every
poster is freed on the next move, and the soak shows no RSS growth. The RAM fallback has no visible artefact,
and CPU per round is lower than Classic's.

**Decision.** No code change. Shrinking the posters further would change the approved look. Open for the user's
review.

## 8. Stale posters
- The evening result (0 stale at 0.35 s and 0.15 s, valid slow reference) stands.
- t38's postercheck numbers are **void**. They used a fast recording as the reference, and on the uncached page
  both rows showed the same placeholder. A visual check of the flagged frames shows the panel switching with the
  cursor.
- **t44 (build38).** CineView's own runtime.json pointed at a new empty cache directory; slow reference over the
  same rows; runtime.json restored afterwards.
  - **Page 1, HBO movie rows, 0.35 s, cold downloads: 0 stale.** 6 frames show the previous poster within
    0.5 s of a move, which is the allowed transition.
  - **Page 2 at 0.15 s** turned out to be kids channels: all series without a reliable identity, so every row
    shows the same placeholder. The 14 flagged frames are the identical-placeholder artefact; visually the panel
    follows the cursor.
  - **t49 (build41), movie rows, 0.15 s, fresh empty cache.** 18 identity lookups and 8 posters downloaded
    during the run.
- **postercheck corrected, and its sensitivity proven.**
  - **One-frame cursor misreads** (row 9 → 10 → 9 within 0.14 s) split a row into fake segments. They are now
    merged.
  - **The neutral placeholder** shown while a poster loads, or when no reliable poster exists, no longer counts as
    "the previous channel's poster". Only a real poster of another channel is stale.
  - **Planted test.** A real previous-channel poster pasted into the t44 recording is detected (stale 0 → 1).
- **Result, all valid runs: 0 stale.**

  | Run | Cache | Speed | Stale |
  |---|---|---|---|
  | t44 | cold | 0.35 s | 0 |
  | t44 | cold (placeholder page) | 0.15 s | 0 |
  | t49 | cold, real downloads | 0.15 s | 0 |
  | t34 | cached | 0.35 s | 0 |
  | t34 | cached | 0.15 s | 0 |

  The previous poster is visible only during the < 0.5 s transition (3–7 frames per run).
- **Not testable within the bounds.** A slow network: simulating it would mean changing the receiver's network
  settings, which is not allowed. Downloads that finished after the cursor had moved on were exercised
  naturally in t44/t49.

## 9. Other fixes
- **Poster log.** It was one endless line, because the golden `_log` wrote a literal backslash-n.
  build41 writes one entry per line.
- **Mockups.**
  - The Modern/Minimal mockups now pair a real HRT1 frame with the same programme's EPG and the receiver's
    tuner values.
  - Ratings, genre and duration come only from data; there are no placeholder numbers.

## Test-harness slips (corrected, no effect on the receiver)
- **Done markers.** Three scripts derived by renaming kept the old done marker, which stalled the queue for
  about 25 min. The markers were appended by hand; the scripts are fixed in the repo.
- **t48.** The loop variable was overwritten by a p6lib helper. t48b repeats the run.
