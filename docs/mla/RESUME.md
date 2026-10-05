# CineView MLA: resume point (updated 2026-10-06 00:50 Riyadh)

| Item | Value |
|---|---|
| Last build | build77 = package **1.0.0~rc7** (published, `release/rc`, SHA256 `6d752cf8…afbca6`) |
| Receiver | Slot 8, Vu+ Duo 4K SE, OpenATV 8.0.1; **rc7 installed** (t77_rc7), Classic navy, posters ON |
| Last successful tests | t81a / t81b (attribution), t82 (No Poster, 5 models), t83 (CineView accelAlloc 0), t84 (EPG / PVR / InfoBar No Poster + Classic EV picon), t77_rc7 (install + five models) |
| Queue on ai-agent | empty |
| Report | `docs/mla/evidence/report/CineView_MLA_Model_Review.html` (published as an artifact) |
| Last commit | see `git log -1` on dev/mla-openatv |

## Waiting for the user
1. Visual approval:
   - No Poster arrangements, especially the Graphical Plus panel without a poster and the Cover Library column;
   - PIL widget-size posters (same size and framing, sharper than ePicLoad).
2. Second device (DM900, OpenATV 7.6.0): output of `diag-mla.sh`. rc7's installer pins the poster cache to USB or
   /tmp (no HDD writes unless `HDD_CACHE=1`).
3. A dedicated HDD-cache test (`/media/hdd/poster`) only after the user's OK.

## Known limitation
- SecondInfoBarECM (non-default SIB mode, Python-owned named widgets, screen created once) keeps the placeholder.
- The remaining accelAlloc warnings are Enigma2-internal: the list picon cache (220×132, cached=1) and one
  start-up surface. They are documented and not changed.

## Rules (unchanged)
- Slot 8 and dev/mla-openatv only.
- No main, no HDD writes, no other slots, no Multiboot or tuner changes.
- No final release without the user's approval.
