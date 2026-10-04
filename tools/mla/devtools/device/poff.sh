#!/bin/bash
# Phase B device test (Slot 8): Classic posters ON vs OFF with the experimental reflow (build26).
# deploy (backup first) -> Classic navy -> shots ON -> all poster switches OFF -> shots OFF -> ON again
# -> restore the rc4 package files (opkg --force-reinstall) and the selection with the EventView line test pack.
. ~/cineview-mla/p6lib.sh
BLD=${1:-build26}; S=~/cineview-mla/shots/poff; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
cat ~/cineview-mla/setcfg.py | $R 'cat > /tmp/cvmla/setcfg.py'
ga() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1 @$($R 'date +%T')"; }
gv() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=video&r=1920"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2)"; grep -a "Skin\] Error" $f | grep -v "progressPercentWidth\|piconMargin" | tail -5'; }
ALL="poster_infobar poster_secondinfobar poster_channelselection poster_epg poster_eventview"
cfg() { for k in $ALL; do printf 'config.plugins.cineviewmla.%s=%s ' $k $1; done; }
shots() {  # $1 tag
  curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=1:0:19:784:C6D4:16E:A00000:0:0:0:"; sleep 10
  X; $RC 352; sleep 4; ga $1_infobar
  X; $RC 352; sleep 1; $RC 352; sleep 5; ga $1_secondinfobar
  X; $RC 358; sleep 5; ga $1_eventview
  X; $RC 108; sleep 5; ga $1_channels
  $RC 365; sleep 6; ga $1_channels_epg
  X; $RC 365; sleep 7; ga $1_epg
  X
}
echo "== deploy $BLD (backup first)"
~/cineview-mla/deploy_b.sh $BLD
$R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set eventview=classic --set pvr=classic 2>&1 | tail -1"
restart ""; st; errs
X; gv video_hbo
shots on
echo "== posters OFF"
restart "python3 /tmp/cvmla/setcfg.py $(cfg False);"; errs
shots off
echo "== posters ON again"
restart "python3 /tmp/cvmla/setcfg.py $(cfg True);"; errs
X; $RC 352; sleep 4; ga on2_infobar; X
echo POFF_SHOTS_DONE
