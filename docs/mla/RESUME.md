# CineView MLA: resume point (updated 2026-10-05 22:10 Riyadh)

| Item | Value |
|---|---|
| Last build | build71 = package 1.0.0~rc6 (same files; rc6 adds only usr/bin hook) |
| Packages | rc5 (build70, device-verified t77), rc5.1 (= rc5 files, OpenATV 7.6/8.0 check), rc6 (build71, t80 running) |
| Receiver | Slot 8, Vu+ Duo 4K SE, OpenATV 8.0.1, rc6 installed (t80) |
| Last successful tests | t77 (rc5 install), t78 (quality A/B), t79 (60-min run, cache dry run, Classic MS 0 errors) |
| Queue on ai-agent | q81.sh: t81a (build71 deployed, accel attribution) -> reinst.sh (rc6 force-reinstall) -> t81b (installed rc6, same steps) |

## Next steps after the queue
1. Read `t81a.log` / `t81b.log` (attribution shares) and write them into the evidence doc and report.
2. Second device (DM900, OpenATV 7.6.0): posters not shown. Run `release/rc/diag-mla.sh` there and read its output.
3. "No poster" behaviour: replace the default placeholder with the real No-Poster layout where the screen can switch
   at runtime. Design + implement + device test.
4. Final report page (`make_report.py`) -> publish; release-candidate summary.

## Rules (unchanged)
- Slot 8 and dev/mla-openatv only.
- No main, no HDD writes, no other slots, no Multiboot or tuner changes.
- No final release without the user's approval.
