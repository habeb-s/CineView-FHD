#!/bin/bash
# t101b: real previews of the two layouts outside the five models - EPG Columns (EPGvertical) and Channel Selection
# Video First (right) -> previews_src/extra/.  Theme navy, posters ON, Cinemax HD; original selection restored.
. ~/cineview-mla/p6lib.sh
O=~/cineview-mla/previews_src/extra; mkdir -p $O/epg $O/channelselection
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
CH="1:0:19:786:C6D4:16E:A00000:0:0:0:"
ga() { curl -s -m 60 -o $1 "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
ORIG=$($R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
$R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=videofirst-right --set epg=columns --set pvr=classic --set eventview=classic-lines 2>&1 | tail -1"; restart
curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$CH"; sleep 8; X
op vertical 9; ga $O/epg/columns.png; X; sleep 2; X; sleep 1
$RC 108; sleep 4; ga $O/channelselection/videofirst-right.png; X; errs
$R "$E apply $ORIG 2>&1 | tail -1"; restart; errs
echo T101B_DONE
