#!/bin/bash
# Details PVR "Cover Library" + Cinema EventView "Feature" + Modern PVR (build53): MovieSelection with the cover of the SELECTED recording; cursor moves
# (the cover / title must follow the selection); posters OFF -> MovieSelection_CVPosterOff (Classic geometry);
# Classic PVR unchanged.  READ-ONLY on the HDD: the list is only opened and navigated, nothing is played, moved,
# deleted or renamed (no OK / no colour keys).  Restore: Classic PVR, posters ON.
exec 9>~/cineview-mla/t59.lock; flock -n 9 || { echo "t59 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build53}
S=~/cineview-mla/shots/t59; rm -rf $S; mkdir -p $S
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
$R "$E apply --theme navy --set pvr=cover 2>&1 | tail -1"; restart ""; errs
echo "== cover ON"; mov cover_on; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_pvr=False;"; errs
echo "== cover OFF"; mov cover_off; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_pvr=True;"
$R "$E apply --theme navy --set pvr=modern 2>&1 | tail -1"; restart ""; errs
echo "== modern ON"; mov modern_on; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_pvr=False;"; errs
echo "== modern OFF"; mov modern_off; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_pvr=True;"
$R "$E apply --theme navy --set pvr=classic 2>&1 | tail -1"; restart ""; errs
echo "== classic (regression)"; mov classic; errs
for t in navy burgundy; do
  $R "$E apply --theme $t --set eventview=feature 2>&1 | tail -1"; restart ""; errs
  echo "== feature $t ON"; evs feature_${t}_on; errs
done
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False;"; errs
echo "== feature burgundy OFF"; evs feature_burgundy_off; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True;"
$R "$E apply --theme navy --set eventview=classic-lines 2>&1 | tail -1"
$R "rm -rf $P"; restart ""; st; errs
echo T59_DONE
