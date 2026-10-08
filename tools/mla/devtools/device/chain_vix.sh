#!/bin/bash
# OpenViX (Slot 4) acceptance chain after the names matrix.  Stops if the GUI or SSH is gone (no recovery, no reboot).
cd ~/cineview-mla
IPK=$PWD/pkg_vix/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openvix1_all.ipk
while ! grep -q T106X_DONE t106xv_names.log; do sleep 20; done
alive() { ./r4.sh 'grep -q linuxrootfs4 /proc/cmdline && pidof enigma2 >/dev/null' && curl -s -m 5 -o /dev/null http://192.168.1.250/api/statusinfo; }
step() { local n=$1; shift; echo "$(date +%T) START $n" >> chain_vix.status
	if ! alive; then echo "$(date +%T) STOP before $n: receiver not answering" >> chain_vix.status; exit 1; fi
	"$@" > vix_$n.log 2>&1; echo "$(date +%T) END $n rc=$?" >> chain_vix.status; }
step models bash t106xv.sh models
step themes bash t106xv.sh themes
step posters bash t106xv.sh posters
step epgpig bash t106xv.sh epgpig
step arabic bash t106lv.sh
step designs bash t106fv.sh
step pvr bash t107pv.sh
step cam_modes bash t106ev.sh
step cam_designs bash t106cv.sh
step cam_scroll bash t106c2v.sh
step lifecycle bash t108v.sh $IPK
echo "$(date +%T) CHAIN_DONE" >> chain_vix.status
