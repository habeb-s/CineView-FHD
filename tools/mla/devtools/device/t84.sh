#!/bin/bash
# t84: No Poster arrangement on the list screens with a fixed layout (build77): GraphicalEPG (Modern, Graphical Plus)
# and the PVR cards (Modern, Cinema Shelf, Cover Library; EMC + native MovieSelection) follow the poster of the
# HIGHLIGHTED event / SELECTED recording: poster card with a real poster, No Poster card otherwise; no placeholder.
# EPG: highlighted event on HBO (film, poster) and on HRT1 (news, generic).  PVR: USB test folder only (tmedia_pvr.sh:
# A identity lookup, B local cover, C generic news); every row of the list is grabbed.  HDD not opened; nothing played,
# deleted or moved.  Restore: Classic navy, posters ON, movielist folder as before.
exec 9>~/cineview-mla/t84.lock; flock -n 9 || { echo "t84 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build77}
S=~/cineview-mla/shots/t84; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accel=$(grep -a -c "accelAlloc failed" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|ShowIf\]\|PosterState" $f | grep -v "progressPercentWidth\|piconMargin" | tail -4 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
ap() { local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"; }
model() {
  case $1 in
    details) echo "--set infobar=details --set secondinfobar=details --set channelselection=posterlist --set epg=graphicalplus --set pvr=cover --set eventview=detailscard";;
    cinema)  echo "--set infobar=cinema --set secondinfobar=cinema --set channelselection=videofirst --set epg=graphicalplus --set pvr=cinema --set eventview=feature";;
    modern)  echo "--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern";;
    classic) echo "--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines";;
  esac
}
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh | tail -6
~/cineview-mla/deploy_b.sh $NEW >/dev/null 2>&1
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
for m in modern cinema details; do
  echo "== $m navy posters ON"; ap --theme navy $(model $m); restart ""; errs
  zap $HBO; X; op graph 8; ga ${m}_epg_hbo; $RC 106; sleep 4; ga ${m}_epg_hbo_r1; $RC 106; sleep 4; ga ${m}_epg_hbo_r2; X; sleep 2; X; sleep 2
  zap $HRT1; X; op graph 8; ga ${m}_epg_hrt1; $RC 106; sleep 4; ga ${m}_epg_hrt1_r1; X; sleep 2; X; sleep 2
  op movies 9; ga ${m}_emc_0; for k in 1 2 3 4; do $RC 108; sleep 4; ga ${m}_emc_$k; done; X; sleep 3
  op nativemovies 9; ga ${m}_ms_0; for k in 1 2 3 4; do $RC 108; sleep 4; ga ${m}_ms_$k; done; X; sleep 3
  errs
done
# Classic EventView strip picon (t68 / t82: no picon on a fresh screen; hidden ON variant drew the default picon)
echo "== classic navy posters ON: EventView strip picon"; ap --theme navy $(model classic); restart ""; errs
for s in "1:0:19:784:C6D4:16E:A00000:0:0:0:" "1:0:19:786:C6D4:16E:A00000:0:0:0:" "$HRT1"; do
  n=$(echo $s | cut -d: -f4); zap $s; X; $RC 358; sleep 6; ga classic_ev_$n; X; sleep 2
done
errs
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "$R2"; st; errs
echo "movielist folder after: '$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')'"
echo T84_DONE
