# CineView MLA 1.0.0

**Design & Development by habeb-s © 2026**

The first release of CineView MLA — a multi-layout Full-HD skin for OpenATV 8.0.

## What's inside
- Five design models: **Classic, Details, Cinema, Modern, Minimal**.
- One design per section, chosen independently: InfoBar, Second InfoBar, Channel Selection, EPG, PVR, Event View.
- Posters On / Off per section — the screen is re-arranged when posters are off.
- Six themes: Dark Navy, Black, Graphite, Deep Purple, Burgundy, Dark Green.
- **CineView Designs** (Plugin Browser): real previews of every design and theme, posters on/off pictures, a short
  card for every option, profiles and design models, and Restore Factory Design.
- Poster engine with verified matching (title, type and year).
- Safe apply: a new design is kept only after you confirm it; otherwise the previous design comes back by itself.
- Fitted message boxes, readable setup values, CineView style for plugin and package management screens.

## Compatibility
- OpenATV 8.0 (Python 3.14) on Enigma2 receivers. Fully tested on Vu+ Duo 4K SE / OpenATV 8.0.1.
- The Smart Installer checks the receiver first and changes nothing when something does not fit.

## Install / update
```sh
wget -qO /tmp/cineview-install.sh "@INSTALLER_URL@" && sh /tmp/cineview-install.sh
```
Running it again updates in place and keeps your design, theme, profiles, settings and poster cache.

## Package
`enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk` — SHA256 `@PKG_SHA@`
