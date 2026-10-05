#!/bin/bash
# EventView key FUNCTIONS, corrected key codes (t54 used 398..401 as green/yellow/red/blue; the Linux codes are
# KEY_RED 398, KEY_GREEN 399, KEY_YELLOW 400, KEY_BLUE 401).  Classic EventView captions (build52).
#  A EPG (vertical, other channel) -> INFO -> EventViewSimple with captions; GREEN (timer editor, then EXIT = cancel),
#    YELLOW (Single EPG), BLUE (Multi EPG), RED (Similar, only if captioned) -> grab each, EXIT back
#  B live INFO -> Classic dashboard with captions; GREEN -> timer editor -> EXIT
#  C InfoBar EPG -> INFO -> InfoBarEventView with captions
#  D posters OFF: A's EventViewSimple_CVPosterOff
# Safety: the timer list is read before and after (nothing may be added); no timer is ever confirmed.
exec 9>~/cineview-mla/t54b.lock; flock -n 9 || { echo "t54b already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build52}
S=~/cineview-mla/shots/t54b; rm -rf $S; mkdir -p $S
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
live() { zap $HBO; X; $RC 358; sleep 5; }
evepg() { zap $HBO; X; op vertical 9; $RC 106; sleep 3; $RC 108; sleep 3; $RC 358; sleep 5; }
echo "== B live INFO (EventViewEPGSelect, live dashboard): captions Add Timer / Single EPG / Multi EPG"
live; ga b_live; key 399 6; ga b_green_timer_editor; X; sleep 3; X; sleep 2
live; key 400 7; ga b_yellow_single_epg; X; sleep 3; X; sleep 2; X; sleep 2
live; key 401 8; ga b_blue_multi_epg; X; sleep 3; X; sleep 2; X; sleep 2
live; key 398 6; ga b_red_uncaptioned; X; sleep 3; X; sleep 2; X; sleep 2
errs
echo "== A EPG -> EventViewSimple: caption Add Timer only"
evepg; ga a_ev; key 399 6; ga a_green_timer_editor; X; sleep 3; X; sleep 2; X; sleep 2; X; sleep 2
errs
T1=$(timers); echo "timers after: $T1"; [ "$T0" = "$T1" ] && echo "TIMERS UNCHANGED" || echo "TIMERS CHANGED !!!"
$R "rm -rf $P"; restart ""; st; errs
echo T54B_DONE
