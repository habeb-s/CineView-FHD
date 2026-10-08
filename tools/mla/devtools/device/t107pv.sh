#!/bin/bash
# t107p - OpenViX (Slot 4): native PVR with a REAL short recording on the slot's own USB storage (never /media/hdd).
#   1 timers.xml backed up; one 90 s timer on the test service, recording folder given explicitly (dirname) =
#     /home/root/cvmla-testmedia/ on the Slot 5 USB rootfs -> no recording-path setting is changed at all
#   2 native MovieSelection on that folder: list, INFO (event view), navigation, poster, playback (MoviePlayer), stop
#   3 the timer entry is deleted, the test recording files are deleted (that folder only), timers.xml compared with
#     the backup, the folder removed if empty
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r4.sh
S=~/cineview-mla/shots/vix_t107p; rm -rf $S; mkdir -p $S
D=/home/root/cvmla-testmedia/
ZAP=${ZAP:-1:0:1:290E:1EDC:71:822FFC:0:0:0:}
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "   cap $1"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
enc() { python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$1"; }
errs() { $R 'f=$(ls -t /home/root/logs/Enigma2_debug_*.log | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors=$(grep -a -c "\[Skin\] Error\|SkinError" $f)"'; }
case "$D" in /media/hdd*) echo "refusing HDD path"; exit 1;; esac
if [ -z "$B" ]; then $R "mkdir -p $D; cp -p /etc/enigma2/timers.xml /tmp/timers.xml.before-t107p; df -h / | tail -1"; fi
curl -s -m 10 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ZAP"; sleep 8
NAME="CineView MLA PVR test"
if [ -n "$B" ] && [ -n "$E" ]; then
	echo "== existing test timer $B..$E (recording already made by this tool)"
	[ -s /tmp/timers.xml.before-t107p ] || true
else
	NOW=$(date +%s); B=$((NOW + 20)); E=$((NOW + 110))
	echo "== timer $B..$E -> $D"
	curl -s -m 15 "http://192.168.1.250/api/timeradd?sRef=$(enc "$ZAP")&begin=$B&end=$E&name=$(enc "$NAME")&description=$(enc "short real recording, deleted after the test")&disabled=0&justplay=0&afterevent=0&dirname=$(enc "$D")" | python3 -c "import json,sys;d=json.load(sys.stdin);print('   timeradd:', d.get('result'), d.get('message'))"
fi
W=$((E - $(date +%s) + 20)); [ $W -gt 0 ] && sleep $W
echo "   files: $($R "ls -la $D")"
$R "ls $D | grep -c '\.ts$'" | grep -q '^0$' && { echo "NO RECORDING"; }
echo "== native PVR"
X; op nativepvr 7; ga 01_list
$RC 358; sleep 3; ga 02_info; $RC 174; sleep 1.5
$RC 108; sleep 1; ga 03_down; $RC 103; sleep 1; ga 04_up
# 04_up is back on the recording row (the list opens on the newest recording; DOWN goes to '..')
ga 05_select
$RC 352; sleep 8; ga 06_playing; $R 'grep -a "Processing screen .MoviePlayer" $(ls -t /home/root/logs/Enigma2_debug_*.log | head -1) | tail -1 | cut -c1-120'
$RC 358; sleep 2; ga 07_player_info; $RC 174; sleep 1.5
$RC 352; sleep 1.5; ga 07b_player_infobar
$RC 128; sleep 3; ga 08_after_stop
X; X; errs
# poster / cover designs of the PVR section on the same recording (layout applied by the engine, GUI restarted)
E2='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P0=$($R "python3 -c \"import json;print(json.load(open('/etc/enigma2/cineview_mla/selection.json'))['layouts']['pvr'])\"")
for lay in ${PVR_LAYOUTS-cover cinema modern minimal}; do
	o=$($R pidof enigma2); $R "$E2 apply --set pvr=$lay 2>&1 | tail -1; init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3"
	for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30
	X; op nativemovies 9; ga 10_layout_$lay; X; errs
done
o=$($R pidof enigma2); $R "$E2 apply --set pvr=$P0 2>&1 | tail -1; init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3"
for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done; sleep 40
echo "   pvr layout restored: $P0"
echo "== cleanup"
curl -s -m 15 "http://192.168.1.250/api/timerdelete?sRef=$(enc "$ZAP")&begin=$B&end=$E" | python3 -c "import json,sys;d=json.load(sys.stdin);print('   timerdelete:', d.get('result'), d.get('message'))"
sleep 3
$R "cd $D && for f in *; do case \"\$f\" in *'$NAME'*) rm -f \"\$f\"; echo \"   deleted \$f\";; esac; done; ls -la $D; rmdir $D 2>/dev/null && echo '   folder removed'"
$R 'cmp -s /etc/enigma2/timers.xml /tmp/timers.xml.before-t107p && echo "   timers.xml identical to the backup" || { echo "   timers.xml differs:"; diff /tmp/timers.xml.before-t107p /etc/enigma2/timers.xml | head; }'
echo T107P_DONE
