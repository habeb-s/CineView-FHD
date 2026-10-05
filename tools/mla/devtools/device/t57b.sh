#!/bin/bash
# Modern SecondInfoBar (t57 grabbed the InfoBar: the 1920-px grab between the two OK presses outlasted the InfoBar
# timeout, so the 2nd OK re-opened the InfoBar — test-timing error, as in t30: OK, 1.5 s, OK) + the EventView picon
# fix (Service source) + the Channel Selection bouquet title (Title source), build54.  Posters ON / OFF, navy and
# green.  Restore: Classic, navy, posters ON.
exec 9>~/cineview-mla/t57b.lock; flock -n 9 || { echo "t57b already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build54}
S=~/cineview-mla/shots/t57b; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|Processing screen .SecondInfoBar" $f | grep -v "progressPercentWidth\|piconMargin\|Summary" | tail -4 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
sib() {  # $1 tag
  zap $HRT1; X; sleep 2; $RC 352; sleep 1.5; $RC 352; sleep 4; ga sib_$1; X; sleep 2
  zap $HBO; X; sleep 2; $RC 352; sleep 1.5; $RC 352; sleep 4; ga sib_$1_hbo; X; sleep 2
}
~/cineview-mla/deploy_b.sh $NEW
for t in navy green; do
  $R "$E apply --theme $t --set infobar=modern --set secondinfobar=modern --set channelselection=modern --set eventview=modern 2>&1 | tail -1"
  restart ""; errs
  echo "== $t posters ON"; sib ${t}_on
  zap $HBO; X; $RC 358; sleep 5; ga ev_${t}_on_live; X; sleep 2
  zap $HBO; X; $RC 108; sleep 5; ga cs_${t}_on; X; sleep 2; errs
done
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_secondinfobar=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False;"; errs
echo "== green posters OFF"; sib green_off
zap $HBO; X; $RC 358; sleep 5; ga ev_green_off_live; X; sleep 2; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_secondinfobar=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True;"
$R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set eventview=classic-lines 2>&1 | tail -1"; restart ""; st; errs
echo T57B_DONE
