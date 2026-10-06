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
- **t61d, remaining parts — RUNTIME TESTED.**
  - Cover OFF (wide list, no cover) and the native MovieSelection with the Cover pack (Ples → Happy Feet) work.
  - Modern navy/green ON (Ples → Happy Feet, HP → local cover) and OFF work, as does the native MovieSelection
    (Dnevnik → default image).
  - Classic leaves EMC in its own skin (fallback).
  - 0 tracebacks, 0 skin errors, 0 crash logs; the movielist folder was restored (unset → unset).
  - **PVR conclusion:** the PVR key (EMC), the native MovieSelection and the Classic fallback are all covered.
- **New sections so that each model owns all six:**
  - `eventview/detailscard` — Details EventView Card: an opaque framed card with the Details grey top line, a
    300×450 poster with the 3-px frame, native named widgets and ScrollLabel; `_CVPosterOff`.
  - `pvr/cinema` — Cinema Shelf: a scrim over the live picture. The left column holds the selected recording
    (340×510 poster, big title, stacked details, short description); the right column holds the full-height list.
    It covers the native MovieSelection and EMC, with `_CVPosterOff` for both.
  - Models: Details → `detailscard`, Cinema → PVR `cinema`.
- **t66 (build62) — RUNTIME TESTED, 2 defects found.**
  - Details Card: live / page down / EPG → INFO / InfoBar EPG → INFO, navy ON, green ON, green OFF.
    - Description visible; a series without identity → default image; 0 tracebacks / skin errors.
    - Defect 1: the IMDb stars label (100 px) wrapped its fifth star onto a second line. The Feature InfoBarEventView
      has the same width. Fixed: 130 px with noWrap.
  - Cinema Shelf on EMC (navy, burgundy, OFF): HP local cover, Ples identity, Dnevnik default; no path descriptions.
    - Defect 2: on the native MovieSelection the rows were 27 px and overlapped. Root cause, read from the
      receiver's MovieList.pyc: `setItemsPerPage` sets the row height to listHeight // config.movielist.itemsperpage.
      `itemHeight` in the skin is ignored, so a 552-px list gives cramped rows.
    - Fix: the list takes the full-height right column (860 px → 43 px rows) and the card moves to the left column.
- **t66b (build63) — RUNTIME TESTED, both fixes confirmed.**
  - Native MovieSelection rows are readable ON and OFF; the stars fit on one line.
  - 0 tracebacks, 0 skin errors, 0 crash logs.
  - accelAlloc stayed at the start-up value 1 in every Details Card and Cinema Shelf step (t66: 3–5 on two Cinema
    steps; t66b: 1).
  - Restored: EventView classic-lines, PVR classic, navy, posters ON, movielist folder unset → unset.
- **Note (Minimal):** the native MovieSelection list is 640 px, giving 32-px rows with the user's itemsperpage. They
  are readable on t63 grabs but tight; this is kept as is until the Minimal look decision.

## 8. Modern accelAlloc (user decision 13:15: "fix Modern first") — ROOT CAUSE IDENTIFIED, fix RUNTIME TESTED

**Facts from the receiver:**
- The receiver log reads `[gFBDC] 5400kB available for acceleration surfaces`.
- In enigma2 57b7a51 (`lib/gdi`), every surface of 48000 bytes or more is a candidate for the pool (`GFX_SURFACE_ACCELERATION_THRESHOLD`).
- PNGs loaded by the skin are cached for good (`LoadPixmap` → `PixmapCache`).
- The native channel list caches every row picon it draws (`listboxservice.cpp` `loadPNG`, `cached=1` by default). The native Picon renderer does the same (`setScale(1)` → `setPixmapFromFile`, accel = `m_scale`, cached).

**Debug dumps of the pool at the moment of failure (dev trigger `setACCELDebug`):**
- t69 (Modern v2): the pool held per-size default posters plus 220×132 picons.
- t71 (Modern v3): 42 × 220×132 picons (4.8 MB) + 816×60; 5021 kB used, largest free block 106 kB.
- t72 (Classic, same navigation): 31 picons (3.5 MB) plus Classic posters; **230 failures in 5 rounds**. The t60 "Classic = 1" came from a lighter round (no zaps, no EMC).

**Fix (Modern Optimized, then `tools/mla/accel_opt.py` for every non-Classic pack):**
- **Default posters:** each default poster is a stretched 4×90 gradient tile plus a film icon under 48000 bytes. There are no per-size PNGs any more.
- **Frames:** each 3-px frame PNG is replaced by four strips of a 4×4 PNG.
- **Poster widgets (`underlay="1"`):**
  - they release their picture when hidden or empty, and decode nothing while hidden;
  - while a cursor runs (changes less than 0.4 s apart), only the position where it stops is decoded;
  - the old block is freed before the new decode;
  - the picture is shown from a widget-size PNG in the poster cache (`sz/`, capped at 400 files), loaded with `loadPNG(accel=-1)`, outside the pool.
- **Picons stay native.** An uncached copy (v3) only added allocations, because the list rows already cache the same files (t70: 344).
- **Cinema InfoBar band:** the 1920×330 solid themed bitmap (2.5 MB pinned) is now an eLabel `steThemePanel` (same colour within 1–3 levels; the black theme is #101214 instead of #000000).

**25-minute soak, identical round** (channel list fast/slow + EventView, SecondInfoBar, EPG, EMC on USB, HBO/HRT1 zap):

| Run | Warnings / 25 min (incl. 1 at start-up) | CPU | RSS end |
|---|---|---|---|
| Modern Large build63 (t67) | 741 | 116 s | 152.6 MB |
| Optimized v1 build64 (t67) | 249 | 96 s | 149.3 MB |
| v2 build65 (t69) | 278 | 91 s | 145.3 MB |
| v3 build66 (t70) | 344 | 94 s | 140.8 MB |
| **v5 build68 (t74)** | **17** | **90 s** | 146.6 MB |
| Classic build68 (t75, reference) | 625 | 130 s | 149.2 MB |

**Final Modern under other conditions (t76, build69):**

| Condition | Warnings (incl. start-up) |
|---|---|
| Posters OFF, 8 min | 3 |
| green, 5 min | 14 |
| burgundy, 5 min | 22 |
| black, 3 min | 4 |
| graphite, 3 min | 13 |
| purple, 3 min | 1 |

- Zaps HBO HD / HRT1 ran in every round; 0 tracebacks; screenshots in `shots/t76`.
- "Tovar" and "Avenija divova" show the default tile in every screen. poster.log has `candidates=0 -> no-reliable-match` for both, so this is the identity policy, not a display fault.
- **Conclusion:** with the identical navigation, the final Modern uses fewer accelerated-pool requests than Classic (17 vs 625 in 25 min) and less CPU (90 s vs 130 s).
- The remaining warnings come from the native list code once the pool is full of its cached picons; Classic hits them first.
- The same optimisation (`accel_opt.py`) now covers Details, Cinema, Minimal and Columns. The approved Classic packs are left untouched.

Status: RUNTIME TESTED. 0 tracebacks, 0 skin errors and 0 crash logs in every run.

## 9. User conditions 20:10 (poster look, memory, cache): implementation

- **Poster appearance:** unchanged. Same widget sizes, same layout, no recompression. Every screen decodes the
  original cached file (never overwritten) at the widget's own size, as before. The `underlay` path keeps a
  lossless PNG of exactly that decode in `<poster cache>/sz/` (keyed by the source path + size). It loads it with
  `loadPNG(accel=-1)`, so the picture sits in normal RAM, not in the 5400 kB accelerated pool. A picture is
  released when its screen hides or the widget empties, and never decoded while hidden. t78 compares before/after
  pixels on the receiver.
- **Default placeholder:** the exact look of `poster_default.jpg`, without a full-size bitmap:
  - background gradient (4×90 PNG, stretched);
  - the original inner frame line (3 px at an 18 px inset on 600×900, scaled) drawn as strips;
  - the film icon cut from the default image at the widget size, in vertical slices under 48000 bytes.
  - Offline comparison with the original image scaled the same way: mean difference about 1 level out of 255
    (400×600: 1.0/0.5/0.8; 300×450: 1.3/0.7/1.0; 146×218: 1.7/1.2/1.5).
  - Superseded: build69/70 capped the icon at 120 px and had no inner line.
- **Accelerated pool:** treated as display memory only, never as storage. The fix does not depend on USB or HDD.
- **Poster cache, release policy** (`_mla_cache_plan`, no side effects; `_mla_cache_root` creates the folder):
  1. `/media/hdd/poster`, only when `/media/hdd` is a real read-write block-device mount (in /proc/mounts,
     `os.path.ismount`, a device other than `/`);
  2. `<mount>/poster` on another real read-write /media block mount (USB first, multiboot media excluded);
  3. `/tmp/CINEVIEW-MLA/poster`.
  - There is one cache for every design and screen, keyed by the event identity. A cached poster is used at once,
    with no network.
  - An upgrade or a normal removal never deletes the cache. Only the `sz/` derivatives are capped (400 files,
    oldest first); original downloads are never deleted.
- **Development (Slot 8):** runtime.json `poster_cache` points to the USB. A path on the HDD device is refused
  unless `"allow_hdd": true`. No HDD write has been made. `cache_plan_dryrun.py` (t79) shows the choice for
  development and for a release install without creating anything.

## 10. t77 (rc5) and t78 (poster quality / pool A/B)

- **t77 — DEVICE VERIFIED.**
  - opkg upgrade rc4 → `1.0.0~rc5` (build70) on Slot 8, after a backup in `state/backup-rc5`.
  - All five models were applied from the installed package; six sections opened per model.
  - 0 tracebacks, 0 skin errors, 0 crash logs.
  - End state: `install ok installed`, skin CineView_FHD_MLA, Classic navy.
  - rc5 is published on dev/mla-openatv in `release/rc` (SHA256 `c8b6220e…64e5`), with `install-mla-rc5.sh`
    (image / model / Python / space / sha256 checks before installing; `DRYRUN=1`) and `uninstall-mla.sh`.
    The dry run on Slot 8 passed. Simulated OpenViX 6.6 and OpenATV 7.6 were refused.
- **t78 — RUNTIME TESTED.** Large build63 vs current build71, same screens and items, minutes apart, gAccel debug on.

| Poster | Mean diff (R,G,B) | PSNR |
|---|---|---|
| EMC Harry Potter (local cover) | 0.02 / 0.02 / 0.02 | 57.1 dB |
| EMC Ples malog pingvina (identity) | 0.01 / 0.01 / 0.01 | 64.3 dB |
| EventView HBO 3 (poster) | 0 / 0 / 0 | 68.5 dB |
| EventView HBO / HBO 2 ("no poster" placeholder) | 1.4 / 0.9 / 1.2 | 36.0 dB |

  - Posters are visually identical. The placeholder differs by about 1 level from the old bitmap (stretched
    gradient); the frame line and icon are the same.
  - **Accelerated pool after the same steps:**
    - Large: 5064 kB used, free 319 kB; posters resident (400×600 937 kB, 208×300 729 kB, 304×450 534 kB, …)
      plus 1955 kB of native picons; 28 accelAlloc failures.
    - build71: 3830 kB used, free 1551 kB; **no poster surface in the pool**, only native picons (3565 kB) and
      816×60; 1 failure (the start-up one).

## 11. accelAlloc attribution per source (user request 22:03) — t81a / t81b, fix t83

**t81a — RUNTIME TESTED.**
- Setup: build71 deployed (the files of rc6), gAccel debug on, fixed zap order (HBO / HRT1 alternating), 3
  diagnostic rounds on Modern.
- Every failure is classified by the size of the surface requested at the moment of failure (enigma2 dumps the pool
  at each failure).

| Source | Failures | Share |
|---|---|---|
| Enigma2 picon cache (220×132, channel list rows, `listboxservice.cpp` `loadPNG(..., cached=1)`) | 3 | 42.9 % |
| CineView poster decode (300×450, 240×360, 160×240) | 3 | 42.9 % |
| Enigma2 image / other surface (1536×1024, right after a zap) | 1 | 14.3 % |

- Pool at the last failure: 5275 kB used in 48 surfaces. 43 of them are 224×132 picons (115 kB each, about
  4.9 MB), plus the 816×60 surface. Free: 99 kB in 2 blocks.
- No poster surface was resident. The CineView failures are first-time decodes, not held blocks.

**t81b — RUNTIME TESTED.** The same steps and order with the INSTALLED package 1.0.0~rc6 (force-reinstalled,
reinst.sh 22:36).

| Source | t81a (build71 deployed) | t81b (rc6 installed) |
|---|---|---|
| Enigma2 picon cache 220×132 | 3 (42.9 %) | 3 (37.5 %) |
| CineView poster first decode | 3 (42.9 %): 300×450, 240×360, 160×240 | 4 (50.0 %): 300×450, 160×240, 400×600, 200×300 |
| Enigma2 image / other 1536×1024 | 1 (14.3 %) | 1 (12.5 %) |
| Total | 7 | 8 |

- Both runs had 0 tracebacks, 0 new skin errors and 0 crash logs.
- The installed package and the deployed build behave the same; the poster count depends on which events first
  need a widget-size copy.
- One t81b context line shows the failure right next to `[ePNG] saving to …/sz`: the ePicLoad block of a first
  decode.

**Root cause of the CineView share — ROOT CAUSE IDENTIFIED (enigma2 57b7a51 source).**
- `lib/gdi/picload.cpp:1348`: `ePicLoad::getData()` allocates its result as
  `new gPixmap(max_x, max_y, 32, NULL, gPixmap::accelAuto)`.
- So the first decode of each poster (when its widget-size copy is not in `sz/` yet) asks the full pool for
  300×450 / 240×360 / 160×240. The request fails, a warning is logged, and the pixmap falls back to RAM.
- Right after that, the patch replaced the block with the accelNever copy. So these are transient requests, not
  residency.

**Fix — IMPLEMENTED (build75), device test t83 queued.**
- The widget-size PNG is now made with PIL from the original cached poster, with no gPixmap at all. Pillow 12.3.0
  is part of OpenATV 8.0.1.
- It is then loaded `loadPNG(path, -1, 0)` (accelNever, uncached). ePicLoad remains the fallback when PIL is
  missing.
- The geometry is ePicLoad's exactly, from the source:
  - fit inside w×h with the aspect kept, sizes truncated;
  - offset `(max − scr) / 2`;
  - borders `background ^ 0xFF000000` = opaque black;
  - EXIF orientation ignored.
- The original poster is only read: never rewritten or recompressed, and its visible size is unchanged.
- **Offline A/B on the receiver** (86 existing ePicLoad `sz/` files vs PIL output from the same originals):
  - geometry and black bars match; the alpha differs only for 2 PNG sources with transparency;
  - PSNR median 30.4 dB (min 22.0). The difference is the scaler: ePicLoad box-averages, PIL LANCZOS is sharper;
  - zoomed crops: same framing, PIL version crisper (text edges), no artefacts.
  - Visual evidence: `shots/szcmp/szcmp.png`, `szcmp2.png` on ai-agent.
- **This changes the poster pixels (sharper), not the size or layout. The user's visual approval is requested.**

**t83 — RUNTIME TESTED (build75, same steps and channel order as t81a/b).**
- The ePicLoad-made `sz/` folder was moved aside (USB dev cache), so EVERY poster took the first-decode path.
- 27 widget-size PNGs were made with PIL during the run (`sized make … (PIL, no gPixmap)` in poster.log); no
  ePicLoad fallback was logged.

| Source | t81a (build71) | t81b (rc6 installed) | **t83 (build75, PIL)** |
|---|---|---|---|
| CineView poster first decode | 3 (42.9 %) | 4 (50.0 %) | **0 (0 %)** |
| Enigma2 list picon cache 220×132 | 3 | 3 | 3 (75 %) |
| Enigma2 other surface 1536×1024 (start-up, InfoBarSummary) | 1 | 1 | 1 (25 %) |
| Total | 7 | 8 | **4** |

- 0 tracebacks, 0 new skin errors, 0 crash logs.
- A/B of the same 17 posters (ePicLoad `sz` vs PIL `sz.t83pil`, identical keys):
  - PSNR min / median / max 25.9 / 31.6 / 38.1 dB;
  - same size, framing and colours; PIL is crisper on small text;
  - grabs `shots/t83/AB_0..2.png` (ai-agent).
- After the run the ePicLoad folder was put back (`sz` 110 files) and the PIL folder kept as `sz.t83pil` (27). Nothing
  was deleted from the poster originals.
- **Conclusion: CineView no longer adds accelAlloc warnings. What remains is Enigma2-internal (list picon cache and one
  start-up surface).**

**Native share (picons, the 1536×1024 surface).**
- These are Enigma2-internal (PixmapCache / list picon cache). They are documented here and not changed, per the
  rule "no risky Enigma2 change".

## 12. No Poster layout instead of a placeholder (user decision 22:03)

**Mechanism — IMPLEMENTED (build73 / 74 / 76 / 77).**
- The poster renderer publishes, per (toggle key, nexts), whether it shows a REAL poster
  (`Components/CineViewMLAPosterState.py`).
- `CineViewMLAShowIf` variants flagged `,poster0` / `,poster1` follow that state. Posters ON and the event has no
  poster → the screen's posters-OFF arrangement for that moment.
- The placeholder widgets (tile / icon / inner frame) are removed from those screens, and the poster widget gets
  `underlay="1"`, so nothing is decoded when there is no poster.
- Screens per build (build step `noposter.py`):
  - build73: 52 dynamic screens (InfoBars, SIBs, channel lists, live EventView, EPG lists, PVR cover / minimal);
  - build74: + both GraphicalEPG ON screens (Modern, Graphical Plus): poster card / No Poster card in the same screen;
  - build76: + PVR cards (Modern, Cinema Shelf, Cover Library; MovieSelection and EMC), 58 dynamic screens.
- Named-widget EventView designs (EventViewSimple / InfoBarEventView, Details Card, Feature, Minimal): the plugin
  opens `<name>_CVPosterOff` when the event has no cached poster (cache only, no network).
- **Remaining static:** SecondInfoBarECM (non-default SIB mode; Python-owned named widgets; the screen is created
  once with the InfoBar). It keeps the default placeholder.

**t82 — RUNTIME TESTED (build73).**
- Five models, navy, posters ON. HBO HD (film, poster), 1:0:19:786 (Cinemax HD) and HRT1 (news, generic): SIB,
  EventView and channel list grabbed.
- Every model: 0 tracebacks, 0 new skin errors, 0 crash logs. accel = start-up warning only (Classic 3).
- With a poster: the posters-ON arrangement as approved. Without one: the posters-OFF arrangement, with no
  placeholder. The Cinema SIB without a poster is identical to the approved posters-OFF screen (t68).
- Harness note: the InfoBar grabs came 5 s after OK, when the Modern InfoBar had already timed out. These are not
  screen faults; the InfoBar is covered by the SIB and channel-list grabs and is re-grabbed later.

**Found and fixed (pre-existing, visible in the approved t68 grabs): Classic EventView strip picon — IMPLEMENTED
(build77), device check in t84.**
- The strip has a picon ON / OFF variant pair.
  - A fresh screen sends only CHANGED_DEFAULT, which the native Picon ignores (Renderer/Picon.py 57b7a51), so the
    picon never loaded. It was missing in t68 ON and OFF.
  - `Picon.changed()` calls `instance.show()` whenever it loads a file, so a hidden variant (text "") drew the
    default picon (t82, Cinemax: "habeb-s" default next to the real picon).
- Fix in `CineViewMLAShowIf` (our converter only):
  - poster-flagged variants run one deferred CHANGED_ALL once the screen is built, and again after each
    poster-state change;
  - hidden variants are re-hidden after the downstream update.

**t84 — RUNTIME TESTED (build77).**
- Models: Modern, Cinema, Details, Minimal (posters ON, navy), plus the Classic EventView strip check.
- Per model:
  - InfoBar 2.5 s after OK on HBO and HRT1;
  - GraphicalEPG with the highlighted event on HBO (+ 2 × RIGHT) and on HRT1 (+ 1 × RIGHT);
  - EMC and native MovieSelection on the USB test folder, every row:
    - trashcan and Latest Recordings;
    - Harry Potter (local cover);
    - Ples malog pingvina (identity lookup);
    - Dnevnik (generic news);
    - the test clip.
- Every model: 0 tracebacks, 0 new skin errors, 0 crash logs. accel = start-up warning only (Minimal 0).
- Results:
  - InfoBar (Modern / Cinema / Details / Minimal): HRT1 drops the poster, and text and picon move to the
    posters-OFF place.
  - GraphicalEPG:
    - Modern: poster card on HBO films; on HRT1 the No Poster card (service name, picon in its one place, times /
      duration pills, title, description), no placeholder.
    - Graphical Plus (Cinema / Details): the same panel without the poster slot. Times are right-aligned (G.times),
      duration left-aligned. **Needs the user's visual approval.**
  - PVR cards:
    - Modern, Cinema Shelf, Cover Library on EMC and MovieSelection: rows with a cover use the cover arrangement;
      Dnevnik, the test clip and folders use the No Poster arrangement (text from the top / title at the top of the
      cover column).
    - The native list keeps its geometry.
  - Classic EventView strip (ShowIf fix): the picon shows on HBO (with poster), Cinemax (with poster) and HRT1 (no
    poster, OFF position), with no stray default picon. **ROOT CAUSE FIXED, RUNTIME TESTED.**
- Grabs: `shots/t84/` on ai-agent.

## 13. Release candidate 1.0.0~rc7 (build77) — DEVICE VERIFIED on Slot 8; NOT final

**Contents compared with rc6:**
- widget-size posters made with PIL (no accelAlloc warnings from CineView, t83);
- No Poster layout on 58 screens plus the named EventView screens (t82 / t84);
- ShowIf Picon fix (t84).

**t77_rc7:**
- backup to `state/backup-rc7` (USB);
- opkg upgrade rc6 → rc7: `install ok installed`;
- factory Classic, then each of the five models applied from the installed package with the six sections opened;
- every model: 0 tracebacks, 0 new skin errors, 0 crash logs;
- end state: Classic navy, skin CineView_FHD_MLA.

**Published on dev/mla-openatv `release/rc`:**
- `enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc7_all.ipk`;
- SHA256 `6d752cf8acdde16ef52abb80d47ddc9b72da3c48c0c004a3168fd9ff29afbca6`;
- unpacked 8.6 MB, the same as build77;
- `SHA256SUMS` updated.

**Installer.** `install-mla.sh` now installs rc7; `install-mla-rc5.sh` keeps rc5.1.
- The same checks run before anything is installed (OpenATV 7.6 / 8.0, any model, arch `all`, Python ≥ 3.9,
  space, SHA256).
- New: the "poster cache" step. Without `HDD_CACHE=1`, runtime.json pins the cache to a real USB mount (not the
  root device, not multiboot media), otherwise to /tmp. An existing setting is kept. **No HDD writes unless the
  user asks for them.**
- The pin logic was tried on Slot 8 against /tmp copies (nothing changed):
  - no runtime.json → /tmp (the Slot 8 USB stick is the root device);
  - `HDD_CACHE=1` → left to the skin;
  - existing setting → kept.
- Raw download from GitHub: SHA256 matches. The published installer with `DRYRUN=1` on Slot 8: all checks passed.

## 14. Remaining work before 1.0.0 (user list 2026-10-06 06:13 / 06:42)

**Static audit — `tools/mla/audit_np.py`.**
- build77: 11 named EventView ON screens (Details Card, Feature, Minimal, Modern) still carried the placeholder,
  shown if the poster picked at open could not be displayed.
- Classic `EventViewSimple` / `InfoBarEventView` `_CVPosterOff` and Classic SecondInfoBarECM had poster widgets
  without `underlay`, which draw the default image themselves. The plugin now opens `_CVPosterOff` with the switch
  ON for an event without a cached poster, so the default image would appear there.
- Fixes:
  - build78: the plugin-switched EventView screens are handled like dynamic screens (placeholder removed,
    underlay, frames follow the real poster);
  - build79: `_CVPosterOff` screens carry no poster widget; every other poster widget is underlay.
- **build79: 0 screens with a placeholder** (static). The picon pairs are in 7 screens (Classic InfoBar / SIB / EV,
  Cinema InfoBar, Modern InfoBar / channel list), all mutually exclusive by condition.

**t85 — RUNTIME TESTED (build79).**
- Five models, channels HBO HD / Cinemax HD / HRT1: InfoBar (2.5 s after OK), SIB, live EventView, channel list,
  GraphicalEPG + INFO. Classic also EPG and PVR (EMC + MovieSelection on USB).
- Every model: 0 tracebacks, 0 new skin errors, 0 crash logs.
- **One picon per place in every grab; no default picon next to a real one** (Classic InfoBar / SIB / EV strip
  zoomed; Cinema InfoBar; Modern channel list).
- **No placeholder in any grab.**
- At this hour HBO's and Cinemax's current films had no poster, so the No Poster arrangement was exercised
  everywhere. "Kraljica ringa (2024)" has a negative identity (`.none`): the reliable-only policy refused the
  Croatian title.
- Classic EPG, EventView and PVR (EMC / MovieSelection): as approved, no placeholder.
- accel per model: Classic 18, Modern 46, Cinema 2, Details 3, Minimal 2. t85 has no pool debug; t81d (build79,
  debug, same steps as t83) attributes them.
- Visual note, not changed: the Cinema InfoBar channel name is a 152-px RunningText, so longer names start
  scrolling at 2.5 s (approved geometry).

**Explicit poster-cache deletion — IMPLEMENTED, tested on /tmp.**
- `sh uninstall-mla.sh cache` shows the folder; `CONFIRM=yes` deletes.
- Only MLA's `id/` and `sz*/` are deleted. Files directly in the folder (original CineView FHD posters) are kept.
- The package is not touched.

**Opaque information areas on the InfoBar family — IMPLEMENTED (build81), NOT RUNTIME VERIFIED.**
- `tools/mla/infoplate.py` covers InfoBar, RadioInfoBar, SecondInfoBar(Simple/ECM), MoviePlayer, PVRState and
  TimeshiftState in every pack.
- Opaque twins `<token>Solid` (same RGB, alpha 00) are added to all six themes:
  - translucent cards → opaque twin, same geometry;
  - translucent PNG panels → an opaque plate under them;
  - full-screen scrims keep their transparency, with opaque plates only behind the information groups (one band
    per row).
- Static audit `tools/mla/audit_infobg.py`: build79 had non-opaque information in the Minimal InfoBar, the
  Classic / Cinema / Minimal SIB and every SecondInfoBarECM; build81 has 0.
- Device test t87 is queued (q87): real OSD alpha (`grab?mode=osd`) inside every information widget, five models ×
  six themes, plus the playback InfoBar; composites over red / yellow / white / dark backgrounds. t87a measures
  build79 for the before/after.

**t85b — RUNTIME TESTED (build79).**
- Named EventView opened from the GraphicalEPG for a LATER event (RIGHT, then INFO), five models:
  - HBO's next event (Duh lorda Farquaada / Ples malog pingvina 2: cached poster) → `EventViewSimple`, poster shown;
  - HRT1's next event (TV kalendar, generic) → `EventViewSimple_CVPosterOff` (log: "Processing screen
    'EventViewSimple_CVPosterOff'"), full-width text, no placeholder.
- 0 tracebacks, 0 new skin errors, 0 crash logs in every model.

**SecondInfoBarECM — decision basis.**
- OpenATV uses it only when "show second infobar" = ECM (`config.usage.show_second_infobar == "3"`,
  `Screens/InfoBarGenerics.py:2072`); not the default.
- Its texts are named, Python-owned widgets (`channel` Label, `epg_description` ScrollLabel), and the dialog is
  instantiated once with the InfoBar.
- Reflowing them per event would need either resizing the native ScrollLabel at runtime or re-instantiating the
  dialog on every show. Both change Enigma2 behaviour, so it is **not safe**.
- State in build79: **no placeholder** (poster `underlay`). Without a poster the poster area stays empty; the
  information is never covered.

**t81d — RUNTIME TESTED (build79, same steps as t81a/b and t83, pool debug on).**
- 46 warnings: **0 CineView**; 42 = 720×45:8 (91.3 %), 3 = list picons 220×132, 1 = 1536×1024 at start-up.
- **720×45:8 = DVB subtitle regions (native Enigma2):**
  - `lib/dvb/subtitle.cpp:449` `region->buffer = new gPixmap(eSize(w, h), 8, 1)`: 8-bit regions, accelAlways;
  - they start with `eDVBSubtitleParser start on pid 0x0d75` (HBO's DVB subtitles) and each is freed about 1.5 s
    later.
- The same surface appears in every run; only the failures change with fragmentation:

| Run | 720×45 allocations | failures |
|---|---|---|
| t81a | 594 | 7 |
| t81b | 249 | 8 |
| t81c (t83) | 186 | 4 |
| t81d | 546 | 46 |

- In t81d the pool held one more native 192×49 surface, and the largest free block fell to 30 kB, below the 35.5 kB
  a subtitle region needs.
- The cause is native: the list picon cache (43 × 115 kB resident) plus the DVB subtitle regions.
- Not a CineView regression. The t85 Modern figure (46) is the same mechanism (HBO subtitles at that hour).
- Documented, not changed: it lies in Enigma2's own picon caching and subtitle rendering.

**rc8 (build79) and t86 package lifecycle.**
- rc8 SHA256: `cd3bfbe59889d3cbedfa55b1583eebb8492c95a2cc7162a50f1c0aa439459bc1` (ai-agent `rc8/`, not published yet).
- **t86 run 1:**
  1. Upgrade rc7 → rc8 with Enigma2 RUNNING, Modern selected: `install ok installed`; postinst rebuilt the
     selection ("your design selection was rebuilt", g000331); after the GUI restart the selection was still
     Modern. 0 errors. **PASS.**
  2. Full receiver reboot: back on `rootsubdir=linuxrootfs8` (Slot 8; STARTUP only read); skin, selection Modern,
     guardian hook and poster cache (850 files) unchanged; 0 tracebacks / skin errors / crash logs. **PASS.**
  3. Normal uninstall (`uninstall-mla.sh`): skin selection removed first; package and skin directory gone;
     Enigma2 restarted on the image's default skin; `/etc/enigma2/cineview_mla` and runtime.json kept; poster
     cache unchanged (850). **PASS.**
  4. Fresh install: **test-harness fault.** The script had put the package in `/tmp`, which the reboot in step 2
     cleared ("No candidates to install"). The skin was selected without the package, so Enigma2 started with
     34 skin errors (missing images) and no crash.
  - Repaired by hand right away: rc8 installed from persistent storage (this is the fresh-install path: postinst
    activated factory), settings + MLA state restored from the USB backup, Classic navy. Result: 0 tracebacks,
    0 skin errors, 0 crash logs.
  - The script is fixed: the package is kept in `/home/root/cvmla` and `FROM=<step>` resumes.
  - Steps 3–6 are re-run as t86 rc8b, followed by t77 rc8 and t87a / t87.
- **t86 rc8b (steps 3–6) — DEVICE VERIFIED.**
  3. Normal uninstall: image default skin; package and skin directory gone; `/etc/enigma2/cineview_mla` +
     runtime.json kept; poster cache 850 files; 0 errors.
  4. Fresh install: postinst "factory design (Classic, Navy) active"; skin selected → GUI restart:
     `install ok installed`, generation g000000; 0 errors.
  5. Purge: package, skin directory, `/etc/enigma2/cineview_mla` and runtime.json gone; **poster cache unchanged
     (850)**; 0 errors.
  6. Restore: rc8 + settings + MLA state from the USB backup, Classic navy, skin selected; 0 errors; boot slot
     linuxrootfs8.
- **Lifecycle result (rc8):** upgrade with GUI running ✓, reboot ✓, uninstall ✓, fresh install ✓, purge ✓, poster
  cache never touched ✓.

**Opaque information areas — measurements.**
- Method (t87 + `osd_alpha.py`): `grab?mode=osd` returns the real framebuffer RGBA. Inside every information
  widget of the screen (rectangle from the deployed XML), every pixel must have alpha 255.
- Composites of the real OSD over solid red / yellow / white / dark backgrounds are saved as `<name>_bg.png`.
- **t87a (build79, before, navy):**

| Model | InfoBar | SecondInfoBar |
|---|---|---|
| Classic | opaque | 54 of 56 not opaque (min alpha 135) |
| Details | opaque | opaque |
| Cinema | opaque | 21 of 44 (min 210) |
| Modern | 25 of 28 (min 235 = the 0x14 card) | 56 of 58 |
| Minimal | 14 of 14 (min 210) | 31 of 33 |

  - Total: 201 information widgets not opaque.
  - The composites show the Classic SIB panels turning red / olive / grey with the background.
- **t87 (build81) on Classic: the SIB was still not opaque (min 135).**
  - Classic's SIB labels paint their own background (`transparent="0"`, steSecondInfoBG). In Enigma2 that fill
    REPLACES the pixels (no blend), so a translucent fill punches through an opaque card.
  - The static audit had only checked the layers under each widget.
  - Fixed in build82/83:
    - an information widget's own translucent theme fill → opaque twin;
    - any translucent theme fill above an opaque region → opaque twin;
    - literal translucent fills (Minimal progress track #B0FFFFFF) → a per-theme mixed opaque colour
      (`mixB0FFFFFF_steThemeOverlay`, same look over the band).
  - The audit now checks own fills too. **build83 static audit: 0 not opaque in every InfoBar-family screen.**
  - t87c (build83, five models × six themes) is queued.
  - **CORRECTION (harness fault): the "build81" run did not run build81.** The t86 reboot had cleared
    `/tmp/cvmla` on the receiver. `deploy.sh` (set -e) writes its file list there first, so every deploy after the
    reboot aborted silently, and t87 hid the output. The receiver kept running build79 (rc8). Proof: the deployed
    Classic SIB XML still had `steSecondInfoBG` where build83 has `steSecondInfoBGSolid` plus plates.
    - The "build81 Classic SIB still 135" result above is therefore build79 data and says nothing about build81.
      The build82/83 own-fill fix still stands on its own reasoning (an own translucent fill replaces the pixels),
      and it is checked on the device now.
    - The same missing directory explains the empty MoviePlayer grabs (the `play` trigger was never written).
    - Fixes: `deploy.sh` creates `/tmp/cvmla`; `op()` too; t87 now compares the md5 of a deployed layout file with
      the build and aborts on a mismatch.
    - The first t87c start (also affected) was stopped; t87c restarted on build83 with the verified deploy.
- **t87c (build83, deploy verified) — Classic, Details (all six themes) and Cinema (four themes) measured before it
  was replaced by t87e:**
  - not opaque: **0** in every InfoBar / SecondInfoBar grab (Classic IB 40, SIB 56; Details IB 46, SIB 89; Cinema IB
    34, SIB 44 information widgets checked per grab); 0 tracebacks, 0 skin errors, 0 crash logs.
  - Classic SIB composites: before (build79) the cards turn red / olive with the video; after they stay navy over
    red / yellow / white / dark. Positions unchanged.
  - **Playback bar (MoviePlayer, USB test clip):** opaque, but PVRState showed a **black box** on the bar's third
    row. Cause: infoplate turned its `backgroundColor="transparent"` (#FF000000) into the "Solid" twin #00000000 =
    black. Fixed in build84: a fully transparent own fill takes the colour of the opaque region under it
    (steThemePanel); a bare transparent eLabel (possible video window) is never changed.
  - **Decorative transparency check (share of the screen that stays translucent, before → after, navy):**

| Screen | before | after (build83) |
|---|---|---|
| Classic IB / Details IB / Cinema IB | 0 % (already opaque panels) | unchanged |
| Classic SIB | 46.8 % (the cards themselves) | 0 %; clear area 41.5 % unchanged |
| Cinema SIB | 55.6 % (full-screen scrim) | **0 %: the whole screen became opaque — wrong** |

  - Cause: the full-screen scrim (z 1) got a plate inserted right after it at the same z. Enigma2 draws equal z in
    document order, so the plate is above the scrim, but the "fill" pass compared z only and made the scrim
    opaque. The same affected the SecondInfoBarECM backgrounds of all packs and the Minimal SIB scrim.
  - Fixed in **build85**: equal-z layers use document order. Only those scrims change back (diff: 5 SIB layout
    files); static audit still 0.
- **t87e: build85, five models × six themes (+ playback bar in navy), deploy verified.**
  - 30 restarts: 0 tracebacks, 0 skin errors, 0 crash logs.
  - osd_alpha now classifies every non-opaque pixel inside an information rectangle:
    - *edge*: alpha ≥ 250, the anti-aliased edge of a rounded shape over an opaque base (under 2 % video; invisible);
    - *corner*: inside the 17 px corner squares, outside a rounded pill / card;
    - *REAL*: anything else = a failure.
  - **Result: 0 REAL in 54 of 55 grabs.** 192 widgets have edge/corner pixels only (Modern / Minimal pills).
  - The one failure: Minimal / Purple SIB, description area (y 796–848, alpha 210 = the overlay scrim showing
    through).
    - **t88** re-tested it: Minimal SIB in Purple and Navy, grabbed 2 / 4 / 5 / 6 / 8 / 12 s after opening
      (RunningText starts scrolling at 4 s), two openings each.
    - Result: 24 of 24 grabs 100 % opaque in that area. **Not reproducible.**
    - Most likely the grab read the framebuffer during a repaint (scrim drawn, plate not yet).
    - Recorded as an unexplained single capture, not as a pass.
  - Playback bar (MoviePlayer) on build85: opaque in all five models; the PVRState black box is gone.
  - **Decorative transparency kept (navy, share of the screen):**

| Screen | translucent before | translucent after | clear (unchanged) |
|---|---|---|---|
| Classic SIB | 46.8 % (cards) | 0 % | 41.5 % |
| Cinema SIB | 55.6 % | 21.2 % (scrim around the panel) | 0 % |
| Modern IB / SIB | 31.1 / 49.7 % | 13.2 / 12.8 % (gradients) | 65.2 / 39.5 % |
| Minimal IB / SIB | 23.1 / 50.9 % | 10.9 / 17.3 % | 76.1 / 42.8 % |
| Classic / Details / Cinema IB, Details SIB | 0 % | 0 % | unchanged |

  - **Visual flaw found in the composites:** the new Modern SIB status-row band ended at x 1580, so the SNR / dB
    pills hung past it over the gradient (clear on white video).
    - build86: a row band absorbs the opaque pills of the same row next to it, measured on the pill rectangle.
      Guards: no tall widgets; never under a translucent layer it must cover.
    - The band now spans 46–1850 at z −2, under the pills (z −1), so the pills keep their look.
    - Only the Modern SIB layout changes; static audit 0.
- **t87f: build86, Modern × six themes (+ playback bar):** 0 REAL not-opaque in 13 grabs; 0 tracebacks / skin
  errors / crash logs; the status band spans the whole row (white-video check).
- **Release candidate 1.0.0~rc9 = build86** — SHA256 `0d2336dab8047ba8c1a699cd1d06fa68f21e51e1f94e4e29c856d5c221ee8946`.
  - Maintainer scripts identical to rc8 (control differs only in Version / Source), so the rc8 lifecycle (t86)
    covers rc9's install / upgrade / uninstall / purge logic.
  - **t77 rc9:** upgrade rc8 → rc9 with the GUI running (`install ok installed`), then the five models from the
    installed package, six sections each: 29 grabs, 0 tracebacks, 0 skin errors, 0 crash logs.
  - Published in release/rc (install-mla.sh → rc9; install-mla-rc8.sh keeps rc8). Raw download SHA verified;
    DRYRUN on the receiver passes.
  - Before / after sheets (navy, five models × IB / SIB, real OSD over red / yellow / white / dark):
    `docs/mla/evidence/opaque_<model>_<ib|sib>.jpg`. Visual approval by the user pending.
  - Status: RUNTIME TESTED on Slot 8. NOT final.
- **t68_rc9 — final QA on the INSTALLED rc9 (NO_DEPLOY=1, package 1.0.0~rc9):** five models × six sections
  (InfoBar, SecondInfoBar, channel list, EPG, EventView, PVR: EMC + native MovieSelection) with posters ON and OFF
  (navy), and every model in the six themes (InfoBar, channel list, EventView).
  - 145 grabs, 0 bad; 71 checks: **0 tracebacks, 0 skin errors, 0 crash logs**; movie folder setting unchanged.
  - Grabs: ai-agent `shots/t68_rc9/` (in the rc9 report).
- **t89 — 25-min performance run on the installed rc9 (Modern, navy, posters ON, same round as t67):** 11 rounds;
  RSS 136 → 143 MiB (flat from round 5); threads 12; open files 96 (stable); 0 tracebacks, 0 skin errors, 0 crash
  logs; 4 accelAlloc warnings including the start-up one (no debug attribution in this run; earlier runs
  attributed the remainder to Enigma2's picon cache and DVB subtitles). Classic + native MovieSelection afterwards:
  0 errors.
- Report "CineView MLA Model Review" republished for rc9 (opaque section, t68_rc9 grabs, t89 row);
  video `docs/mla/evidence/video/CineView_MLA_rc9_2026-10-06.mp4`.
- Playback InfoBar:
  - On this receiver the PVR key opens EMC, whose player uses EMC's own skin file
    (`EnhancedMovieCenter/CoolSkin/EMCMediaCenter_1080.xml`), not a CineView screen.
  - The native MoviePlayer screens of the CineView packs are covered statically. From t87 on, the device check
    opens the native MoviePlayer on the USB test clip (devtool `play`, the same call as InfoBar.movieSelected).

## 15. User list 2026-10-06 14:31 (approved: opaque information areas, PIL poster sizing) — remaining items

**Approved by the user (14:31):** the opaque information panels (Main InfoBar, SecondInfoBar, playback bar; video does
not tint them; decorative transparency kept; no position / size change) and the PIL poster method (widget-size copy
made from the original file, original kept as it is; visible size, quality and layout must not change).

**1. Minimal / SecondInfoBar description leak (t87e, once).**
- **t90 (rc9, installed):** 3 receiver reboots (Slot 8 rootsubdir checked before / after); after each reboot
  Purple and Navy × posters ON / OFF; SIB opened and closed 6 times each, OSD grabbed 2 / 4 / 6 s after opening;
  the description band (60..1860 × 780..920) must be alpha 255 everywhere.
- **Reproduced:** reboot 1, Purple, posters ON, FIRST opening after the restart, 4 s: 19 % of the band (rows
  889–919 of the 310,780 1550×140 RunningText, i.e. its bottom 31 rows) showed the scrim's alpha 210. Not on the
  later openings; not on reboot 2's first Purple opening. Trigger proven: RunningText starts to scroll at 4 s
  (`startdelay=4000`). The exact repaint path inside Enigma2 is not proven, and Enigma2 is not modified.
- **Fix (build87):** a scrolling text widget (RunningText) that lies entirely inside one opaque region paints its
  own background in exactly that region's colour (`transparent="0"`, `backgroundColor=<region colour>`), so it no
  longer depends on how the area below is repainted while it scrolls. Same look. Only when nothing else is drawn
  under it inside its rectangle; a No Poster text variant is not blocked by the poster widget of the same toggle
  (that poster is hidden / released in exactly the states the variant is shown). 261 widgets in the InfoBar family.
- **Results** (216 grabs each: 3 reboots × 2 themes × posters ON/OFF × 6 openings × 3 grab times):

| Run | Build | Leaks | Errors | Boot slot after each reboot |
|---|---|---|---|---|
| t90 | rc9 (build86 layouts) | **1 / 216** (reboot 1, Purple, posters ON, opening 1, 4 s) | 0 | linuxrootfs8 ×3 |
| t90b | build87 (scroll-fill) | **0 / 216** | 0 | linuxrootfs8 ×3 |

  - build87 was verified active after the reboots (layout md5; active generation carries `transparent="0"
    backgroundColor="steThemeOverlaySolid"` on the description RunningText). Look unchanged (composite check).
  - One leak in 216 is a low base rate, so 0 / 216 alone is not strong proof. **t93** (queued) repeats only the
    trigger, A/B: the first opening after an Enigma2 restart, Purple, grabs at 3.6 / 3.9 / 4.2 / 4.5 / 5.0 s,
    15 restarts on build86 vs 15 on build87.
  - **t93 result:** build86 0 / 75 grabs, build87 0 / 75 grabs, 0 errors. The focused trigger did NOT reproduce the
    leak on the old layouts either, so the condition is narrower than "first opening after a restart": both real
    occurrences came early after a cold start (t90: first Purple opening after a receiver REBOOT) or in a long
    session (t87e). The A/B therefore cannot separate the builds statistically.
  - **Conclusion (honest):** observed 2 times on rc9 layouts (t87e, t90), 0 times on build87 in 216 + 75 grabs. The
    fix removes the dependence by construction - the leaking rows lie inside the RunningText rectangle, and with
    `transparent="0"` + the region colour the widget itself paints that whole rectangle opaque, whatever was drawn
    below it - but the rarity of the event means its absence on build87 is not, by itself, statistical proof.
    Status: ROOT CAUSE IDENTIFIED (trigger: RunningText scroll start; Enigma2's internal repaint order not proven),
    fix IMPLEMENTED and RUNTIME TESTED without regression; event too rare to prove absence by counting.

**3. Poster cache (final policy).**
- Runtime (unchanged, already shipped): `_mla_cache_plan` = 1. `/media/hdd/poster` when /media/hdd is a real
  read-write block-device mount other than the root filesystem; 2. persistent USB (multiboot media excluded);
  3. `/tmp/CINEVIEW-MLA/poster`. One cache for every design and screen; never deleted by upgrade / remove / purge;
  explicit deletion only with `uninstall-mla.sh cache` + `CONFIRM=yes` (MLA's own `id/` and `sz*/` only).
- Installer for the next RC: no pin by default (release order, HDD first); `HDD_CACHE=0` opts out (pins USB / /tmp);
  an existing setting is kept — this receiver stays pinned to its USB development cache during tests.
- **t92 dedicated HDD test** (user informed before the write):
  - check (read-only): `/dev/sda1` ext4 rw, block device, not the root filesystem, 657 GB free, writable;
    `/media/hdd/poster` already existed, empty, dated 2026-10-03 (kept). The skin's own plan, extracted from the
    installed renderer without importing it and without the development pin: `/media/hdd/poster (HDD (real mount
    /dev/sda1))`. PASS.
  - write: ONE new file `.cineview-mla-hddtest-1791287289-14823.jpg` (exclusive create, 8738 bytes, a copy of a USB
    cache poster), write + fsync 3.9 ms, read back identical, removed; the folder empty again as before (only its
    modification time changed). Nothing else listed, deleted, renamed or moved; no mount change; no fsck. PASS.

**t91 (build87 deployed, on top of the rc9 package):** 180 grabs, 0 bad; 31 checks: 0 tracebacks, 0 skin errors,
0 crash logs; `config.usage.show_second_infobar` restored to its original value ('2') after every model; movie folder
setting unchanged.
- **2. SecondInfoBarECM** (setting = ECM only during the test): the five ECM screens have ONE poster element, a
  `CineViewMLAPosterX underlay="1"` at 1535,28 300×390, with no frame or card around it; without a real poster the
  renderer hides itself and drops its picture (`_release`). Grabs, five models: HBO (poster) → poster on the
  right; HRT1 (no poster) and posters OFF → plain panel, no placeholder, no empty frame, no overlap; the text keeps
  its native width (Enigma2's own named `channel` / `epg_description` widgets are not resized - no runtime resizing
  in 1.0.0, as decided). Minimal / Classic posters OFF use their `_CVPosterOff` ECM screen (full-width text).
- **4. No Poster pairs incl. Classic** (navy, posters ON): InfoBar, EPG card, EMC rows, MovieSelection rows on HBO
  (film, poster) vs HRT1 (news) for all five models (`shots/t91/<model>_{ib,epg}_{hbo,hrt1}`, `_emc_0..4`,
  `_ms_0..4`). Classic: InfoBar poster + picon with a poster, picon in the poster's place without; EPG description
  starts at the left without a poster; Classic EMC shows its live-TV preview window (no poster place by design).
- **5. Picons under fast channel switching:** per model 3 bursts of 8 CH+/CH− zaps + a single zap; grabs 0.3 / 1 /
  2.5 s after a burst and 0.3 / 1.3 s after the single zap (the zaps really changed channel: Kino TV, HBO 3,
  Cinemax 2, Cinemax, CineStar Action, CineStar 2); the InfoBar's picon places cut out on one sheet per model
  (`picons_<model>.png`, `t91_picons.py`): **one picon per place in every grab of Classic, Details, Cinema and
  Modern (60 grabs)**, no fallback or second logo; Minimal has no picon in its InfoBar (thumbnail + name): its
  15 grabs show the thumbnail with a poster and the No Poster layout without, never a stray logo. Channel list
  grabs while the cursor runs: `csfast_<model>.png`.

**Release candidate 1.0.0~rc10 = build87** — SHA256 `d90ea53515e9fb9ec3e262c700786ac094a515e24f4a5a4060d208afee86387c`
(published in release/rc; `install-mla.sh` = rc10 with the final cache policy; `install-mla-rc9.sh` keeps rc9).
- **t87g** (build87, five models × navy / purple + playback bar): 889 information widgets checked, **0 real
  not-opaque**, 74 edge / corner-only; 0 errors.
- **t86_rc10 lifecycle:** upgrade rc9 → rc10 with the GUI running (Modern kept, selection rebuilt g000176) → reboot
  (linuxrootfs8) → normal uninstall (image skin; state kept) → fresh install (factory Classic) → purge → restore:
  every step 0 tracebacks / skin errors / crash logs; poster cache 1035 files throughout.
- **t77_rc10 short final QA** (installed rc10): five models × six sections, 30 grabs, 12 checks, 0 errors.
- **Real installer from GitHub** on the receiver: compatibility checks, download, sha256 OK, backup; opkg then
  refused because the same version was already installed ("nothing was changed by this script") - correct.
- **Installer cache step** (the block exactly as shipped, pointed at a scratch runtime.json in /tmp; the real setting
  untouched): existing pin → kept; no pin → `/media/hdd/poster (HDD /dev/sda1, read-write mount)`, nothing written;
  no pin + `HDD_CACHE=0` → pinned off the HDD (/tmp on this receiver: its USB stick is Slot 8's root device and is
  excluded on purpose).
- `/media/hdd/poster` after all tests: empty, mtime 2026-10-06 14:48:09 (t92) - no other test wrote there.
- Report "CineView MLA Model Review" version 3 = the 1.0.0 review (release status table first).
- Status: RELEASE CANDIDATE on Slot 8 - **not released**; waiting for the user's approval.

**User 19:25:** approved visually - the rc10 scrolling-text fill, and SecondInfoBarECM without a poster in Classic,
Modern and Minimal. Classic No Poster approval pending on one PVR/EMC grab (HRT1 news selected, preview area empty;
HBO poster recording for comparison).
- Finding (no new test; t91 grabs of build87 = rc10): in Classic, the PVR box at the top left is NOT a poster area.
  With Classic active CineView defines no EMC screen, so EMC uses its own skin (`CoolSkin/EMCSelection_left_pig_1080.xml`:
  `render="Pig"` live TV 70,100 438×220, plus EMC's native `Cover` widget used only with EMC's own cover option);
  Classic's native MovieSelection uses `PigTemplate` (live TV) too. Both show the LIVE channel whatever recording is
  selected (HBO "Ples malog pingvina" and HRT1 "Dnevnik" alike); no poster and no placeholder in either.
  An empty box there would mean hiding EMC's live preview / a new Classic EMC screen = a Classic design change,
  not done without the user's decision. Sheet: `docs/mla/evidence/classic_pvr_hbo_vs_hrt1.jpg`.

**User 19:54 - final decisions (not to be reopened):** scrolling-text fill APPROVED; SecondInfoBarECM without a poster
APPROVED; Classic PVR / EMC APPROVED AS IT IS (native live-TV preview, no poster box). No further design change to
these. Remaining: Stage A documentation, Stage B 1.0.0 package from the build87 files (version only) + upgrade /
reboot / quick five-model check + receiver-captured video, Stage C release only after the user's explicit approval.

## 16. Stage B — 1.0.0 package (2026-10-06 20:00–20:40)
- `enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk`, SHA256 `33ac3843a668b03c35f3163abbdf5aecd7d2edc1e72fc5cb9505ea5597c007a8`,
  packaged from build87 (commit bf30b71). Compared with rc10: data payload identical (590 files + symlinks, `diff -r
  --no-dereference`), the 4 maintainer scripts identical; control differs only in `Version` (1.0.0~rc10 → 1.0.0) and
  `Source`. Staged on ai-agent `final100/` - NOT published (Stage C needs the user's approval).
- **t94 (receiver):** package copied to persistent storage (SHA verified there) → Modern selected → `opkg install`
  with Enigma2 RUNNING ("your design selection was rebuilt", g000009; enigma2 kept running) → GUI restart: `1.0.0 install
  ok installed`, selection Modern → receiver REBOOT: linuxrootfs8, 1.0.0, Modern → quick pass Classic / Details / Cinema /
  Modern / Minimal (InfoBar, channel list) → restore Classic navy. 13 checks: 0 tracebacks, 0 skin errors, 0 crash logs.
- **t94b:** t94's SecondInfoBar step pressed OK while the InfoBar was still open (it closed the InfoBar, the SIB never
  opened), so those frames showed only video. Re-recorded the SIB step alone for the five models on the installed
  1.0.0; all five SIBs captured; 0 errors. (A test-script sequencing fault, not a skin issue.)
- Video `CineView_MLA_1.0.0_stageB_2026-10-06.mp4`: the receiver's own frames (grab jpg 1280×720, 5–7 fps as captured)
  of every step, with build / commit / change / test / remaining on the cards.
