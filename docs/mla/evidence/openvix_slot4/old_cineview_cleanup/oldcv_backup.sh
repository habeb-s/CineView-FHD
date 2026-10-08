#!/bin/sh
# runs ON the receiver (Slot 4 OpenViX 6.9): BACKUP ONLY of the old CineView FHD 2.1 items (nothing is changed).
set -u
grep -q "rootsubdir=duo4kse/linuxrootfs4" /proc/cmdline || { echo "NOT Slot 4 - stop"; exit 1; }
C=/usr/lib/enigma2/python/Components
P=/usr/lib/enigma2/python/Plugins/Extensions
B=/home/root/oldcv-backup-20261008
mkdir -p $B/opkg-info
cp -p /etc/enigma2/settings $B/settings
for p in enigma2-plugin-skins-cineview-fhd-offline-openvix enigma2-plugin-skins-cineview-fhd-universal-offline; do
  cp -p /var/lib/opkg/info/$p.* $B/opkg-info/ 2>/dev/null; opkg status $p > $B/opkg-info/$p.status
done
LIST=""
for f in $C/Converter/CineViewBitrate.py $C/Converter/CineViewBitrate.pyc $C/Converter/CineViewCPUTemp.py $C/Converter/CineViewCPUTemp.pyc \
         $C/Converter/CineViewCamInfo.py $C/Converter/CineViewCamInfo.pyc $C/Converter/CineViewIMDb.py $C/Converter/CineViewIMDb.pyc \
         $C/Converter/CineViewTransponder.py $C/Converter/CineViewTransponder.pyc $C/Converter/CineViewTransponderInfo.py \
         $C/Converter/CineViewTransponderInfo.pyc $C/Renderer/CineViewPosterX.py $C/Renderer/CineViewPosterX.pyc \
         /etc/enigma2/CineViewControl-before-update-20260922-185907.tar.gz \
         /usr/share/enigma2/CineView_FHD /usr/share/enigma2/CineView_FHD.rollback-broken-20260922 $P/CineViewControl \
         /etc/enigma2/CineView_FHD-before-latest-merge-20260922-221719 /root/cineview-openvix-backups /usr/share/cineview-fhd-offline; do
  [ -e "$f" ] && LIST="$LIST ${f#/}"
done
tar -C / -czf $B/oldcv-files.tgz $LIST || { echo "BACKUP FAILED"; exit 2; }
tar -tzf $B/oldcv-files.tgz > $B/oldcv-files.list || { echo "BACKUP UNREADABLE"; exit 2; }
echo "entries: $(wc -l < $B/oldcv-files.list)  size: $(du -k $B/oldcv-files.tgz | cut -f1) KB"
(cd $B && sha256sum oldcv-files.tgz settings > SHA256SUMS && cat SHA256SUMS)
echo BACKUP_DONE
