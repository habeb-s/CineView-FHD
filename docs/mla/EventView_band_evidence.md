# EventView "blank band" — device evidence (Slot 8, OpenATV 8.0.1 / 57b7a51)

**Status:** ROOT CAUSE IDENTIFIED (for the screenshots) — framebuffer-grab tearing, not a layout/state defect.
On-screen visibility (what a viewer sees on the TV) is **not verified** — needs a human look or a camera.

## Symptom
In some OpenWebif grabs (`/grab?mode=osd`) of the Classic EventView, the top part of a swimming description box
(RunningText `movetype=swimming,direction=top`) is empty while text is visible lower in the box.

## Tests
| Run | Build | What | Result |
|---|---|---|---|
| evfast (20:4x) | build16 | 6 channels x 2 rounds, 8 grabs per EventView + next/back | 4/120 frames flagged |
| evfast (22:19) | build18 (hidden ShowIf variants get empty text) | same | 4/120 frames flagged — the hidden-variant fix did **not** change the rate |
| evtear (22:2x) | build18 | ONE EventView kept open (Cinemax), 40 back-to-back grabs while the description swims | 8 of 80 boxes flagged |

## Why this is grab tearing
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
