#!/bin/bash
# T-D (user scenario 3): the selection UI crashes (in-process Python bsod, Enigma2 keeps running, guardian
# NOT triggered) while a trial design is unconfirmed -> trial watch restores the last good design.
. ~/cineview-mla/p6lib.sh
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/plugin.py
$R "python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py apply --theme purple --trial 2>&1 | tail -1"
$R "cat > $P.tmp && mv $P.tmp $P && rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/__pycache__" < /tmp/plugin_buggy.py
o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 5; o2=$(pid); g D01_trial_up; st
openui; g D02_ui_crash; st
for k in 01 02 03 04 05 06 07 08; do sleep 3; g D03_$k; p=$(pid); [ "$p" != "$o2" ] && { echo "e2 restarted by trial watch at k=$k"; break; }; done
$R "cat > $P.tmp && mv $P.tmp $P && rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/__pycache__; md5sum $P" < ~/cineview-mla/build13$P
newe2 $o2; sleep 15; X; $RC 352; sleep 2; g D04_after_infobar; st; e2log 14
echo DONE-D
