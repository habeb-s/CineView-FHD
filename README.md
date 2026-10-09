# CineView FHD 2.1

Official Full HD CineView skin.

## CineView FHD 2.3.6 — recording-safe restarts, OpenBH smart install (issue #8)

* Installers, the package and the online updater no longer restart Enigma2 while it records; the change is
  installed and you are asked to restart Enigma2 after the recording.
* OpenBH: the smart link works again (snapshot `snapshots/openbh-final-20261009`), and the OpenBH package restores
  the PVR poster / FILE / PATH lines and the persistent poster cache.
* Releases are built by `.github/workflows/build-cineview-release.yml` from `PLUGIN_VERSION` in
  `updater/CineViewUpdater/plugin.py`; published releases are never rebuilt or replaced.
* Details, tests and the checks that still need a real OpenBH receiver: `docs/fixes/issue-8-20261009.md`.

## CineView FHD 2.3.5 — receiver temperature fix (2026-10-09)

The `CPU: xx°C` label in the InfoBar / Second InfoBar showed `CPU: --°C` on receivers whose driver reports the
temperature outside the three fixed paths the 2.3.4 converter read (for example Octagon SF8008 / HiSilicon, which
reports it in `/proc/hisi/msp/pm_cpu`; the OpenBH variant listed that file but could not parse it). The converter
`components/Converter/CineViewCPUTemp.py` now also reads other kernel thermal zones, other Enigma2 driver files and
the HiSilicon driver — each only if present — and shows `CPU: N/A` when there is no valid reading. Receivers that
already showed a temperature keep exactly the same reading. Nothing else changed: same skin design, sizes and
positions.

* Online update (CineView Control → BLUE) offers 2.3.5 through `update.json`.
* The smart link installs the 2.3.5 layer (SHA256-pinned) on top of the pinned image snapshot.
* Packages are built reproducibly from the 2.3.4 release by `tools/build_2.3.5.py` and checked by
  `tools/verify_2.3.5.py`; details and test evidence: `docs/fixes/cputemp-20261009.md`.
* Rollback: reinstall the 2.3.4 package from release `v2.3.4`
  (`opkg install --force-reinstall --force-downgrade <ipk>`), or restore the backup the installer writes to `/tmp`.

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
The smart installer routes OpenBH 6.0 build 001 to the final live OpenBH snapshot finalized on 2026-09-23.

The OpenBH snapshot is pinned and SHA256-verified before installation. Its final compatibility layer preserves OpenBH-native screen contracts and reapplies the accepted CineView layouts after future option changes.

Snapshot source commit:

    0d5c9b884244ba1ea0235fe9d668c2581f843abd

Snapshot SHA256:

    9017ab3455632ef5f93d46def51a8d26738f6bd8ce24ddacedabaad31bcadf3c

Engineering history, manifests and validation evidence are stored under:

    snapshots/openbh-final-20260923/

**CineView FHD 2.1 — Designed by habeb-s**
