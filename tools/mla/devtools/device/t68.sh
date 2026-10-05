#!/bin/bash
# Final visual report material: the five models (Classic, Details, Cinema, Modern, Minimal) on all six sections,
# posters ON and OFF (navy), and every model in the six themes (InfoBar + Channel Selection + EventView).
# Each model is applied exactly as the CineView MLA "Apply a design model" menu does (plugin MODELS).
# PVR = EMC through the PVR key path + the native MovieSelection, both on the USB test folder (HDD not opened).
# Nothing is played, deleted or moved.  Restore: Classic, navy, posters ON, movielist folder as before.
exec 9>~/cineview-mla/t68.lock; flock -n 9 || { echo "t68 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build64}
S=~/cineview-mla/shots/t68; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accel=$(grep -a -c "accelAlloc failed" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error" $f | grep -v "progressPercentWidth\|piconMargin" | tail -3 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
ap() { local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | sed "s/^/   apply: /"; echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"; }
POSTERS="infobar secondinfobar channelselection epg pvr eventview"
pset() { local c=""; for s in $POSTERS; do c="$c python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_$s=$1;"; done; echo "$c"; }
model() {  # $1 model -> composer --set list (same table as plugin MODELS)
  case $1 in
    classic) echo "--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines";;
    details) echo "--set infobar=details --set secondinfobar=details --set channelselection=posterlist --set epg=graphicalplus --set pvr=cover --set eventview=detailscard";;
    cinema)  echo "--set infobar=cinema --set secondinfobar=cinema --set channelselection=videofirst --set epg=graphicalplus --set pvr=cinema --set eventview=feature";;
    modern)  echo "--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern";;
    minimal) echo "--set infobar=minimal --set secondinfobar=minimal --set channelselection=minimal --set epg=minimal --set pvr=minimal --set eventview=minimal";;
  esac
}
six() {  # $1 tag: the six sections (+ native MovieSelection)
  zap $HBO; X; $RC 352; sleep 4; ga ${1}_ib; X; sleep 2
  $RC 352; sleep 1.5; $RC 352; sleep 4; ga ${1}_sib; X; sleep 2
  $RC 108; sleep 4; $RC 108; sleep 3; ga ${1}_cs; X; sleep 2
  op graph 8; $RC 106; sleep 3; ga ${1}_epg; X; sleep 2; X; sleep 2
  $RC 358; sleep 5; ga ${1}_ev; X; sleep 2
  op movies 9; for k in 1 2 3; do $RC 108; sleep 3; done; sleep 2; ga ${1}_emc; X; sleep 3
  op nativemovies 9; $RC 108; sleep 4; ga ${1}_ms; X; sleep 3
}
three() {  # $1 tag: theme strip
  zap $HBO; X; $RC 352; sleep 4; ga ${1}_ib; X; sleep 2
  $RC 108; sleep 4; $RC 108; sleep 3; ga ${1}_cs; X; sleep 2
  $RC 358; sleep 5; ga ${1}_ev; X; sleep 2
}
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
for m in ${MODELS_LIST:-classic details cinema modern minimal}; do
  echo "== $m navy posters ON"; ap --theme navy $(model $m); restart ""; errs
  six ${m}_navy_on; errs
  echo "== $m navy posters OFF"; restart "$(pset False)"; errs
  six ${m}_navy_off; errs
  restart "$(pset True)"
  for t in green burgundy black graphite purple; do
    echo "== $m $t ON"; ap --theme $t $(model $m); restart ""; errs
    three ${m}_${t}_on; errs
  done
done
ap --theme navy $(model classic)
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "$R2"; st; errs
echo "movielist folder after: '$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')'"
echo T68_DONE
