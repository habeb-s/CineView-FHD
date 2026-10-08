#!/bin/bash
# t108v - OpenViX (Slot 4): package lifecycle.  usage: t108v.sh <ipk>
#   L1 prerm guard: removal refused while CineView MLA is the selected skin (package stays installed)
#   L2 previous skin selected (CineView_FHD, the slot's own skin before the test) with the GUI stopped, package removed,
#      GUI starts on that skin; MLA files gone, user state /etc/enigma2/cineview_mla kept
#   L3 restore: same package installed again, MLA selected, GUI restart: the user's design/theme selection is back
#   L4 --force-reinstall and preinst 100x (BusyBox re-exec: no shell crash)
# HDD never used.  No reboot.
R=~/cineview-mla/r4.sh
IPK=${1:?ipk}
S=~/cineview-mla/shots/vix_t108; rm -rf $S; mkdir -p $S
PK=enigma2-plugin-skins-cineview-fhd-mla
ST=/etc/enigma2/cineview_mla
ga() { curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "   cap $1"; }
restart_gui() { local o=$($R pidof enigma2); $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; $1 init 3"
	for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30; }
errs() { $R 'f=$(ls -t /home/root/logs/Enigma2_debug_*.log | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors=$(grep -a -c "\[Skin\] Error\|SkinError" $f) crashlogs_today=$(ls /home/root/logs | grep -i crash | grep -c 2026-10-08)"'; }
sel() { $R "python3 -c \"import json;d=json.load(open('$ST/selection.json'));print(d['theme'], ','.join('%s=%s'%kv for kv in sorted(d['layouts'].items())))\""; }
$R 'grep -q "rootsubdir=duo4kse/linuxrootfs4" /proc/cmdline' || { echo "NOT Slot 4"; exit 1; }
SEL0=$(sel); echo "selection before: $SEL0"
echo "== L1 removal while selected"
$R "opkg remove $PK 2>&1 | tail -3; opkg status $PK | grep Status"
echo "== L2 previous skin, then remove"
restart_gui "sed -i 's#^config.skin.primary_skin=.*#config.skin.primary_skin=CineView_FHD/skin.xml#' /etc/enigma2/settings; opkg remove $PK 2>&1 | tail -2;"
$R "opkg status $PK | grep -c Status; ls -d /usr/share/enigma2/CineView_FHD_MLA /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA 2>&1 | sed 's/^/   /'; ls /usr/lib/enigma2/python/Components/Converter /usr/lib/enigma2/python/Components/Renderer /usr/lib/enigma2/python/Components | grep -c CineViewMLA; ls $ST | tr '\n' ' '; echo; grep primary_skin /etc/enigma2/settings"
f=$($R 'ls -t /home/root/logs/Enigma2_debug_*.log | head -1'); $R "grep -a 'Loading skin\|primary_skin\|skin.xml' $f | tail -3 | cut -c1-200"
ga L2_after_remove_infobar_previous_skin; errs
echo "== L3 restore"
cat "$IPK" | $R 'cat > /tmp/cvmla-test.ipk'
$R "opkg install /tmp/cvmla-test.ipk 2>&1 | grep -v '^Downloading\|^Collected'; rm -f /tmp/cvmla-test.ipk; opkg status $PK | grep 'Version\|Status'"
restart_gui "sed -i 's#^config.skin.primary_skin=.*#config.skin.primary_skin=CineView_FHD_MLA/skin.xml#' /etc/enigma2/settings;"
SEL1=$(sel); echo "selection after restore: $SEL1"; [ "$SEL1" = "$SEL0" ] && echo "   SELECTION KEPT" || echo "   SELECTION DIFFERS"
$R "grep primary_skin /etc/enigma2/settings; readlink /usr/share/enigma2/CineView_FHD_MLA/active"
$R "python3 -c 'import json;print(\"pin:\", json.load(open(\"$ST/runtime.json\")).get(\"poster_cache\"))'"
X() { for i in 1 2 3 4; do ~/cineview-mla/rc.sh 174; sleep 0.6; done; sleep 1.5; }
X; ~/cineview-mla/rc.sh 352; sleep 2; ga L3_restored_infobar; X; errs
echo "== L4 reinstall + preinst 100x"
cat "$IPK" | $R 'cat > /tmp/cvmla-test.ipk'
$R "opkg install --force-reinstall /tmp/cvmla-test.ipk 2>&1 | tail -2; rm -f /tmp/cvmla-test.ipk; opkg status $PK | grep 'Version\|Status'"
$R 'P=/var/lib/opkg/info/enigma2-plugin-skins-cineview-fhd-mla.preinst; n=0; for i in $(seq 1 100); do $P upgrade >/dev/null 2>&1; [ $? -ge 128 ] && n=$((n+1)); done; echo "   preinst crashes: $n/100"'
restart_gui; errs
echo T108V_DONE
