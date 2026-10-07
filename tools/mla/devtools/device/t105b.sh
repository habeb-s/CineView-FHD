#!/bin/bash
# t105b - OpenBH 5.6 (Slot 5) first compatibility run, step 2: open every section through its NATIVE entry point
# with the golden (unchanged) MLA core and record, per step: screen grab, Designs rows, and only the NEW log lines
# (tracebacks, skin errors, missing-element warnings).  Factory design (Classic, Navy).
# PVR: MovieSelection on /home/root/cvmla-testmedia (slot root filesystem) - never the HDD; the folder setting is
# restored at the end.  Devtool CineViewMLAScreenOpen installed for the run and removed at the end.
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r5.sh
S=~/cineview-mla/shots/t105; mkdir -p $S
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
rows() { $R 'rm -f /tmp/cvmla/rows.txt; echo rows > /tmp/cvmla/open.txt'; sleep 1.6; $R 'cat /tmp/cvmla/rows.txt 2>/dev/null' > $S/rows_$1.txt; }
LOGF=""
mark() { LOGF=$($R 'ls -t /home/root/logs/Enigma2_debug_*.log | head -1'); N=$($R "wc -l < $LOGF"); }
delta() {  # $1 step name
	$R "tail -n +$((N + 1)) $LOGF" > $S/log_$1.txt
	local tb=$(grep -a -c "Traceback" $S/log_$1.txt) se=$(grep -a -c "\[Skin\] Error\|SkinError" $S/log_$1.txt) mi=$(grep -a -c "Skin is missing element" $S/log_$1.txt) na=$(grep -a -c "is not implemented" $S/log_$1.txt)
	local scr=$(grep -a -o "\[Skin\] Processing screen '[^']*'" $S/log_$1.txt | sed "s/.*'\(.*\)'/\1/" | sort -u | tr '\n' ' ')
	printf "%-16s tb=%s skinerr=%s missing=%s notimpl=%s screens: %s\n" "$1" $tb $se $mi $na "$scr" | tee -a $S/summary.txt
}
step() {  # $1 name, $2.. command words: key:<code> | op:<verb> | wait:<s>
	local name=$1; shift
	X; sleep 1; mark
	for a in "$@"; do case $a in key:*) $RC ${a#key:} ;; op:*) op ${a#op:} 5 ;; wait:*) sleep ${a#wait:} ;; esac; done
	sleep 2; ga $name; delta $name
}
$R 'grep -q "rootsubdir=duo4kse/linuxrootfs5" /proc/cmdline' || { echo "NOT Slot 5"; exit 1; }
rm -f $S/summary.txt
echo "== deploy devtool, test folder; restart GUI"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
cat ~/cineview-mla/mi/tools/mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P /home/root/cvmla-testmedia && cat > $P/plugin.py && touch $P/__init__.py"
VD=$($R 'sed -n "s/^config.movielist.last_videodir=//p" /etc/enigma2/settings'); echo "last_videodir before: '${VD:-(default)}'"
o=$($R pidof enigma2); $R 'init 4; for i in $(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'
for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 35
mark; N=0; delta 00_startup

step 01_infobar key:352 wait:1
step 02_secondinfobar key:352 wait:1.5 key:352 wait:2
step 03_chanselect key:103 wait:2
step 04_epg_grid op:graph
step 05_epg_single op:single
step 06_epg_multi op:multi
step 07_epg_infobar op:infobarepg
step 08_eventview op:eventview
step 09_evsimple op:evsimple
step 10_pvr op:nativemovies wait:2
step 11_pluginbrowser op:pluginbrowser
step 12_designs op:designs; rows 12_designs
step 13_setup_ui op:setup:userinterface
step 14_setup_usage op:setup:usage
step 15_msg_info op:msg_info
step 16_msg_yesno op:msg_yesno
step 17_msg_long op:msg_long
X
echo "== poster cache (pinned /tmp): $($R 'find /tmp/CINEVIEW-MLA -type f | wc -l') files"
echo "== restore: devtool removed, PVR folder setting back"
o=$($R pidof enigma2)
$R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; rm -rf $P /tmp/cvmla; sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings; [ -n '$VD' ] && echo 'config.movielist.last_videodir=$VD' >> /etc/enigma2/settings; init 3"
for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
sleep 40
echo "   devtool present: $($R "ls -d $P 2>/dev/null | wc -l"); last_videodir: $($R 'sed -n "s/^config.movielist.last_videodir=//p" /etc/enigma2/settings')"
echo "   crash logs (new today): $($R 'ls /home/root/logs | grep -i crash | grep -c 2026-10-07')"
echo T105B_DONE
