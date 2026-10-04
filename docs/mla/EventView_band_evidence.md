# EventView "blank band" — device evidence (Slot 8, OpenATV 8.0.1 / 57b7a51)

**Status (2026-10-04):** OPEN. The partly cleared box is real in the **displayed** framebuffer (2–6 ms while the
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
