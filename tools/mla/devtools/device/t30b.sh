#!/bin/bash
# build29 device test (Slot 8) — replaces t28/t29, whose results are void: two t28 instances ran at the same
# time (two queue chains), so key presses, grabs and recordings of both runs were interleaved.
#  1. Phase B remaining screens through their NATIVE entry points (dev-only trigger plugin CineViewMLAScreenOpen,
#     removed at the end): EPGSelectionMulti, QuickEPG, InfoBarEventView (InfoBar EPG + INFO),
#     EventViewSimple (EventViewSimple(event, ServiceReference) like MovieSelection), SecondInfoBarECM
#     (show_second_infobar=3 temporarily, restored to 2) — posters OFF and ON.
#  2. EventView "classic-lines" on real events: displayed-framebuffer recordings + jumpcheck.
#  3. Channel Selection Poster List / Video First / Video First (list right): navigation recordings (video+OSD),
#     posters ON and OFF, plus stills.
#  4. EventView real use: line by line vs classic continuous.
exec 9>~/cineview-mla/t30b.lock; flock -n 9 || { echo "t30 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t30; mkdir -p $S; rm -rf $S/rec_* $S/cs_*
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
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
recstart() { $R "nohup sh /tmp/cvmla/grabloop.sh $1 /tmp/cvmla/rec >/dev/null 2>&1 &"; sleep 1; }
recget() { sleep 2; $R 'for i in $(seq 1 90); do [ -f /tmp/cvmla/rec.done ] && break; sleep 1; done; cd /tmp/cvmla && tar -cf - rec' | tar -C $S -xf - && mv $S/rec $S/rec_$1; $R 'rm -rf /tmp/cvmla/rec /tmp/cvmla/rec.done'; echo "   $1 recorded $(ls $S/rec_$1 | wc -l) frames"; }
screens() {  # $1 tag
  zap $HBO; X
  op multi 7; ga $1_epg_multi; X
  op quick 7; ga $1_quickepg; X
  op infobarepg 7; $RC 358; sleep 5; ga $1_infobareventview; X
  op evsimple 6; ga $1_eventviewsimple; X
}
sib_ecm() {  # $1 tag
  restart "python3 /tmp/cvmla/setcfg.py config.usage.show_second_infobar=3;"; errs
  zap $HBO; X; $RC 352; sleep 1.5; $RC 352; sleep 2.5; ga $1_sib_ecm; X
  restart "python3 /tmp/cvmla/setcfg.py config.usage.show_second_infobar=2;"; errs
}

echo "== 0. state + dev trigger plugin (Slot 8, removed at the end)"
$R "pkill -f fbrec2; pkill -f grabloop; rm -f $U/rec.bin $U/rec.bin.frames; grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings"
cat ~/cineview-mla/setcfg.py | $R 'cat > /tmp/cvmla/setcfg.py'
cat ~/cineview-mla/fbrec2.py | $R 'cat > /tmp/cvmla/fbrec2.py'
$R 'cat > /tmp/cvmla/grabloop.sh' <<'SH'
#!/bin/sh
end=$(( $(date +%s) + $1 )); rm -rf $2; mkdir -p $2
rm -f $2.done
while [ $(date +%s) -lt $end ]; do grab -q -j 75 -r 1280 $2/$(date +%s%N).jpg; done
touch $2.done
SH
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py && ls $P"
$R "rm -rf /tmp/cvmla/rec /tmp/cvmla/rec.done"; $R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set eventview=classic-lines --set pvr=classic 2>&1 | tail -1"

echo "== 3. Channel Selection designs: navigation recordings, posters ON then OFF"
for pw in True False; do
  [ $pw = False ] && restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=False;" && errs
  for d in posterlist videofirst videofirst-right; do
    $R "$E apply --set channelselection=$d 2>&1 | tail -1"; restart ""; errs
    tag=${d}_$([ $pw = True ] && echo on || echo off)
    zap $HBO; X
    recstart 38
    $RC 108; sleep 5
    for i in 1 2 3 4 5; do $RC 108; sleep 2.5; done
    for i in 1 2 3 4; do $RC 103; sleep 0.8; done
    sleep 4; X
    recget $tag
    zap $HBO; X; $RC 108; sleep 5; ga cs_${tag}_open; $RC 108; sleep 3; ga cs_${tag}_down1; X
  done
done
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=True;"; errs

echo "== 4. EventView real use: line by line vs classic"
$R "$E apply --set channelselection=classic 2>&1 | tail -1"; restart ""; errs
zap $CINEMAX; X; recstart 32; $RC 358; sleep 28; X; recget eventview_lines
$R "$E apply --set eventview=classic 2>&1 | tail -1"; restart ""; errs
zap $CINEMAX; X; recstart 32; $RC 358; sleep 28; X; recget eventview_classic

echo "== 5. restore dev state, remove trigger plugin"
$R "$E apply --set channelselection=classic --set eventview=classic-lines 2>&1 | tail -1; rm -rf $P; ls /usr/lib/enigma2/python/Plugins/Extensions | grep -c ScreenOpen"
restart ""; st; errs
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings"
echo T30_DONE
