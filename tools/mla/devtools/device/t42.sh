#!/bin/bash
# Vertical EPG after the page-index fix (build37, Slot 8): the native five-column screen must be visible instead of
# the bare numbered channel list (t37).  Opens from HBO (16.0E movie channels), grabs: start, RIGHT (next column),
# DOWN x2 (next events), INFO (event view) + EXIT, key 6 (next channel page), key 0 (back to the current channel/now).
# Also checks that Event/Service follow the active column (OpenWebif now/next of the column channel for comparison).
# Restore: Classic EPG (unchanged selection), dev trigger removed.
exec 9>~/cineview-mla/t42.lock; flock -n 9 || { echo "t42 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build37}
S=~/cineview-mla/shots/t42; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|Processing screen .EPGvertical" $f | grep -v "progressPercentWidth\|piconMargin" | tail -4'; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "$E apply --set epg=classic 2>&1 | tail -1"
restart ""; errs
curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$HBO"; sleep 8; X
op vertical 9; ga v0_start
$RC 106; sleep 3; ga v1_right
$RC 108; sleep 2; $RC 108; sleep 3; ga v2_down2
$RC 358; sleep 5; ga v3_info; X; sleep 3; ga v4_back
$RC 7; sleep 4; ga v5_key6_nextpage   # KEY_6 = 7
$RC 11; sleep 4; ga v6_key0_now       # KEY_0 = 11
X; sleep 2; errs
for s in "$HBO" "1:0:19:785:C6D4:16E:A00000:0:0:0:" "1:0:19:786:C6D4:16E:A00000:0:0:0:"; do
  curl -s -m 8 "http://192.168.1.250/api/epgservicenow?sRef=$s" | TZ=Asia/Riyadh python3 -c "import json,sys,time; e=(json.load(sys.stdin).get('events') or [{}])[0]; print('   now', e.get('sname',''), time.strftime('%H:%M', time.localtime(e.get('begin_timestamp',0))), e.get('title',''))"
done
$R "rm -rf $P"; restart ""; st; errs
echo T42_DONE
