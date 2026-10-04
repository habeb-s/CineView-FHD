#!/bin/bash
# Modern-model skin features on the receiver (Slot 8, active build unchanged): cornerRadius (all / top), border,
# translucent card, gradient with alpha blending, rounded Label background, rounded ePixmap.  Probe screen from
# CineViewMLAFeatureProbe over HRT1 (FTA, 16.0E).  Grabs: composite (all) and OSD only (alpha at the corners).
# The probe plugin is removed afterwards.
exec 9>~/cineview-mla/t41.lock; flock -n 9 || { echo "t41 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t41; rm -rf $S; mkdir -p $S
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAFeatureProbe
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
g() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=$2&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "FeatureProbe\|Skin\] Error\|Skin\] Warning" $f | grep -v "progressPercentWidth\|piconMargin" | tail -6'; }
tar -C ~/cineview-mla/repo/tools/mla/devtools -czf - CineViewMLAFeatureProbe | $R 'cat > /tmp/cvmla/probe.tgz'
restart "tar -C /usr/lib/enigma2/python/Plugins/Extensions -xzf /tmp/cvmla/probe.tgz && echo probe-installed;"
curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$HRT1"; sleep 8; X
pc=$($R 'p=$(python3 -c "import json; print(json.load(open(\"/etc/enigma2/cineview_mla/runtime.json\")).get(\"poster_cache\",\"\"))"); find $p -name "*.jpg" 2>/dev/null | head -1')
echo "poster: $pc"
python3 ~/cineview-mla/repo/tools/mla/devtools/device/probe_modern.py "$pc" | $R 'cat > /tmp/cvmla/probe.json.tmp && mv /tmp/cvmla/probe.json.tmp /tmp/cvmla/probe.json'
sleep 7; g probe_all all; g probe_osd osd; g probe_video video
X; sleep 2; errs
python3 - $S <<'PY'
import sys
from PIL import Image
S = sys.argv[1]
o = Image.open(S + "/probe_osd.png").convert("RGBA")
a = Image.open(S + "/probe_all.png").convert("RGB")
def px(im, x, y): return im.getpixel((x, y))
# corner pixel (2,2 inside the box) vs centre-edge pixel of each card: a rounded corner leaves the corner transparent
for name, (x, y, w, h) in {"A": (80, 80, 560, 300), "B": (700, 80, 560, 300), "C": (1320, 80, 520, 300), "pill1": (80, 440, 200, 52), "pill2": (300, 440, 240, 52), "poster": (80, 540, 200, 300)}.items():
	print("%-6s corner_tl osd=%s  edge_mid osd=%s  corner_bl osd=%s" % (name, px(o, x + 2, y + 2), px(o, x + w // 2, y + 2), px(o, x + 2, y + h - 3)))
for yy in (705, 800, 900, 1000, 1075):
	print("scrim y=%d osd=%s" % (yy, px(o, 1700, yy)))
PY
restart "rm -rf $P /tmp/cvmla/probe.json /tmp/cvmla/probe.tgz;"; errs
echo T41_DONE
