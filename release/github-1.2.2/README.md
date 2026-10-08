# CineView MLA — Smart Installer

Design & Development by habeb-s © 2026

One installer for **OpenATV 8.0**, **OpenBH 5.6** and **OpenViX 6.9**. It identifies the receiver and the image,
checks Python and compatibility, downloads the matching package, verifies its SHA256 and installs it.

## Install / update (telnet or SSH on the receiver)

```
wget -qO /tmp/cineview-install.sh https://raw.githubusercontent.com/habeb-s/CineView-MLA-Install/main/cineview-install.sh && sh /tmp/cineview-install.sh
```

Options (before `sh`): `DRYRUN=1` checks only · `ROLLBACK=1` previous release · `RESTART=1` restart the GUI without asking

## Uninstall

```
wget -qO /tmp/cineview-uninstall.sh https://raw.githubusercontent.com/habeb-s/CineView-MLA-Install/main/cineview-uninstall.sh && sh /tmp/cineview-uninstall.sh
```

Untested image versions are refused. Your design, theme, profiles and settings are kept on update and rollback.
