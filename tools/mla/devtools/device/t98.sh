#!/bin/bash
# t98 - CineView Designs checklist, part 1 (non-destructive; user 2026-10-06 23:10).
#   D0 backup of the CineView MLA state + settings (USB state folder) and a state snapshot
#   D1 open CineView Designs (plugin main(), as the Plugin Browser entry) - full grab + rows/keys/texts
#   D2 every row in turn (DOWN): grab + rows dump (preview, description, value per row)
#   D3 YELLOW preview on a layout row and on the theme row; YELLOW on a row without preview (message)
#   D4 MENU profiles menu; "Apply a design model" list; back out without choosing
#   D5 RED cancel -> state unchanged (selection.json md5 before / after)
# Nothing is applied in this part.  usage: t98.sh <tag> -> shots/t98_<tag>
. ~/cineview-mla/p6lib.sh
TAG=${1:?tag}
S=~/cineview-mla/shots/t98_$TAG; rm -rf $S; mkdir -p $S/frames
ga() { curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1"; }
fr() { local end=$(( $(date +%s) + $2 )) i=0; while [ $(date +%s) -lt $end ]; do curl -s -m 10 -o $S/frames/$(printf "%s_%03d" $1 $i).jpg "http://192.168.1.250/grab?format=jpg&r=1280&mode=all"; i=$((i+1)); done; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
rows() { $R 'rm -f /tmp/cvmla/rows.txt; echo rows > /tmp/cvmla/open.txt'; sleep 1.6; $R 'cat /tmp/cvmla/rows.txt 2>/dev/null' > $S/rows_$1.txt; }
SEL=/etc/enigma2/cineview_mla/selection.json
echo "== D0 backup"
$R "TS=\$(date +%Y%m%d-%H%M%S); B=/media/usb/cineview-mla/state/backup-t98-\$TS; mkdir -p \$B && tar -C /etc/enigma2 -czf \$B/cineview_mla.tgz cineview_mla && cp -p /etc/enigma2/settings \$B/settings && ls \$B && md5sum $SEL"
MD0=$($R "md5sum $SEL | cut -c1-32")
LOG0=$($R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); wc -l < $f')
X; sleep 1
echo "== D1 open"
op designs 5; ga D1_open; rows D1; cat $S/rows_D1.txt
echo "== D2 rows"
N=$(grep -c "^[ >] *[0-9]" $S/rows_D1.txt)
for i in $(seq 1 $((N - 1))); do $RC 108; sleep 1.2; ga $(printf "D2_row%02d" $i); rows $(printf "D2_row%02d" $i); grep "^>" $S/rows_$(printf "D2_row%02d" $i).txt; done
echo "== D3 preview"
for k in $(seq 1 $((N - 1))); do $RC 103; sleep 0.3; done; sleep 1; rows D3_top; grep "^>" $S/rows_D3_top.txt   # back to the top (theme row)
$RC 400; sleep 2.5; ga D3_preview_theme; $RC 174; sleep 1.5
$RC 108; sleep 1; $RC 400; sleep 2.5; ga D3_preview_infobar; fr D3_preview_infobar 2; $RC 174; sleep 1.5
for k in $(seq 1 $((N - 2))); do $RC 108; sleep 0.3; done; sleep 1   # last row (native option, no preview)
rows D3_last; grep "^>" $S/rows_D3_last.txt
$RC 400; sleep 2; ga D3_nopreview_msg; sleep 4.5; ga D3_nopreview_gone
echo "== D4 MENU"
$RC 139; sleep 2; ga D4_profiles_menu; $RC 352; sleep 2; ga D4_models; $RC 174; sleep 1.5; ga D4_back
echo "== D5 RED"
$RC 398; sleep 2; ga D5_closed
MD1=$($R "md5sum $SEL | cut -c1-32"); echo "   selection.json unchanged: $([ "$MD0" = "$MD1" ] && echo yes || echo NO)"
X
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); tail -n +'$LOG0' $f | grep -a "Skin\] Error\|Traceback\|CineViewMLA\]" | grep -v "progressPercentWidth\|piconMargin" | tail -12 | cut -c1-200; echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"'
echo T98_DONE
