#!/bin/bash
# t100 - CineView Designs + Processing + MessageBox in the six themes (visual review sheet).  Theme set through the
# engine (composer apply, as t95), Enigma2 restarted, screens opened by the devtool, grabs; the original selection
# (theme + layouts) is applied again at the end.  usage: t100.sh <tag>
. ~/cineview-mla/p6lib.sh
TAG=${1:?tag}
S=~/cineview-mla/shots/t100_$TAG; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ga() { curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
ORIG=$($R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
echo "original: $ORIG"
for t in navy black graphite purple burgundy green; do
	echo "== $t"
	$R "$E apply --theme $t 2>&1 | tail -1"; restart
	X; op designs 5; ga ${t}_1_designs; X
	op pluginbrowser 5; op processing 1.5; ga ${t}_2_processing; sleep 5; X
	op msg_yesno 2.5; ga ${t}_3_msgbox; $RC 174; sleep 1; X
	errs
done
echo "== restore: $ORIG"
$R "$E apply $ORIG 2>&1 | tail -1"; restart
$R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('now', d['theme'], d['layouts'])\""; errs
echo T100_DONE
