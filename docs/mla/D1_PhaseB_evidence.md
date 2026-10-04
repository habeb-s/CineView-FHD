# D1 Channel Selection + Phase B (Classic posters off) + EventView line by line — device evidence

Slot 8, OpenATV 8.0.1 (enigma2 57b7a51, Python 3.14.7), Vu+ Duo 4K SE, 16.0°E only.  Branch `dev/mla-openatv`.
Nothing here is released; main is untouched.  Every deploy backed up to `/media/usb/cineview-mla/state/backup-<build>`.

## 0. t28 / t29 are void
Two copies of `t28.sh` ran at the same time (two queue chains were started).  Key presses, restarts, grabs and
recordings of both runs were interleaved — that explains the corrupt PNGs, the wrong screens (EMC opened instead of
MovieSelection) and part of the log noise.  All t28/t29 results are discarded; t30–t32 run under `flock`.

## 1. Root cause found: background panels covered the text (inherited from the golden CineView FHD)
**Symptom (t30, build29, posters ON and OFF):** Multi EPG had no header, tabs, description or button labels; QuickEPG
showed an empty panel; InfoBarEventView and EventViewSimple showed only the empty box; SecondInfoBarECM had no
bottom row (picon, name, colour labels).

**Mechanism (source of 57b7a51 + device):**
- `Screen.createGUIScreen()` creates renderers and named widgets first and the plain skin `<eLabel>`s
  (`additionalWidgets`) last.
- `eWidget::insertIntoParent()` inserts a child after every sibling with `z <= own z`.  With equal zPosition, the
  element created later is drawn on top.
- So an opaque background `<eLabel ... zPosition="0">` covers every widget with zPosition 0.

**Scope:** a static check (`tools/mla/zorder_check.py`) on the build found 120 covered widgets in 18 screens:
EPGSelectionMulti, QuickEPG, GraphicalInfoBarEPG, GraphicalEPGPIG, EPGvertical, EPGverticalPIG, EventViewSimple,
InfoBarEventView (+ their `_CVPosterOff` twins), and SecondInfoBarECM (Classic, Details, Cinema).  The golden
`CineView_FHD/skin.xml` has the same pattern, so this defect exists in the released CineView FHD too.  Screens with
no hits (InfoBar, SecondInfoBar, EventView, ChannelSelection, EPGSelection, GraphicalEPG) match the screens that
always rendered correctly.

**Fix (build30, commit 1c9d0eb):**
- The background eLabel of each affected screen goes to `zPosition="-1"`, the pattern of enigma2's own
  `skin_default.xml`.
- Geometry and colours are unchanged; only layout packs are changed; no enigma2 file is modified.
- After the fix: `ZORDER_SUMMARY covered=0`.

**Revealed by the fix (build31, commit f253c77):** in Multi EPG (posters ON) the description box lay under the
poster.  Posters ON now puts the description under the poster (1210,540 555×175); posters OFF keeps the full column.
`zorder_check.py --posters` finds no other text under a visible poster.

**Still in core (not changed, needs your decision — approved screens):**
- PluginBrowser / PluginBrowserList / PluginBrowserGrid: MENU and HELP key labels are covered.
- QuickMenu, PackageAction: HELP is covered.
- **PackageActionLog: the log text itself is covered.**

## 2. Phase B — the remaining Classic screens with posters OFF (t31 build30, t32 build31)
Opened through their native entry points by a dev-only trigger plugin, `tools/mla/devtools/CineViewMLAScreenOpen`.
It was installed in Slot 8 only and removed after each run.

| Screen | How it was opened | Result |
|---|---|---|
| Multi EPG | `InfoBar.openMultiServiceEPG()` | |
| QuickEPG | `openInfoBarEPG()` with `infobar_type_mode = "single"` in memory only (restored, not saved) | |
| InfoBar EPG | `openInfoBarEPG()` | |
| InfoBarEventView | INFO key in InfoBar EPG (native `getEventViewInstance`) | |
| EventViewSimple | `EventViewSimple(event, ServiceReference)` — the same call as MovieSelection INFO. EMC replaces MovieSelection on the PVR key on this receiver. | |
| SecondInfoBarECM | `show_second_infobar=3` temporarily (restored to 2), OK OK | |

Results (each screen tested with posters OFF and ON):
- All six screens render with their text after the fix.
- With posters OFF, every screen widens into the poster area.
- The three named-widget screens are served by `<name>_CVPosterOff`. The log shows "Processing screen
  'EventViewSimple_CVPosterOff'", "'InfoBarEventView_CVPosterOff'" and "'SecondInfoBarECM_CVPosterOff'".
- Regression grabs (posters on and off): InfoBar, SecondInfoBar, EventView and ChannelSelection are unchanged.
- 0 tracebacks, 0 new skin errors and 0 crash logs in every enigma2 start.

`[gSurface] ERROR: accelAlloc failed` is present since at least 12:17 today (21 per start with posters on, 1 with
posters off).  In `gpixmap.cpp` a failed accel allocation falls back to normal memory (`data = new unsigned char[]`),
so nothing is lost on screen.  The count grows with poster use within one session; this is a performance item to
study, not a display defect.

## 3. EventView "line by line" on real events (t30, build29, pack classic-lines)
- Setup: displayed-framebuffer recordings of the two description boxes, 5 fps, checked with `jumpcheck.py`.
- Channels: Cinemax, HBO, HBO2, HRT1.
- **58 line moves, 0 doubled/stale lines.**
- Real-use recordings (video+OSD): line by line and Classic continuous, about 6 fps, 30 s each.

## 4. Channel Selection — Poster List / Video First (list left / list right), posters ON and OFF (t30b)
Navigation in every recording:
- open the list;
- 5 steps down, 2.5 s apart;
- 4 fast steps up, 0.8 s apart;
- exit.

Each recording is ~37 s at 6.5–7.0 fps.

| Recording | frames | info panel after a cursor move (`lagcheck.py`) |
|---|---|---|
| Poster List, posters ON | 259 | 10 navigation moves: 0.15–0.18 s = one capture step (median 0.16 s) |
| Poster List, posters OFF | 259 | median 0.14 s, p90 0.17 s |
| Video First (left), ON / OFF | 243 / 240 | median 0.00 s, p90 0.16 / 0.15 s (cursor detection noisier: transparent list over video) |
| Video First (right), ON / OFF | 248 / 239 | median 0.00 s, p90 0.28 / 0.15 s (same caveat) |

- The panel follows the highlighted channel in every recording: picon, name, now and next, times and description.
  Contact sheets were checked by eye (e.g. 146 HBO → 147 HBO 2 → 148 HBO 3 → … → back up).
- Posters: a cached poster appears immediately. A missing one shows the neutral frame and fills in later
  (e.g. "Supergirl" next poster on HBO 2 after ~20 s).
- With posters OFF, the detail panel and the video card reflow into the poster space.

**Open D1 issue:** in the narrow Video First list a very long service name ("CineStar TV Action and Thriller HD")
overlaps the progress bar.  `ServiceList.py` sizes the name cell to exclude the bar, so the overrun happens in the
native C++ list drawing.  Not yet investigated.

## 5. Status
| Item | State |
|---|---|
| Z-order fix (18 screens) | RUNTIME TESTED (t31/t32 grabs) — awaiting your visual approval |
| Multi EPG description vs poster | RUNTIME TESTED (t32) |
| Phase B posters OFF, remaining screens | RUNTIME TESTED |
| EventView line by line (classic-lines pack) | RUNTIME TESTED on real events, 0/58 stale lines; old continuous motion stays the factory pack |
| D1 Poster List / Video First L/R | RUNTIME TESTED, posters on/off, panel follows cursor; open: long-name overlap in narrow list |
| Core screens with covered labels (PluginBrowser*, QuickMenu, PackageAction*) | ROOT CAUSE IDENTIFIED — not changed |

## 6. Evening fixes (user requests 2026-10-04 20:12) — t34 (build33), t35/t36 (build34)
Evidence: `evidence/evening_fixes/` (stills, logs, postercheck output, EPG mockups). Review page: "CineView MLA إصلاحات المساء".

| Item | Result | State |
|---|---|---|
| Long service names (narrow list) | Root cause in `listboxservice.cpp`: the name is laid out with the cell width and then moved right by the picon (`xoffs += iconWidth + itemsDistances`). The CineView MLA plugin wraps `ServiceListLegacy.setMode` and narrows the name cell by that offset (D1 designs only; no enigma2 file touched). Log: `name cell 413 -> 337 px (picon offset 76)`. The t34 run failed with an ImportError (`getTextBoundarySize` lives in `Tools.TextBoundary`), fixed in build34. | RUNTIME TESTED |
| Poster List background | Both panels `steThemePanel` (opaque, same hue as the old translucent overlay) | RUNTIME TESTED |
| Fast navigation posters | `postercheck.py` segment method: 0.35 s steps (215 frames) and 0.15 s steps (143 frames): stale = 0; previous channel's posters only within the first 0.5 s after a move (11 / 6 frames = repaint) | RUNTIME TESTED |
| Core z-order (approved: PluginBrowser*, QuickMenu, PackageAction, PackageActionLog) | Background eLabel `zPosition=-1`, geometry unchanged; MENU/HELP and the log text visible (PackageActionLog opened with a fixed sample text — no opkg command ran) | RUNTIME TESTED |
| Regression | InfoBar, SIB, EventView, Classic channel list, default/Multi/Quick/InfoBar EPG, InfoBarEventView, EventViewSimple: 0 tracebacks, 0 new skin errors, 0 crash logs | RUNTIME TESTED |
| accelAlloc failed | Pool = 5400 kB (`[gFBDC]` at boot). Posters were decoded at full size (600x888/600x900, 2.1 MB) -> pool full after two. Fix: `ePicLoad` (native, synchronous) decodes at widget size; fallback to loadJPG never used (poster.log). Same sequence: 31 -> 1 failures; Enigma2 RSS while browsing Poster List 168.3 -> 149.8 MB; CPU for 5 navigation rounds 8.7 s -> 9.1 s (unchanged within noise). Memory over 10 min (before the fix): +0.4 MB after the first round, no leak. The remaining failure is a 1536x1024 surface at zap (larger than the whole pool; not CineView). | RUNTIME TESTED |
| EventView motion | Classic continuous = factory pack; "line by line" = separate pack | kept |

**Open:** name clip also applies to the Classic radio list while a D1 design is selected (event text ends ~73 px earlier there); `EPGvertical` opens with a channel picker first — full flow to be checked before Columns; video artefacts in grabs since ~20:36 come from the stream (seen before and after the changes; tuner untouched).

## 7. D2 EPG proposals (not implemented)
`tools/mla/p9epg/` — spec, real-data builder (OpenWebif read-only), renderer. Graphical Plus (grid full height + side panel; posters off: 3-hour grid + text panel) and Columns (5 channels side by side + event card). Single Cards dropped: Classic Single EPG already has list + event panel + poster.
