# CineView FHD 2.1

Official Full HD CineView skin.

## Smart installation

Use the same smart link on supported images:

    wget -qO- https://raw.githubusercontent.com/habeb-s/CineView-FHD/main/install.sh | sh

### OpenATV
The smart installer now routes OpenATV 7.4 / 7.5 / 7.6 / 8.0 to the final live OpenATV snapshot captured from the Vu+ Duo 4K SE on 2026-09-23.

The final OpenATV snapshot is pinned and SHA256-verified before install. The installer creates a rollback archive under /tmp and does not modify /media/hdd data.

Snapshot source commit:

    b76abeb9d369e8395a1470a06e1378c081505eb0

Snapshot SHA256:

    3cb41ec6b54d9ecf4bd12edb1731fee178179d66c3e1dedd131d7c74380c4683

Engineering notes and the complete 2026-09-22 to 2026-09-23 work history are stored under:

    snapshots/openatv-final-20260923/

### OpenViX
The smart installer routes OpenViX 6.9 build 002 to the final live OpenViX snapshot captured from the Vu+ Duo 4K SE on 2026-09-23.

The final OpenViX snapshot is pinned and SHA256-verified before install. The final activation hook is image-aware: OpenViX uses its own final visual helper and does not run the OpenATV post-processor.

Snapshot source commit:

    b14044bb26995b60d7862c1733306e978f01022f

Snapshot SHA256:

    ec20a8e4d31c82fe5242e89af9c29f5b029f6d522b18ff4bea940c180a3733bc

Engineering notes and validation evidence are stored under:

    snapshots/openvix-final-20260923/

### OpenBH
The OpenBH image-specific port is not published yet. The complete OpenATV engineering reference is preserved in the repository so the visual/layout work can be ported without repeating the OpenATV session.

**CineView FHD 2.1 — Designed by habeb-s**
