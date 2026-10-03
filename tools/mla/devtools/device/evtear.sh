#!/bin/bash
# EventView blank-band discrimination: one EventView kept open while the descriptions swim; 40 rapid OSD grabs.
# A real layout/state defect is persistent from frame to frame; a framebuffer read racing a clear+redraw
# (grab tearing) is random, with a random boundary, top part blank (the grab reads top-down).
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/evtear; rm -rf $S; mkdir -p $S
X; curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=1:0:19:786:C6D4:16E:A00000:0:0:0:"; sleep 3
$RC 358; sleep 5
for k in $(seq -w 1 40); do curl -s -m 10 -o $S/t$k.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; done
X; echo EVTEAR_DONE $(ls $S | wc -l)
