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

| Section | Classic | Details | Cinema | Modern | Minimal |
|---|---|---|---|---|---|
| InfoBar | tested, approved | tested (P7), pending | tested (P7), pending | mockup, pending | mockup, pending |
| SecondInfoBar | tested, approved | tested (P7), pending | tested (P7), pending | mockup, pending | mockup, pending |
| Channel Selection | tested, approved | Poster List: tested, look approved in direction | Video First L/R: tested, look approved in direction | mockup, pending | mockup, pending |
| EPG — Graphical | tested, approved | Graphical Plus: device-tested build36 (ON/OFF, 6 themes, cursor follow), look pending | — (proposal: Graphical Plus with the Cinema palette) | mockup, pending | mockup, pending |
| EPG — Single / Multi / Quick / InfoBar | tested, approved (Classic only) | uses Classic | uses Classic | not started | not started |
| PVR | Classic, tested | Cover Library: planned | — | not started | not started |
| EventView | Classic + "line by line" option, tested | — | Feature: planned | mockup, pending | mockup, pending |

**Approved-and-tested section count per model** (out of the 6 sections IB, SIB, CS, EPG, PVR, EV):
- Classic 6/6.
- Details 0/6 approved. IB, SIB and CS are tested but the final look is not yet approved; Graphical Plus is in test.
- Cinema 0/6 approved. IB, SIB and CS are tested, look pending.
- Modern 0/6 (mockups).
- Minimal 0/6 (mockups).

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

**EventView — Feature (Cinema).** Native `EventViewSimple` / `EventViewEPGSelect` sources: Event, Service,
`epg_description` (ScrollLabel), key_*. Plan:
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
  Device check t42 is queued. The Columns design decision waits for that run.
- **Modern skin features**: the probe `CineViewMLAFeatureProbe` and t41 are queued (cornerRadius all/top,
  border, 80 % card, gradient with alpha blending, rounded Label background, rounded ePixmap).

## Order of work (autonomous run 2026-10-04 night)
1. Fixes from the user's video review: name clip scope, Video First dimming, poster tests, EventView AR/EN.
2. EPG Graphical Plus: implement and test.
3. Study the `EPGvertical` flow for Columns.
4. Long soak tests (memory, CPU, threads, cache).
5. Modern / Minimal mockups for approval.
6. After approval: generate the packs and test them on the device. Then PVR Cover Library and EventView Feature.
