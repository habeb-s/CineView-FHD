#!/bin/bash
# t106f - OpenBH (Slot 5): CineView Designs functions through the real UI (remote keys), and guardian recovery.
#   F0 design model from the Profiles menu (Modern) -> Apply -> Keep
#   F1 profile save / load / delete
#   F2 theme -> Apply -> Keep            F3 theme -> Apply -> no answer -> automatic rollback
#   F4 Restore Factory Design            R  guardian: 3rd start without healthy/clean signal -> rollback
# Same key sequences as the accepted OpenATV run (t102 part F).  Original selection restored at the end.
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r5.sh
S=~/cineview-mla/shots/t106f; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ST=/etc/enigma2/cineview_mla
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "   cap $1"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
rows() { $R 'rm -f /tmp/cvmla/rows.txt; echo rows > /tmp/cvmla/open.txt'; sleep 1.6; $R 'cat /tmp/cvmla/rows.txt 2>/dev/null' > $S/rows_$1.txt; }
cur() { rows cur; grep "^>" $S/rows_cur.txt | sed 's/^> *//' | cut -d" " -f1; }
goto() { local c=$(cur) n
	[ -z "$c" ] && { echo "   goto: no list"; return 1; }
	if [ "$1" -gt "$c" ]; then for n in $(seq 1 $(( $1 - c ))); do $RC 108; sleep 0.3; done; elif [ "$1" -lt "$c" ]; then for n in $(seq 1 $(( c - $1 ))); do $RC 103; sleep 0.3; done; fi
	sleep 0.8; c=$(cur); [ "$c" = "$1" ] || { echo "   goto $1: cursor at $c"; return 1; }; }
val() { rows v; grep "^[ >] *$1 " $S/rows_v.txt | sed 's/.*| //'; }
sel() { $R "python3 -c \"import json;d=json.load(open('$ST/selection.json'));print(d['theme'], ','.join('%s=%s'%kv for kv in sorted(d['layouts'].items())))\""; }
pid5() { $R 'pidof enigma2'; }
newe2() { local old=$1; for i in $(seq 1 120); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$old" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; }
waithealthy() { for k in $(seq 1 40); do sleep 4; $R 'grep -a "CineViewMLA\] session healthy" $(ls -t /home/root/logs/Enigma2_debug_*.log | head -1) >/dev/null' && return 0; done; return 1; }
errs() { $R 'f=$(ls -t /home/root/logs/Enigma2_debug_*.log | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors=$(grep -a -c "\[Skin\] Error\|SkinError" $f) crashlogs_today=$(ls /home/root/logs | grep -i crash | grep -c 2026-10-07)"'; }
ORIG=$($R "python3 -c \"import json;d=json.load(open('$ST/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
echo "selection before: $(sel)"; X

echo "== F0 design model Modern from the Profiles menu -> Apply -> Keep"
op designs 6; $RC 139; sleep 2; ga F0_menu; $RC 352; sleep 2; ga F0_models
for i in 1 2 3; do $RC 108; sleep 0.5; done; $RC 352; sleep 3; ga F0_model_selected; sleep 5
o=$(pid5); $RC 399; sleep 3; ga F0_apply_q; $RC 352
newe2 $o; waithealthy; sleep 3; ga F0_keep_prompt; $RC 103; sleep 1; $RC 352; sleep 5; echo "   after keep: $(sel)"; errs
X; $RC 352; sleep 2; ga F0_modern_infobar; X

echo "== F1 profiles: save / load / delete"
op designs 6; $RC 139; sleep 2; $RC 108; sleep 1; $RC 352; sleep 3; ga F1_keyboard; $RC 399; sleep 3; ga F1_saved; sleep 4
echo "   saved file: $($R "ls '$ST/profiles/'")"
$RC 139; sleep 2; $RC 108; sleep 0.6; $RC 108; sleep 1; $RC 352; sleep 2; ga F1_pick; $RC 352; sleep 2.5; ga F1_loaded; sleep 6
$RC 139; sleep 2; $RC 108; sleep 0.6; $RC 108; sleep 0.6; $RC 108; sleep 1; $RC 352; sleep 2; $RC 352; sleep 2; ga F1_delete_q; $RC 103; sleep 1; $RC 352; sleep 2
echo "   profiles after delete: '$($R "ls '$ST/profiles/' 2>/dev/null")'"; $RC 398; sleep 2; X

echo "== F2 theme -> Apply -> Keep"
op designs 6; goto 0; $RC 106; sleep 1; echo "   theme -> $(val 0)"; o=$(pid5); $RC 399; sleep 3; ga F2_apply_q; $RC 352
newe2 $o; waithealthy; sleep 3; ga F2_keep_prompt; $RC 103; sleep 1; $RC 352; sleep 5; echo "   kept: $(sel)"; errs

echo "== F3 theme -> Apply -> no answer -> automatic rollback"
B3=$(sel); op designs 6; goto 0; $RC 106; sleep 1; echo "   theme -> $(val 0)"; o=$(pid5); $RC 399; sleep 3; $RC 352
newe2 $o; waithealthy; sleep 3; ga F3_keep_prompt; echo "   not answered ..."; o=$(pid5); newe2 $o; sleep 30
A3=$(sel); echo "   before: $B3"; echo "   after:  $A3"; [ "$A3" = "$B3" ] && echo "   ROLLED BACK" || echo "   NOT ROLLED BACK"
$R "tail -3 $ST/history.log"; errs

echo "== F4 Restore Factory Design"
op designs 6; $RC 401; sleep 2; ga F4_factory_q; $RC 103; sleep 1; o=$(pid5); $RC 352; newe2 $o; sleep 30
echo "   after factory: $(sel)"; X; $RC 352; sleep 2; ga F4_infobar_factory; X; errs

echo "== R guardian recovery: active != last-known-good, 3rd unclean start -> rollback"
$R "$E apply --theme black --set infobar=cinema 2>&1 | tail -1"
echo "   active=$($R "readlink /usr/share/enigma2/CineView_FHD_MLA/active") lkg=$($R "cat $ST/lkg")"
o=$(pid5); $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; rm -f $ST/clean_exit; echo 2 > $ST/boot.count; init 3"
newe2 $o; sleep 30
echo "   active=$($R "readlink /usr/share/enigma2/CineView_FHD_MLA/active") lkg=$($R "cat $ST/lkg") boot.count=$($R "cat $ST/boot.count")"
$R "tail -3 $ST/history.log"; errs; X; $RC 352; sleep 2; ga R_after_recovery; X

echo "== restore: $ORIG"
o=$(pid5); $R "$E apply $ORIG 2>&1 | tail -1; init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3"; newe2 $o; sleep 30
echo "   selection: $(sel)"; errs
echo T106F_DONE
