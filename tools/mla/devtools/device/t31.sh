#!/bin/bash
# build30 (z-order fix) device test, Slot 8: Phase B screens through native entry points (dev trigger plugin,
# removed at the end), posters OFF and ON, plus regression grabs of InfoBar / SecondInfoBar / EventView / ChannelSelection.
exec 9>~/cineview-mla/t31.lock; flock -n 9 || { echo "t31 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
BLD=${1:-build30}
S=~/cineview-mla/shots/t31; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
U=/media/usb/cineview-mla/tmp
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
CINEMAX="1:0:19:786:C6D4:16E:A00000:0:0:0:"
ALL="poster_infobar poster_secondinfobar poster_channelselection poster_epg poster_eventview"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; echo "   retry grab $1"; done; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accelAlloc=$(grep -a -c "accelAlloc failed" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Skin\] Error\|Traceback\|ScreenOpen\]\|Processing screen .*CVPosterOff" $f | grep -v "progressPercentWidth\|piconMargin" | tail -8'; }
cfg() { for k in $ALL; do printf 'config.plugins.cineviewmla.%s=%s ' $k $1; done; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
recstart() { $R "nohup sh /tmp/cvmla/grabloop.sh $1 /tmp/cvmla/rec >/dev/null 2>&1 &"; sleep 1; }
recget() { sleep 2; $R 'while pgrep -f grabloop.sh >/dev/null; do sleep 1; done; cd /tmp/cvmla && tar -cf - rec' | tar -C $S -xf - && mv $S/rec $S/rec_$1; $R 'rm -rf /tmp/cvmla/rec'; echo "   $1 recorded $(ls $S/rec_$1 | wc -l) frames"; }
screens() {  # $1 tag
  zap $HBO; X
  op multi 7; ga $1_epg_multi; X
  op quick 7; ga $1_quickepg; X
  op infobarepg 7; ga $1_infobarepg; $RC 358; sleep 5; ga $1_infobareventview; X
  op evsimple 6; ga $1_eventviewsimple; X
}
sib_ecm() {  # $1 tag
  restart "python3 /tmp/cvmla/setcfg.py config.usage.show_second_infobar=3;"; errs
  zap $HBO; X; $RC 352; sleep 1.5; $RC 352; sleep 2.5; ga $1_sib_ecm; X
  restart "python3 /tmp/cvmla/setcfg.py config.usage.show_second_infobar=2;"; errs
}

echo "== 0. deploy $BLD + dev trigger plugin"
~/cineview-mla/deploy_b.sh $BLD
cat ~/cineview-mla/setcfg.py | $R 'cat > /tmp/cvmla/setcfg.py'
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py && ls $P"
$R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set eventview=classic-lines --set pvr=classic 2>&1 | tail -1"
for pw in False True; do
  tag=$([ $pw = True ] && echo on || echo off)
  echo "== posters $tag"
  restart "python3 /tmp/cvmla/setcfg.py $(cfg $pw);"; errs
  screens $tag; errs
  zap $HBO; X; $RC 352; sleep 2; ga ${tag}_infobar; $RC 352; sleep 2.5; ga ${tag}_sib; X
  $RC 358; sleep 5; ga ${tag}_eventview; X
  $RC 108; sleep 5; ga ${tag}_chsel; X
  sib_ecm $tag
done
echo "== restore: remove trigger plugin"
$R "rm -rf $P; ls /usr/lib/enigma2/python/Plugins/Extensions | grep -c ScreenOpen"
restart ""; st; errs
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings"
echo T31_DONE
