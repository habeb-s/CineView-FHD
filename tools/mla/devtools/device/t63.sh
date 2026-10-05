#!/bin/bash
# Minimal prototype (build56) on the receiver: the six sections, posters ON and OFF, for the user's look approval.
#  * six themes: InfoBar, SecondInfoBar, Channel Selection (text contrast over live video);
#  * navy + green: also Graphical EPG (cursor), EventView (live / from the EPG / InfoBar EPG), PVR = EMC (the PVR
#    key here) on the USB test folder, native MovieSelection on the USB test folder;
#  * navy posters OFF: everything again.
# Read-only on the HDD (not opened); PVR only up / down / EXIT.  Restore: Classic, navy, posters ON, movielist folder.
exec 9>~/cineview-mla/t63.lock; flock -n 9 || { echo "t63 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build58}
S=~/cineview-mla/shots/t63; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error" $f | grep -v "progressPercentWidth\|piconMargin\|Summary" | tail -4 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
ap() {  # apply through the engine; a refused selection is reported loudly (t61: EMC Cool*Color flags refused)
  local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | sed "s/^/   apply: /"
  echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"
}
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
bars() {  # $1 tag
  zap $HRT1; X; sleep 2; $RC 352; sleep 2.5; ga ib_$1; X; sleep 2
  $RC 352; sleep 1.5; $RC 352; sleep 4; ga sib_$1; X; sleep 2
  zap $HBO; X; $RC 108; sleep 5; ga cs_$1; $RC 108; sleep 3; $RC 108; sleep 3; ga cs_$1_down2; X; sleep 2
}
rest() {  # $1 tag
  zap $HBO; X; op graph 9; ga epg_$1; $RC 106; sleep 3; ga epg_$1_right; X; sleep 2; X; sleep 2
  zap $HBO; X; $RC 358; sleep 5; ga ev_$1_live; X; sleep 2
  op vertical 9; $RC 106; sleep 3; $RC 108; sleep 3; $RC 358; sleep 5; ga ev_$1_simple; X; sleep 2; X; sleep 2; X; sleep 2
  op infobarepg 7; $RC 358; sleep 5; ga ev_$1_infobar; X; sleep 2; X; sleep 2; X; sleep 2
  op movies 9; ga emc_$1; $RC 108; sleep 4; $RC 108; sleep 4; ga emc_$1_down2; X; sleep 3
  op nativemovies 9; ga ms_$1; $RC 108; sleep 4; ga ms_$1_down1; X; sleep 3
}
ALL="--set infobar=minimal --set secondinfobar=minimal --set channelselection=minimal --set epg=minimal --set pvr=minimal --set eventview=minimal"
OFF="infobar secondinfobar channelselection epg pvr eventview"
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh >/dev/null
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
for t in navy green black burgundy graphite purple; do
  ap --theme $t $ALL; restart ""; errs
  echo "== $t posters ON"; bars ${t}_on
  case $t in navy|green) rest ${t}_on;; esac
  errs
done
ap --theme navy $ALL
restart "for s in $OFF; do python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_\$s=False; done;"; errs
echo "== navy posters OFF"; bars navy_off; rest navy_off; errs
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
restart "for s in $OFF; do python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_\$s=True; done; $R2"
ap --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines
$R "rm -rf $P"; restart ""; st; errs
echo "movielist folder after: '$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')'"
echo T63_DONE
