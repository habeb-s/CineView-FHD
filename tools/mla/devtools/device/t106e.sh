#!/bin/bash
# t106e - OpenBH (Slot 5): CAM / ECM information on the live InfoBar for each "Server / CAM information" mode
# (config.plugins.cineviewmla.servermode = full | profile | hide), with the softcam already running on the image.
# Setting written with the GUI stopped; previous value restored at the end.  Live /tmp/ecm.info captured per mode.
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r5.sh
S=~/cineview-mla/shots/t106e; rm -rf $S; mkdir -p $S
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; }
restart_gui() { local o=$($R pidof enigma2); $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; $1 init 3"
	for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30; }
K=config.plugins.cineviewmla.servermode
M0=$($R "sed -n 's/^$K=//p' /etc/enigma2/settings"); echo "servermode before: '${M0:-(default profile)}'"
echo "softcam: $($R 'for p in $(pidof oscam-emu oscam ncam 2>/dev/null); do cat /proc/$p/comm; done' | sort -u | tr '\n' ' ')"
for m in full profile hide; do
	restart_gui "sed -i '/^$K=/d' /etc/enigma2/settings; echo $K=$m >> /etc/enigma2/settings;"
	curl -s -m 10 -o /dev/null "http://192.168.1.250/api/zap?sRef=${ZAP:-1:0:19:786:C6D4:16E:A00000:0:0:0:}"; sleep 20
	$R 'cat /tmp/ecm.info' > $S/ecm_$m.txt
	X; sleep 1; $RC 352; sleep 2.5; ga ib_${m}_a; sleep 2.5; ga ib_${m}_b
	python3 -c "from PIL import Image
for s in 'ab': Image.open('$S/ib_${m}_'+s+'.png').crop((660,830,1080,1010)).resize((840,360)).save('$S/cam_${m}_'+s+'.png')"
	echo "== $m: using=$(sed -n 's/^using: //p' $S/ecm_$m.txt) address=$(sed -n 's/^address: //p' $S/ecm_$m.txt | sed 's/[0-9]*\.[0-9]*\.[0-9]*\./x.x.x./')"
	X
done
restart_gui "sed -i '/^$K=/d' /etc/enigma2/settings; [ -n '$M0' ] && echo '$K=$M0' >> /etc/enigma2/settings;"
echo "servermode restored: '$($R "sed -n 's/^$K=//p' /etc/enigma2/settings")'"
echo T106E_DONE
