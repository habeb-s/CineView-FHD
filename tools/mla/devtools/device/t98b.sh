#!/bin/bash
# t98b - CineView Designs checklist, part 2 (functions; user 2026-10-06 23:10).  Every change is put back:
#   E1 Posters - Main InfoBar -> No, GREEN (saved, no restart) -> InfoBar without poster -> back to Yes
#   E2 Second InfoBar timeout -> next value, GREEN -> /etc/enigma2/settings -> back to the original value
#   E3 MENU profiles: save (only if no profile "My CineView" exists), load (RED: nothing applied), delete
#   E4 MENU model "Details" -> message -> RED: nothing applied
#   E5 BLUE factory -> question -> default No: nothing happens
#   E6 trial DECLINED: theme -> next, GREEN, restart -> keep prompt -> No -> automatic revert (theme back)
#   E7 trial KEPT: theme -> next, GREEN, restart -> Yes -> committed; then the original theme back the same way
# usage: t98b.sh <tag> -> shots/t98b_<tag>.  Backup taken by t98 part 1 (D0) and again here.
. ~/cineview-mla/p6lib.sh
TAG=${1:?tag}
S=~/cineview-mla/shots/t98b_$TAG; rm -rf $S; mkdir -p $S/frames
ga() { curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
rows() { $R 'rm -f /tmp/cvmla/rows.txt; echo rows > /tmp/cvmla/open.txt'; sleep 1.6; $R 'cat /tmp/cvmla/rows.txt 2>/dev/null' > $S/rows_$1.txt; }
cur() { rows cur; grep "^>" $S/rows_cur.txt | sed 's/^> *//' | cut -d" " -f1; }
goto() {  # goto <index>: move the list cursor and verify
	local c=$(cur) n
	[ -z "$c" ] && { echo "   goto: no list"; return 1; }
	if [ "$1" -gt "$c" ]; then for n in $(seq 1 $(( $1 - c ))); do $RC 108; sleep 0.3; done; elif [ "$1" -lt "$c" ]; then for n in $(seq 1 $(( c - $1 ))); do $RC 103; sleep 0.3; done; fi
	sleep 0.8; c=$(cur); [ "$c" = "$1" ] || { echo "   goto $1: cursor at $c - ABORT"; X; exit 2; }
	grep "^>" $S/rows_cur.txt
}
val() { rows v; grep "^[ >] *$1 " $S/rows_v.txt | sed 's/.*| //'; }
sel() { $R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print(d['theme'], ','.join('%s=%s'%kv for kv in sorted(d['layouts'].items())))\""; }
waithealthy() { for k in $(seq 1 40); do sleep 4; $R 'grep -a "CineViewMLA\] session healthy" /home/root/logs/$(ls -t /home/root/logs | grep debug | head -1) >/dev/null' && return 0; done; return 1; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
$R "TS=\$(date +%Y%m%d-%H%M%S); B=/media/usb/cineview-mla/state/backup-t98b-\$TS; mkdir -p \$B && tar -C /etc/enigma2 -czf \$B/cineview_mla.tgz cineview_mla && cp -p /etc/enigma2/settings \$B/settings && echo backup \$B"
SEL0=$(sel); echo "selection before: $SEL0"
X; sleep 1

echo "== E1 poster switch (Main InfoBar)"
op designs 5; goto 7; ga E1_row; $RC 106; sleep 1; echo "   value now: $(val 7)"; $RC 399; sleep 2.5; ga E1_saved_msg; sleep 6
$R "grep cineviewmla.poster_infobar /etc/enigma2/settings || echo '(poster_infobar: default)'"
X; $RC 352; sleep 3; ga E1_infobar_noposter; X
op designs 5; goto 7; $RC 105; sleep 1; echo "   value back: $(val 7)"; $RC 399; sleep 2.5; sleep 6
$R "grep cineviewmla.poster_infobar /etc/enigma2/settings || echo '(poster_infobar: default = Yes)'"
X; $RC 352; sleep 3; ga E1_infobar_poster; X

echo "== E2 Second InfoBar timeout"
op designs 5; goto 16; T0=$(val 16); $RC 106; sleep 1; T1=$(val 16); echo "   $T0 -> $T1"; ga E2_row; $RC 399; sleep 2; sleep 6
$R "grep second_infobar_timeout /etc/enigma2/settings || echo '(second_infobar_timeout: default)'"
op designs 5; goto 16; $RC 105; sleep 1; echo "   back: $(val 16)"; $RC 399; sleep 8
$R "grep second_infobar_timeout /etc/enigma2/settings || echo '(second_infobar_timeout: default)'"

echo "== E3 profiles"
HAVE=$($R "ls '/etc/enigma2/cineview_mla/profiles/My CineView.json' 2>/dev/null")
op designs 5
if [ -z "$HAVE" ]; then
	$RC 139; sleep 2; ga E3_menu; $RC 108; sleep 1; $RC 352; sleep 3; ga E3_keyboard; $RC 399; sleep 3; ga E3_saved
	$R "cat '/etc/enigma2/cineview_mla/profiles/My CineView.json'"; sleep 4
	$RC 139; sleep 2; ga E3_menu2; $RC 108; sleep 0.6; $RC 108; sleep 1; $RC 352; sleep 2; ga E3_pick; $RC 352; sleep 2.5; ga E3_loaded; sleep 6
	$RC 398; sleep 2; echo "   after RED: $(sel)"
	op designs 5; $RC 139; sleep 2; $RC 108; sleep 0.6; $RC 108; sleep 0.6; $RC 108; sleep 1; ga E3_menu_delete; $RC 352; sleep 2; $RC 352; sleep 2; ga E3_confirm; $RC 103; sleep 1; $RC 352; sleep 2
	$R "ls '/etc/enigma2/cineview_mla/profiles/' 2>/dev/null; ls '/etc/enigma2/cineview_mla/profiles/My CineView.json' 2>/dev/null || echo '   profile deleted'"
	$RC 398; sleep 2
else
	echo "   a user profile 'My CineView' exists - save/delete skipped (never overwritten)"; $RC 398; sleep 2
fi

echo "== E4 model"
op designs 5; $RC 139; sleep 2; $RC 352; sleep 2; $RC 108; sleep 1; ga E4_models; $RC 352; sleep 2.5; ga E4_model_msg; sleep 6; rows E4; grep "Design -" $S/rows_E4.txt
$RC 398; sleep 2; echo "   after RED: $(sel)"

echo "== E5 factory question"
op designs 5; $RC 401; sleep 2; ga E5_factory_q; $RC 352; sleep 3; echo "   after default No: $(sel)"; $RC 398; sleep 2

echo "== E6 trial declined"
op designs 5; goto 0; $RC 106; sleep 1; echo "   theme -> $(val 0)"; ga E6_theme; o=$(pid); $RC 399; sleep 3; ga E6_restart_q; $RC 352
newe2 $o; waithealthy; sleep 3; ga E6_keep_prompt; echo "   trial: $(sel)"
o=$(pid); $RC 352; sleep 2; newe2 $o; waithealthy; sleep 2; echo "   after No: $(sel)"; ga E6_after_revert
$R "tail -4 /etc/enigma2/cineview_mla/history.log"; errs

echo "== E7 trial kept + original theme back"
for step in next back; do
	op designs 5; goto 0; if [ $step = next ]; then $RC 106; else $RC 105; fi; sleep 1; echo "   theme -> $(val 0)"
	o=$(pid); $RC 399; sleep 3; $RC 352; newe2 $o; waithealthy; sleep 3; ga E7_${step}_prompt
	$RC 103; sleep 1; $RC 352; sleep 5; echo "   kept: $(sel)"; X; $RC 352; sleep 3; ga E7_${step}_infobar; X
done
$R "tail -6 /etc/enigma2/cineview_mla/history.log"
SEL1=$(sel); echo "selection after: $SEL1"; echo "   restored: $([ "$SEL0" = "$SEL1" ] && echo yes || echo NO)"
errs
echo T98B_DONE
