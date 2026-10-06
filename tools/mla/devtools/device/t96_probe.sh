#!/bin/bash
# t96 probe (user 2026-10-06 22:00): the real screens of Plugin Browser -> "Install Plugins" (green) while the plugin
# information is downloaded, and after.  Receiver frames (jpg, as fast as the receiver delivers) + PNG grabs + the LIVE
# dialog stack (devtool 'stack': class / skinName / widgets / sources).  Nothing is installed or removed.
# usage: t96_probe.sh <tag>   (shots/t96_<tag>)
. ~/cineview-mla/p6lib.sh
TAG=${1:?tag}
S=~/cineview-mla/shots/t96_$TAG; rm -rf $S; mkdir -p $S/frames
ga() { curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1"; }
fr() { local end=$(( $(date +%s) + $2 )) i=0; while [ $(date +%s) -lt $end ]; do curl -s -m 10 -o $S/frames/$(printf "%s_%03d" $1 $i).jpg "http://192.168.1.250/grab?format=jpg&r=1280&mode=all"; i=$((i+1)); done; echo "   frames $1: $i"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
stk() { $R 'rm -f /tmp/cvmla/stack.txt; echo stack > /tmp/cvmla/open.txt'; sleep 2; $R 'cat /tmp/cvmla/stack.txt 2>/dev/null' > $S/stack_$1.txt; echo "-- stack $1:"; cat $S/stack_$1.txt; }
logs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Skin\] Error\|Traceback" $f | grep -v "progressPercentWidth\|piconMargin" | tail -4 | cut -c1-170'; }
X; sleep 1
op pluginbrowser 6; ga 0_pluginbrowser; stk 0_pluginbrowser
$RC 399    # green = Install Plugins
( sleep 1.2; stk 1_downloading ) &
fr 1_downloading 7
ga 1_downloading_end
wait
sleep 8; ga 2_after; stk 2_after
fr 2_after 3
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); grep -a -n "PluginBrowser\|PluginDownload\|PackageAction\|Processing\|Downloading plugin\|opkg" $f | tail -25 | cut -c1-200' > $S/log_excerpt.txt
X; sleep 2; X; sleep 2; X
logs
echo T96_DONE
