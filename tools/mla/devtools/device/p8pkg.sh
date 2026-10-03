#!/bin/bash
# T8: opkg install / upgrade / remove / reinstall of the CineView MLA ipk on Slot 8 (rootfs on USB only).
# usage: p8pkg.sh <ipk v1> <ipk v2 (higher version)>
# Backups first; every step leaves a bootable GUI.  Ends with v2 installed, MLA selected, Classic navy.
. ~/cineview-mla/p6lib.sh
IPK1=${1:?ipk1}; IPK2=${2:?ipk2}
B=/media/usb/cineview-mla/state/backup-t8; S=~/cineview-mla/shots/p8pkg; rm -rf $S; mkdir -p $S
ga() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1 @$($R 'date +%T')"; }
stop() { O=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; pidof enigma2 || echo e2-stopped'; }
start() { $R 'init 3'; newe2 $O; sleep 25; }
skin() { $R 'grep "^config.skin.primary_skin" /etc/enigma2/settings || echo "primary_skin=<default>"'; }
# 0. backups (settings, state, every MLA file, the hook)
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings && tar -C /etc/enigma2 -czf $B/cineview_mla-state.tgz cineview_mla && tar -C / -czf $B/mla-files.tgz usr/share/enigma2/CineView_FHD_MLA usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA \$(cd / && ls usr/lib/enigma2/python/Components/CineViewMLA*.py usr/lib/enigma2/python/Components/Renderer/CineViewMLA*.py usr/lib/enigma2/python/Components/Converter/CineViewMLA*.py) usr/bin/enigma2_pre_start.sh && ls -l $B"
cat $IPK1 | $R 'cat > /tmp/cvmla/v1.ipk'; cat $IPK2 | $R 'cat > /tmp/cvmla/v2.ipk'
# 1. fresh install: remove the tar-deployed MLA files (no package owns them), install v1
stop
$R 'rm -rf /usr/share/enigma2/CineView_FHD_MLA /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA /usr/lib/enigma2/python/Components/CineViewMLA*.py /usr/lib/enigma2/python/Components/Renderer/CineViewMLA*.py /usr/lib/enigma2/python/Components/Converter/CineViewMLA*.py /usr/bin/enigma2_pre_start.sh; echo removed-tar-files'
$R 'opkg install /tmp/cvmla/v1.ipk 2>&1 | tail -8; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E "Version|Status"; ls -l /usr/share/enigma2/CineView_FHD_MLA/active /usr/bin/enigma2_pre_start.sh'
start; st; e2log 8; X; $RC 352; sleep 2; ga T8_1_fresh_ib; X
# 2. choose Details (both sections) then UPGRADE to v2: the selection must be rebuilt with the new packs
$R 'python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py apply --set infobar=details --set secondinfobar=details 2>&1 | tail -1'
stop; $R 'opkg install /tmp/cvmla/v2.ipk 2>&1 | tail -8; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E "Version|Status"; cat /tmp/cineview_mla_postinst.log | tail -2'
start; st; e2log 8; X; $RC 352; sleep 2; ga T8_2_upgraded_ib; X
# 3. remove while selected -> must be refused
$R 'opkg remove enigma2-plugin-skins-cineview-fhd-mla 2>&1 | tail -4; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Status'
# 4. remove after selecting the default skin (GUI stopped, settings edited, then GUI starts on the default skin)
stop; skin
$R 'cp -p /etc/enigma2/settings /tmp/cvmla/settings.t8 && sed -i "/^config.skin.primary_skin=/d" /etc/enigma2/settings && opkg remove enigma2-plugin-skins-cineview-fhd-mla 2>&1 | tail -4; ls -d /usr/share/enigma2/CineView_FHD_MLA /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA /usr/bin/enigma2_pre_start.sh 2>&1; ls /usr/lib/enigma2/python/Components/Renderer/ | grep -c CineViewMLA; ls /etc/enigma2/cineview_mla | head'
skin; start; ga T8_4_removed_default_skin; $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); grep -a -c Traceback $f'
# 5. reinstall v2, MLA selected again (settings restored), factory Classic navy
stop; $R 'opkg install /tmp/cvmla/v2.ipk 2>&1 | tail -4; cp -p /tmp/cvmla/settings.t8 /etc/enigma2/settings'; skin
$R 'python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py rollback --to factory | tail -1'
start; st; e2log 8; X; $RC 352; sleep 2; ga T8_5_reinstalled_ib; X
$R 'opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E "Version|Status"'
echo T8_DONE
