#!/bin/bash
# T-B: trial confirmed with YES -> committed, survives a GUI restart.  T-C: factory design -> navy, lkg=factory.
. ~/cineview-mla/p6lib.sh
openui; $RC 106; sleep 1.5; o=$(pid); $RC 399; sleep 5; $RC 352; newe2 $o; o2=$(pid); st
for k in $(seq 1 30); do sleep 4; $R 'grep -a "CineViewMLA\] session healthy" /home/root/logs/$(ls -t /home/root/logs | grep debug | head -1) >/dev/null' && break; done
sleep 2; g B01_prompt; $RC 103; sleep 1; g B02_yes_selected; $RC 352; sleep 4; g B03_after_yes; st; e2log 6
o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 20; X; $RC 352; sleep 2; g B04_after_restart_infobar; st
echo DONE-B
openui; g C01_ui; $RC 401; sleep 2; g C02_factory_q; $RC 103; sleep 1; o=$(pid); $RC 352; newe2 $o; sleep 20; X; $RC 352; sleep 2; g C03_after_factory_infobar; st; e2log 8
echo DONE-C
