#!/bin/bash
. ~/cineview-mla/p6lib.sh
B=/media/usb/cineview-mla/state/backup-p6
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings.pre-p6 && tar -C /etc/enigma2 -czf $B/cineview_mla-state.pre-p6.tgz cineview_mla && tar -C / -czf $B/mla-files.pre-build13.tgz usr/share/enigma2/CineView_FHD_MLA/mla usr/share/enigma2/CineView_FHD_MLA/mla_assets usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA usr/lib/enigma2/python/Components/Renderer/CineViewMLAPosterX.py && ls -l $B"
sh ~/cineview-mla/repo/tools/mla/deploy.sh ~/cineview-mla/build13
o=$(pid); $R 'rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/__pycache__; init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'
newe2 $o; sleep 20; st; e2log 10
