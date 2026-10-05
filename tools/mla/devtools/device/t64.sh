#!/bin/bash
# Cinema EventView "Feature" re-test (build58): t59 showed an EMPTY description (native ScrollLabel with the
# translucent steThemeOverlay background); now an opaque theme background.  Live / from the EPG / InfoBar EPG,
# posters ON and OFF, page down.  Restore: EventView classic-lines, posters ON.
exec 9>~/cineview-mla/t64.lock; flock -n 9 || { echo "t64 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build58}
S=~/cineview-mla/shots/t64; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|Processing screen .MovieSelection\|CineViewMLAPosterX.*Service\|posters-off names" $f | grep -v "progressPercentWidth\|piconMargin\|Summary" | tail -6 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
mov() {  # $1 tag: open the recordings list, move down 3 x 1, up 1; EXIT
  zap $HBO; X; op movies 8; ga pvr_$1_open; for k in 1 2 3; do $RC 108; sleep 4; ga pvr_$1_down$k; done; $RC 103; sleep 4; ga pvr_$1_up1; X; sleep 3
}
evs() {  # $1 tag: live INFO (EventView), vertical EPG other event -> INFO (EventViewSimple), InfoBar EPG -> INFO
  zap $HBO; X; $RC 358; sleep 5; ga ev_$1_live; $RC 109; sleep 3; ga ev_$1_live_pagedown; X; sleep 2
  op vertical 9; $RC 106; sleep 3; $RC 108; sleep 3; $RC 358; sleep 5; ga ev_$1_simple; X; sleep 2; X; sleep 2; X; sleep 2
  op infobarepg 7; $RC 358; sleep 5; ga ev_$1_infobar; X; sleep 2; X; sleep 2; X; sleep 2
}
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
for t in navy burgundy; do
  $R "$E apply --theme $t --set eventview=feature 2>&1 | tail -1"; restart ""; errs
  echo "== feature $t ON"; evs feature_${t}_on; errs
done
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False;"; errs
echo "== feature burgundy OFF"; evs feature_burgundy_off; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True;"
$R "$E apply --theme navy --set eventview=classic-lines 2>&1 | tail -1"
$R "rm -rf $P"; restart ""; st; errs
echo T64_DONE
