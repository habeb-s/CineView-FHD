#!/bin/sh
# Slot 5 (OpenBH 5.6) cleanup of the OLD CineView project (user 2026-10-07 13:02).  Inventory 13:10:
#   packages (maintainer habeb/openai or habeb-s, no prerm/postrm):
#     enigma2-plugin-cineview-mx-openbh 2.0.0-openbh56-mx (meta, 0 files)
#     enigma2-skin-mx-slim-line-se 2.0.0-openbh56-mx (our MX build, 1545 files; NOT the image default -
#       OpenBH 5.6 default is MX_Slim-Line_NP from enigma2-plugin-skins-mxslimlinenp, untouched)
#     enigma2-plugin-skins-cineview-fhd-openbh 2.4.13-openbh (407 files)
#   unowned leftovers: CineViewControl *.pyc, /etc/enigma2/CineView_FHD_skin_base.xml, /tmp/CineViewBitrate.log,
#     /usr/uninstall/*.del of the 3 packages; settings lines config.plugins.cineview.theme and the CineView display skin.
# Never: /media/hdd, other slots (incl. /var/volatile/tmp/GetImageliste_* = internal flash multiboot mount), STARTUP.
# Rollback copy: agent ~/cineview-mla/slot5/rollback-*.
set -u
ROOTDEV=$(stat -c %d /)
del() {
	for p in "$@"; do
		case "$p" in /media/*|/var/volatile/tmp/GetImageliste*|/boot*) echo "REFUSED  $p"; continue ;; esac
		[ -e "$p" ] || [ -L "$p" ] || { echo "absent   $p"; continue; }
		case "$p" in /var/volatile/*) ;; *) [ "$(stat -c %d "$p")" = "$ROOTDEV" ] || { echo "REFUSED (other fs) $p"; continue; } ;; esac
		rm -rf -- "$p" && echo "deleted  $p" || echo "FAILED   $p"
	done
}
grep -q "rootsubdir=duo4kse/linuxrootfs5" /proc/cmdline || { echo "NOT Slot 5 - stop"; exit 1; }
echo "== stop GUI"
init 4; for i in $(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done
pidof enigma2 >/dev/null && { echo "enigma2 still running - stop"; exit 1; }

echo "== settings"
python3 - <<'PYEOF'
p = "/etc/enigma2/settings"
lines = open(p).read().split("\n")
out = []
for l in lines:
    if l == "config.plugins.cineview.theme=navy" or l.startswith("config.skin.display_skin=display/CineView_FHD/") \
            or l.startswith("config.skin.primary_skin=CineView") or l.startswith("config.skin.primary_skin=MX_Slim-Line_SE/"):
        print("removed line: " + l); continue
    out.append(l)
open(p, "w").write("\n".join(out))
PYEOF

echo "== package manager"
opkg remove enigma2-plugin-cineview-mx-openbh 2>&1
opkg remove enigma2-skin-mx-slim-line-se 2>&1
opkg remove enigma2-plugin-skins-cineview-fhd-openbh 2>&1
opkg list-installed | grep -i -E "cineview|mx-slim-line-se" || echo "no old CineView package installed"

echo "== leftovers"
C=/usr/lib/enigma2/python/Components
del /usr/share/enigma2/CineView_FHD /usr/share/enigma2/MX_Slim-Line_SE /usr/share/enigma2/display/CineView_FHD \
    /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl /usr/share/doc/enigma2-plugin-skins-cineview-fhd-openbh \
    $C/Converter/CineViewBitrate.py $C/Converter/CineViewBitrate.pyc $C/Converter/CineViewCPUTemp.py $C/Converter/CineViewCPUTemp.pyc \
    $C/Converter/CineViewCamInfo.py $C/Converter/CineViewCamInfo.pyc $C/Converter/CineViewIMDb.py $C/Converter/CineViewIMDb.pyc \
    $C/Converter/CineViewTransponder.py $C/Converter/CineViewTransponder.pyc \
    $C/Converter/CineViewTransponderInfo.py $C/Converter/CineViewTransponderInfo.pyc \
    $C/Renderer/CineViewPosterX.py $C/Renderer/CineViewPosterX.pyc \
    /etc/enigma2/CineView_FHD_skin_base.xml /var/volatile/tmp/CineViewBitrate.log \
    /usr/uninstall/enigma2-plugin-cineview-mx-openbh.del /usr/uninstall/enigma2-plugin-skins-cineview-fhd-openbh.del \
    /usr/uninstall/enigma2-skin-mx-slim-line-se.del
sync
echo CLEANUP_DONE
