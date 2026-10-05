#!/bin/bash
# HD / 16:9 fix verification (CineViewMLAServiceInfo, build48): same protocol as t53 (baseline build44: native
# ServiceInfo -> misses), 3 rounds x 6 themes x Classic / Modern: apply theme -> restart Enigma2 -> zap HRT1 -> OK ->
# grab -> automatic chip / icon detection; ShowIf debug log of every chip update (events + rechecks).
# Restore: Classic, navy, debug flag removed.
exec 9>~/cineview-mla/t56.lock; flock -n 9 || { echo "t56 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build48}
S=~/cineview-mla/shots/t56; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 9; }
detect() {  # $1 design $2 png -> "HD=1 AR=1"
python3 - "$1" "$2" <<'PY'
import sys
from PIL import Image, ImageStat
d, p = sys.argv[1], sys.argv[2]
im = Image.open(p).convert("RGB")
if d == "modern":
    def pill(x):  # opaque pill colour #344660 inside the chip box
        r, g, b = im.getpixel((x, 835))  # vertical middle of the 34-px pill, 6 px inside its left edge
        return int(abs(r - 52) < 14 and abs(g - 70) < 14 and abs(b - 96) < 14)
    print("HD=%d AR=%d" % (pill(1248), pill(1498)))
else:
    def icon(x):
        return int(ImageStat.Stat(im.crop((x, 1027, x + 60, 1059)).convert("L")).stddev[0] > 25)
    print("HD=%d AR=%d" % (icon(1008), icon(1216)))
PY
}
~/cineview-mla/deploy_b.sh $NEW
$R "touch /etc/enigma2/cineview_mla/debug_showif"
miss=0; n=0
for design in classic modern; do
  for round in 1 2 3; do
    for t in black burgundy graphite green purple navy; do
      $R "$E apply --theme $t --set infobar=$design 2>&1 | tail -1" >/dev/null
      restart ""
      zap $HRT1; X; sleep 2; $RC 352; sleep 2.5
      tag=${design}_r${round}_$t; ga $tag; X
      r=$(detect $design $S/$tag.png); n=$((n+1)); case "$r" in *=0*) miss=$((miss+1));; esac
      vi=$(curl -s -m 8 "http://192.168.1.250/api/currenttime" >/dev/null; $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); grep -a -c "ShowIf\] dbg" $f')
      echo "$tag $r dbg_lines=$vi"
      $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); grep -a "ShowIf\] dbg" $f' > $S/$tag.dbg.txt
    done
  done
done
echo "SUMMARY samples=$n missing=$miss"
$R "rm -f /etc/enigma2/cineview_mla/debug_showif"
$R "$E apply --theme navy --set infobar=classic 2>&1 | tail -1"; restart ""; st
echo T56_DONE
