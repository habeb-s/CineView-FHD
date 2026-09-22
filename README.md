# CineView FHD 2.1

Official Full HD CineView skin with a pinned live OpenViX reference snapshot.

## Supported installation paths

- OpenViX 6.9 build 002: installs the exact live snapshot captured from the Vu+ Duo 4K SE on 2026-09-22.
- OpenATV 7.4 / 7.5 / 7.6 / 8.0: keeps the existing CineView FHD 2.1 smart-installer path.
- Python 3
- Full HD 1920×1080

## Installation

    wget -qO- https://raw.githubusercontent.com/habeb-s/CineView-FHD/main/install.sh | sh

For the immutable OpenViX snapshot directly:

    wget -qO- https://raw.githubusercontent.com/habeb-s/CineView-FHD/3c4519ba47ba59444ff2392507e67d9c133f14ec/install-openvix-live.sh | sh

The OpenViX installer is pinned to snapshot commit `981fddfe4d88519c96101ab10951d65163cb2eaf` and validates SHA256 `a55d3dfc3282c04f6b82be77fbd11e9c8435d4e5361b862f5c8c859eb5cbac29` before installation. It creates a rollback archive under `/tmp` and does not use `/media/hdd`.

**CineView FHD 2.1 — Designed by habeb-s**
