#!/bin/bash
# EventView band: measure partial-repaint time in the DISPLAYED framebuffer while descriptions swim.
# Every probe is bracketed by OSD grabs so the screen under test is documented.
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/evprobe; rm -rf $S; mkdir -p $S
cat ~/cineview-mla/fbprobe.py | $R 'cat > /tmp/cvmla/fbprobe.py'
gg() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; }
for ch in "1:0:19:786:C6D4:16E:A00000:0:0:0:|Cinemax" "1:0:19:784:C6D4:16E:A00000:0:0:0:|HBO"; do
  ref=${ch%%|*}; n=${ch##*|}
  X; curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ref"; sleep 5
  $RC 358; sleep 1; gg ${n}_a
  $R "python3 /tmp/cvmla/fbprobe.py 950 1530 250 500 2 ${n}_right_static_before_startdelay"
  $R "python3 /tmp/cvmla/fbprobe.py 950 1530 250 500 25 ${n}_right_swimming"
  gg ${n}_b
  $R "python3 /tmp/cvmla/fbprobe.py 95 575 250 500 25 ${n}_left_swimming"
  $R "python3 /tmp/cvmla/fbprobe.py 950 1530 170 225 8 ${n}_right_title"
  gg ${n}_c; X
done
echo EVPROBE_DONE
