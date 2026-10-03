#!/bin/bash
# T-E: Enigma2 PROCESS crash (SIGKILL) during an unconfirmed trial -> recover() at the respawn reverts.
. ~/cineview-mla/p6lib.sh
$R "python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py apply --theme purple --trial 2>&1 | tail -1"
o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 5; o2=$(pid); X; $RC 352; sleep 2; g E01_trial_infobar; st
$R "kill -9 $o2"; echo "killed $o2"; newe2 $o2; sleep 20; X; $RC 352; sleep 2; g E02_after_respawn_infobar; st; e2log 6
echo DONE-E
