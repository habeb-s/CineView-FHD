# CineView MLA 1.0.0 — release notes

**CineView MLA — Design & Development by habeb-s © 2026**

| | |
|---|---|
| Package | `enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk` |
| SHA256 | `273f9dfbea2e50d3cc31a3b85cc56b13d170a3df6d55f53352b7d39b2676d6eb` |
| Build | build94, commit 9e68174 (branch `dev/mla-openatv`) — `version.json` in the plugin folder carries version / build / commit |
| Target | Vu+ Duo 4K SE, OpenATV 8.0.1 (Python 3.14) — the receiver this release was verified on |
| Status | RELEASE CANDIDATE until the owner approves the release |

## What is in 1.0.0
- Five design models (Classic, Details, Cinema, Modern, Minimal) on six sections (InfoBar, SecondInfoBar, channel
  list, EPG, EventView, PVR), six colour themes, chosen in **CineView Designs** (Plugins menu).
- Posters: widget-size copy made from the original file (original untouched); a real No Poster layout when an event
  has no poster — never a placeholder.
- Information areas of the InfoBar, SecondInfoBar and playback bar are fully opaque in the theme colour; the decorative
  scrims around them stay translucent.
- SecondInfoBarECM without a poster: plain panel, no placeholder.
- Classic PVR / EMC keeps its native live-TV preview (no poster box) by design.
- Plugin icon and logo (option A); rights line in CineView Designs and the package data.
- Plugin / package management: the busy dialog (Processing) in CineView style, one wait message instead of two,
  colour keys only when they have a function, mode title (Install / Remove / Update Plugins) in Plugin Manager.
- CineView Designs: final wording (Apply Design, Restore Factory Design, no development details on screen), a real
  receiver preview for every design and theme, Posters On/Off pictures, CineView Info Card for options without a
  picture, readable values (checklist: docs/mla/CineView_Designs_Checklist.md).
- Message boxes fit their content; Setup pages: 27 px values, whole rows; Burgundy: readable red key text.

## Install
On the receiver (telnet / ssh):

```
wget -q -O /tmp/install-mla.sh "https://raw.githubusercontent.com/habeb-s/CineView-FHD/dev/mla-openatv/release/rc/install-mla.sh" && sh /tmp/install-mla.sh
```

- Checks only: `DRYRUN=1 sh /tmp/install-mla.sh`. Every check runs before anything is installed.
- Then select **CineView_FHD_MLA** in Menu > Setup > User Interface > Skin and restart the GUI.
- The package refuses images other than OpenATV 8.0.x with Python 3.14 (clear message, nothing changed).

## Poster cache
One cache for every design and screen, chosen at Enigma2 start:
1. `/media/hdd/poster` when `/media/hdd` is a real read-write mount of a block device;
2. persistent USB;
3. `/tmp` (last resort, lost at reboot).

`HDD_CACHE=0 sh /tmp/install-mla.sh` keeps it off the HDD. The cache is never deleted by an upgrade or a normal
removal; `CONFIRM=yes sh /tmp/uninstall-mla.sh cache` deletes only CineView MLA's own cache folders.

## Uninstall / rollback
- Select another skin first, then `sh /tmp/uninstall-mla.sh` (keeps `/etc/enigma2/cineview_mla`) or
  `sh /tmp/uninstall-mla.sh purge` (removes it too).
- Earlier release candidates stay installable: `install-mla-rc10.sh`, `install-mla-rc9.sh` in `release/rc/`.
- Inside CineView Designs: **Factory design** restores Classic / Navy; every applied design is a sealed generation
  with automatic rollback to the last known good one.

## Verified on the receiver (Slot 8)
Package screens t97 (build90): Install / Remove / Update Plugins lists, Plugin Action Log, Processing (one and several
lines) before/after - 0 tracebacks, 0 skin errors. Final package t95 (build88): install with the GUI running, five models, reboot, Plugin Browser + CineView Designs, Python check —
0 tracebacks, 0 skin errors, 0 crash logs, 0 plugin load errors. Earlier on the same skin files: full lifecycle
(upgrade / reboot / uninstall / fresh install / purge / restore), final QA of five models × six sections, opaque
information areas over red / yellow / white / dark video, picons under fast zapping, No Poster pairs, 25-minute
performance run, dedicated HDD cache test. Evidence: `docs/mla/Morning_Run_2026-10-05_evidence.md`.

## Known limits
- The Processing dialog has square corners: a rounded window broke the redraw of the screen behind it on the
  receiver (evidence section 18).
- Built and verified for OpenATV 8.0.1 / Python 3.14 on the Vu+ Duo 4K SE; other receivers and images are outside 1.0.0.
- Minimal SecondInfoBar: a one-frame description leak seen twice on rc9 at the moment the text starts to scroll was
  fixed in rc10 (the scrolling text paints its own background); not seen since, but the event was too rare to prove
  its absence by counting.
