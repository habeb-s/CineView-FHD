# CineView MLA — five integrated models (plan and status)

User order 2026-10-04 22:06: five integrated models — **Classic, Details, Cinema, Modern, Minimal**. Each one is a
visual identity across the skin, not only InfoBar variants. Every screen stays independently selectable in
CineView Designs; a **profile** applies one model to all sections at once.

## Sections per model
The sections are InfoBar, SecondInfoBar, Channel Selection, EPG (Graphical / Single / Multi / Quick / InfoBar EPG),
PVR (MovieSelection; EMC stays EMC-native) and EventView. Shared core screens (Plugin Browser, Quick Menu, Setup,
removal/log screens) keep one CineView presentation for all models; only the theme colours change.

Status words: **tested** = implemented and exercised on the receiver (Slot 8); **approved** = the user approved the
look; **pending** = the user still has to approve it.

Status as of 2026-10-05 midday (build63, Slot 8). **RT** = RUNTIME TESTED on the receiver with posters ON and OFF;
**approved** = the user approved the look; **pending** = look awaiting approval.

| Section | Classic | Details | Cinema | Modern | Minimal |
|---|---|---|---|---|---|
| InfoBar | RT, approved | RT (P7), pending | RT (P7), pending | RT (t43, t57), direction approved | RT (t63), pending |
| SecondInfoBar | RT, approved | RT (P7), pending | RT (P7), pending | RT (t57b), direction approved | RT (t63), pending |
| Channel Selection | RT, approved | Poster List: RT, direction approved | Video First: RT, direction approved | RT (t57b; bouquet name from Title), direction approved | RT (t63), pending |
| EPG — Graphical | RT, approved | Graphical Plus: RT (t55), approved | Graphical Plus (shared) | Modern grid: RT (t57) | RT (t63), pending |
| EPG — Vertical | Classic | — | — | — | — ; **Columns** pack (any model): RT (t58), approved |
| PVR (native MovieSelection + EMC) | native; EMC keeps its own skin (fallback) | Cover Library: RT (t61b–d) | **Cinema Shelf**: RT (t66/t66b) | RT (t61b–d) | RT (t63) |
| EventView | Classic + line-by-line, RT | **Details Card**: RT (t66/t66b) | Feature: RT (t64b; description fixed) | RT (t57b, t65; one fixed picon) | RT (t63) |

Every model now owns all six sections; the CineView MLA menu "Apply a design model to every section" applies
`MODELS` in `mla/plugin/CineViewMLA/plugin.py`. Single / Multi / Quick / InfoBar EPG stay Classic in every model.

## Mapping proposal (pending approval)
- **Details**: InfoBar/SIB Details, Channel Selection *Poster List*, EPG *Graphical Plus*, PVR *Cover Library*, EventView *Details card*.
- **Cinema**: InfoBar/SIB Cinema, Channel Selection *Video First (left/right)*, EPG Graphical Plus in the Cinema layout,
  EventView *Feature* (big poster).
- **Modern**: rounded floating cards and chips. `cornerRadius` and gradients exist in 57b7a51 skin.py; they are not
  yet verified on this receiver, and that check comes first.
- **Minimal**: low occlusion. Gradient scrims instead of boxes; an InfoBar under 12 % of the picture; small optional posters.

## PVR and EventView plans (§4, contracts checked in 57b7a51 source)
**PVR — Cover Library (Details).** MovieSelection has no native cover grid. `self["list"]` is `MovieList`, a
fixed-row eListbox whose row height comes from `itemsperpage`. Drawing a grid would mean writing a new list
class, which is forbidden ("no invented target widgets"). Plan:
- Keep the native list, at 6 rows.
- Add a large cover of the SELECTED recording: `CineViewMLAPosterX` on `source="Service"` (ServiceEvent).
  `_source_event` already reads a ServiceEvent's event; the device test must confirm that a recording's
  meta event resolves to an identity.
- Below the cover: title, recording date, channel, duration and description, plus the native free-space and
  trash widgets.
- Keep `PigTemplate` and the coloured keys. EMC stays EMC-native.
- Posters OFF: the list widens to the full width (named widget → `MovieSelection_CVPosterOff` through the
  CineView MLA plugin, the same mechanism as EPG).
- Device tests needed: real recordings on USB in Slot 8 only. HDD recordings may only be read: no writing,
  no deleting.

**EventView — Feature (Cinema).** Native `EventView*` widgets (EventView.py, verified): Event, Service,
`epg_description`, `FullDescription`, `datetime`, `duration`, `channel`, key_* (skinName list `[<skin>, "EventView"]`). Plan:
- A big poster (400x600) on the left. Title, times, genre and IMDb (reliable only) in a column, and the
  description in the native ScrollLabel (paging stays native).
- Both description motions (`classic` / `classic-lines`) remain options. Neither is forced.
- Posters OFF: the description spans the full width (`_CVPosterOff` screen).

**Order after the user's look decision:** Modern InfoBar (device run t43) → Modern SIB / CS / EPG /
EventView → Minimal → PVR Cover Library → EventView Feature.

## Rules for every design
- **Posters ON / OFF.** OFF reflows the screen: no hole, no reserved frame.
  - Named Python widgets use `<screen>_CVPosterOff` screens through the CineView MLA plugin.
  - Source widgets use `CineViewMLAShowIf`.
- **Six themes.**
- **Arabic and English**, with long texts.
- **Fast navigation**: no stale poster.
- **Live values** checked against OpenWebif.
- **Z-order / overlap checks**: `zorder_check.py --posters`.
- **Save / restore / automatic revert** through the engine.
- **No unreliable posters or IMDb ratings.**
- **Performance**: no growth of RSS, threads or poster cache.

## Device findings, night of 2026-10-04
- **Graphical Plus** (build35 t37, build36 t40): opens in all six themes. Details follow the highlighted cell
  (Bajkeri → Holland → Kaskader). Posters OFF selects `GraphicalEPG_CVPosterOff`: the grid widens to 1540 px
  (~3 h at the default 180-min setting) with no reserved poster space. build35 had a SkinError (`date` widget);
  fixed in build36, which runs with 0 tracebacks and 0 skin errors. In the OFF panel the title shrank to 2 lines
  and the description is left-aligned (justified 240 px text had wide gaps).
- **Vertical EPG (Columns study).** The visible screen was only a numbered channel list. Cause: the inherited
  CineView screen draws `self["list"]` (a MenuList used only as the page index by EpgSelection.py) at 1730x700,
  z=19, over the five columns. This defect already exists in the golden skin. Fix (build37): the native
  contract (receiver `skin_default.xml`, "DO NOT CHANGE THIS LINE"): zero width, z=-10, 5 rows (3 for PIG).
  Device check t42: five columns visible, navigation works. **Columns is feasible on the native vertical EPG**
  (list1..list5, piconCh/currCh/Active), with no new widgets. Its look is to be proposed after the Modern
  decision.
- **Modern skin features (t41, OSD alpha measured).** These work: cornerRadius all/top on eLabel, Label and
  ePixmap; the 80 % card; the gradient with alpha blending. `borderWidth` on a rounded translucent eLabel is not
  drawn.
- **Modern InfoBar (t43).** Runs on the receiver: posters ON/OFF, six themes, AR/EN, live values equal to
  OpenWebif. The look is pending.

## Order of work (autonomous run 2026-10-04 night)
1. Fixes from the user's video review: name clip scope, Video First dimming, poster tests, EventView AR/EN.
2. EPG Graphical Plus: implement and test.
3. Study the `EPGvertical` flow for Columns.
4. Long soak tests (memory, CPU, threads, cache).
5. Modern / Minimal mockups for approval.
6. After approval: generate the packs and test them on the device. Then PVR Cover Library and EventView Feature.
