#!/bin/bash
# EventView coloured-key captions (build45) + the REAL key functions (user decision 2026-10-05 05:23).
#  A EPG (vertical, other channel) -> INFO -> EventViewSimple with captions; GREEN (timer editor, then EXIT = cancel),
#    YELLOW (Single EPG), BLUE (Multi EPG), RED (Similar, only if captioned) -> grab each, EXIT back
#  B live INFO -> Classic dashboard with captions; GREEN -> timer editor -> EXIT
#  C InfoBar EPG -> INFO -> InfoBarEventView with captions
#  D posters OFF: A's EventViewSimple_CVPosterOff
# Safety: the timer list is read before and after (nothing may be added); no timer is ever confirmed.
exec 9>~/cineview-mla/t54.lock; flock -n 9 || { echo "t54 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build45}
S=~/cineview-mla/shots/t54; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|Processing screen .\(EventView\|InfoBarEventView\|TimerEntry\|EPGSelection\|ChoiceBox\)" $f | grep -v "progressPercentWidth\|piconMargin\|Summary" | tail -6 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
timers() { curl -s -m 8 "http://192.168.1.250/api/timerlist" | python3 -c "import json,sys; t=json.load(sys.stdin).get('timers',[]); print(len(t), sorted((x.get('serviceref','')[-30:], x.get('begin')) for x in t))"; }
key() { $RC $1; sleep ${2:-4}; }
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "$E apply --theme navy --set infobar=classic --set epg=classic --set eventview=classic-lines 2>&1 | tail -1"
restart ""; errs
T0=$(timers); echo "timers before: $T0"
evepg() { zap $HBO; X; op vertical 9; $RC 106; sleep 3; $RC 108; sleep 3; $RC 358; sleep 5; }
echo "== A EPG -> EventViewSimple + keys"
evepg; ga a_ev_captions; X; sleep 2; X; sleep 2; X; sleep 2
for k in "398 green_timer_editor" "399 yellow_single_epg" "401 blue_multi_epg" "400 red_similar"; do
  evepg; key ${k%% *} 6; ga a_${k#* }; for i in 1 2 3 4; do X; sleep 1.5; done
done
errs
echo "== B live INFO -> dashboard + keys"
zap $HBO; X; $RC 358; sleep 5; ga b_live_captions; key 398 5; ga b_green_timer_editor; X; sleep 3; X; errs
echo "== C InfoBar EPG -> InfoBarEventView"
zap $HBO; X; op infobarepg 7; $RC 358; sleep 5; ga c_infobar_eventview; X; sleep 2; X; sleep 2; X; errs
echo "== D posters OFF"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False;"; errs
evepg; ga d_ev_captions_off; X; sleep 2; X; sleep 2; X
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True;"
T1=$(timers); echo "timers after: $T1"; [ "$T0" = "$T1" ] && echo "TIMERS UNCHANGED" || echo "TIMERS CHANGED !!!"
$R "rm -rf $P"; restart ""; st; errs
echo T54_DONE
