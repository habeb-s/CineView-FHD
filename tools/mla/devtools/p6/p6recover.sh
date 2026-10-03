#!/bin/bash
# Manual-free recovery used ONLY if a P6 crash test exceeds its time limit (Slot 8):
# 1) restore the good plugin, 2) engine rollback to factory, 3) GUI restart, 4) verify; last resort: restore backups.
. ~/cineview-mla/p6lib.sh
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/plugin.py
echo "RECOVERY START @$($R 'date +%T')"
$R "cat > $P.tmp && mv $P.tmp $P && rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/__pycache__" < ~/cineview-mla/build13$P
$R 'python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py rollback --to factory; echo 0 > /etc/enigma2/cineview_mla/boot.count; init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'
up; sleep 20; st
if ! curl -s -m 5 http://192.168.1.250/api/statusinfo | grep -q currservice; then
  echo "GUI still down -> restoring pre-P6 backups"
  $R 'B=/media/usb/cineview-mla/state/backup-p6; init 4; sleep 5; tar -C / -xzf $B/mla-files.pre-build13.tgz; tar -C /etc/enigma2 -xzf $B/cineview_mla-state.pre-p6.tgz; cp -p $B/settings.pre-p6 /etc/enigma2/settings; init 3'
  up; st
fi
echo "RECOVERY END"
