# CineView MLA — OpenBH 5.6 (Slot 5) — Second Full Runtime Run

Date: 2026-10-07 · Receiver: Vu+ Duo 4K SE · Slot 5 = OpenBH 5.6.008 (BlackHole/enigma2 52dedddc314a, Python 3.13.12)
Branch: `dev/mla-multiimage` · Builds tested: `1.0.0~openbh5`, `1.0.0~openbh6` (final, SHA256 `ab62b1e1…ad373ec4`)
Evidence: `docs/mla/evidence/openbh_t106/` (logs + contact sheets). Every PASS below comes from opening the screen / using the function on the receiver.

Status: **RUNTIME TESTED** on OpenBH 5.6 Slot 5 (not released, no tag).

## Fixes in this run (each followed by the OpenATV parity gate: PASS)

| # | Problem found on the receiver | Root cause (proven) | Fix |
|---|---|---|---|
| 1 | CineView profiles / design model / profile menus opened **empty** | OpenBH `Screens.ChoiceBox(session, title, list, …, **kwargs)` takes the items as `list=`; `choiceList=` (OpenATV) is swallowed by `**kwargs` | ImageAdapter `choice_list()` → `list=` on OpenBH, `choiceList=` on OpenATV (unchanged call). Test `test_image_adapter.py` |
| 2 | Arabic: Grid / Multi / InfoBar-Grid red key wrapped into a clipped 2nd line | OpenBH's Arabic text for "IMDb Search" is 50 characters; eLabel wraps in the 400×45 px bar | OpenBH EPG transform: colour keys `noWrap="1"` (skin.py noWrap → eLabel::setNoWrap). English unchanged |
| 3 | (test tool) guardian step did not create active ≠ last-known-good | CLI `apply` commits lkg; trial apply needed | `t106f.sh` uses `apply --trial` |

Earlier in this phase (already reported): ServiceInfo `interesting_events`, ImageAdapter native rows, OpenBH Plugin Browser, OpenBH EPG contract, ShowIf picon (double logo), valueFont→secondfont, guardian last resort.

## Per screen / function

| Screen / function | Result | Notes |
|---|---|---|
| InfoBar | PASS | 5 models × posters on/off × 6 themes × Arabic; live tuner/bitrate/CPU/weather |
| SecondInfoBar | PASS | now/next populated; single channel logo |
| ChannelSelection (+ info panel) | PASS | panel populated on a channel with EPG |
| Single EPG | PASS | |
| Grid EPG (PiG and pack grid) | PASS | all 5 EPG packs with `grid.pig` off; PiG video is black in screen grabs (grab limitation) |
| Multi EPG | PASS | service column width = OpenBH user setting (native), same truncation as OpenATV golden |
| InfoBar Grid EPG | PASS | |
| EventView / EventViewSimple | PASS | first-run "empty" = test channel without EPG; colour buttons present |
| Native PVR (MovieSelection) | PARTIAL | opens/renders on a slot-local empty folder; recordings not exercised (HDD forbidden) |
| Plugin Browser | PASS | OpenBH-native screen, CineView look, 0 warnings |
| CineView Designs | PASS | |
| Profiles save / load / delete | PASS | after fix 1 |
| Design model (Profiles menu) → Apply → Keep | PASS | after fix 1 |
| Theme Apply → Keep | PASS | |
| Apply → no answer → auto rollback | PASS | history: `trial: revert` → previous generation |
| Restore Factory Design | PASS | |
| Guardian recovery (3rd unclean start) | PASS | `guardian: count=3: rollback to last-known-good` |
| Themes (6) | PASS | |
| Posters On/Off + reflow | PASS | Classic and Details |
| Poster engine | PASS | cache `/tmp/CINEVIEW-MLA/poster` |
| Picons | PASS | |
| ECM / CAM info (full / profile / hide) | PASS | live ncam + ecm.info; one scrolling line as on OpenATV |
| Arabic (ar_AE) | PARTIAL | all screens open, 0 errors; red key text now one line but its start is cut (see decision) |
| Setup screens | PASS | |
| MessageBox (info / yes-no / long) | PASS | |
| EMC | NOT AVAILABLE | not installed (instruction) |

Counts (whole run): crashes **0** · tracebacks **0** · skin errors **0** · OpenATV regressions **0** · open issues **1** (design decision).
Remaining log warnings are harmless: optional elements not drawn by the design ("missing element"), `ePixmap mode="infobar"`, `piconMargin` (OpenATV attributes OpenBH ignores).

## Summary

- OpenATV parity: **PASS** (every build; 25/628 files differ from golden build94, only the allowed shared code + OpenBH-only files)
- OpenBH 5.6 compatibility: **92 %** (23 PASS, 2 PARTIAL of 25 items; EMC excluded)
- Common Core reuse: **96 %** (OpenBH overlay = 9 files + ImageAdapter entries)
- OpenBH Adapter remaining work: **5 items**
  1. Arabic red key in EPG footers — needs a design decision (below)
  2. OpenBH equivalent of the channel-name clip hook (`ServiceListLegacy` absent) — guarded off
  3. OpenBH equivalent of the Plugin Browser package-wait hook (`PackageAction` absent) — guarded off
  4. static `backgroundColorMarked` item from the first run
  5. PVR with real recordings on non-HDD storage
- HDD modifications: **NONE** (one read-only directory listing during the final check)

## Decision needed

OpenBH's own Arabic text for the red key in Grid/Multi EPG is longer than the 400 px CineView key slot. Options: (a) keep the approved slot (text one line, start cut); (b) OpenBH-only: wider red slot or smaller font for the 4 keys; (c) OpenBH-only shorter CineView text for that key. (b)/(c) change the approved look on OpenBH only.

Known item shared with the OpenATV golden (not changed): Classic PVR header sort/view icons overlap the date line.

## Cleanup done on Slot 5

Removed: test tool `CineViewMLAScreenOpen`, `/home/root/cvmla-testmedia` (empty), `/tmp/cvmla`, debug logging (`config.crash.enabledebug`, `debug_path` lines → defaults as before), today's `Enigma2_debug_*.log`, `/home/root/settings.before-debuglog-20261007`. Restored the last channel (`config.tv.lastservice/lastroot`) to the pre-test values. Kept: the installed test build `1.0.0~openbh6`, the agent SSH key (access for the next phase). Not changed: `config.audio.volume` (35 before the run, 0 now — left for the user).
