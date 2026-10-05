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
- **t54b (build54, correct codes) — RUNTIME TESTED.**
  - Live INFO: captions "Add Timer", "Single EPG", "Multi EPG". GREEN opened the RecordTimer editor and EXIT
    cancelled it. YELLOW opened the Single EPG of the channel. BLUE opened the Multi EPG.
  - EPG-opened event: caption "Add Timer"; GREEN opened the timer editor.
  - Timer list before and after: 0 → 0 (nothing was added).
  - Every caption shown has a real function.
  - RED has no caption, but it still opens the native (empty) Similar list. That is native EventViewEPGSelect
    behaviour, unchanged by CineView.
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

## 4b. Device results of the new packs
- **Modern SIB / CS / EPG / EventView (t57, build51) — RUNTIME TESTED with 2 findings.**
  - 0 tracebacks and 0 new skin errors in 3 themes, posters ON/OFF.
  - CS: rounded selection row; the right card follows the CURSOR service (HBO HD → HBO 2 → Kino TV); NOW / NEXT
    with posters; the CineView default image when no reliable poster exists; full reflow when posters are OFF.
  - EPG: the card follows the cell; OFF = wider grid, IMDb in the footer.
  - EventViewSimple / InfoBarEventView: ON/OFF reflow; caption "Add Timer".
  - Finding 1: the live EventView picon was missing (session.CurrentService picon in a screen opened while the
    service plays). Fixed in build54: the picon now comes from the screen's own "Service" source. Re-test t57b.
  - Finding 2: the CS bouquet title was empty because it was declared as a named widget. Fixed in build54: it is now
    the "Title" source. Re-test t57b.
  - The SecondInfoBar grabs showed the InfoBar. The 1920-px grab between the two OK presses outlasted the InfoBar
    timeout (a test-timing error). t57b uses OK, 1.5 s, OK, as in t30.
- **Columns (t58, build51) — RUNTIME TESTED.**
  - Five channel columns: picon, name, active-column highlight, time + title rows.
  - The event card follows column and event (HBO 3 HD → Peter Pan).
  - Posters ON and OFF (card reflow), navy and burgundy.
  - INFO opens EventViewSimple for the selected event.
  - 0 errors.
  - Minor: a third title line of a long event is cut at the row edge (native row height = list height /
    `vertical_itemsperpage`).
- **PVR (t59) — NOT EXERCISED.** InfoBar.showMovies (the PVR key) opens EnhancedMovieCenter on this receiver, so
  MovieSelection (Cover Library / Modern PVR) was never on screen; EMC showed its own skin. The user requires PVR to
  work on EMC (decision 08:45) → section 5.
- **Performance soak (t60, build54).**
  - Modern 25 min (15 rounds of CS + EventView + SIB + EPG): RSS 146 → 152.5 MB, flat after round 3; peak 159 MB;
    threads 15; fds 98, flat; CPU per 2 rounds ≈ 15–16 s, no slowdown; 0 tracebacks.
  - Classic 10 min (baseline): RSS 146.7 → 150.4 MB; threads 15.
  - **accelAlloc failures:**
    - Modern: 639 (≈ 43 per round, growing linearly).
    - Classic: 1 over the whole run.
  - No memory growth, no slowdown and no picture loss in any grab. But this is a clear Modern-specific increase, so the
    known issue is NOT simply accepted for Modern.
  - t62 measures which Modern screen and which surface sizes fail (posters ON vs OFF).

- **t57b (build54) — RUNTIME TESTED.**
  - Modern SecondInfoBar now opens with the corrected timing (OK, 1.5 s, OK): NOW / NEXT cards, live chips
    (HD · 1920×1080 · 16:9 · SNR · dB), posters ON/OFF, navy and green, 0 errors.
  - CS bouquet title is shown.
  - The live EventView picon was shown, but a second, stray default picon appeared where the hidden ON/OFF variant
    sits: a Picon whose poster-switch variant is hidden still draws itself on every change. Fixed (build57+): one
    picon at a fixed place for both modes.
- **accelAlloc root cause (t62, build55) — ROOT CAUSE IDENTIFIED.** Failures per Modern step, posters ON:
  CS 10 moves 5, EventView 2, EPG open 3, EPG moves 4; InfoBar and SIB 0. Failures by surface size: 240×360 (7),
  300×450 (6), 400×600 (2), 1536×1024 (1, at start-up, also present with Classic).
  **With posters OFF: 0 failures in every step** (only the start-up 1536×1024).
  So the Modern-specific failures are the large poster surfaces (Modern shows 240–400 px wide posters, often two per
  screen) that no longer fit in the receiver's small accelerated pool. The picture then falls back to normal RAM:
  every poster still appeared in every grab, RSS stayed flat, CPU per round stayed flat.
  Options for the user: accept (fallback only), or smaller Modern poster sizes.
- **Test-harness errors found and fixed this morning** (none of them a skin defect):
  - t54 colour-key codes;
  - t57 OK timing;
  - t61: the EMC packs were REFUSED by the engine's colour validation because of EMC's numeric `Cool*Color="1"`
    flags, the apply output was not checked, so t61 tested Classic. Fixed: numeric `*Color` values are flags; the
    tests now print "APPLY FAILED".
  - A script copied over a RUNNING test (t61) killed it mid-run; the receiver was verified Classic afterwards.
    Rule: never replace a running test script.
- **Cinema EventView Feature (t59, build53) — DEFECT FOUND.**
  - The native ScrollLabel description was EMPTY in every Feature screen (live, from the EPG, InfoBar EPG, ON and
    OFF). Layout, poster, titles, times, IMDb and key captions were correct.
  - The only difference from the working Modern / Classic screens is the translucent `steThemeOverlay` background
    colour.
  - First hypothesis: the translucent `steThemeOverlay` background colour. Changed to an opaque colour (build58).
    **t64 disproved it**: the description was still empty.
  - **Root cause.** Feature's full-screen dim eLabel sat at zPosition 1, while Modern's and Classic's sit below
    0. The native ScrollLabel draws its text label at z 0 whatever zPosition the skin gives it.
  - Fix (build60): every plain eLabel of the Feature screens is now below z 0. `zorder_check.py` now treats
    FullDescription / epg_description as z 0: it flags the old build58 pack (6 cases) and passes all 30 packs of
    build60. Re-test t64b.

## 5. PVR on the screen the PVR key really opens (EMC) — IMPLEMENTED, device test t61
- **EMC contract.** Read from EMC's compiled modules on the receiver (no source is shipped):
  - `EMCSelection.__init__`: skinName = ["EMCSelectionExtended", "EMCSelection"]; "EMCSelectionOwn" only when
    `config.EMC.use_orig_skin`. The CoolSkin XML is an embedded fallback.
  - EMC widgets: list (MovieCenter, `Cool*` layout attributes), wait, key_* Buttons, spacefree, Cover, CoverBg,
    CoverBgLbl, Video, music tags; source "Service" (EMCServiceEvent).
- **Packs.** "cover" (Details) and "modern" now also ship `EMCSelection` and `EMCSelection_CVPosterOff`.
  - Classic ships none, so EMC keeps its own skin: the safe fallback.
  - `EMCSelectionOwn` is the user's explicit EMC choice and is never replaced.
- **Plugin.** The pvr poster switch also covers EMCSelection, for EMC's default name list only.
- **Covers.** The poster renderer now uses, in order:
  1. a cover file next to the recording (`<name>.jpg`, `<file>.jpg`, `.png`, folder.jpg), read-only;
  2. otherwise the identity engine on the recording's own title (from .eit, or from .meta when there is no .eit);
  3. otherwise the CineView default image.
- **Test media.** On the Slot 8 USB stick only (`tmedia_pvr.sh`), with three cases:
  - A: identity from the title;
  - B: local cover file;
  - C: generic programme → default image.
  - The HDD is never opened.

- **EMC PVR, re-run t61b (build57, the engine fix applied) — RUNTIME TESTED with 2 findings.**
  - EMC now opens the CineView screens.
  - Cover Library:
    - live picture + details on the left; list + cover on the right;
    - local cover file (Harry Potter) shown;
    - generic "Dnevnik" → CineView default image;
    - OFF = wide list.
  - Modern: two rounded cards, cover, pills; OFF reflow; green theme.
  - Native MovieSelection with the Cover pack on the USB folder: narrowed list + identity poster
    ("Ples malog pingvina" → Happy Feet).
  - 0 tracebacks, 0 skin errors. The movielist folder was restored (unset → unset).
  - Finding 1: EMC's list columns, shifted from its 1190-px CoolSkin, left a 200-px title column in the 690-px
    Cover list. Fixed: columns are laid out from the right edge.
  - Finding 2: `MovieInfo FullDescription` returns the FILE PATH for EMC's service. Fixed: EMC screens use
    `MovieInfo ShortDescription` (.meta) + `EventName ExtendedDescription` (.eit), like EMC's own skin.
  - Re-test t61c (build59).
  - Not yet confirmed: in EMC the identity recording ("Ples malog pingvina") showed the default image at first sight,
    while MovieSelection later showed its poster. This is probably the first-time download; t61c will show it.

## 5b. Minimal — mockups published for approval
Artifact "CineView Minimal — النماذج": 6 sections × posters ON/OFF × 6 themes. The frame is HRT1 with the letterbox
and subtitles cropped out. The self-review found weak text contrast on bright video, so the spec now puts a solid
tint (≈86 %) under every text line. The page also carries the first Modern PVR mockup.

## 6. Pending at the time of writing
t57 (Modern SIB/CS/EPG/EV), t58 (Columns), t59 (Cover, Feature, Modern PVR), t60 (performance soak:
Modern 25 min vs Classic 10 min, accelAlloc counted), t54b (key functions).

## 7. After the 08:45 decisions (second half of the morning)

- **Cinema EventView Feature, t64b (build60) — RUNTIME TESTED, the description defect is fixed.**
  - Root cause (from t64): the dim eLabel at z 1 covered the native ScrollLabel, which draws its text at z 0.
  - Fix: every plain eLabel of the pack is below z 0; `zorder_check.py` now treats FullDescription/epg_description
    as z 0 and reports 0 covered widgets on build60/62.
  - t64b: live INFO, page down, EPG → INFO (EventViewSimple), InfoBar EPG → INFO; navy ON, burgundy ON, burgundy OFF.
    The full description is visible in every screen; OFF reflows from the left edge; only captioned keys are drawn.
  - 0 tracebacks, 0 new skin errors, 0 crash logs.
  - Still open for approval: the look.
- **Modern EventView picon, t65 (build60) — RUNTIME TESTED, fixed.**
  - One Service-source picon at a fixed place, for ON and OFF.
  - HBO HD → HBO picon, HBO 2 HD → HBO 2 picon; no stray default picon. OFF: one picon, text from the left edge.
  - 0 tracebacks, 0 skin errors.
- **EMC PVR, t61d (build61) — identity cover in EMC RUNTIME TESTED.**
  - EMC's event for a recording has no description, so the poster engine now reads the recording's own .meta
    (name / description) through eServiceCenter. Path-valued descriptions are dropped (EMC returns the file path for
    FullDescription / ExtendedDescription).
  - Cover Library (navy ON):
    - Harry Potter → local cover file;
    - Ples malog pingvina → identity poster (Happy Feet);
    - Dnevnik → CineView default image.
  - The description is the recording's short description, with no path.
  - Remaining cosmetic point: in the 690-px Cover list, EMC's progress bar and date leave about 320 px for the
    title ("Harry Potter i plameni p…"). The title is shown in full under the cover.
  - EMC shows the folder path as the "description" of its trashcan entry (EMC's own data).
- **New sections so that each model owns all six (IMPLEMENTED — NOT RUNTIME VERIFIED until t66):**
  - `eventview/detailscard`: Details EventView Card. A framed opaque card with the Details grey top line, a 300×450
    poster with the 3-px frame, and native named widgets plus ScrollLabel; `_CVPosterOff`.
  - `pvr/cinema`: Cinema Shelf. A scrim over the live picture, a 340×510 poster, the big title of the selected
    recording, a metadata row and the short description, with the list underneath. Both native MovieSelection and
    EMC are covered; `_CVPosterOff` for both.
  - The models now map Details → `detailscard` and Cinema → `cinema` PVR. Both packs pass bounds and z-order checks.
