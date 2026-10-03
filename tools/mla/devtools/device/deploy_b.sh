#!/bin/bash
. ~/cineview-mla/p6lib.sh
BLD=${1:?build}
B=/media/usb/cineview-mla/state/backup-$BLD
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings.pre-p6 && tar -C /etc/enigma2 -czf $B/cineview_mla-state.pre-p6.tgz cineview_mla && tar -C / -czf $B/mla-files.pre-$BLD.tgz usr/share/enigma2/CineView_FHD_MLA usr/lib/enigma2/python/Components/CineViewMLAPosterMatch.py usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA usr/lib/enigma2/python/Components/Renderer/CineViewMLAPosterX.py && ls -l $B"
sh ~/cineview-mla/repo/tools/mla/deploy.sh ~/cineview-mla/$BLD
o=$(pid); $R 'rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/__pycache__; init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'
newe2 $o; sleep 20; st; e2log 10
