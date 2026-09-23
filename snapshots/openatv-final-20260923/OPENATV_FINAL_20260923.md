# CineView FHD — OpenATV Final Live Snapshot — 2026-09-23

Source receiver:
- Vu+ Duo 4K SE
- OpenATV 8.0.0-beta
- Enigma2 package captured live on 2026-09-23
- Full HD target: 1920x1080

This snapshot is the accepted OpenATV reference after the 2026-09-22 to 2026-09-23 refinement session.

## Finalized areas

### Core CineView skin
- Main InfoBar transponder formatting kept at 11470 H 30000.
- Main InfoBar layout intentionally frozen after its correction.
- Poster frames added around CineViewPosterX where requested.
- SecondInfoBar rebuilt as a separate two-event current/next layout with poster frames.
- SecondInfoBarSimple aligned with the same contract.

### OpenATV full-screen page unification
- MultiBoot Manager / Selector / Wizard polished to full-screen CineView layout.
- HotkeySetup / HotkeySetupSelect unified.
- LanguageSelection unified.
- CineView_FHD / AtileHD setup override made full-screen and duplicate external title removed.
- GraphicalEPG converted to CineView full-screen layout with poster frame, title/event area, timeline and CineViewPosterX widget.
- Skin selection/settings and related OpenATV pages refined by the OpenATV audit layer.

### EMC / PVR
- EnhancedMovieCenter left-PIG 1080 layout converted to full-screen FHD CineView styling.
- Larger MiniTV preview.
- Larger filename/path/event-description areas.
- Poster/cover area separated from the MiniTV.
- Selected-item poster renderer uses LukaPosterXEMC.
- Poster logic uses meaningful title extraction and falls back to a media frame when internet poster lookup fails.
- Dynamic green sort button rebuilt with a true 580x56 FHD asset so long labels stay inside the button.
- Red/yellow/blue button assets normalized to their rendered FHD sizes.
- Date/progress/list spacing refined.

### Poster / renderer work
- CineViewPosterX live renderer is preserved from the receiver.
- LukaPosterXEMC live renderer is preserved from the receiver.
- Current EMC internet lookup behavior for Black Bag 2025 did not return an online poster in the final session and therefore used the media-frame fallback. This is preserved as-is in the exact final snapshot for reproducibility.
- GraphicalEPG contains both the poster frame and CineViewPosterX widget. Internet-poster retrieval in EPG should be revalidated per target image when porting.

### Other compatibility work preserved
- CineViewControl current live files.
- CineView converter files.
- OAWeather live plugin state is saved in the full engineering archive for later OpenBH/OpenViX reference.
- All receiver-side CineView OpenATV backup points from the refinement session are preserved in the full engineering archive.

## Porting rule for OpenBH
Do not blindly copy OpenATV screen contracts by screen name. Re-audit OpenBH's native screen/plugin contracts, then port the visual/layout intent:
- keep the main InfoBar formatting contract,
- keep SecondInfoBar as a separate current/next overlay,
- keep poster frames,
- keep full-screen FHD page identity,
- preserve image-specific widget/source names where OpenBH differs.

## Safety
The smart installer for this snapshot:
- uses /tmp for rollback,
- does not modify /media/hdd,
- validates the snapshot SHA256 before install,
- validates skin XML before replacing the live skin.
