#!/bin/bash
# t99 - MessageBox look (four sample boxes, display only), a native Setup page (shared look), CineView Designs
# (EventView line-by-line preview, profiles ChoiceBox title).  Nothing is changed.  usage: t99.sh <tag>
. ~/cineview-mla/p6lib.sh
TAG=${1:?tag}
S=~/cineview-mla/shots/t99_$TAG; rm -rf $S; mkdir -p $S
ga() { curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
LOG0=$($R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); wc -l < $f')
X; sleep 1
for m in msg_info msg_yesno msg_long msg_list; do op $m 2.5; ga M_$m; $RC 174; sleep 1.5; done
op setup 4; ga S_setup_userinterface; $RC 174; sleep 1.5; X
op designs 5
for k in 1 2 3 4 5 6; do $RC 108; sleep 0.4; done; sleep 1; ga D_eventview_row
$RC 400; sleep 2.5; ga D_eventview_preview; $RC 174; sleep 1.5
$RC 139; sleep 2; ga D_profiles_title; $RC 174; sleep 1.5; $RC 398; sleep 1.5; X
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); tail -n +'$LOG0' $f | grep -a "Skin\] Error\|Traceback\|applet" | tail -8 | cut -c1-200; echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"'
echo T99_DONE
