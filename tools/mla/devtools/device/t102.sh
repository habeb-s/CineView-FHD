#!/bin/bash
# t102 (user 2026-10-07 05:36) - final CineView Designs acceptance on the INSTALLED package.
#   W. slow walk, first row -> last row: continuous frames + grab + row dump per row; checks: no "g000", "build",
#      "commit", "trial", "?" placeholder; green "Apply Design", blue "Restore Factory Design"
#   M. MessageBox: one line, Yes/No, four answers, long text (display only)
#   S. ten native Setup pages, top and scrolled (display only, EXIT)
#   F. functions: profiles (save/load/delete), Apply -> Keep, Apply -> no answer (automatic revert), Factory
#      (real) -> the original selection back, Processing
#   T. six themes: CineView Designs (preview row + Info Card row), Processing, MessageBox Yes/No + long, a Setup page
# Original selection, posters, settings restored; backup first.  usage: t102.sh <tag>
exec 9>~/cineview-mla/t102.lock; flock -n 9 || { echo "t102 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
TAG=${1:?tag}
S=~/cineview-mla/shots/t102_$TAG; rm -rf $S; mkdir -p $S/frames
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1"; }
fr() { local end=$(( $(date +%s) + $2 )) i=0; while [ $(date +%s) -lt $end ]; do curl -s -m 10 -o $S/frames/$(printf "%s_%03d" $1 $i).jpg "http://192.168.1.250/grab?format=jpg&r=1280&mode=all"; i=$((i+1)); done; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
rows() { $R 'rm -f /tmp/cvmla/rows.txt; echo rows > /tmp/cvmla/open.txt'; sleep 1.6; $R 'cat /tmp/cvmla/rows.txt 2>/dev/null' > $S/rows_$1.txt; }
cur() { rows cur; grep "^>" $S/rows_cur.txt | sed 's/^> *//' | cut -d" " -f1; }
goto() { local c=$(cur) n
	[ -z "$c" ] && { echo "   goto: no list"; return 1; }
	if [ "$1" -gt "$c" ]; then for n in $(seq 1 $(( $1 - c ))); do $RC 108; sleep 0.3; done; elif [ "$1" -lt "$c" ]; then for n in $(seq 1 $(( c - $1 ))); do $RC 103; sleep 0.3; done; fi
	sleep 0.8; c=$(cur); [ "$c" = "$1" ] || { echo "   goto $1: cursor at $c - ABORT"; X; exit 2; }; }
val() { rows v; grep "^[ >] *$1 " $S/rows_v.txt | sed 's/.*| //'; }
sel() { $R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print(d['theme'], ','.join('%s=%s'%kv for kv in sorted(d['layouts'].items())))\""; }
waithealthy() { for k in $(seq 1 40); do sleep 4; $R 'grep -a "CineViewMLA\] session healthy" /home/root/logs/$(ls -t /home/root/logs | grep debug | head -1) >/dev/null' && return 0; done; return 1; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error" $f | grep -v "progressPercentWidth\|piconMargin" | tail -3 | cut -c1-170'; }
$R "TS=\$(date +%Y%m%d-%H%M%S); B=/media/usb/cineview-mla/state/backup-t102-\$TS; mkdir -p \$B && tar -C /etc/enigma2 -czf \$B/cineview_mla.tgz cineview_mla && cp -p /etc/enigma2/settings \$B/settings && echo backup \$B"
ORIG=$($R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
SEL0=$(sel); echo "selection before: $SEL0"
X; sleep 1

echo "== W slow walk"
op designs 5; rows W00; ga W00; fr W00 3
N=$(grep -c "^[ >] *[0-9]" $S/rows_W00.txt)
for i in $(seq 1 $((N - 1))); do $RC 108; fr $(printf "W%02d" $i) 3; ga $(printf "W%02d" $i); rows $(printf "W%02d" $i); done
for f in $S/rows_W*.txt; do grep "^>" $f | cut -c1-90; grep "key_yellow\|status" $f | head -2 | cut -c1-140; done > $S/walk_rows.txt
echo "   rows: $N"
echo "   forbidden words on screen (status/keys/description): $(cat $S/rows_W*.txt | grep -v '^[ >] *[0-9]' | grep -ci 'g0000\|build[0-9]\|commit\|trial\|generation\|last known')"
grep -h "key_green\|key_blue\|status" $S/rows_W00.txt
$RC 398; sleep 2; X

echo "== M MessageBox"
for m in msg_info msg_yesno msg_list msg_long; do op $m 2.5; ga M_$m; fr M_$m 2; $RC 174; sleep 1.5; done

echo "== S Setup pages"
for k in UserInterface Usage Time EPG Recording Audio Subtitle Playback ChannelSelection Logs; do
	op setup:$k 4; ga S_${k}_top; for n in $(seq 1 13); do $RC 108; sleep 0.25; done; sleep 1.5; ga S_${k}_scrolled; $RC 174; sleep 1.5; X
done
errs

echo "== F1 profiles"
HAVE=$($R "ls '/etc/enigma2/cineview_mla/profiles/My CineView.json' 2>/dev/null")
if [ -z "$HAVE" ]; then
	op designs 5; $RC 139; sleep 2; ga F1_menu; $RC 108; sleep 1; $RC 352; sleep 3; $RC 399; sleep 3; ga F1_saved; sleep 4
	$RC 139; sleep 2; $RC 108; sleep 0.6; $RC 108; sleep 1; $RC 352; sleep 2; ga F1_pick; $RC 352; sleep 2.5; ga F1_loaded; sleep 6
	$RC 398; sleep 2; echo "   after RED: $(sel)"
	op designs 5; $RC 139; sleep 2; $RC 108; sleep 0.6; $RC 108; sleep 0.6; $RC 108; sleep 1; $RC 352; sleep 2; $RC 352; sleep 2; ga F1_confirm; $RC 103; sleep 1; $RC 352; sleep 2
	$R "ls '/etc/enigma2/cineview_mla/profiles/My CineView.json' 2>/dev/null || echo '   profile deleted'"; $RC 398; sleep 2
else echo "   user profile 'My CineView' exists - skipped"; fi

echo "== F2 Apply -> Keep (theme -> next)"
op designs 5; goto 0; $RC 106; sleep 1; echo "   theme -> $(val 0)"; o=$(pid); $RC 399; sleep 3; ga F2_apply_q; $RC 352
newe2 $o; waithealthy; sleep 3; ga F2_keep_prompt; $RC 103; sleep 1; $RC 352; sleep 5; echo "   kept: $(sel)"; errs

echo "== F3 Apply -> no answer -> automatic revert (theme -> next again)"
op designs 5; goto 0; $RC 106; sleep 1; echo "   theme -> $(val 0)"; o=$(pid); $RC 399; sleep 3; $RC 352
newe2 $o; waithealthy; sleep 3; ga F3_keep_prompt; echo "   not answered ..."; o=$(pid); newe2 $o; waithealthy; sleep 2
echo "   after timeout: $(sel)"; $R "tail -4 /etc/enigma2/cineview_mla/history.log"; errs

echo "== F4 Factory (real)"
op designs 5; $RC 401; sleep 2; ga F4_factory_q; $RC 103; sleep 1; o=$(pid); $RC 352; newe2 $o; sleep 25
echo "   after factory: $(sel)"; X; $RC 352; sleep 3; ga F4_infobar_factory; X
op designs 5; ga F4_designs_factory; rows F4; grep status $S/rows_F4.txt; X; errs

echo "== F5 Processing"
op pluginbrowser 5; op processing 1.5; ga F5_processing; sleep 5; op processing2 1.5; ga F5_processing2; sleep 5; X

echo "== T six themes"
for t in navy black graphite purple burgundy green; do
	$R "$E apply --theme $t 2>&1 | tail -1"; restart ""
	op designs 5; ga T_${t}_1_preview; goto 14; sleep 1; ga T_${t}_2_infocard; X
	op pluginbrowser 5; op processing 1.5; ga T_${t}_3_processing; sleep 5; X
	op msg_yesno 2.5; ga T_${t}_4_yesno; $RC 174; sleep 1; op msg_long 2.5; ga T_${t}_5_long; $RC 174; sleep 1
	op setup:UserInterface 4; ga T_${t}_6_setup; $RC 174; sleep 1; X; errs
done

echo "== restore: $ORIG"
$R "$E apply $ORIG 2>&1 | tail -1"; restart ""
SEL1=$(sel); echo "selection after: $SEL1"; echo "   restored: $([ "$SEL0" = "$SEL1" ] && echo yes || echo NO)"
$R "B=\$(ls -d /media/usb/cineview-mla/state/backup-t102-* | tail -1); diff \$B/settings /etc/enigma2/settings | grep '^[<>]' | grep -v 'nextWakeup\|startCounter\|shutdownOK' || echo '   settings: same as the backup (counters aside)'"
errs
echo T102_DONE
