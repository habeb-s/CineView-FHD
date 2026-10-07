#!/bin/bash
# t107p - OpenBH (Slot 5): native PVR with a REAL short recording on the slot's own USB storage (never /media/hdd).
#   1 timers.xml backed up; one 90 s timer on the test service, recording folder given explicitly (dirname) =
#     /home/root/cvmla-testmedia/ on the Slot 5 USB rootfs -> no recording-path setting is changed at all
#   2 native MovieSelection on that folder: list, INFO (event view), navigation, poster, playback (MoviePlayer), stop
#   3 the timer entry is deleted, the test recording files are deleted (that folder only), timers.xml compared with
#     the backup, the folder removed if empty
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r5.sh
S=~/cineview-mla/shots/t107p; rm -rf $S; mkdir -p $S
D=/home/root/cvmla-testmedia/
ZAP=${ZAP:-1:0:19:786:C6D4:16E:A00000:0:0:0:}
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "   cap $1"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
enc() { python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$1"; }
errs() { $R 'f=$(ls -t /home/root/logs/Enigma2_debug_*.log | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors=$(grep -a -c "\[Skin\] Error\|SkinError" $f)"'; }
case "$D" in /media/hdd*) echo "refusing HDD path"; exit 1;; esac
$R "mkdir -p $D; cp -p /etc/enigma2/timers.xml /tmp/timers.xml.before-t107p; df -h / | tail -1"
curl -s -m 10 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ZAP"; sleep 8
NOW=$(date +%s); B=$((NOW + 20)); E=$((NOW + 110))
NAME="CineView MLA PVR test"
echo "== timer $B..$E -> $D"
curl -s -m 15 "http://192.168.1.250/api/timeradd?sRef=$(enc "$ZAP")&begin=$B&end=$E&name=$(enc "$NAME")&description=$(enc "short real recording, deleted after the test")&disabled=0&justplay=0&afterevent=0&dirname=$(enc "$D")" | python3 -c "import json,sys;d=json.load(sys.stdin);print('   timeradd:', d.get('result'), d.get('message'))"
sleep $((E - $(date +%s) + 20))
echo "   files: $($R "ls -la $D")"
$R "ls $D | grep -c '\.ts$'" | grep -q '^0$' && { echo "NO RECORDING"; }
echo "== native PVR"
X; op nativemovies 7; ga 01_list
$RC 358; sleep 3; ga 02_info; $RC 174; sleep 1.5
$RC 108; sleep 1; ga 03_down; $RC 103; sleep 1; ga 04_up
# select the recording row (the list starts on '..' / directories): move until the selected row is the .ts
for i in 1 2 3; do $RC 108; sleep 0.8; done; ga 05_select
$RC 352; sleep 6; ga 06_playing; $RC 352; sleep 1.5; ga 07_player_infobar
$RC 128; sleep 3; ga 08_after_stop
$RC 352; sleep 2; ga 09_after_stop_ok
X; X; errs
echo "== cleanup"
curl -s -m 15 "http://192.168.1.250/api/timerdelete?sRef=$(enc "$ZAP")&begin=$B&end=$E" | python3 -c "import json,sys;d=json.load(sys.stdin);print('   timerdelete:', d.get('result'), d.get('message'))"
sleep 3
$R "cd $D && for f in *; do case \"\$f\" in *'$NAME'*) rm -f \"\$f\"; echo \"   deleted \$f\";; esac; done; ls -la $D; rmdir $D 2>/dev/null && echo '   folder removed'"
$R 'cmp -s /etc/enigma2/timers.xml /tmp/timers.xml.before-t107p && echo "   timers.xml identical to the backup" || { echo "   timers.xml differs:"; diff /tmp/timers.xml.before-t107p /etc/enigma2/timers.xml | head; }'
echo T107P_DONE
