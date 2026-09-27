# CineView FHD Validation Protocol

## Static gate
- Parse all changed XML.
- Compile/import changed Python where target environment permits.
- Verify referenced renderers/converters/classes exist on the target image.
- Validate package metadata/dependencies when packaging.
Static success means only: IMPLEMENTED — NOT RUNTIME VERIFIED.

## Runtime gate
- Restart/reload Enigma2 as required.
- Confirm Enigma2 returns without crash/skin fallback.
- Open every changed screen through the real UI path.
- Exercise navigation and colored actions.
- Inspect runtime/crash logs.

## Visual gate
On actual rendered UI verify 1920x1080 bounds, clipping, baseline/font fit, list rows, selection, poster aspect/frame, icons, colored buttons, headers/footers, transparency and z-order.

## Dynamic-data gate
For service/tuner/event/bitrate/transponder fields, change channel/service/condition and prove values update from the intended live source. Fixed placeholder-like values fail validation.

## Regression gate
Retest shared/adjacent screens touched by common fonts/colors/renderers/converters/templates. At minimum preserve channel viewing/zapping and any previously working CineView screens affected by shared definitions.

## Negative cases when relevant
Missing poster/EPG/storage/network/optional plugin; empty lists; long names; Arabic and English text; SD/HD/FHD/UHD services; unavailable optional dependency. Fail gracefully.

## Evidence
Record exact target image/build/model, changed files, backup path, commands/checks, runtime observations and unresolved items. Never synthesize evidence.
