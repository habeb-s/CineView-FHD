#!/bin/bash
# PVR on the screen the PVR key really opens here: EnhancedMovieCenter (EMCSelection), build57.
#  * test media on the Slot 8 USB stick only (tmedia_pvr.sh): A identity from the recording's own title, B local
#    cover file next to the recording, C generic programme -> default image; the original USB test clip.
#  * Details "cover" and Modern "modern" PVR packs: EMC posters ON (cursor over the four recordings), posters OFF
#    (EMCSelection_CVPosterOff), the native MovieSelection on the same USB folder (ON); Classic PVR = EMC's own skin
#    (safe fallback, nothing CineView).
#  * Nothing is played, moved, deleted or renamed: only up / down / EXIT.  The HDD is not opened.
# Restore: Classic PVR, navy, posters ON, movielist folder as before.
exec 9>~/cineview-mla/t61.lock; flock -n 9 || { echo "t61 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build57}
S=~/cineview-mla/shots/t61; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|Processing screen .\(EMC\|Movie\)\|posters-off names\|CineViewMLAPosterX" $f | grep -v "progressPercentWidth\|piconMargin\|Summary" | tail -6 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
ap() {  # apply through the engine; a refused selection is reported loudly (t61: EMC Cool*Color flags refused)
  local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | sed "s/^/   apply: /"
  echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"
}
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
emc() {  # $1 tag: EMC through the PVR path (InfoBar.showMovies), cursor down over every entry, up
  zap $HBO; X; op movies 9; ga emc_$1_open; for k in 1 2 3 4 5; do $RC 108; sleep 4; ga emc_$1_down$k; done; $RC 103; sleep 4; ga emc_$1_up1; X; sleep 3
}
nat() {  # $1 tag: native MovieSelection on the USB test folder
  zap $HBO; X; op nativemovies 9; ga ms_$1_open; for k in 1 2 3; do $RC 108; sleep 4; ga ms_$1_down$k; done; X; sleep 3
}
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
for d in cover modern; do
  for t in navy green; do
    [ $d = cover ] && [ $t = green ] && continue
    ap --theme $t --set pvr=$d; restart ""; errs
    echo "== $d $t posters ON (EMC)"; emc ${d}_${t}_on; errs
  done
  restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_pvr=False;"; errs
  echo "== $d posters OFF (EMC)"; emc ${d}_off; errs
  restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_pvr=True;"; errs
  echo "== $d native MovieSelection (USB folder)"; nat ${d}_on; errs
done
ap --theme navy --set pvr=classic; restart ""; errs
echo "== classic: EMC own skin (fallback)"; emc classic; errs
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "$R2"; st; errs
echo "movielist folder after: '$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')'"
echo T61_DONE
