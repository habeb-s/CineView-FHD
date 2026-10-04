#!/bin/bash
# EventView "line jumps" trial (approved 2026-10-04 16:04, Slot 8 only, not final).
# Installs the test pack layouts/eventview/classic-lines (= installed Classic pack, only the 8 description
# widgets: step=29,steptime=1740 instead of step=1,steptime=60) and records the DISPLAYED framebuffer of the
# description boxes (fbrec.py, 10 fps, 14 s) with long English/Arabic texts (TextTest2, temporary) and a live
# event, for Classic and for the test pack.  Ends with the test pack ACTIVE (switch back in CineView Designs).
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/evlines; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
L=/usr/share/enigma2/CineView_FHD_MLA/layouts/eventview
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2)"'; }
B=/media/usb/cineview-mla/state/backup-evlines
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings && tar -C /etc/enigma2 -czf $B/cineview_mla-state.tgz cineview_mla && ls $B"
cat ~/cineview-mla/fbrec.py | $R 'cat > /tmp/cvmla/fbrec.py'
tar -C ~/cineview-mla/repo/tools/mla/devtools -czf - CineViewMLATextTest2 | $R 'cat > /tmp/cvmla/tt2.tgz'
echo "== test pack classic-lines"
$R "rm -rf $L/classic-lines && cp -a $L/classic $L/classic-lines && sed -i 's/\"id\": \"classic\"/\"id\": \"classic-lines\"/; s/\"name\": \"CineView Classic\"/\"name\": \"Classic - line jumps (TEST)\"/' $L/classic-lines/manifest.json && sed -i 's/step=1,steptime=60,startdelay=4000/step=29,steptime=1740,startdelay=4000/g' $L/classic-lines/screens.openatv.xml && grep -c 'step=29,steptime=1740' $L/classic-lines/screens.openatv.xml && grep -o '\"name\": \"[^\"]*\"' $L/classic-lines/manifest.json"
$R "grep -q classic-lines /media/usb/cineview-mla/state/aux-installed 2>/dev/null || echo '$L/classic-lines (EventView line-jump TEST pack, Slot 8)' >> /media/usb/cineview-mla/state/aux-installed"
rec() {  # $1 tag $2 x $3 w
  $R "python3 /tmp/cvmla/fbrec.py $2 245 $3 261 10 14 /tmp/cvmla/rec.bin"
  $R 'cat /tmp/cvmla/rec.bin' > $S/$1.bin; $R 'rm -f /tmp/cvmla/rec.bin'
}
tt() {  # $1 lang -> TextTest2 trigger for the EventView screen
  python3 - "$1" <<'PY' | $R 'cat > /tmp/cvmla/texttest2.json.tmp && mv /tmp/cvmla/texttest2.json.tmp /tmp/cvmla/texttest2.json'
import json,sys
n=json.load(open('/home/aiadmin/cineview-mla/arabic/long.json'))[sys.argv[1]]
d={"file":"eventview.xml","screen":"EventView","seconds":24,"title_now":n["title_now"],"desc_now":n["desc_now"],"short_now":n["desc_now"][:180],
   "title_next":n["title_next"],"desc_next":n["desc_next"],"short_next":n["desc_next"][:160]}
print(json.dumps(d,ensure_ascii=False))
PY
}
round() {  # $1 tag
  for lang in en ar; do
    X; tt $lang; sleep 4.2; rec ${1}_${lang}_now 95 480; X
    X; tt $lang; sleep 4.2; rec ${1}_${lang}_next 950 580; X
  done
  X; curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=1:0:19:786:C6D4:16E:A00000:0:0:0:"; sleep 6
  $RC 358; sleep 4.5; rec ${1}_live_next 950 580; X
  errs
}
echo "== Classic (factory) + TextTest2"
$R "$E rollback --to factory 2>&1 | tail -1"
restart 'tar -C /usr/lib/enigma2/python/Plugins/Extensions -xzf /tmp/cvmla/tt2.tgz && echo devtool-installed; grep -q CineViewMLATextTest2 /media/usb/cineview-mla/state/aux-installed || echo "/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLATextTest2 (devtool, Slot 8)" >> /media/usb/cineview-mla/state/aux-installed;'
st; errs; round classic
echo "== line jumps (classic-lines)"
$R "$E apply --set eventview=classic-lines 2>&1 | tail -1"; restart ""; st; errs; round lines
echo "== remove TextTest2, keep the test pack active"
restart 'rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLATextTest2 /tmp/cvmla/texttest2.json; sed -i "/CineViewMLATextTest/d" /media/usb/cineview-mla/state/aux-installed; cat /media/usb/cineview-mla/state/aux-installed;'
st; errs
X; $RC 358; sleep 3; curl -s -m 20 -o $S/final_eventview.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; X
for f in $S/*.bin; do python3 ~/cineview-mla/fbana.py $f ${f%.bin}.gif $(basename ${f%.bin}); done
echo EVLINES_DONE
