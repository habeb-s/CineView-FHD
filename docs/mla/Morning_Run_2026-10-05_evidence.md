# CineView MLA — morning run 2026-10-05 (user decisions of 05:23)

Receiver: Vu+ Duo 4K SE, OpenATV 8.0.1 (enigma2 57b7a51, Python 3.14.7), Slot 8 only. Branch `dev/mla-openatv`.
Nothing was written to the HDD, to other slots, to `main`, to the tuner, or to multiboot.

Status words follow CLAUDE.md: IMPLEMENTED — NOT RUNTIME VERIFIED / RUNTIME TESTED / DEVICE VERIFIED.

## 1. HD / 16:9 indicators disappearing — ROOT CAUSE IDENTIFIED, fix RUNTIME TESTED (t56)
**Baseline t53 (build44, native ServiceInfo).**
- Protocol: 2 rounds × 6 themes × {Classic, Modern}; per sample: apply theme → restart Enigma2 → zap HRT1 → OK → grab →
  automatic detection.
- Result: **5 of 24 samples missing** (Classic `r1_graphite`, `r2_navy`; Modern `r1_black`, `r1_navy`, `r2_black`).
  Classic's native Pixmap icons miss exactly like Modern's chips, so the cause is not Modern.
- Debug log (Modern chips, `CineViewMLAShowIf` with `debug_showif`):
  - every sample: one `changed (0,)` at connect time with `videoinfo=None` (no service playing yet) → False;
  - good samples: then `changed (3, 15)` events (CHANGED_SPECIFIC, evVideoSizeChanged) with
    `videoinfo=1920|1080|...` → True (16 log lines);
  - **every missing sample: no further event at all** (8 log lines = the connect-time evaluation only).
- Source (57b7a51 `Components/Converter/ServiceInfo.py`): IsHD / Is4K re-evaluate only on evVideoSizeChanged /
  evVideoGammaChanged, IsWidescreen / IsSD only on evVideoSizeChanged. VideoSize (every change) and HasTeletext
  (evUpdatedInfo) are correct in the same frames.
- **Root cause.** After an Enigma2 start the decoder sometimes sends no video-size event after the screen's
  converters are connected. The native converter keeps its connect-time value (False) until the next size change.
- Evidence files: `docs/mla/evidence/t53/` (log, debug logs, bottom crops of two missing and two good samples).

**Fix (CineView side only, no Enigma2 file changed): `CineViewMLAServiceInfo`** (`mla/components/Converter/`).
- Subclass of the native converter: same tokens, same result logic.
- The video-geometry tokens are also re-evaluated on evStart / evUpdatedInfo / evVideoSizeChanged /
  evVideoFramerateChanged / evVideoProgressiveChanged / evVideoGammaChanged, and once more 1.5 s and 4 s after
  evStart / evUpdatedInfo (the native eAVControl fallback reads the running decoder while sVideoInfo is -1).
- The build rewrites only those tokens in every MLA skin file (86 places, all designs). Other ServiceInfo tokens
  stay native.
- **Verification t56 (build48).**
  - Same protocol as t53, 3 rounds × 6 themes × {Classic, Modern} = 36 samples.
  - **Result: 36 of 36 samples show HD and 16:9** (baseline t53: 5 of 24 missing).
  - The failure condition itself happened 4 times (Modern `r1_purple`, `r2_graphite`, `r2_navy`, `r2_purple`):
    not a single evVideoSizeChanged after the converters connected.
  - In those 4 samples the chips turned True from the start / info events (the eAVControl fallback reads the
    running decoder) and stayed True through both rechecks. With the native converter they would have stayed hidden.
  - Chance check: at the baseline miss rate (5/24 ≈ 21 %), 36 clean samples by luck has a probability of about 0.0002.
  - Evidence: `docs/mla/evidence/t56/` (log, Modern debug logs, crops).

## 2. Graphical Plus — RUNTIME TESTED (t55, build46)
- 3 hours: confirmed earlier from the timeline labels (≈181 min ON and OFF; the receiver uses the default 180).
- Posters OFF panel: genre / IMDb moved to a footer. The description now runs directly under the duration, with no
  hole (grab `a1_off_start`: 5.6/10 ★★★ at the bottom).
- Long titles in the grid, the native option `config.epgselection.graph_event_alignment`:
  - default "Left" (17): one line, cut at the cell edge;
  - "Left, wrapped" (81): up to three lines, but very short cells break words letter by letter ("F / ut / ur").
  - Recommendation: keep the default. Both modes are native drawing, so the skin can't improve them further.
- Fast vs slow navigation, same 9-key sequence (0.25 s vs 2.5 s per key): at keys 3, 6 and 9 poster, title and times
  are identical (poster diff 0.3–0.5, title 0.0, times 0.0 → SAME). The poster follows the selected event.
- 0 tracebacks, 0 new skin errors.

## 3. EventView coloured-key captions — captions RUNTIME TESTED (t54); key functions re-test t54b
- Captions appear only for keys that have a function:
  - EPG-opened event: "Add Timer";
  - live INFO: "Add Timer", "Single EPG", "Multi EPG";
  - InfoBarEventView: none (no key is assigned there natively);
  - posters OFF: same captions.
- **Test-script error found:** t54 sent 398 / 399 / 400 / 401 as green / yellow / blue / red. The Linux codes are
  RED 398, GREEN 399, YELLOW 400, BLUE 401. Corrected reading of t54:
  - GREEN (sent as "yellow") on the EPG-opened event opened the RecordTimer editor; EXIT cancelled it; timer list
    unchanged (0 → 0).
  - YELLOW / BLUE without a caption did nothing (correct).
  - RED without a caption opened an empty native list (native behaviour of EventViewEPGSelect, not CineView).
- t54b repeats the functional part with the correct codes (live: GREEN timer editor, YELLOW Single EPG,
  BLUE Multi EPG). **Pending.**
- Pre-existing, not from this change: the Classic `EPGSelection` list carries attributes 57b7a51 does not know
  (`setEventItemFont`, `setEventTimeFont`, `setColWidths`, `setColGap`, `setIconDistance`). They are only log
  errors with no visual effect. Left unchanged (approved Classic screen).

## 4. New packs (IMPLEMENTED — NOT RUNTIME VERIFIED until their tests run)
| Pack | Section / model | Contract notes | Device test |
|---|---|---|---|
| `secondinfobar/modern` | Modern SIB | source widgets; NOW/NEXT cards; header chips (fixed converter) | t57 |
| `channelselection/modern` | Modern CS | native legacy list, rounded `selectionPixmap`; cursor-service NOW/NEXT (`EventName NextNameOnly`, `EventTime NextStartTime` on ServiceEvent, verified in EventInfo.py); name clip extended to "modern" | t57 |
| `epg/modern` | Modern Graphical EPG | Graphical Plus contract, `_CVPosterOff` | t57 |
| `eventview/modern` | Modern EventView | live: source-based; Simple / InfoBar: named widgets + `_CVPosterOff` | t57 |
| `pvr/modern` | Modern PVR | native MovieList with native rounded selected row (`itemCornerRadiusSelected`), `_CVPosterOff` | t59 |
| `epg/columns` | Columns | native EPGvertical (list1..5, currCh, Active, piconCh), index list zero-width contract | t58 |
| `pvr/cover` | Details Cover Library | Classic screen + narrower list + cover of the selected recording; OFF = Classic geometry | t59 |
| `eventview/feature` | Cinema Feature | named EventViewBase widgets, native ScrollLabel, `_CVPosterOff` incl. live EventView | t59 |

Plugin changes (technical): `pvr` poster switch (MovieSelection only for the plain "MovieSelection" name; the
user's MovieSelectionSlim keeps its own screen); live EventView `_CVPosterOff` name; MENU → "Apply a design model to
every section".

## 5. Minimal — mockups published for approval
Artifact "CineView Minimal — النماذج": 6 sections × posters ON/OFF × 6 themes. The frame is HRT1 with the letterbox
and subtitles cropped out. The self-review found weak text contrast on bright video, so the spec now puts a solid
tint (≈86 %) under every text line. The page also carries the first Modern PVR mockup.

## 6. Pending at the time of writing
t57 (Modern SIB/CS/EPG/EV), t58 (Columns), t59 (Cover, Feature, Modern PVR), t60 (performance soak:
Modern 25 min vs Classic 10 min, accelAlloc counted), t54b (key functions).
