#!/bin/bash
# After the old CineView FHD removal: debug log on (test only, removed by cleanup_slot4_openvix.sh), then the real
# screens, CineView Designs functions + guardian, and native PVR with a real recording.  HDD never used.
cd ~/cineview-mla
R=./r4.sh
o=$($R pidof enigma2)
$R 'init 4; for i in $(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; grep -q "^config.crash.enabledebug=" /etc/enigma2/settings || echo config.crash.enabledebug=True >> /etc/enigma2/settings; init 3'
for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30
echo "== screens (t106v), devtool installed for the test"
DEVTOOL=1 bash t106v.sh postclean infobar sib chansel mark chansel_down grid single multi ibgrid eventview evsimple pvr plugins pkgremove pkgdownload designs setup_ui msg_yesno
echo "== CineView Designs functions + guardian (t106fv)"
bash t106fv.sh
echo "== native PVR with a real recording (t107pv, no layout loop)"
PVR_LAYOUTS="" bash t107pv.sh
echo POST_TESTS_DONE
