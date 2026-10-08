#!/bin/bash
# First install of the CineView MLA OpenViX test package on Slot 4 (OpenViX 6.9).  usage: vix_install.sh <ipk>
# Backup first (Slot 4 rootfs only), poster cache pinned to /tmp BEFORE the first GUI start (HDD never used),
# skin + debug log selected while Enigma2 is stopped (Enigma2 writes settings on exit).  No reboot, no slot change.
R=~/cineview-mla/r4.sh
IPK=${1:?ipk}
B=/home/root/mla-backup-20261008-openvix
$R 'grep -q "rootsubdir=duo4kse/linuxrootfs4" /proc/cmdline && grep -q "^distro=.openvix" /usr/lib/enigma.info' || { echo "NOT Slot 4 OpenViX - stop"; exit 1; }
$R "[ -e $B/settings ] || { mkdir -p $B && cp -p /etc/enigma2/settings $B/settings && opkg list-installed > $B/opkg-installed.txt && ls -la /usr/share/enigma2 > $B/skins.txt && ls -d /etc/enigma2/cineview_mla > $B/mla_state_before.txt 2>&1; }; sha256sum $B/settings; ls $B"
cat "$IPK" | $R 'cat > /tmp/cvmla-test.ipk'
$R 'opkg install /tmp/cvmla-test.ipk 2>&1 | grep -v "^Downloading\|^Collected"; rm -f /tmp/cvmla-test.ipk; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep "Version\|Status"'
$R 'opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -q "Status: install ok installed"' || { echo "INSTALL FAILED"; exit 2; }
$R 'mkdir -p /etc/enigma2/cineview_mla && python3 - <<EOF
import json
p = "/etc/enigma2/cineview_mla/runtime.json"
try:
    rt = json.load(open(p))
except Exception:
    rt = {}
rt.setdefault("poster_cache", "/tmp/CINEVIEW-MLA/poster")
json.dump(rt, open(p, "w"), indent=1, sort_keys=True)
print("pin:", rt["poster_cache"])
EOF'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
cat ~/cineview-mla/mi/tools/mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P /home/root/cvmla-testmedia && cat > $P/plugin.py && touch $P/__init__.py && echo devtool ok"
o=$($R pidof enigma2)
$R 'init 4; for i in $(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; pidof enigma2 && echo STILL-RUNNING
S=/etc/enigma2/settings
sed -i "s#^config.skin.primary_skin=.*#config.skin.primary_skin=CineView_FHD_MLA/skin.xml#" $S
grep -q "^config.skin.primary_skin=" $S || echo "config.skin.primary_skin=CineView_FHD_MLA/skin.xml" >> $S
grep -q "^config.crash.enabledebug=" $S && sed -i "s#^config.crash.enabledebug=.*#config.crash.enabledebug=True#" $S || echo "config.crash.enabledebug=True" >> $S
grep -n "primary_skin\|enabledebug" $S; init 3'
for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done; echo "new e2 pid=$p"
for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done
sleep 30
$R 'grep primary_skin /etc/enigma2/settings; ls -t /home/root/logs/ | head -3; f=/home/root/logs/$(ls -t /home/root/logs | grep Enigma2_debug | head -1); echo LOG $f; grep -a -c Traceback $f; grep -a "Traceback\|\[Skin\] Error\|SkinError\|missing element\|CineViewMLA\]" $f | head -40; ls /tmp/CINEVIEW-MLA 2>&1 | head'
echo VIX_INSTALL_DONE
