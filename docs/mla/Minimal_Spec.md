# CineView Minimal — specification (six sections)

Status: **draft for approval** (user decision 2026-10-05 05:23: approve the direction, then a full spec, then
rendered mockups before the final look). Target: OpenATV 8.0.1 / enigma2 57b7a51, 1920x1080, Slot 8.

## 1. Identity: what makes Minimal different from Modern

| | Modern | Minimal |
|---|---|---|
| Surfaces | floating rounded cards (cornerRadius 28), opaque pills | **no cards**: text sits on a soft scrim tinted with the theme colour |
| Structure | boxes and chips | **typography and hairlines**: size, weight and spacing carry the hierarchy |
| Technical data | always-visible chips (HD, 1920×1080, 16:9, SNR, dB) | **hidden by default**; one plain text line in the expanded view only |
| Height | InfoBar card 250 px | InfoBar **130 px** (12 % of the screen) |
| Posters | 146x218 in the bar | **small thumbnails** (70x105 in the bar), larger only when expanded |
| Accent | pills and progress fill | **one accent per screen**: the progress hairline or the selection mark |
| Corners | rounded everywhere | **square**; only the poster has a 6 px radius |

Rules:
- At most **two text sizes per block**, and at most **one accent colour** per screen.
- **No borders and no frames** (t41: `borderWidth` is not drawn on rounded translucent labels anyway).
- **Details on demand.** Each layer shows only the essentials. The next layer, opened with the native key
  the screen already has, shows more: InfoBar → (OK) SecondInfoBar → (INFO) EventView. Channel list → (INFO)
  EventView. No new keys or actions.
- **Every value is live.** Nothing fixed, the same converters as Classic. IMDb appears only when the identity is
  reliable; genre only when the EPG has it.

## 2. Colour (six themes)

Theme roles from the existing theme files. No new colour constants per theme.

| Role | Use in Minimal | navy | black | burgundy | graphite | green | purple |
|---|---|---|---|---|---|---|---|
| `steThemePrimary` | scrim tint (gradient end, alpha 0x24 ≈ 86 %) | #0A1D35 | #000000 | #501C2C | #292D32 | #153B2B | #38204F |
| `steThemeAccent` / `secondFG` | progress hairline, selection mark, "NOW"/"NEXT" | #F9C731 | (same) | | | | |
| `steThemeText` | primary text | #F0F0F0 | (same) | | | | |
| `grey` | secondary text (channel, times, next) | Classic grey | | | | | |

- **Scrims.** `backgroundColor="#ff000000,#24RRGGBB,vertical,1"`: transparent at the top, theme colour at the
  bottom. The build fills in RRGGBB per theme, the same way `steThemeCard` is generated today. The gradient with
  alpha blending is verified on the receiver (t41).
- **Contrast over video.** Text sits only on the darkest 45 % of the scrim (alpha ≥ 0xA0). Checked per theme on
  bright frames (HRT1 stage scene), as for Video First.

## 3. Sections — layout, posters ON / OFF, native contract

All coordinates are 1920x1080. "x0" is where text starts: **ON** = after the thumbnail, **OFF** = 60. OFF is a
real reflow: no thumbnail, no placeholder, no reserved gap. Source widgets switch with `CineViewMLAShowIf`;
named Python widgets use `<screen>_CVPosterOff` through the CineView MLA plugin (proven mechanism).

### 3.1 InfoBar (`InfoBar`; `RadioInfoBar` stays Classic)
- **Scrim:** 0,880 → 1920x200.
- **Thumbnail:** 60,948, 70x105 (ON only).
- **Text:** x0 = 150 (ON) / 60 (OFF).

| Element | Geometry | Source / converter |
|---|---|---|
| Number · channel name | x0,960, 1080x30, 24, grey | ChannelNumber + ServiceName NameOnly |
| Now title | x0,994, 1060x44, 34, text, single line, swims if long | session.Event_Now EventName Name (+ RTL variant) |
| Progress hairline | x0,1046, 1060x3, accent fill on a faint track | EventTime Progress |
| Times | 1240,960, 620x30, 24, right-aligned | EventTime Start/End + ClockToText |
| Next | 1240,1000, 620x34, 26, grey, right-aligned: "HH:MM  title" | session.Event_Next |

Nothing technical is shown. Recording and timer state appear as a single accent dot before the times
(native RecordState).

### 3.2 SecondInfoBar (`SecondInfoBar`, `SecondInfoBarSimple`): the expanded layer
- **Scrim:** 0,500 → 1920x580.
- **Poster:** 60,640, 220x330 (ON).
- **Text:** x0 = 310 (ON) / 60 (OFF).
- **Content:**
  - "NOW  HH:MM – HH:MM" (accent, 22).
  - Title (40, up to 2 lines).
  - Description (23, 5 lines, swims).
  - Hairline at y 920.
  - "NEXT  HH:MM  title" (26, grey).
  - Next description (21, 2 lines).
- **Tech line** at y 1040, grey 20, plain text:
  "16.0°E · DVB-S2 11636 H · 1920×1080 · 16:9 · SNR 72 % · 11.6 dB" (live converters, values separated by " · ").
- `SecondInfoBarECM` stays Classic.

### 3.3 Channel Selection (`ChannelSelection`, `ChannelSelectionRadio`, `SimpleChannelSelection`)
- **List column:** 0..820 on a horizontal scrim (theme tint, alpha ≈ 0x28). The video stays visible to its right.
- **Rows:** 50 px. Number (grey 21), name (25), now title (20, grey) in one line.
  - The selected row gets a 4 px accent bar at its left edge and brighter text; there is no row background box.
  - Name clipping uses the same native-contract fix as Video First (cell narrowed by the picon offset).
- **Info area for the cursor row:**
  - Position: 900,760 (OFF) / 1070,760 (ON, after a 140x210 thumbnail at 900,750).
  - Contents: title (34, 1 line), "times · genre" (22, accent), description (21, 4 lines).
- **Sources:** `ServiceEvent` (follows the cursor, not the playing channel; same rule as Poster List).
- **Contract:** the list is the native `list` widget; skin only sets font, item height and colours.

### 3.4 EPG
- **Graphical (`GraphicalEPG`).**
  - **Header** for the selected cell (`Event` / `Service` sources):
    - title (34);
    - "channel · times · duration" (22, accent);
    - description (21, 2 lines).
  - **Thumbnail:** 60,40, 110x165 (ON); text starts at x0 = 196 (ON) / 60 (OFF).
  - **Grid:** the native `list` at 60,260, 1800x700. Cell colours are theme roles. No cell borders beyond
    the native 1 px separator. The selected cell is an accent outline via the native selection colour.
  - **Time span:** the user's setting (default 3 h). The OFF header simply starts at x 60; the grid is already
    full width.
  - **Keys:** small colour bars with grey captions on one line at y 1000 (native key_* sources).
- **Single / Multi / QuickEPG / InfoBar EPG.** The same header (selected event) above the native list; the list
  uses the full width below it. Posters ON = header thumbnail.

### 3.5 PVR (`MovieSelection`; EMC stays EMC-native)
- **List:** the native `MovieList` at 60,120, 1800x640 (rows from `itemsperpage`; font sizes via the existing
  skin attributes).
- **Details strip** at y 790 for the selected recording (`Service` = ServiceEvent of the recording):
  - title (34);
  - "date · channel · duration" (22, accent);
  - description (21, 3 lines).
- **Posters:** ON = cover thumbnail 110x165 at 60,790, text from x0 = 196; OFF = text from 60.
  - `CineViewMLAPosterX` on `Service` must be verified on real recordings in Slot 8 USB storage only. HDD
    recordings may only be read.
- **Kept:** native free-space / trash widgets as one grey line at y 1000; native coloured keys.
- **Not shown:** the PiG (Minimal shows no picture-in-picture here; playback preview stays native).

### 3.6 EventView (`EventView` dashboard, `EventViewSimple`, `InfoBarEventView`, `EventViewEPGSelect` via the plugin rule)
- **Reading layout:** a darkened full screen (theme tint, alpha ≈ 0x30) with one centred text column 360..1560.
- **ON:**
  - Thumbnail 200x300 at 360,120.
  - "channel · times" (24, accent) and the title (46, 2 lines) to the right of it, from x 590.
  - Description below from y 450 (24, 13 lines).
- **OFF:**
  - Meta line and title from x 360.
  - Description directly under the title (18 lines).
- **Bottom:** "NEXT  HH:MM  title" at y 960 (grey), then coloured-key captions (native `ColorButtonsSequence`, as in
  Classic since build45).
- **Description motion:** both motions remain options (continuous / line by line with restart-to-top).
- The EPG rule stays: an event of another channel or a later time gets the event-based screen
  (`EventViewSimple`), never the live dashboard.

## 4. Behaviour and tests (per section, before any approval request)
1. Posters ON / OFF: real reflow; `zorder_check --posters` with 0 overlaps; device grabs of both.
2. Six themes: scrim tint per theme, text contrast on a bright frame.
3. Arabic and English, long titles and descriptions: right-aligned RTL variants, no clipping, no overlap.
4. Fast navigation (Channel Selection, EPG): information follows the cursor; 0 stale posters (postercheck with a
   slow reference).
5. Live values equal to OpenWebif (SNR, dB, times, titles).
6. Save / restore / automatic revert through the engine.
7. Performance: soak with Minimal active; accelAlloc tracked as a known issue.

## 5. Open questions for the look approval
- Should the InfoBar show the next programme (right side) or only now? Minimal keeps it now.
- Should the channel list keep picons? The spec keeps them, at 60 % of Classic size.
- How strong should the scrim be over very bright video? The spec uses alpha 0x24 at the bottom; the mockups
  show it on a real HRT1 frame.
