#!/bin/bash
# t106v - OpenViX (Slot 4) runtime runner for the multi-image phase.
#   usage: t106.sh <tag> [steps...]          env: INSTALL=<ipk>  ZAP=<service ref>  DEVTOOL=1 (deploy test tool)
#   steps (default: all sections): infobar sib chansel grid single multi ibgrid eventview evinfo evsimple pvr
#                                  plugins designs setup_ui setup_usage msg_info msg_yesno msg_long
#                                  (extra) pkgremove pkgdownload console mark chansel_down
# Per step: close everything, open through the NATIVE entry point, grab, new log lines only (tracebacks, skin errors,
# missing elements, unimplemented attributes, screens processed).  Poster cache stays pinned to /tmp (HDD never used).
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r4.sh
TAG=${1:?tag}; shift
S=~/cineview-mla/shots/t106v_$TAG; rm -rf $S; mkdir -p $S
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
rows() { $R 'rm -f /tmp/cvmla/rows.txt; echo rows > /tmp/cvmla/open.txt'; sleep 1.6; $R 'cat /tmp/cvmla/rows.txt 2>/dev/null' > $S/rows_$1.txt; }
LOGF=""; N=0
mark() { LOGF=$($R 'ls -t /home/root/logs/Enigma2_debug_*.log | head -1'); N=$($R "wc -l < $LOGF"); }
delta() {
	$R "tail -n +$((N + 1)) $LOGF" > $S/log_$1.txt
	local tb=$(grep -a -c "Traceback" $S/log_$1.txt) se=$(grep -a -c "\[Skin\] Error\|SkinError" $S/log_$1.txt) mi=$(grep -a -c "Skin is missing element" $S/log_$1.txt) na=$(grep -a -c "is not implemented" $S/log_$1.txt)
	local scr=$(grep -a -o "\[Skin\] Processing screen '[^']*'" $S/log_$1.txt | sed "s/.*'\(.*\)'/\1/" | grep -v Summary | sort -u | tr '\n' ' ')
	local err=$(grep -a "CineViewMLAScreenOpen\] error" $S/log_$1.txt | sed 's/.*error: //' | head -1 | cut -c1-80)
	printf "%-14s tb=%s skinerr=%s missing=%s notimpl=%s screens: %s%s\n" "$1" $tb $se $mi $na "$scr" "${err:+ TOOL-ERROR: $err}" | tee -a $S/summary.txt
}
restart_gui() { local o=$($R pidof enigma2); $R 'init 4; for i in $(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'
	for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30; }
run() {
	local name=$1
	X; sleep 1; mark
	case $name in
		infobar) $RC 352; sleep 1.5 ;;
		sib) $RC 352; sleep 1.5; $RC 352; sleep 2 ;;
		chansel) $RC 103; sleep 2.5 ;;
		grid) op graph ;;
		single) op single ;;
		multi) op multi ;;
		ibgrid) op infobarepg ;;
		eventview) op eventview ;;
		evinfo) $RC 358; sleep 3 ;;
		evsimple) op evsimple ;;
		pvr) op nativemovies 7 ;;
		plugins) op pluginbrowser ;;
		pkgremove) op pkgremove 12 ;;
		pkgdownload) op pkgdownload 40 ;;
		console) op console 5 ;;
		mark) $RC 103; sleep 2.5; op mark_on 2 ;;
		chansel_down) $RC 103; sleep 2.5; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 0.3; done; sleep 1.5 ;;
		designs) op designs 6; rows designs ;;
		setup_ui) op setup:userinterface ;;
		setup_usage) op setup:usage ;;
		msg_info) op msg_info 3 ;;
		msg_yesno) op msg_yesno 3 ;;
		msg_long) op msg_long 3 ;;
		*) echo "unknown step $name"; return ;;
	esac
	sleep 1.5; ga $name; delta $name
	[ "$name" = mark ] && op mark_off 2  # display flag back off before the channel list closes
}
$R 'grep -q "rootsubdir=duo4kse/linuxrootfs4" /proc/cmdline' || { echo "NOT Slot 4"; exit 1; }
$R 'python3 -c "import json;print(\"pin:\", json.load(open(\"/etc/enigma2/cineview_mla/runtime.json\")).get(\"poster_cache\"))"'
NEED_RESTART=0
if [ -n "$INSTALL" ]; then
	cat $INSTALL | $R "cat > /tmp/cvmla-test.ipk"
	$R "opkg install /tmp/cvmla-test.ipk 2>&1 | grep -v '^Downloading\|^Collected'; rm -f /tmp/cvmla-test.ipk; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep 'Version\|Status'"
	# a failed maintainer script leaves "half-installed" with the NEW version recorded but the OLD files: stop
	$R "opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -q 'Status: install ok installed'" || { echo "INSTALL FAILED - not testing a half-installed package"; exit 2; }
	NEED_RESTART=1
fi
if [ "${DEVTOOL:-1}" = "1" ]; then
	P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
	if ! $R "cmp -s $P/plugin.py - " < ~/cineview-mla/mi/tools/mla/devtools/CineViewMLAScreenOpen/plugin.py 2>/dev/null; then
		cat ~/cineview-mla/mi/tools/mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P /home/root/cvmla-testmedia && cat > $P/plugin.py && touch $P/__init__.py"
		NEED_RESTART=1
	fi
fi
[ "$NEED_RESTART" = "1" ] && { echo "== GUI restart"; restart_gui; mark; N=0; delta 00_startup; }
if [ -n "$ZAP" ]; then curl -s -m 10 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ZAP"; sleep 25; fi
curl -s -m 10 http://192.168.1.250/api/getcurrent | python3 -c "import json,sys;d=json.load(sys.stdin);print('playing:',d['info'].get('name'),'| now:',repr(d.get('now',{}).get('title')),'| next:',repr(d.get('next',{}).get('title')))"
rm -f $S/summary.txt
STEPS=${*:-infobar sib chansel grid single multi ibgrid eventview evinfo evsimple pvr plugins designs setup_ui setup_usage msg_info msg_yesno msg_long}
for s in $STEPS; do run $s; done
X
echo "poster cache /tmp: $($R 'find /tmp/CINEVIEW-MLA -type f 2>/dev/null | wc -l') files; crash logs today: $($R 'ls /home/root/logs | grep -i crash | grep -c 2026-10-08')"
echo T106_DONE
