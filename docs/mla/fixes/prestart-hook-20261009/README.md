# CineView MLA 1.0.5 — coexistence with other add-ons on Enigma2's pre-start hook

## Report

Smart Installer 1.3.4 stopped on receivers where another add-on is installed:

```
/usr/bin/enigma2_pre_start.sh belongs to another add-on; CineView MLA does not replace it.
```

## Cause

- Every checked image starts Enigma2 through `enigma2.sh`, which runs **one** pre-start hook: the single file
  `/usr/bin/enigma2_pre_start.sh` (OpenATV 7.6 / 8.0, OpenBH 5.6 / 6.0, OpenViX 6.9 — checked in each image's
  `enigma2.sh`). Only one package can own a file.
- CineView MLA 1.0.0–1.0.4 owned that file to start its boot guardian (crash-loop protection: last-known-good,
  factory design, default skin). An add-on that also uses the hook could not be installed next to it, and the
  installer / preinst refused CineView MLA where another add-on already owned the file.

## Fix (1.0.5)

- The guardian is started by Python's standard start-up hook: `site-packages/cineview_mla_guardian.pth` (the same
  mechanism the images use for their own `distutils-precedence.pth`). Its one line acts only inside the `enigma2`
  process (`/proc/self/comm`) and runs `mla/guardian/prestart.py` during `Py_Initialize` in enigma2's `python.cpp` —
  before the settings and the skin are loaded, the same moment as before. Every other Python program returns at
  once. The guardian runs with a time limit; any error is only logged — Enigma2's start is never blocked.
- `guardian.sh` runs once per start: when the start-up hook is installed, any other caller (for example a hook file
  left by an earlier version) does nothing, so the crash counter never counts a start twice.
- The package no longer contains `/usr/bin/enigma2_pre_start.sh`. On update, a hook file left by an earlier
  CineView MLA is removed only if it is still CineView's own text and no other package owns it. Another add-on's
  hook is never replaced, edited or disabled.
- preinst: the "foreign pre-start hook → stop" check is replaced by a check of the Python `site-packages` folder.
- Smart Installer 1.3.5 reports another add-on's hook as kept ("…kept as it is"); only `ROLLBACK=1` (to 1.0.4,
  which still needs the file) stops there. The uninstaller does not stop Enigma2 while a recording is running.

## Device tests (Vu+ Duo 4K SE, real Enigma2) — `logs/`

A stand-in third-party add-on (`cvtest-prestart`, owns `/usr/bin/enigma2_pre_start.sh` and logs each run) was
installed next to CineView MLA.

| Image | Result |
|---|---|
| OpenATV 8.0.1 | installer 1.3.4 reproduces the message; 1.3.5 installs; both hooks run at every start, the guardian exactly once (`boot.count=1` written ~1 s after Enigma2 starts); install / upgrade / remove / fresh install with the add-on present; `ROLLBACK=1` precheck stops cleanly (`stepA*.log`) |
| OpenBH 5.6 | upgrade 1.0.0 → 1.0.3 → 1.0.5, coexistence, uninstaller, fresh install (`stepB_openbh56*.log`) |
| OpenViX 6.9 | upgrade with the installer, coexistence, uninstaller with the add-on present, fresh install, add-on removed (`stepC_openvix69_weather.log`) |
| OpenBH 6.0 | coexistence with the final 1.0.5, installer keeps the add-on's hook, uninstaller with the add-on present (it keeps running), fresh install (`bh60_FCW.log`, `bh60_X.log`) |

The OpenATV, OpenBH 5.6 and OpenViX rows were run with the first 1.0.5 build (pre-start fix only); the final
packages carry the same guardian and start-up hook files byte for byte (`tools/mla/verify105.py` checks them against
the repository), and their postinst adds only `composer.py ensure`. The final packages were then installed, upgraded
and restarted many times on all four images (`../weather-builtin-20261009/logs/`).
