# CineView FHD Architecture Guide

CineView spans three layers that must be reasoned about separately:

1. Native Enigma2/image contract — Python Screen classes, self[...] sources/widgets, actions, converters/renderers and image-specific behavior.
2. CineView presentation — image-specific skin XML/assets/layout rules implementing the approved FHD design.
3. Distribution/compatibility — installer detection, image-specific compatibility helpers, packages and updater.

Correct dependency direction is: requirement -> verified native contract -> CineView implementation. Never infer a native contract from a desired XML layout.

## Image isolation
OpenATV, OpenViX and OpenBH may expose different Screen classes, widgets, converters, renderers and setup behavior. Share code only when compatibility is demonstrated. Prefer image-specific adapters over corrupting native behavior with one forced contract.

## Repository evidence
Historical snapshots are useful for known-good references and rollback archaeology. lab/ and generated dist/ outputs are not release authority. Current live device state plus committed source and verified release artifacts determine reality.

## High-risk boundaries
Skin engineering must not spill into boot/multiboot, storage formatting, tuner configuration, satellite/channel databases, network configuration or unrelated plugins. Any such change requires a separately proven requirement and explicit authorization when high-impact.
