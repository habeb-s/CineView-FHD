#!/bin/bash
# C-1/C-2 (approved 2026-10-04 11:58) device test on Slot 8: backup -> opkg upgrade to the build -> Classic navy ->
# Arabic titles (TextTest2, temporary) on InfoBar / SecondInfoBar / EventView, live LTR titles, channel-list
# description from the top; tracebacks; TextTest2 removed at the end.
. ~/cineview-mla/p6lib.sh
IPK=${1:?ipk}; TAG=${2:?tag}
S=~/cineview-mla/shots/$TAG; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ga() { mkdir -p $(dirname $S/$1); curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1 @$($R 'date +%T.%N' | cut -c1-12)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") engine=$(grep -a -o "engine=identity" $f | head -1)"'; }
B=/media/usb/cineview-mla/state/backup-$TAG
echo "== backup $B"
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings && tar -C /etc/enigma2 -czf $B/cineview_mla-state.tgz cineview_mla && tar -C / -czf $B/mla-files.tgz usr/share/enigma2/CineView_FHD_MLA usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA usr/lib/enigma2/python/Components && opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version > $B/version && ls -l $B | tail -5"
echo "== upgrade"
cat $IPK | $R 'cat > /tmp/cvmla/up.ipk'
tar -C ~/cineview-mla/repo/tools/mla/devtools -czf - CineViewMLATextTest2 | $R 'cat > /tmp/cvmla/tt2.tgz'
restart 'opkg install /tmp/cvmla/up.ipk 2>&1 | tail -3; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E "Version|Status"; '"$E"' rollback --to factory 2>&1 | tail -1; tar -C /usr/lib/enigma2/python/Plugins/Extensions -xzf /tmp/cvmla/tt2.tgz && echo devtool-installed; grep -q CineViewMLATextTest2 /media/usb/cineview-mla/state/aux-installed 2>/dev/null || echo "/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLATextTest2 (devtool, Slot 8)" >> /media/usb/cineview-mla/state/aux-installed;'
st; errs
$R "grep -c 'dir=rtl' /usr/share/enigma2/CineView_FHD_MLA/active/infobar.xml /usr/share/enigma2/CineView_FHD_MLA/active/secondinfobar.xml /usr/share/enigma2/CineView_FHD_MLA/active/eventview.xml; grep -c 'movetype=swimming,direction=top,step=2,steptime=65' /usr/share/enigma2/CineView_FHD_MLA/active/channelselection.xml"
arab() {  # $1 file $2 screen $3 tag
  python3 - "$1" "$2" > /tmp/tt2.json <<'PY'
import json,sys
n=json.load(open('/home/aiadmin/cineview-mla/arabic/narrow.json'))
d={"file":sys.argv[1],"screen":sys.argv[2],"seconds":24,"title_now":n["title_now"],"desc_now":n["desc_now"],"short_now":n["desc_now"][:180],
   "title_next":n.get("title_next",n["title_now"]),"desc_next":n.get("desc_next",n["desc_now"]),"short_next":n.get("desc_next",n["desc_now"])[:160]}
print(json.dumps(d,ensure_ascii=False))
PY
  X; cat /tmp/tt2.json | $R 'cat > /tmp/cvmla/texttest2.json.tmp && mv /tmp/cvmla/texttest2.json.tmp /tmp/cvmla/texttest2.json'; sleep 4; ga ${3}_t2; sleep 4; ga ${3}_t6; sleep 5; ga ${3}_t11; X
}
echo "== Arabic (Classic navy)"
arab infobar.xml InfoBar arabic/ib
arab secondinfobar.xml SecondInfoBar arabic/sib
arab eventview.xml EventView arabic/eventview
echo "== live LTR titles"
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$HBO"; sleep 9
X; $RC 352; sleep 1; ga live/ib_t1; sleep 4; ga live/ib_t5
X; $RC 352; sleep 1; $RC 352; sleep 3; ga live/sib_t3; X
$RC 358; sleep 3; ga live/eventview_t3; X
echo "== channel list description"
for i in 1 2; do X; $RC 108; sleep 0.8; ga chlist/r${i}_t1; sleep 1.2; ga chlist/r${i}_t2; sleep 2; ga chlist/r${i}_t4; sleep 5; ga chlist/r${i}_t9; $RC 108; sleep 1.5; ga chlist/r${i}_next_t1; X; done
errs
echo "== remove devtool"
restart 'rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLATextTest2 /tmp/cvmla/texttest2.json; sed -i "/CineViewMLATextTest/d" /media/usb/cineview-mla/state/aux-installed; echo "aux: $(cat /media/usb/cineview-mla/state/aux-installed | wc -l) lines";'
st; errs
echo C12_DONE
