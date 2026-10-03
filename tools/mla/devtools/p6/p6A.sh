#!/bin/bash
# T-A: trial design applied from the UI, prompt NOT answered -> automatic revert.
. ~/cineview-mla/p6lib.sh
st; openui; g A01_ui; $RC 106; sleep 1.5; g A02_theme_purple; o=$(pid); $RC 399; sleep 5; g A03_restart_question; st
$RC 352; newe2 $o; o2=$(pid); g A04_trial_up; st; e2log 6
for k in 01 02 03 04 05 06 07 08 09 10 11 12; do sleep 8; g A05_$k; p=$(pid); [ "$p" != "$o2" ] && { echo "e2 restarted (revert) at k=$k"; break; }; done
newe2 $o2; sleep 15; g A06_after_revert; st; e2log 12
echo DONE-A
