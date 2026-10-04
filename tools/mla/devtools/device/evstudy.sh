#!/bin/bash
# EventView blank band - prevention study (Slot 8, device only, nothing shipped).
# Variants are TEMPORARY layout packs layouts/eventview/evexpN created on the receiver from the installed Classic
# pack (only the RunningText options of the event descriptions differ), applied with the composer, measured, and
# removed again (factory restored at the end).  Per variant and channel: fbprobe on the right and the left
# description (25 s each, displayed framebuffer), enigma2 CPU over 20 s without the probe, tracebacks/crash logs.
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/evstudy; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
L=/usr/share/enigma2/CineView_FHD_MLA/layouts/eventview
cat ~/cineview-mla/fbprobe.py | $R 'cat > /tmp/cvmla/fbprobe.py'
cat ~/cineview-mla/setcfg.py | $R 'cat > /tmp/cvmla/setcfg.py'
gg() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) crashlogs=$(ls /home/root/logs | grep -c crash) e2pid=$(pidof enigma2)"'; }
cpu() { $R 'p=$(pidof enigma2); a=$(awk "{print \$14+\$15}" /proc/$p/stat); t0=$(awk "{print \$1}" /proc/uptime); sleep 20; b=$(awk "{print \$14+\$15}" /proc/$p/stat); t1=$(awk "{print \$1}" /proc/uptime); awk -v a=$a -v b=$b -v t0=$t0 -v t1=$t1 "BEGIN{printf \"   cpu enigma2 = %.1f %% of one core over %.0f s\n\", (b-a)/100/(t1-t0)*100, t1-t0}"'; }
mkpack() {  # $1 id  $2 sed expression applied to the description options of the EventView screens
  $R "rm -rf $L/$1 && cp -a $L/classic $L/$1 && sed -i 's/\"id\": \"classic\"/\"id\": \"$1\"/; s/\"name\": \"CineView Classic\"/\"name\": \"EV study $1\"/' $L/$1/manifest.json && sed -i '$2' $L/$1/screens.openatv.xml && grep -c 'steptime=60' $L/$1/screens.openatv.xml; grep -o 'options=\"movetype=swimming,direction=top,step=[0-9]*,steptime=[0-9]*' $L/$1/screens.openatv.xml | sort | uniq -c"
}
measure() {  # $1 tag
  for ch in "1:0:19:786:C6D4:16E:A00000:0:0:0:|Cinemax" "1:0:19:784:C6D4:16E:A00000:0:0:0:|HBO"; do
    ref=${ch%%|*}; n=${ch##*|}
    X; curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ref"; sleep 5
    $RC 358; sleep 5; gg ${1}_${n}_a
    $R "python3 /tmp/cvmla/fbprobe.py 950 1530 250 500 25 ${1}_${n}_right"
    $R "python3 /tmp/cvmla/fbprobe.py 95 575 250 500 25 ${1}_${n}_left"
    gg ${1}_${n}_b
    cpu; gg ${1}_${n}_c; X
  done
  errs
}
st; errs
echo "== V0 baseline: Classic (rc4 factory), posters on"
measure V0
echo "== V1 Classic, EventView posters OFF (repaint-source hypothesis)"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False;"; measure V1
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True;"
echo "== V2 steptime 60 -> 120 (half the repaints, half the speed)"
mkpack evexp2 's/step=1,steptime=60,startdelay=4000/step=1,steptime=120,startdelay=4000/g'
$R "$E apply --set eventview=evexp2 2>&1 | tail -1"; restart ""; st; measure V2
echo "== V3 line jumps: one whole line (29 px) every 1740 ms = same reading speed (16.7 px/s), one repaint per line"
mkpack evexp3 's/step=1,steptime=60,startdelay=4000/step=29,steptime=1740,startdelay=4000/g'
$R "$E apply --set eventview=evexp3 2>&1 | tail -1"; restart ""; st; measure V3
echo "== cleanup: factory, study packs removed"
$R "$E rollback --to factory 2>&1 | tail -1; rm -rf $L/evexp2 $L/evexp3; ls $L"; restart ""; st; errs
echo EVSTUDY_DONE
