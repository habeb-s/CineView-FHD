#!/bin/sh
# runs ON the receiver (Slot 4 OpenViX 6.9), user-requested cleanup of the OLD CineView FHD 2.1 only.
# Requires the verified backup /home/root/oldcv-backup-20261008 (made by oldcv_backup.sh).  Explicit paths only;
# CineView MLA (CineView_FHD_MLA, CineViewMLA*, enigma2_pre_start.sh), the image and other add-ons are not touched.
set -u
B=/home/root/oldcv-backup-20261008
grep -q "rootsubdir=duo4kse/linuxrootfs4" /proc/cmdline || { echo "NOT Slot 4 - stop"; exit 1; }
(cd $B && sha256sum -c SHA256SUMS) || { echo "backup not verified - stop"; exit 1; }
case "$(sed -n 's/^config.skin.primary_skin=//p' /etc/enigma2/settings)" in CineView_FHD/*) echo "old skin selected - stop"; exit 1;; esac
C=/usr/lib/enigma2/python/Components
P=/usr/lib/enigma2/python/Plugins/Extensions
init 4; for i in $(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done
pidof enigma2 >/dev/null && { echo "GUI still running - stop"; init 3; exit 3; }
echo "== packages"
opkg remove enigma2-plugin-skins-cineview-fhd-offline-openvix enigma2-plugin-skins-cineview-fhd-universal-offline 2>&1
echo "== files and folders of the old CineView FHD"
for f in $C/Converter/CineViewBitrate.py $C/Converter/CineViewBitrate.pyc $C/Converter/CineViewCPUTemp.py $C/Converter/CineViewCPUTemp.pyc \
         $C/Converter/CineViewCamInfo.py $C/Converter/CineViewCamInfo.pyc $C/Converter/CineViewIMDb.py $C/Converter/CineViewIMDb.pyc \
         $C/Converter/CineViewTransponder.py $C/Converter/CineViewTransponderInfo.py $C/Converter/CineViewTransponderInfo.pyc \
         $C/Renderer/CineViewPosterX.py $C/Renderer/CineViewPosterX.pyc /etc/enigma2/CineViewControl-before-update-20260922-185907.tar.gz; do
  [ -f "$f" ] && rm -f "$f" && echo "removed $f"
done
for d in /usr/share/enigma2/CineView_FHD /usr/share/enigma2/CineView_FHD.rollback-broken-20260922 $P/CineViewControl \
         /etc/enigma2/CineView_FHD-before-latest-merge-20260922-221719 /root/cineview-openvix-backups /usr/share/cineview-fhd-offline; do
  [ -d "$d" ] && rm -rf "$d" && echo "removed $d/"
done
echo "== settings lines of the old plugin"
S=/etc/enigma2/settings
grep -n "^config.plugins.cineview\." $S
sed -i '/^config\.plugins\.cineview\./d' $S
sed -i 's#Plugins/Extensions/CineViewControl,##' $S
echo "remaining old references in settings: $(grep -c 'CineViewControl\|^config.plugins.cineview\.' $S)"
init 3
echo REMOVE_DONE
