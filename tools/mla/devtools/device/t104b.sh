#!/bin/bash
# t104b - true fresh install with the files published in habeb-s/CineView-MLA (t104 scenario 1 was refused by the
# package's prerm guard: the selected skin cannot be removed - correct behaviour).
#   a official uninstaller (fixed, purge keeps backup/) -> package removed, state gone except backup/
#   b Smart Installer fresh: "No earlier installation", HDD_CACHE=0 pin written BEFORE any GUI start (guard)
#   c skin selected (settings line, GUI stopped - same as Menu > Skin), GUI start -> factory design, 0 errors
#   d restore the original selection, profiles and runtime.json
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t104b; rm -rf $S; mkdir -p $S
F=enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk; INST=/tmp/ghv/inst.sh; PKG=/tmp/ghr/$F
ST=/etc/enigma2/cineview_mla; E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1"; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error" $f | grep -v "progressPercentWidth\|piconMargin" | tail -3 | cut -c1-170'; }
state() { $R "opkg status enigma2-plugin-skins-cineview-fhd-mla | sed -n 's/^Version: //p'; readlink /usr/share/enigma2/CineView_FHD_MLA/active; python3 -c \"import json;print('pin=%s' % json.load(open('$ST/runtime.json')).get('poster_cache'))\" 2>/dev/null || echo pin=none; python3 -c \"import json;d=json.load(open('$ST/selection.json'));print(d['theme'], d['layouts']['infobar'])\" 2>/dev/null; sed -n 's/^config.skin.primary_skin=//p' /etc/enigma2/settings" | tr '\n' ' '; echo; }
hddsnap() { $R 'd=/media/hdd/poster; [ -d $d ] && echo "$(find $d -type f | wc -l) files, $(find $d -type f -mmin -30 | wc -l) changed in 30 min" || echo none'; }
H0=$(hddsnap); echo "hdd poster before: $H0"
TS=$($R 'date +%Y%m%d-%H%M%S'); BK=/media/usb/cineview-mla/state/backup-t104b-$TS
$R "mkdir -p $BK && tar -C /etc/enigma2 -czf $BK/cineview_mla.tgz cineview_mla && cp -p /etc/enigma2/settings $BK/settings && echo backup $BK"
ORIG=$($R "python3 -c \"import json;d=json.load(open('$ST/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
echo "orig: $ORIG"; echo "state before: $(state)"
X

echo "== a uninstall (purge)"
cat ~/cineview-mla/repo/product/install/cineview-uninstall.sh | $R "cat > /tmp/cineview-uninstall.sh"
o=$(pid); $R "sh /tmp/cineview-uninstall.sh purge" < /dev/null 2>&1 | tee $S/a_uninstall.txt | sed 's/^/   | /'
newe2 $o; sleep 15
echo "   state: $(state)"; $R "ls -A $ST; ls $ST/backup | tail -3; ls /tmp/cineview-uninstall.sh 2>/dev/null"; errs; ga a_default_skin

echo "== b fresh install"
cat $INST | $R "cat > /tmp/cineview-install.sh"; cat $PKG | $R "cat > /tmp/cvmla-gh.ipk"
$R "cd /tmp; CVMLA_COLOR=1 HDD_CACHE=0 CVMLA_PKG_URL=/tmp/cvmla-gh.ipk sh /tmp/cineview-install.sh" < /dev/null > $S/b_fresh.ansi 2>&1; echo "   exit=$?"
sed 's/\x1b\[[0-9;]*m//g; s/\r//g' $S/b_fresh.ansi | tee $S/b_fresh.txt | sed 's/^/   | /'
echo "   state: $(state)"
PIN=$($R "python3 -c \"import json;print(json.load(open('$ST/runtime.json')).get('poster_cache'))\"" 2>/dev/null)
case "$PIN" in /tmp/*) echo "   pin guard OK: $PIN" ;; *) echo "   PIN GUARD FAILED ($PIN) - writing /tmp pin, stopping"; $R "printf '{\"poster_cache\": \"/tmp/CINEVIEW-MLA/poster\"}' > $ST/runtime.json"; exit 3 ;; esac

echo "== c select skin + GUI start"
o=$(pid); $R "init 4; for i in \$(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; sed -i '/^config.skin.primary_skin=/d' /etc/enigma2/settings; echo config.skin.primary_skin=CineView_FHD_MLA/skin.xml >> /etc/enigma2/settings; init 3"
newe2 $o; sleep 28
echo "   state: $(state)"; errs; ga c_fresh_skin
$RC 358; sleep 2; ga c_fresh_infobar; X

echo "== d restore"
$R "tar -C /tmp -xzf $BK/cineview_mla.tgz cineview_mla/runtime.json cineview_mla/profiles 2>/dev/null; cp -p /tmp/cineview_mla/runtime.json $ST/runtime.json; cp -a /tmp/cineview_mla/profiles/. $ST/profiles/ 2>/dev/null; rm -rf /tmp/cineview_mla /tmp/cvmla-gh.ipk; $E apply $ORIG 2>&1 | tail -1"
o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 28
echo "   state: $(state)"; errs
grep -ci "g0000\|generation\|dev/mla\|build9\|dev-cache\|/tmp/cineview_mla_postinst" $S/*.txt | sed 's/^/   internal words: /'
H1=$(hddsnap); echo "hdd poster before: $H0"; echo "hdd poster after:  $H1"
echo T104B_DONE
