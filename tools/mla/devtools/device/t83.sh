#!/bin/bash
# t83: the same attribution run as t81 (fixed zap order, gAccel debug, 8 rounds) on build75: the widget-size poster
# PNG is made with PIL from the original (no gPixmap; ePicLoad.getData() allocates accelAuto, picload.cpp:1348).
# The derived widget-size folder sz/ (USB dev cache) is moved aside for the run, so EVERY poster takes the first-decode
# path; afterwards the ePicLoad-made folder is put back and the PIL-made one is kept as sz.t83pil for the A/B
# comparison of identical posters.  Originals are only read.  Nothing on the HDD.
exec 9>~/cineview-mla/t83.lock; flock -n 9 || { echo "t83 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build75}
C=/media/usb/cineview-mla/dev-cache/reference/poster
$R "cd $C && [ -d sz ] && [ ! -e sz.t83bak ] && mv sz sz.t83bak; rm -rf sz.t83pil; echo sz aside: \$(ls sz.t83bak | wc -l) files"
$R ': > /tmp/CINEVIEW-MLA/poster.log 2>/dev/null; true'
cd ~/cineview-mla && ./t81.sh $NEW deploy c
echo "== t83: widget-size PNGs made with PIL during the run: $($R 'grep -a -c "sized make" /tmp/CINEVIEW-MLA/poster.log')"
$R 'grep -a "sized make\|sized save\|sized load\|picload fallback" /tmp/CINEVIEW-MLA/poster.log | cut -c1-150 | tail -8'
$R "cd $C && mv sz sz.t83pil && mv sz.t83bak sz && echo restored: sz \$(ls sz | wc -l) files, sz.t83pil \$(ls sz.t83pil | wc -l) files"
echo T83_DONE
