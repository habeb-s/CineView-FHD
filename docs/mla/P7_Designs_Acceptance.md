# P7 — Details & Cinema families: device acceptance (Slot 8, OpenATV 8.0.1 / enigma2 57b7a51)

Device: Vu+ Duo 4K SE · Slot 8 (USB) · 16.0°E only · branch `dev/mla-openatv`.
Families are independent layout packs (`layouts/infobar/<id>`, `layouts/secondinfobar/<id>`), generated from one
spec (`tools/mla/p7/spec_p7.py`) by `gen_details.py` / `gen_cinema.py`. Classic packs are not modified.

## Test matrix (per family, `p7family.sh`)
| Stage | What is exercised |
|---|---|
| tour | 5 channels (HBO, HRT1, RTL, N1, Cinemax): InfoBar, SecondInfoBar at +3 s and +15 s, webif signal values for cross-check |
| Arabic | live screens rendered with a long Arabic title/description (devtool TextTest2), posters on and off, +2 s and +13 s |
| posters off | both switches off -> poster, frame and default image hidden, text widens |
| independence | Classic InfoBar + family SecondInfoBar |
| themes | the six themes (navy, black, graphite, burgundy, green, purple) on InfoBar + SecondInfoBar, OSD-layer navy-residue check |
| end | rollback to factory (Classic navy) |

## Details — run 1 (build18, 22:08–22:19): findings
| # | Finding (evidence) | Fix | Build |
|---|---|---|---|
| D-1 | NEXT description (23 px) showed half of an 11th line: real line pitch is 26 px, the spec formula gave 27 | pitch measured on device (21→24, 22→25, 23→26, 24→28, 25→29) and the formula replaced; boxes re-sized | 19 |
| D-2 | One-line titles swam vertically (wrapped text in a one-line box: half lines while moving) | one-line boxes swim horizontally, `noWrap` | 19 |
| D-3 | Posters off: NEXT description stayed under the (hidden) poster, leaving a gap | posters-off variant moves it under the title (15 lines) | 19 |
| D-4 | No poster (legacy engine, no match): filled grey box | neutral CineView default image under the poster widget + border-only frame | 19 |
| D-5 | IMDb `-- --` shown when there is no rating | converter argument `,hide` (new families only; Classic unchanged) | 19 |
| D-6 | Lone `–` between empty times when there is no event | the dash comes from the event (`ClockToText Format:–`) | 19 |
| D-7 | Event progress bar stayed blue in Deep Purple | `infobar/pbar.png` added to the theme bitmaps (all themes; navy pixel-identical) | 19 |
| D-8 | Channel name "running" from the right edge: half of a long name missing for seconds | service/provider/city fields swim horizontally (start shown first) | 20 |
| D-9 | Arabic one-line title (RTL variant, horizontal swim): the box first shows the MIDDLE of the title | under investigation (`rtltest.sh`, 7 RunningText configurations side by side) | — |
| D-10 | Legacy poster engine (default) shows wrong posters for news: "Dnevnik 3" -> *Diary of a Wimpy Kid: Dog Days* | not a family defect; the identity engine (P5, opt-in) rejects generic titles — decision needed | — |

Passed in run 1: live data on all 5 channels (SNR/AGC/BER equal to webif), independence (Classic IB + Details SIB),
Deep Purple (navy residue 0.44 % IB / 0.35 % SIB), Arabic right-aligned descriptions, 0 tracebacks, factory restore.

## Details — run 2 (build20, 23:13–23:29)
- Tour, 5 channels: SecondInfoBar opened every time (opener fixed in the test script: OK, OK within 1 s).
  Live values differ per channel and agree with webif `/api/signal` sampled seconds apart (AGC 75/71/73/76 % equal; SNR within 1 %, e.g. HBO 74 vs 73; TP 11636 H / 11636 V / 11678 H / 11553 H,
  bitrate 4.75 / 1.60 / 3.14 / 3.08 Mbps).
- D-1…D-8 verified fixed on screen: no half lines, NEXT description under the title with posters off, default image
  in empty poster slots, no `--` without IMDb data, no lone dash, purple progress bar, service names start visible.
- D-9 (Arabic one-line title): `rtltest.sh` showed that 57b7a51 RunningText mis-measures RTL text in horizontal
  modes (A/B/C/D/G: the box starts in the middle or at the end of the title).  Fix: RTL variant of one-line boxes
  pages vertically by exactly one line pitch (row H): the first line is shown first, whole lines only.  Verified
  in rtltest; on the InfoBar the first line of the Arabic title is shown at +2 s.
- Posters off, independence (Classic IB + Details SIB), Deep Purple: pass; tracebacks 0; factory restored.
- Open: D-10 (legacy poster engine) — in this run also "Movie top ten" -> *Top 10 Hamsters*.
