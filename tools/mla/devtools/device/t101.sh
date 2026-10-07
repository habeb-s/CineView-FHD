#!/bin/bash
# t101 (user 2026-10-07): real preview pictures for CineView Designs.
#   A. Posters On / Off for the five models, every section (InfoBar, SecondInfoBar, channel list, Graphical EPG,
#      native MovieSelection on the USB test folder, EventView), theme navy, HBO HD -> previews_src/posters/<model>/
#   B. The six themes: channel list (Classic) -> previews_src/themes/<theme>.png
# Posters / movie folder are set only while Enigma2 is stopped (setcfg.py) and put back; the original selection and
# posters ON are restored at the end.  USB test media only, HDD not opened.  usage: t101.sh
exec 9>~/cineview-mla/t101.lock; flock -n 9 || { echo "t101 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
cat ~/cineview-mla/repo/tools/mla/devtools/device/setcfg.py | $R "mkdir -p /tmp/cvmla && cat > /tmp/cvmla/setcfg.py"
O=~/cineview-mla/previews_src; rm -rf $O; mkdir -p $O/posters $O/themes
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $1 "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $1 && break; done; echo "cap $(basename $(dirname $1))/$(basename $1) $(ok $1 && echo ok || echo BAD)"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
model() {
  case $1 in
    details) echo "--set infobar=details --set secondinfobar=details --set channelselection=posterlist --set epg=graphicalplus --set pvr=cover --set eventview=detailscard";;
    cinema)  echo "--set infobar=cinema --set secondinfobar=cinema --set channelselection=videofirst --set epg=graphicalplus --set pvr=cinema --set eventview=feature";;
    modern)  echo "--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern";;
    minimal) echo "--set infobar=minimal --set secondinfobar=minimal --set channelselection=minimal --set epg=minimal --set pvr=minimal --set eventview=minimal";;
    classic) echo "--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines";;
  esac
}
ORIG=$($R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
echo "original: $ORIG"
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
P0=$($R "grep '^config.plugins.cineviewmla.poster_' /etc/enigma2/settings"); echo "poster settings before: ${P0:-(all default = on)}"
POSTERS="infobar secondinfobar channelselection epg pvr eventview"
pset() { local c=""; for s in $POSTERS; do c="$c python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_$s=$1;"; done; echo "$c"; }
shots() {  # $1 dir
  zap $HBO; X
  $RC 352; sleep 3; ga $1/infobar.png
  $RC 352; sleep 4; ga $1/secondinfobar.png; X; sleep 1.5
  $RC 108; sleep 4; ga $1/channelselection.png; X; sleep 1.5
  op graph 8; ga $1/epg.png; X; sleep 2; X; sleep 1
  op nativemovies 9; $RC 108; sleep 4; ga $1/pvr.png; X; sleep 3; X
  $RC 358; sleep 5; ga $1/eventview.png; X; sleep 2
}
echo "== A posters on/off"
for m in classic details cinema modern minimal; do
  $R "$E apply --theme navy $(model $m) 2>&1 | tail -1"
  for st in on off; do
    v=True; [ $st = off ] && v=False
    restart "$(pset $v) $R2"; mkdir -p $O/posters/$m/$st; shots $O/posters/$m/$st; errs
  done
done
echo "== B themes"
for t in navy black graphite purple burgundy green; do
  $R "$E apply --theme $t $(model classic) 2>&1 | tail -1"; restart "$(pset True) $R2"
  zap $HBO; X; $RC 108; sleep 4; ga $O/themes/$t.png; X; sleep 1; errs
done
echo "== restore: $ORIG + posters on + movie folder"
if [ -z "$P0" ]; then R3="sed -i '/^config.plugins.cineviewmla.poster_/d' /etc/enigma2/settings;"; else R3="$(pset True)"; fi
$R "$E apply $ORIG 2>&1 | tail -1"; restart "$R3 $R2"
$R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('now', d['theme'], d['layouts'])\"; grep '^config.plugins.cineviewmla.poster_\|^config.movielist.last_videodir' /etc/enigma2/settings"; errs
echo T101_DONE
