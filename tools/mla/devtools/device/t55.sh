#!/bin/bash
# Graphical Plus refinements (build46; user decisions 2026-10-05 05:23):
#  A long titles in the grid: native single-line titles (graph_event_alignment default 17 = Left) and the user option
#    "Left, wrapped" (81 = RT_HALIGN_LEFT 1 | RT_VALIGN_CENTER 16 | RT_WRAP 64, grc.h) x posters ON/OFF
#  B OFF panel: genre / IMDb as a footer, description directly under the duration
#  C fast navigation: the same key sequence fast (0.25 s/step) and slow (2.5 s/step); at 3 checkpoints the
#    settled panel (poster + title crop) must be identical between both runs
# The wrapped option is removed from settings afterwards (enigma2 stopped); restore epg=classic.
exec 9>~/cineview-mla/t55.lock; flock -n 9 || { echo "t55 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build46}
S=~/cineview-mla/shots/t55; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
views() { zap $HBO; X; op graph 9; ga $1_start; $RC 106; sleep 2; $RC 106; sleep 3; ga $1_right2; $RC 103; sleep 2; $RC 103; sleep 2; $RC 103; sleep 3; ga $1_up3; X; sleep 2; }
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "$E apply --theme navy --set epg=graphicalplus 2>&1 | tail -1"
restart ""; errs
echo "== A1 single-line titles (default), posters ON / OFF"
views a1_on
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=False;"; views a1_off; errs
echo "== A2 wrapped titles (user option), posters OFF / ON"
restart "python3 /tmp/cvmla/setcfg.py config.epgselection.graph_event_alignment=81;"; views a2_off; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=True;"; views a2_on; errs
restart "sed -i '/config.epgselection.graph_event_alignment=/d' /etc/enigma2/settings;"; errs
echo "== C fast vs slow navigation, same key sequence"
SEQ="106 106 108 106 108 108 105 106 108"
CHK=" 3 6 9 "
run() {  # $1 tag $2 step seconds
  zap $HBO; X; op graph 9; n=0
  for k in $SEQ; do $RC $k; sleep $2; n=$((n+1)); case "$CHK" in *" $n "*) sleep 2; ga c_$1_k$n;; esac; done
  X; sleep 2
}
run fast 0.25; run slow 2.5
python3 - $S <<'PY'
import sys
from PIL import Image, ImageChops, ImageStat
S = sys.argv[1]
def crop(n, box): return Image.open("%s/%s.png" % (S, n)).convert("L").crop(box)
for k in (3, 6, 9):
    res = []
    for name, box in (("poster", (1374, 120, 1614, 480)), ("title", (1374, 500, 1856, 582)), ("times", (1634, 240, 1856, 270))):
        d = ImageStat.Stat(ImageChops.difference(crop("c_fast_k%d" % k, box), crop("c_slow_k%d" % k, box))).mean[0]
        res.append("%s=%.1f" % (name, d))
    print("checkpoint key %d: %s -> %s" % (k, " ".join(res), "SAME" if all(float(r.split("=")[1]) < 6 for r in res) else "DIFFERENT"))
PY
$R "rm -rf $P"; $R "$E apply --set epg=classic 2>&1 | tail -1"; restart ""; st; errs
$R "grep -E 'graph_event_alignment|cineviewmla.poster_epg' /etc/enigma2/settings"
echo T55_DONE
