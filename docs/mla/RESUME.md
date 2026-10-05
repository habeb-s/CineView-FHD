# CineView MLA: resume point (updated 2026-10-05 22:55 Riyadh)

| Item | Value |
|---|---|
| Last build | build76: build75 (PIL widget-size posters) + No Poster cards on GraphicalEPG and PVR |
| Builds | build71 = rc6 files; build73 = No Poster infrastructure (52 dynamic screens); build74 = + EPG cards; build75 = + PIL sizing; build76 = + PVR cards (58 dynamic) |
| Packages | rc5 / rc5.1 published (dev/mla-openatv `release/rc`); rc6 (build71) on ai-agent only, installed on Slot 8 |
| Receiver | Slot 8, Vu+ Duo 4K SE, OpenATV 8.0.1, rc6 installed (reinst.sh, 22:36) |
| Last successful tests | t81a (attribution: picons 42.9 %, CineView first decode 42.9 %, 1536×1024 14.3 %), reinst rc6 OK |
| Queue on ai-agent | t81b (rc6 installed) → q82: t82 (build73 No Poster IB/SIB/CS/EV) → q83: t83 (build75, sz/ aside, attribution) → q84: t84 (build76 EPG/PVR No Poster cards) |
| Last commit | see `git log -1` on dev/mla-openatv |

## Next steps after the queue
1. t81b vs t81a: before/after rc6 (same build files, installed package vs deploy).
2. t83: the CineView share should be 0. Check `sized make` count, `sz.t83pil` vs `sz` (identical posters, A/B).
3. t82 / t84 grabs: No Poster layout on every dynamic screen; prepare a visual sheet for the user's approval.
4. Second device (DM900, OpenATV 7.6.0): posters not shown. rc5.1 = build70 had the development cache default
   (/media/usb/...). rc6+ has the release order (HDD real mount → USB → /tmp). **Installing rc6 on the DM900
   would write posters to its HDD if one is mounted.** The user must be told before that. Run `diag-mla.sh` there.
5. Final report page (`make_report.py`) → publish; release-candidate summary (rc7 from build76+ after tests).

## Known limitation
- SecondInfoBarECM (non-default SIB mode, Python-owned named widgets, screen created once with the InfoBar) keeps
  the default placeholder: it cannot switch layout per event.

## Rules (unchanged)
- Slot 8 and dev/mla-openatv only.
- No main, no HDD writes, no other slots, no Multiboot or tuner changes.
- No final release without the user's approval.
