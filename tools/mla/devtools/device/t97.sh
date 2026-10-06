#!/bin/bash
# t97 (user 2026-10-06 22:00): every busy / processing state of Plugin / package management, opened for real.
#   A. Plugin Browser -> green  Install Plugins  (opkg update + list: "Downloading plugin information")
#   B. Plugin Browser -> red    Remove Plugins   (opkg list-installed: "Getting plugin information")
#   C. Plugin Browser -> yellow Update Plugins   (opkg update + list-upgradable)
#   D. Plugin Action Log (devtool 'pkglog': fixed sample text, no opkg command)
#   E. global Processing dialog with the native feed-update text (one line) and feed-reset text (several lines),
#      shown over the Plugin Browser by the devtool (display only: no opkg command, no feed touched)
# Nothing is installed or removed.  Receiver PNG grabs + jpg frames + live dialog stacks.
# usage: t97.sh <tag>   -> shots/t97_<tag>
. ~/cineview-mla/p6lib.sh
TAG=${1:?tag}
S=~/cineview-mla/shots/t97_$TAG; rm -rf $S; mkdir -p $S/frames
ga() { curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1 @$(date +%T)"; }
fr() { local end=$(( $(date +%s) + $2 )) i=0; while [ $(date +%s) -lt $end ]; do curl -s -m 10 -o $S/frames/$(printf "%s_%03d" $1 $i).jpg "http://192.168.1.250/grab?format=jpg&r=1280&mode=all"; i=$((i+1)); done; echo "   frames $1: $i"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
stk() { $R 'rm -f /tmp/cvmla/stack.txt; echo stack > /tmp/cvmla/open.txt'; sleep 2; $R 'cat /tmp/cvmla/stack.txt 2>/dev/null' > $S/stack_$1.txt; echo "-- stack $1:"; grep -a "== \|description\|key_\|Title" $S/stack_$1.txt | cut -c1-140; }
busy() {  # $1 name, $2 key, $3 seconds of frames while busy, $4 wait after
	case $2 in op:*) $R "echo ${2#op:} > /tmp/cvmla/open.txt" ;; *) $RC $2 ;; esac
	( sleep 1.3; stk ${1}_busy ) &
	sleep 0.6; ga ${1}_busy_a
	fr ${1}_busy $3
	wait
	sleep $4; ga ${1}_done; stk ${1}_done
	fr ${1}_done 2
	$RC 174; sleep 3
}
LOGLINE0=$($R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); wc -l < $f')
X; sleep 1
op pluginbrowser 6; ga 0_pluginbrowser; stk 0_pluginbrowser
busy A_install 399 6 10
busy B_remove op:pkgremove 3 4   # devtool = native PackageAction(MODE_REMOVE); the red key's
# OpenWebif key event can reach the new screen, whose red key is Close (t97 after-run 22:23:29: opened and closed at once)
busy C_update 400 6 30   # 23 updates on this receiver: the list takes longer
ga 3_back_pluginbrowser
X; sleep 1
op pkglog 4; ga D_log; stk D_log; fr D_log 2; X; sleep 1
op pluginbrowser 6
op processing 1.5; ga E1_processing; fr E1_processing 2; sleep 4
op processing2 1.5; ga E2_processing_multiline; fr E2_processing_multiline 2; sleep 4
ga E3_after_hide
X; sleep 2; X
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); tail -n +'$LOGLINE0' $f | grep -a -n "CineViewMLA\] package\|PackageAction\|Processing\|Skin\] Error\|Traceback" | tail -30 | cut -c1-200' > $S/log_excerpt.txt
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash) package_waiting_hook=$(grep -a -c "package waiting installed" $f)"; grep -a "Skin\] Error\|Traceback" $f | grep -v "progressPercentWidth\|piconMargin" | tail -4 | cut -c1-170'
echo T97_DONE
