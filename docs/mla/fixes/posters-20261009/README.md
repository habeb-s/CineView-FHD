# CineView MLA 1.0.3 — posters with localised (Polish) EPG titles (2026-10-09)

## Report
Octagon SF8008 (OpenATV 7.6.0, Python 3.13, CineView_FHD_MLA 1.0.2, Modern layouts, theme black): no posters.

## Where the chain broke (fetch / save / display)
Traced on the receiver with the event on air, HBO2 HD "Królewskie święta 1 (odc. 5)":

| Stage | Evidence | Result |
|---|---|---|
| Settings / skin binding | 18 `CineViewMLAPosterX` widgets in active/{infobar, secondinfobar, eventview, epg, channelselection, pvr}.xml, `toggle=config.plugins.cineviewmla.poster_*`, no value stored = shown | OK |
| Service | `/tmp/CINEVIEW-MLA/poster.log`: IMDb / TVmaze answered with candidates for every query | OK |
| Cache | `/media/hdd/poster` (HDD mount, writable); matched posters saved in `id/`, rejections as `id/<key>.none` | OK |
| Display | `underlay="1"` widgets show nothing for a title without a reliable match (`_show_default` -> `_release`), the Modern layout switches to its No-Poster variant | by design |
| **Identification** | `identity key=krolewskie swieta 1~series~ ... -> no-reliable-match best=imdb/A Royal Christmas/2014 0.00` | **broken** |

Root cause: the P5 identity engine (`mla/components/_lib/CineViewMLAPosterMatch.py`) was tuned on Croatian EPG
("(SAD, 2012, film)"). Polish EPG names the work differently and the engine used none of it:
* `Tytuł oryginalny: A Royal Christmas Holiday` + `US, 2023` (110 of 1929 current events) — ignored; the Polish title
  was compared with the English title (similarity 0.0–0.3) and rejected;
* `serial komediowy (USA, 2002)` — "serial" was not a known series word;
* "(odc. 5)" was taken as a certain series; HBO2 lists the film "A Royal Christmas Holiday" that way -> kind veto;
* a localised **series** title had no acceptance path at all (films had one: exact year + cast).
Result on the receiver before the fix: 5 of 32 identified titles matched; 13 of 172 events on air.

## Fix (1.0.3)
`CineViewMLAPosterMatch.py`
* original title from the description (`Tytuł oryginalny:`, `Original title:`, `Originaltitel:`, `Originalni naslov:`,
  `Titre original:`, ...) is searched and compared; production year from the "US, 2023" line after it;
  the identity key uses the original title (old negative markers do not block the new lookup);
* Polish "serial" = series; "(odc. N)" is a soft kind (matching kind preferred; the other kind only with a
  near-identical title, never via the exact-year shortcut);
* localised series without an original title: accepted only like a localised film — IMDb's own top-2 answer for
  the Polish title, same kind, year inside the run AND a lead actor named in the description;
* live sport / service slots are not looked up ("Piłka nożna:", "Football:", "MMA:", "Wrestling:", "Sport",
  "Teleexpress", "Przerwa w programie").
`tools/mla/patches/posterx_identity.py`: the renderer searches the original title first, the localised title when it
finds nothing. Nothing else changed: same widgets, sizes, cache, threshold, ambiguity rule.

## Evidence
* Replay of real Octagon EPG (`tools/mla/replay_poster_match.py`, live IMDb/TVmaze/iTunes answers, cached):
  * 172 events on air: matches 13 -> 72;
  * 1648 events of the next 18 h (93 services): 143 -> 589; 7 lost, all justified (2x news "Teleexpress";
    4x "RESET" = a French 2023 entertainment show that had shown a 2022 Chinese drama's poster; "Beyond the Beaten
    Path" 2023 vs the 2017 work); 2 changed, both corrections ("Django" -> Django Unchained, was Django 1966;
    "Zemsta" -> Wajda's 2002 film, was the 1957 film). Every gained match was reviewed.
* Offline tests `tools/mla/test_poster_match.py`: all passed (Croatian cases unchanged).
* Device (SF8008, 1.0.3 via Smart Installer 1.3.3, GUI restarted only after `isRecording=false`):
  `01`/`02` InfoBar + Second InfoBar "Królewskie święta 1 (odc. 5)" -> A Royal Christmas Holiday;
  `04`/`05` InfoBar + Event View Castle (current and next); `07` Multi EPG "Anioły i demony" -> Angels & Demons;
  `09` Multi EPG "Diabli nadali" -> The King of Queens (cast rule); `10` channel list;
  `03`/`08` the remaining limit: an animated series in the format without original title and without cast
  ("Harmidom" = The Loud House) keeps the No-Poster layout — no evidence, no poster.
  `poster_log_before.txt` / `poster_log_after.txt`; HDD cache: 0 files removed, only new posters added.
* Packages: `package_verify_103.txt` (only the two modules + version.json differ from 1.0.2, all ten load with their
  Python).

## Rollback
Receiver: `ROLLBACK=1 sh /tmp/cineview-install.sh` (Smart Installer 1.3.3 -> 1.0.2), or restore
`/home/root/cineview-backup-20261009-posters/*.pyc` and restart the GUI. Source: revert this commit.
