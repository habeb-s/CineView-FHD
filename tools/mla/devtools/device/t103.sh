#!/bin/bash
# t103 (user 2026-10-07 08:05) - Smart Installer on the receiver, package served from the agent (LAN only, nothing
# published).  Terminal output captured with a tty (colours).  Scenarios:
#   1 DRYRUN           2 same version installed (verification only)   3 SHA mismatch -> stops, nothing changed
#   4 upgrade 1.0.0~rc10 -> 1.0.0 (rc10 installed first with --force-downgrade), RESTART=1
#   5 cleanup: no installer / ipk / temp folder left; poster cache, profiles, settings, backups untouched
# usage: t103.sh <ipk>
. ~/cineview-mla/p6lib.sh
IPK=${1:?ipk}; S=~/cineview-mla/shots/t103; rm -rf $S; mkdir -p $S
SHA=$(sha256sum $IPK | cut -c1-64); D=$(dirname $(readlink -f $IPK)); F=$(basename $IPK)
( cd $D && exec python3 -m http.server 8089 --bind 192.168.1.42 ) > $S/http.log 2>&1 & HP=$!
sleep 1
URL="http://192.168.1.42:8089/$F"
T="ssh -tt -o BatchMode=yes -o IdentitiesOnly=yes -i $HOME/.ssh/vuplus_aiagent root@192.168.1.250"
push() { cat ~/cineview-mla/repo/product/install/cineview-install.sh | $R "cat > /tmp/cineview-install.sh"; }
run() {  # $1 name, $2 env
	local s=${SHA_OVERRIDE:-$SHA}
	push; echo "== $1"; $T "cd /tmp; $2 CVMLA_PKG_URL=$URL CVMLA_PKG_SHA=$s sh /tmp/cineview-install.sh" < /dev/null > $S/$1.ansi 2>&1
	sed 's/\x1b\[[0-9;]*m//g; s/\r//g' $S/$1.ansi | tee $S/$1.txt | sed 's/^/   | /'
	$R "ls /tmp/cineview-install.sh /tmp/.cvmla.* 2>/dev/null | sed 's/^/   LEFT: /'; true"
}
state() { $R "opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version; readlink /usr/share/enigma2/CineView_FHD_MLA/active; ls /etc/enigma2/cineview_mla/profiles 2>/dev/null | wc -l; ls /etc/enigma2/cineview_mla/backup 2>/dev/null | wc -l; python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print(d['theme'], d['layouts']['infobar'])\"" | tr '\n' ' '; echo; }
CACHE0=$($R 'for d in /media/hdd/poster /media/usb/cineview-mla/poster /tmp/CINEVIEW-MLA/poster; do [ -d $d ] && echo "$d $(find $d -type f | wc -l)"; done' | tr '\n' ' ')
echo "cache before: $CACHE0"; echo "state before: $(state)"
run 1_dryrun "DRYRUN=1"
run 2_same ""
SHA_OVERRIDE=0000000000000000000000000000000000000000000000000000000000000000 run 3_badsha "FORCE=1"
echo "state after bad sha: $(state)"
echo "== 4 upgrade from rc10"
cat ~/cineview-mla/repo/release/rc/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc10_all.ipk | $R "cat > /tmp/rc10.ipk && opkg install --force-downgrade /tmp/rc10.ipk >/dev/null 2>&1; rm -f /tmp/rc10.ipk; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version"
o=$(pid); run 4_upgrade "RESTART=1"; newe2 $o; sleep 25
echo "state after upgrade: $(state)"
CACHE1=$($R 'for d in /media/hdd/poster /media/usb/cineview-mla/poster /tmp/CINEVIEW-MLA/poster; do [ -d $d ] && echo "$d $(find $d -type f | wc -l)"; done' | tr '\n' ' ')
echo "cache after: $CACHE1"
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"'
grep -ci "g0000\|generation\|dev/mla\|build9\|/tmp/cineview_mla_postinst" $S/*.txt | sed 's/^/   internal words: /'
kill $HP
echo T103_DONE
