#!/bin/bash
# t84: No Poster arrangement on the list screens with a fixed layout (build77): GraphicalEPG (Modern, Graphical Plus)
# and the PVR cards (Modern, Cinema Shelf, Cover Library; EMC + native MovieSelection) follow the poster of the
# HIGHLIGHTED event / SELECTED recording: poster card with a real poster, No Poster card otherwise; no placeholder.
# EPG: highlighted event on HBO (film, poster) and on HRT1 (news, generic).  PVR: USB test folder only (tmedia_pvr.sh:
# A identity lookup, B local cover, C generic news); every row of the list is grabbed.  HDD not opened; nothing played,
# deleted or moved.  Restore: Classic navy, posters ON, movielist folder as before.
exec 9>~/cineview-mla/t85.lock; flock -n 9 || { echo "t85 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build79}
S=~/cineview-mla/shots/t85; rm -rf $S; mkdir -p $S
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
    minimal) echo "--set infobar=minimal --set secondinfobar=minimal --set channelselection=minimal --set epg=minimal --set pvr=minimal --set eventview=minimal";;
    classic) echo "--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines";;
  esac
}
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh | tail -2
~/cineview-mla/deploy_b.sh $NEW >/dev/null 2>&1
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
CIN="1:0:19:786:C6D4:16E:A00000:0:0:0:"
for m in classic modern cinema details minimal; do
  echo "== $m navy posters ON"; ap --theme navy $(model $m); restart ""; errs
  for s in $HBO $CIN $HRT1; do
    n=$(echo $s | cut -d: -f4)
    zap $s; X; $RC 352; sleep 2.5; ga ${m}_${n}_ib; X; sleep 2
    $RC 352; sleep 1.5; $RC 352; sleep 4; ga ${m}_${n}_sib; X; sleep 2
    $RC 358; sleep 6; ga ${m}_${n}_ev; X; sleep 2
    $RC 108; sleep 6; ga ${m}_${n}_cs; X; sleep 2
  done
  for s in $HBO $HRT1; do
    n=$(echo $s | cut -d: -f4)
    zap $s; X; op graph 8; ga ${m}_${n}_epg; $RC 358; sleep 6; ga ${m}_${n}_epgev; X; sleep 2; X; sleep 2; X; sleep 2
  done
  if [ $m = classic ]; then
    op movies 9; for k in 0 1 2 3 4; do [ $k -gt 0 ] && { $RC 108; sleep 4; }; ga ${m}_emc_$k; done; X; sleep 3
    op nativemovies 9; for k in 0 1 2 3; do [ $k -gt 0 ] && { $RC 108; sleep 4; }; ga ${m}_ms_$k; done; X; sleep 3
  fi
  errs
done
ap --theme navy $(model classic)
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "$R2"; st; errs
echo "movielist folder after: '$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')'"
echo T85_DONE
