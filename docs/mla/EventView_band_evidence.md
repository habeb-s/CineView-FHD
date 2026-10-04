# EventView "blank band" — device evidence (Slot 8, OpenATV 8.0.1 / 57b7a51)

**Status (2026-10-04 12:30):** OPEN — a complete prevention is not possible in the skin on this image; a ~95 %
reduction exists (line jumps, V3 below) but it changes the approved Classic motion, so it is NOT in any release
and waits for your decision.  See "Prevention study" at the end.

**Earlier status (2026-10-04 morning):** OPEN. The partly cleared box is real in the **displayed** framebuffer (2–6 ms while the
text swims, measured on the receiver — see the update at the end); it is not created by the grab tool.  Whether a
viewer perceives it on the TV is not verified.  The 2026-10-03 reading below ("grab tearing") is superseded.

## Symptom
In some OpenWebif grabs (`/grab?mode=osd`) of the Classic EventView, the top part of a swimming description box
(RunningText `movetype=swimming,direction=top`) is empty while text is visible lower in the box.

## Tests
| Run | Build | What | Result |
|---|---|---|---|
| evfast (20:4x) | build16 | 6 channels x 2 rounds, 8 grabs per EventView + next/back | 4/120 frames flagged |
| evfast (22:19) | build18 (hidden ShowIf variants get empty text) | same | 4/120 frames flagged — the hidden-variant fix did **not** change the rate |
| evtear (22:2x) | build18 | ONE EventView kept open (Cinemax), 40 back-to-back grabs while the description swims | 8 of 80 boxes flagged |

## 2026-10-03 reading (superseded by the 2026-10-04 measurement)
- evtear, right box, first visible text row per frame (px below the box top):
  `93, 61, 0, 0, 55, 0, 8, 0, 0, 0, 42, 0, 0, 3, 236, 0, 4, 0, 0, 5, 0, 0, 6, 31, 0, 82, 0, …, 88, …, 146, 0`
  — the box flips between "normal" and "band" from one grab to the next (well under a second) and the band
  height is random. A layout or renderer-state defect would persist between consecutive frames.
- Lines that ARE visible in a banded frame sit exactly where the previous full frame had them (e.g. r1_c4 f6->f7:
  line 5 at y≈100 in both), i.e. the content did not move; only the upper part was not (yet) painted.
- The blank part is always the TOP of the box and text the bottom: the grab reads the framebuffer top-down while
  the swimming label repaints its box every 60 ms (clear + draw).  Static widgets never show the effect.
- It happens with the Classic packs too and independently of the ShowIf variants.

## Consequences
- The evband/evfast detector is not a valid acceptance test for swimming text; screenshots of moving text can
  show partial repaints.  QA screenshots of swimming boxes are taken before `startdelay` or judged on several frames.
- No code change is made for this.  If a viewer ever sees a flicker on the TV itself, the mitigation is a larger
  `steptime` (fewer repaints) for EventView descriptions — not applied, Classic is approved as it is.

## Update 2026-10-04 04:40–04:55 — is the band on the screen or only in the screenshots?
**Rendering path (source + device):**
- enigma2 57b7a51 `main/enigma.cpp`: the buffered composition mode is commented out → `cmImmediate`: widgets paint
  directly into the framebuffer page that is being displayed. The device log shows `double buffering available`,
  `pages: 2`, but without buffered composition nothing is flipped; `/sys/class/graphics/fb0/pan` stayed `0,0`.
- `aio-grab` (`getosd`) reads the page at the displayed `yoffset` — i.e. exactly what the HDMI output scans out.
  A raw `dd` of `/dev/fb0` and an OpenWebif grab taken a moment apart are identical (04:44).
- So a box that is partly cleared in a grab was partly cleared **in the displayed framebuffer**; the grab does not
  create the band, it only catches it.

**Measurement (`fbprobe.py`, on the receiver, reads the displayed page every 0.15–0.6 ms, top third of the box):**
| Screen / box | time | blank moments (top third ≈ 0 text) | duration avg / max |
|---|---|---|---|
| EventView Cinemax, right description swimming | 25 s | 30 | 2.6 / 6.0 ms |
| EventView Cinemax, left description swimming | 25 s | 23 | 1.9 / 2.9 ms |
| EventView HBO, right description swimming | 25 s | 6 | 2.4 / 2.7 ms |
| EventView HBO, left description (fits, static) | 25 s | 0 | — |
| Test screen: static Label | 20 s | 0 | — |
| Test screen: same text, continuous swim (transparent) | 20 s | 1 | 1.9 ms |
| Test screen: line jumps (step = 1 line, 1.8 s) | 20 s | 1 | 1.4 ms |
| Test screen: continuous swim, opaque background | 20 s | 1 | 1.4 ms |

**Conclusion:** the blank state is real in the displayed framebuffer (2–6 ms, up to ~1.2 times/s on EventView,
only while text swims; never on static text).  At 60 Hz a 2–6 ms blank overlaps the scan-out of that box in roughly
one of four or five cases, so it can reach the TV as a one-frame flicker of the text.  Whether it is perceptible
cannot be decided without watching the TV → **status: OPEN (not resolved)**.  The EventView screen produces far
more blank moments than an isolated test box with the same text, so the extra repaints come from the EventView
screen itself (other widgets/poster repaints overlapping the transparent text boxes); not pursued further without a
visual confirmation, and no change was made to the approved Classic EventView.

## Prevention study 2026-10-04 12:10–12:28 (`evstudy.sh`, build25 / 1.0.0~rc4 dev, nothing shipped)
**Why the skin cannot remove it completely:** in 57b7a51 the buffered composition mode is disabled in the source
(`cmImmediate`), so every repaint of a RunningText box first fills the box with its background and then draws the
text — directly in the displayed page.  The 2–6 ms between the two steps is the blank.  No skin attribute and no
Python renderer can make that repaint atomic; only fewer repaints (or none) reduce how often it is visible.

**Method:** each variant is a temporary layout pack `layouts/eventview/evexpN` (copy of the installed Classic pack;
only the `options` of the 8 EventView description widgets changed), applied with the composer, measured, then
factory restored and the packs deleted.  Per channel: `fbprobe.py` on the right and left description (25 s each,
displayed framebuffer, top third of the box), enigma2 CPU over 20 s without the probe, tracebacks, crash logs.

| Variant | Description options | Cinemax right dips (avg/max ms) | Cinemax left dips | CPU enigma2, Cinemax (swimming) | HBO (text fits, static) |
|---|---|---|---|---|---|
| V0 baseline (Classic) | `step=1,steptime=60` continuous swim | 26 (4.2/5.9) | 42 (2.8/5.9) | 28.3 % | 0 / 2 dips; CPU 8.5 % |
| V1 posters OFF (EventView) | same | 21 (4.1/6.1) | 29 (2.6/4.5) | 32.5 % | 0 / 0; 11.5 % |
| V2 half the repaints | `step=1,steptime=120` (half speed) | 16 (4.6/6.0) | 28 (2.5/3.2) | 27.6 % | 0 / 0; 11.8 % |
| V3 line jumps | `step=29,steptime=1740` (one whole line every 1.74 s = same reading speed 16.7 px/s) | **2** (4.4/5.4) | **1** (8.7/8.7) | 21.1 % | 0 / 0; 11.7 % |

0 tracebacks, no crash, enigma2 PID unchanged within every variant.  Screenshots: `evidence/evstudy/`.

**Findings**
- V1: switching the EventView posters off does not remove the dips → the poster renderer is not the source.
- V2: half the repaints removes only about a third of the dips; continuous swimming stays visible.
- V3: ~95 % fewer blank moments, ~7 points less CPU, whole lines stay aligned (line pitch 29 px for size 25);
  the remaining dips (1–2 per 25 s) are the repaint at each jump.  It is a **different motion**: the text moves one
  line at a time instead of gliding.
- Static text never blanks.  Long descriptions that swim also cost ~20 % of one CPU core (28 % vs 8–12 %).

**Decision (per your instruction):** no experimental change enters a release.  The approved Classic EventView stays
as it is in rc4.  Options for you: (a) keep it and accept the rare one-frame flicker; (b) approve V3 line jumps
for EventView descriptions (and, if you want, the other Classic descriptions); (c) evaluate V3 on the TV first —
I can install it as a temporary dev pack on Slot 8 so you can see it on the screen.

## Line-by-line trial — doubled Arabic line (user report 2026-10-04 17:01, video 0:29–0:31)
**Frame-by-frame (recording `evidence/evlines`, lines_ar_now, frames #46–#73, 10 fps of the DISPLAYED framebuffer):**
- #49 (t=4.9 s): the jump repaint caught half-way (lower half still empty).
- #50–#66 (t=5.0–6.6 s, 17 identical frames = the whole 1.7 s pause): one text line (box rows 126–138)
  shows two different lines drawn on top of each other; the line above shows stray marks.  #67 (next jump):
  clean again.  Identical in 17 consecutive frames → **it was on the screen, not a recording artefact.**
- Classic continuous scrolling in the same recording: no doubled lines (its known defect is the short blank band).
- Mechanism: the description label is transparent; after a 29 px move the region is repainted as
  "panel background, then text".  In this one jump a band of the box got the new text without the background
  being redrawn first, so the old glyphs stayed under the new ones until the next move.

**Fix (in build28, pack `classic-lines`):** the 8 EventView description labels are no longer transparent; they
paint `steSecondInfoBG` themselves — the same ARGB value as the panel they sit on, so the look is unchanged
(TV/OSD composition identical) — and every repaint of the label overwrites its whole box.  A stale line can then
only survive if the label itself is not repainted, which is not what happens on a move.

**Measurements (pixel-exact check of every move, `jumpcheck.py`: the settled frame must equal the previous settled
frame shifted by whole lines):**
| Run (TextTest2, 60 s each, 5 fps) | moves | doubled/stale lines |
|---|---|---|
| first recording, transparent, Arabic (the reported case) | 8 | **1** |
| A transparent: Arabic + English, two runs | 112 | 0 |
| B opaque: Arabic + English, two runs | 111 | 0 (one 4 s recorder stall flagged and checked by eye: clean) |
The defect is rare (1 in ~120 moves with the transparent label); 0 in 111 with the opaque label proves nothing
statistically on its own — the fix is the mechanism above.  A further real-EventView check (live events, posters)
runs with build28 (`t28.sh`).  Old continuous scrolling stays available: EventView «CineView Classic» (factory)
and «CineView Classic (line by line)» are two packs in CineView Designs.
