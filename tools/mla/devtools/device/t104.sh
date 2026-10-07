#!/bin/bash
# t104 (user 2026-10-07 08:23) - final installer validation with the EXACT files published in the private repo
# habeb-s/CineView-MLA: installer from main (gh api), package = release asset (gh release download), both compared
# with the raw file on main.  The receiver cannot read a private repo, so the bytes are handed over as a local file
# (CVMLA_PKG_URL=/tmp/...); the SHA256 is the one EMBEDDED in the published installer (no override).
#   1 fresh install (package removed, state folder moved away; GUI stopped so nothing can fall back to the HDD)
#   2 reinstall (FORCE=1, RESTART=1)   3 upgrade 1.0.0~rc10 -> 1.0.0 (RESTART=1)
#   4 damaged package (one byte appended) -> must stop, nothing changed
#   5 reboot (STARTUP = linuxrootfs8, checked read-only)   6 Plugin Browser + CineView Designs
#   7 restore: original selection, profiles, runtime.json; devtool removed
# All runs HDD_CACHE=0 (no HDD writes on this receiver).  HDD poster folder compared read-only before/after.
exec 9>~/cineview-mla/t104.lock; flock -n 9 || { echo "t104 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t104; rm -rf $S; mkdir -p $S
F=enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk
INST=/tmp/ghv/inst.sh; PKG=/tmp/ghr/$F
cmp $PKG /tmp/ghv/$F || { echo "release asset != main file"; exit 1; }
EMB=$(sed -n 's/^PKG_SHA="${CVMLA_PKG_SHA:-\([0-9a-f]*\)}"/\1/p' $INST)
echo "embedded sha: $EMB"; echo "package sha:  $(sha256sum $PKG | cut -c1-64)"
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ST=/etc/enigma2/cineview_mla
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
rows() { $R 'rm -f /tmp/cvmla/rows.txt; echo rows > /tmp/cvmla/open.txt'; sleep 1.6; $R 'cat /tmp/cvmla/rows.txt 2>/dev/null' > $S/rows_$1.txt; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error" $f | grep -v "progressPercentWidth\|piconMargin" | tail -3 | cut -c1-170'; }
state() { $R "opkg status enigma2-plugin-skins-cineview-fhd-mla | sed -n 's/^Version: //p'; readlink /usr/share/enigma2/CineView_FHD_MLA/active; python3 -c \"import json;print('pin=%s' % json.load(open('$ST/runtime.json')).get('poster_cache'))\" 2>/dev/null || echo pin=none; ls $ST/profiles 2>/dev/null | wc -l; python3 -c \"import json;d=json.load(open('$ST/selection.json'));print(d['theme'], d['layouts']['infobar'])\" 2>/dev/null" | tr '\n' ' '; echo; }
hddsnap() { $R 'd=/media/hdd/poster; [ -d $d ] && echo "$(find $d -type f | wc -l) files, $(find $d -type f -mmin -720 | wc -l) changed in 12h" || echo none'; }
run() {  # $1 name, $2 env, $3 package file on receiver
	cat $INST | $R "cat > /tmp/cineview-install.sh"
	echo "== $1"
	$R "cd /tmp; $2 CVMLA_COLOR=1 HDD_CACHE=0 CVMLA_PKG_URL=${3:-/tmp/cvmla-gh.ipk} sh /tmp/cineview-install.sh" < /dev/null > $S/$1.ansi 2>&1
	echo "   exit=$?"
	sed 's/\x1b\[[0-9;]*m//g; s/\r//g' $S/$1.ansi | tee $S/$1.txt | sed 's/^/   | /'
	$R "ls /tmp/cineview-install.sh /tmp/.cvmla.* 2>/dev/null | sed 's/^/   LEFT: /'; true"
}
waitup() { for i in $(seq 1 150); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 25; echo "   webif up @$($R 'date +%T')"; }

H0=$(hddsnap); echo "hdd poster before: $H0"
TS=$($R 'date +%Y%m%d-%H%M%S'); BK=/media/usb/cineview-mla/state/backup-t104-$TS
$R "mkdir -p $BK && tar -C /etc/enigma2 -czf $BK/cineview_mla.tgz cineview_mla && cp -p /etc/enigma2/settings $BK/settings && echo backup $BK"
ORIG=$($R "python3 -c \"import json;d=json.load(open('$ST/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
echo "orig: $ORIG"; echo "state before: $(state)"
cat $PKG | $R "cat > /tmp/cvmla-gh.ipk"
X

echo "== 1 fresh install (GUI stopped)"
o=$(pid); $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; opkg remove enigma2-plugin-skins-cineview-fhd-mla >/dev/null 2>&1; rm -rf $ST.t104fresh; mv $ST $ST.t104fresh; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -c Version; ls -d $ST 2>/dev/null; true"
run 1_fresh ""
$R 'init 3'; newe2 $o; sleep 25
echo "   state: $(state)"; errs; ga 1_fresh_live

o=$(pid); run 2_reinstall "FORCE=1 RESTART=1"; newe2 $o; sleep 25
echo "   state: $(state)"; errs

echo "== 3 upgrade from rc10"
cat ~/cineview-mla/repo/release/rc/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc10_all.ipk | $R "cat > /tmp/rc10.ipk && opkg install --force-downgrade /tmp/rc10.ipk >/dev/null 2>&1; rm -f /tmp/rc10.ipk; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version"
o=$(pid); run 3_upgrade "RESTART=1"; newe2 $o; sleep 25
echo "   state: $(state)"; errs

echo "== 4 damaged package"
B4=$(state); $R "cp /tmp/cvmla-gh.ipk /tmp/cvmla-bad.ipk && printf x >> /tmp/cvmla-bad.ipk"
run 4_badsha "FORCE=1" /tmp/cvmla-bad.ipk
A4=$(state); echo "   before: $B4"; echo "   after:  $A4"; [ "$B4" = "$A4" ] && echo "   UNCHANGED" || echo "   CHANGED!"
$R "rm -f /tmp/cvmla-bad.ipk"

echo "== 5 reboot"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "cat /boot/STARTUP | grep -o 'rootsubdir=[a-z0-9]*'"
timeout 20 $R 'sync; reboot' || true; sleep 40; waitup
$R "grep -o 'rootsubdir=[a-z0-9]*' /proc/cmdline; uptime"
echo "   state: $(state)"; errs; ga 5_after_reboot

echo "== 6 Plugin Browser + CineView Designs"
X; op pluginbrowser 5; ga 6_pluginbrowser; rows 6_pluginbrowser; X
op designs 5; ga 6_designs; rows 6_designs; X
grep -i "cineview" $S/rows_6_pluginbrowser.txt | head -3
grep -ci "g0000\|build9\|commit\|trial\|dev-cache\|/media/usb" $S/rows_6_designs.txt | sed 's/^/   internal words in Designs rows: /'
grep -ci "g0000\|generation\|dev/mla\|build9\|dev-cache\|/tmp/cineview_mla_postinst" $S/[1-4]_*.txt | sed 's/^/   internal words: /'
errs

echo "== 7 restore"
$R "rm -rf $P; cp -a $ST.t104fresh/profiles/. $ST/profiles/ 2>/dev/null; cp -p $ST.t104fresh/runtime.json $ST/runtime.json; mv $ST.t104fresh $BK/state-before-fresh; $E apply $ORIG 2>&1 | tail -1"
o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 28
echo "   state: $(state)"; errs
$R "rm -f /tmp/cvmla-gh.ipk; ls $P 2>/dev/null | wc -l"
H1=$(hddsnap); echo "hdd poster before: $H0"; echo "hdd poster after:  $H1"
echo T104_DONE
