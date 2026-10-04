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
| EPG — Graphical | tested, approved | Graphical Plus: implementation approved, device tests running | — (proposal: Graphical Plus with the Cinema palette) | mockup, pending | mockup, pending |
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

## Order of work (autonomous run 2026-10-04 night)
1. Fixes from the user's video review: name clip scope, Video First dimming, poster tests, EventView AR/EN.
2. EPG Graphical Plus: implement and test.
3. Study the `EPGvertical` flow for Columns.
4. Long soak tests (memory, CPU, threads, cache).
5. Modern / Minimal mockups for approval.
6. After approval: generate the packs and test them on the device. Then PVR Cover Library and EventView Feature.
