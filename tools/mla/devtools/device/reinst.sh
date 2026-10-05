#!/bin/bash
# Re-install an .ipk over the same version (opkg --force-reinstall) on Slot 8, so the receiver runs exactly the
# package files (after a deploy_b.sh build overlay).  Backup first.  usage: reinst.sh <ipk> <tag>
. ~/cineview-mla/p6lib.sh
IPK=${1:?ipk}; TAG=${2:?tag}
B=/media/usb/cineview-mla/state/backup-$TAG
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings && tar -C /etc/enigma2 -czf $B/cineview_mla-state.tgz cineview_mla && echo backup $B"
cat $IPK | $R 'cat > /tmp/cvmla/up.ipk'
o=$(pid)
$R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; opkg install --force-reinstall /tmp/cvmla/up.ipk 2>&1 | tail -2; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E "Version|Status"; init 3'
newe2 $o; sleep 28; st
echo REINST_DONE
