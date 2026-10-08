#!/bin/bash
# t106c2 - OpenViX (Slot 4): CAM field in the InfoBar of Details and Cinema followed over a whole scroll cycle.
# The native InfoBar timeout (5 s default) hides the bar before the cycle ends, so the timeout is set to
# "No timeout" for this test only (written with the GUI stopped) and the previous value is restored afterwards.
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r4.sh
S=~/cineview-mla/shots/vix_t106c; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ZAP=${ZAP:-1:0:1:290E:1EDC:71:822FFC:0:0:0:}
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; }
restart_gui() { local o=$($R pidof enigma2); $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; $1 init 3"
	for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30; }
K=config.plugins.cineviewmla.servermode; T=config.usage.infobar_timeout
M0=$($R "sed -n 's/^$K=//p' /etc/enigma2/settings"); T0=$($R "sed -n 's/^$T=//p' /etc/enigma2/settings")
echo "before: servermode='$M0' infobar_timeout='${T0:-(default 5)}'"
ORIG=$($R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
for dsg in details cinema; do
	$R "$E apply --set infobar=$dsg 2>&1 | tail -1"
	restart_gui "sed -i '/^$K=/d;/^$T=/d' /etc/enigma2/settings; echo $K=full >> /etc/enigma2/settings; echo $T=0 >> /etc/enigma2/settings;"
	curl -s -m 10 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ZAP"; sleep 10
	for i in $(seq 1 20); do $R "[ -s /tmp/ecm.info ]" && break; sleep 3; done
	X; $RC 352; for k in 1 2 3 4 5 6 7 8 9 10; do sleep 1; ga ${dsg}_ibfull_$k; done; X
	echo "== $dsg done"
done
restart_gui "sed -i '/^$K=/d;/^$T=/d' /etc/enigma2/settings; [ -n '$M0' ] && echo '$K=$M0' >> /etc/enigma2/settings; [ -n '$T0' ] && echo '$T=$T0' >> /etc/enigma2/settings;"
$R "$E apply $ORIG 2>&1 | tail -1"; restart_gui
echo "restored: servermode='$($R "sed -n 's/^$K=//p' /etc/enigma2/settings")' infobar_timeout='$($R "sed -n 's/^$T=//p' /etc/enigma2/settings")'"
echo T106C2_DONE
