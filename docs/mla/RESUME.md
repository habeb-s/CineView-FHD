# CineView MLA: resume point (updated 2026-10-05 23:58 Riyadh)

| Item | Value |
|---|---|
| Last build | build77 = PIL widget-size posters (no gPixmap) + No Poster layout incl. EPG / PVR cards + ShowIf Picon fix |
| Builds | build71 = rc6 files; build73 No Poster infra; build74 EPG cards; build75 PIL sizing; build76 PVR cards; build77 ShowIf fix |
| Packages | rc5 / rc5.1 published (`release/rc`); rc6 (build71) on ai-agent only; rc7 (build77) queued (q85) |
| Receiver | Slot 8, Vu+ Duo 4K SE, OpenATV 8.0.1; rc6 installed, build deployed over it by the tests |
| Last successful tests | t81a / t81b (attribution), t82 (No Poster, 5 models, clean), **t83 (CineView accelAlloc share 0)** |
| Queue on ai-agent | t84 (build77: EPG / PVR / InfoBar No Poster + Classic EV picon) → q85: package rc7 if t84 clean → t77.sh rc7 install test |
| Last commit | see `git log -1` on dev/mla-openatv |

## Next steps after the queue
1. t84 grabs: EPG cards, PVR rows (EMC + MovieSelection), InfoBar, Classic EventView strip picon.
2. t77_rc7.log: install from the package, five models, 0 errors → publish rc7 in `release/rc` (+ SHA256SUMS,
   installer pointing to rc7), only if clean.
3. Report page (`make_report.py`) → publish as an artifact.
4. Second device (DM900, OpenATV 7.6.0): posters not shown; needs `diag-mla.sh` output from that receiver.
   - rc5.1 (build70) default cache was `/media/usb/...`; without a USB stick that path is created on the root
     filesystem (flash). rc6+ uses real mounts only.
   - rc6+ release order puts posters on `/media/hdd/poster` when an HDD is mounted. **Tell the user before they
     install rc6/rc7 on the DM900.**

## Known limitation
- SecondInfoBarECM (non-default SIB mode, Python-owned named widgets, screen created once) keeps the placeholder.

## Rules (unchanged)
- Slot 8 and dev/mla-openatv only.
- No main, no HDD writes, no other slots, no Multiboot or tuner changes.
- No final release without the user's approval.
