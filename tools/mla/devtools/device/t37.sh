#!/bin/bash
# build35 device run (Slot 8), autonomous order 2026-10-04 22:06:
#  A1 long channel names: Classic TV + radio, Poster List, Video First L/R (+ radio list while a D1 design is active)
#  A2 Video First card dimming (steThemeCard) on several channels
#  B  EPG Graphical Plus: posters ON/OFF, cursor moves, six themes
#  C  EPGvertical flow (OK / right / down / INFO) for the Columns study
#  restore: Classic, classic-lines, navy, posters on, dev trigger plugin removed
exec 9>~/cineview-mla/t37.lock; flock -n 9 || { echo "t37 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build35}
S=~/cineview-mla/shots/t37; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"; CINEMAX="1:0:19:786:C6D4:16E:A00000:0:0:0:"; HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|name clip:\|ScreenOpen\] error\|Processing screen .GraphicalEPG\|Processing screen .ChannelSelection" $f | tail -6'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
apply() { $R "$E apply $* 2>&1 | tail -1"; }

~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "grep -E 'e1like_radio_mode|graph_prevtimeperiod|graph_itemsperpage' /etc/enigma2/settings; echo defaults-if-empty"

echo "== A1 long names"
for d in classic posterlist videofirst videofirst-right; do
  apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=$d --set epg=classic --set eventview=classic-lines --set pvr=classic
  restart ""; errs
  zap $HBO; X; $RC 108; sleep 5; ga a1_${d}_tv; X
  op radio 7; ga a1_${d}_radio; X; zap $HBO; X
done
echo "== A2 Video First dimming"
apply --set channelselection=videofirst; restart ""; errs
for ch in "$HBO|hbo" "$CINEMAX|cinemax" "$HRT1|hrt1"; do zap ${ch%%|*}; X; $RC 108; sleep 5; ga a2_vf_${ch##*|}; X; done
apply --set channelselection=videofirst-right; restart ""; errs
zap $HRT1; X; $RC 108; sleep 5; ga a2_vfr_hrt1; X

echo "== B Graphical Plus"
apply --set channelselection=classic --set epg=graphicalplus; restart ""; errs
zap $HBO; X
op graph 9; ga b_gp_on; $RC 106; sleep 3; ga b_gp_on_right; $RC 108; sleep 3; ga b_gp_on_down; $RC 108; sleep 3; ga b_gp_on_down2; X
errs
for th in black burgundy graphite green purple; do
  apply --theme $th; restart ""; zap $HBO; X; op graph 9; ga b_gp_on_$th; X
done
apply --theme navy
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=False;"; errs
zap $HBO; X; op graph 9; ga b_gp_off; $RC 106; sleep 3; ga b_gp_off_right; $RC 108; sleep 3; ga b_gp_off_down; X
errs
apply --theme burgundy; restart ""; zap $HBO; X; op graph 9; ga b_gp_off_burgundy; X
apply --theme navy
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=True;"; errs

echo "== C EPGvertical flow (Classic EPG)"
apply --set epg=classic; restart ""; errs
zap $HBO; X
op vertical 8; ga c_v0; $RC 352; sleep 5; ga c_v1_ok; $RC 106; sleep 3; ga c_v2_right; $RC 108; sleep 3; ga c_v3_down; $RC 358; sleep 4; ga c_v4_info; X
errs

echo "== restore"
$R "rm -rf $P"
apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set eventview=classic-lines --set pvr=classic
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=True config.plugins.cineviewmla.poster_channelselection=True config.usage.show_second_infobar=2;"; st; errs
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings; ls /usr/lib/enigma2/python/Plugins/Extensions | grep -c ScreenOpen"
echo T37_DONE
