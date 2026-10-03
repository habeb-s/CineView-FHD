#!/bin/bash
# P6-a: open CineView Designs, walk the list, preview. No apply. Slot 8 only.
RC=~/cineview-mla/rc.sh; S=~/cineview-mla/shots/p6
g() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; echo "cap $1"; }
$RC 174 174 174; sleep 1; $RC 399; sleep 3; $RC 106 106 106; sleep 1; $RC 352; sleep 4; g ui00_open
for i in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15; do $RC 108; sleep 1.5; g ui$i; done
# theme row: back to top, change theme value right once (not applied), preview
$RC 104 104; sleep 1; $RC 102; sleep 1.5; g ui20_top; $RC 106; sleep 2; g ui21_theme_right
$RC 400; sleep 3; g ui22_preview_fullscreen; $RC 174; sleep 1.5; g ui23_back
$RC 105; sleep 1.5
# cancel (red) -> expect close without saving
$RC 398; sleep 2; g ui24_after_red
echo done
