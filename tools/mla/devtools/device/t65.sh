#!/bin/bash
# Modern EventView picon fix (build60: one fixed picon place; t57b showed a stray default picon from the hidden
# ON/OFF variant) + accelAlloc count for the same screen.  Live INFO, posters ON and OFF, navy.
# Restore: Classic EventView (classic-lines), posters ON.
exec 9>~/cineview-mla/t65.lock; flock -n 9 || { echo "t65 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build60}
S=~/cineview-mla/shots/t65; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
ap() { local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | sed "s/^/   apply: /"; echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"; }
~/cineview-mla/deploy_b.sh $NEW
ap --theme navy --set eventview=modern; restart ""; errs
for z in $HBO "1:0:19:785:C6D4:16E:A00000:0:0:0:"; do zap $z; X; $RC 358; sleep 5; ga ev_on_$(echo $z | cut -d: -f4); X; sleep 2; done; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False;"; errs
zap $HBO; X; $RC 358; sleep 5; ga ev_off_784; X; sleep 2; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True;"
ap --theme navy --set eventview=classic-lines; restart ""; st; errs
echo T65_DONE
