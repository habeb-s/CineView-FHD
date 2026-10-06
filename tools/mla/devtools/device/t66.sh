#!/bin/bash
# New model sections (build62): Details EventView Card ("detailscard") and Cinema PVR Shelf ("cinema").
#  * EventView: live INFO (+ page down), vertical EPG -> INFO (EventViewSimple), InfoBar EPG -> INFO; posters ON
#    (navy, green) and OFF.
#  * PVR: EMC through the PVR path (InfoBar.showMovies) over the USB test recordings (tmedia_pvr.sh: the HDD is not
#    opened), posters ON (navy, burgundy) and OFF; the native MovieSelection on the same USB folder ON and OFF.
#    Nothing is played, moved, deleted or renamed: only up / down / page / EXIT.
# Restore: EventView classic-lines, PVR classic, navy, posters ON, movielist folder as before.
exec 9>~/cineview-mla/t66.lock; flock -n 9 || { echo "t66 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build62}
S=~/cineview-mla/shots/t66; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accel=$(grep -a -c "accelAlloc" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|Processing screen .\(EMC\|Movie\|EventView\)\|posters-off names" $f | grep -v "progressPercentWidth\|piconMargin\|Summary" | tail -6 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
ap() {
  local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | sed "s/^/   apply: /"
  echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"
}
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
evs() {
  zap $HBO; X; $RC 358; sleep 5; ga ev_$1_live; $RC 109; sleep 3; ga ev_$1_live_pagedown; X; sleep 2
  op vertical 9; $RC 106; sleep 3; $RC 108; sleep 3; $RC 358; sleep 5; ga ev_$1_simple; X; sleep 2; X; sleep 2; X; sleep 2
  op infobarepg 7; $RC 358; sleep 5; ga ev_$1_infobar; X; sleep 2; X; sleep 2; X; sleep 2
}
emc() { zap $HBO; X; op movies 9; ga emc_$1_open; for k in 1 2 3 4; do $RC 108; sleep 4; ga emc_$1_down$k; done; $RC 103; sleep 4; ga emc_$1_up1; X; sleep 3; }
nat() { zap $HBO; X; op nativemovies 9; ga ms_$1_open; for k in 1 2 3; do $RC 108; sleep 4; ga ms_$1_down$k; done; X; sleep 3; }
cfg() { restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.$1;"; errs; }
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
for t in navy green; do
  ap --theme $t --set eventview=detailscard; restart ""; errs
  echo "== detailscard $t ON"; evs card_${t}_on; errs
done
cfg poster_eventview=False
echo "== detailscard green OFF"; evs card_green_off; errs
cfg poster_eventview=True
for t in navy burgundy; do
  ap --theme $t --set pvr=cinema; restart ""; errs
  echo "== cinema PVR $t ON (EMC)"; emc cinema_${t}_on; errs
done
echo "== cinema PVR burgundy native MovieSelection ON"; nat cinema_on; errs
cfg poster_pvr=False
echo "== cinema PVR OFF (EMC)"; emc cinema_off; errs
echo "== cinema PVR native MovieSelection OFF"; nat cinema_off; errs
cfg poster_pvr=True
ap --theme navy --set eventview=classic-lines
ap --theme navy --set pvr=classic
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "$R2"; st; errs
echo "movielist folder after: '$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')'"
echo T66_DONE
