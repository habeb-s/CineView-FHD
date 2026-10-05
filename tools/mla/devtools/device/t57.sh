#!/bin/bash
# Modern SecondInfoBar + Channel Selection + EventView + EPG packs (build50) on the receiver: posters ON / OFF (real reflow),
# three themes for text contrast (navy, burgundy, green), cursor movement in the channel list (the right card must
# follow the CURSOR service), skin errors / tracebacks after each step.  Look still pending the user's approval.
# Restore: Classic everywhere, navy, posters ON.
exec 9>~/cineview-mla/t57.lock; flock -n 9 || { echo "t57 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build50}
S=~/cineview-mla/shots/t57; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|rror" $f | grep -v "progressPercentWidth\|piconMargin\|Summary\|accelAlloc" | tail -6 | cut -c1-170'; }
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
evs() {  # $1 tag: live INFO (EventView), vertical EPG other event -> INFO (EventViewSimple), InfoBar EPG -> INFO
  zap $HBO; X; $RC 358; sleep 5; ga ev_$1_live; X; sleep 2
  op vertical 9; $RC 106; sleep 3; $RC 108; sleep 3; $RC 358; sleep 5; ga ev_$1_simple; X; sleep 2; X; sleep 2; X; sleep 2
  op infobarepg 7; $RC 358; sleep 5; ga ev_$1_infobar; X; sleep 2; X; sleep 2; X; sleep 2
}
epg() {  # $1 tag: Graphical EPG, cursor right / down (the card follows the highlighted cell)
  zap $HBO; X; op graph 9; ga epg_$1_open; $RC 106; sleep 3; ga epg_$1_right; $RC 108; sleep 3; ga epg_$1_down; X; sleep 2; X; sleep 2
}
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
for t in navy burgundy green; do
  $R "$E apply --theme $t --set infobar=modern --set secondinfobar=modern --set channelselection=modern --set eventview=modern --set epg=modern 2>&1 | tail -1"
  restart ""; errs
  echo "== $t posters ON"
  zap $HRT1; X; sleep 2; $RC 352; sleep 2.5; ga ib_${t}_on; $RC 352; sleep 4; ga sib_${t}_on; X; sleep 2
  zap $HBO; X; $RC 108; sleep 5; ga cs_${t}_on_open; $RC 108; sleep 3; ga cs_${t}_on_down1; $RC 108; sleep 3; $RC 108; sleep 3; ga cs_${t}_on_down3; X; sleep 2; errs
  evs ${t}_on; errs
  epg ${t}_on; errs
  if [ $t = navy ]; then
    echo "== $t posters OFF"
    restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_secondinfobar=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_infobar=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=False;"; errs
    zap $HRT1; X; sleep 2; $RC 352; sleep 2.5; ga ib_${t}_off; $RC 352; sleep 4; ga sib_${t}_off; X; sleep 2
    zap $HBO; X; $RC 108; sleep 5; ga cs_${t}_off_open; $RC 108; sleep 3; ga cs_${t}_off_down1; X; sleep 2; errs
    evs ${t}_off; errs
    epg ${t}_off; errs
    restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_secondinfobar=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_infobar=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=True;"
  fi
done
$R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set eventview=classic-lines --set epg=classic 2>&1 | tail -1"; $R "rm -rf $P"; restart ""; st; errs
echo T57_DONE
