#!/bin/bash
. ~/cineview-mla/p6lib.sh
$R 'cp -p /media/usb/cineview-mla/state/runtime.json.pre-p5 /etc/enigma2/cineview_mla/runtime.json && cat /etc/enigma2/cineview_mla/runtime.json'
o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 25; st
$R 'python3 /tmp/cvmla/plog.py engine= | tail -1'
echo RESTORE_DONE
