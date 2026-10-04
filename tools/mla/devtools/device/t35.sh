#!/bin/bash
# build34 follow-up (Slot 8): name clip (fixed import) on Video First L/R and Poster List, opaque Poster List,
# EPGvertical + GraphicalEPG contract check for the D2 proposals, posters decoded at widget size (ePicLoad):
# accelAlloc count + CPU/RSS with the same sequences as t34; restore.  Dev trigger plugin removed at the end.
exec 9>~/cineview-mla/t35.lock; flock -n 9 || { echo "t35 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build34}
S=~/cineview-mla/shots/t35; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|name clip\|ScreenOpen\] \|Processing screen .EPGvertical\|Processing screen .GraphicalEPG" $f | tail -6'; }
cpu() { $R 'p=$(pidof enigma2); set -- $(cut -d" " -f14,15 /proc/$p/stat); echo $(( ($1 + $2) * 10 )) $(grep VmRSS /proc/$p/status | tr -s " " | cut -d" " -f2)'; }
navloop() { for r in $(seq 1 $1); do $RC 108; sleep 3; for i in 1 2 3 4 5 6; do $RC 108; sleep 0.6; done; for i in 1 2 3 4 5 6; do $RC 103; sleep 0.6; done; X; done; }
fails() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); grep -a -c "accelAlloc failed" $f'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
for d in videofirst videofirst-right posterlist; do
  $R "$E apply --theme navy --set channelselection=$d --set eventview=classic-lines 2>&1 | tail -1"; restart ""; errs
  zap $HBO; X; $RC 108; sleep 5; ga d1_${d}; $RC 108; sleep 3; ga d1_${d}_down1; X
done
$R "$E apply --set channelselection=classic 2>&1 | tail -1"; restart ""; errs
zap $HBO; X
op vertical 8; ga epg_vertical; $RC 106; sleep 3; ga epg_vertical_right; $RC 108; sleep 3; ga epg_vertical_down; X
op graph 8; ga epg_graph; X
errs
echo "== posters at widget size: accelAlloc and CPU (same sequences as t34)"
restart "touch /tmp/cvmla/acceldebug;"; errs
zap $HBO; X; $RC 352; sleep 3; X; $RC 358; sleep 5; X; $RC 108; sleep 5; X
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); cp $f /media/usb/cineview-mla/tmp/accel_fix.log'; $R 'cat /media/usb/cineview-mla/tmp/accel_fix.log' > $S/accel_fix.log; $R 'rm -f /media/usb/cineview-mla/tmp/accel_fix.log /tmp/cvmla/acceldebug'
echo "   accel fails (Classic, posters on, zap+IB+EV+CS) = $(fails)"
$R "$E apply --set channelselection=posterlist 2>&1 | tail -1"; restart ""; errs
zap $HBO; X; $RC 108; sleep 4; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 4; done; X
a=$(cpu); navloop 5; b=$(cpu); echo "   posters ON (Poster List, 5 rounds): cpu_ms ${a% *}->${b% *} rss_kB ${a#* }->${b#* } accel_fails=$(fails)"
$R "$E apply --set channelselection=classic 2>&1 | tail -1"
$R "rm -rf $P"; restart ""; st; errs
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings; ls /usr/lib/enigma2/python/Plugins/Extensions | grep -c ScreenOpen"
echo T35_DONE
