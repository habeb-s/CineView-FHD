#!/bin/bash
# build32 (Multi EPG description exactly 6 lines; restore through a restart — t32 wrote settings while enigma2 ran and lost them) device check, Slot 8: Multi EPG posters ON/OFF via the
# dev trigger plugin (removed at the end) + regression grabs QuickEPG / EventViewSimple.
exec 9>~/cineview-mla/t33.lock; flock -n 9 || { echo "t33 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
BLD=${1:-build32}
S=~/cineview-mla/shots/t33; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
~/cineview-mla/deploy_b.sh $BLD
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set eventview=classic-lines --set pvr=classic 2>&1 | tail -1"
for pw in True False; do
  tag=$([ $pw = True ] && echo on || echo off)
  restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=$pw config.plugins.cineviewmla.poster_eventview=$pw;"; errs
  zap $HBO; X
  op multi 7; ga ${tag}_epg_multi; $RC 108; sleep 3; ga ${tag}_epg_multi_down1; X
  op quick 7; ga ${tag}_quickepg; X
  op evsimple 6; ga ${tag}_eventviewsimple; X
done
$R "rm -rf $P"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=True config.plugins.cineviewmla.poster_eventview=True;"; st; errs
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings"
echo T33_DONE
