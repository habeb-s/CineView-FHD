#!/bin/bash
# EventView opened from an EPG must show the SELECTED event (build40: EventViewEPGSelect -> Classic EventViewSimple
# screen).  Device t42: INFO on HBO 2 'Nevjesta!' in the vertical EPG showed HBO HD 'Holland' texts with the
# 'The Bride!' poster.  Cases (Slot 8, Classic everywhere, navy):
#  A vertical EPG from HBO HD: RIGHT (HBO 2 column), DOWN, INFO -> grab (title/time/poster of the selected event)
#  B Graphical EPG (Classic): DOWN (HBO 2 row), RIGHT (next event), INFO -> grab
#  C regression: INFO from the live InfoBar -> Classic EventView dashboard (unchanged)
#  D posters OFF: A again (EventViewSimple_CVPosterOff)
# OpenWebif titles of the selected rows are fetched for comparison.  Restore: posters on, dev trigger removed.
exec 9>~/cineview-mla/t47.lock; flock -n 9 || { echo "t47 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build40}
S=~/cineview-mla/shots/t47; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"; HBO2="1:0:19:785:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|EPG event view\|Processing screen .EventView" $f | tail -4 | cut -c1-200'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
nownext() { curl -s -m 8 "http://192.168.1.250/api/epgservice?sRef=$1" | TZ=Asia/Riyadh python3 -c "import json,sys,time; ev=json.load(sys.stdin).get('events') or []; print(' | '.join('%s %s' % (time.strftime('%H:%M', time.localtime(e['begin_timestamp'])), e['title']) for e in ev[:3]))"; }
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "$E apply --theme navy --set epg=classic --set eventview=classic-lines 2>&1 | tail -1"
restart ""; errs
echo "   HBO 2 events: $(nownext $HBO2)"; echo "   HBO events: $(nownext $HBO)"
echo "== A vertical EPG -> INFO"
zap $HBO; X; op vertical 9; $RC 106; sleep 3; $RC 108; sleep 3; ga a_vertical_sel; $RC 358; sleep 5; ga a_vertical_info; X; sleep 2; X; errs
echo "== B Graphical EPG -> INFO"
zap $HBO; X; op graph 9; $RC 108; sleep 3; $RC 106; sleep 3; ga b_graph_sel; $RC 358; sleep 5; ga b_graph_info; X; sleep 2; X; errs
echo "== C live InfoBar INFO (regression)"
zap $HBO; X; $RC 358; sleep 5; ga c_live_info; X; errs
echo "== D posters OFF, vertical EPG -> INFO"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False;"; errs
zap $HBO; X; op vertical 9; $RC 106; sleep 3; $RC 108; sleep 3; $RC 358; sleep 5; ga d_vertical_info_off; X; sleep 2; X; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True;"
$R "rm -rf $P"; restart ""; st; errs
$R "grep -E 'cineviewmla.poster' /etc/enigma2/settings"
echo T47_DONE
