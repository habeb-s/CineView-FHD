#!/bin/bash
# T-F: a design pack that fails validation (missing required screen; malformed XML) is refused by the UI,
#      active generation untouched.  Fixtures exist only in Slot 8 and are removed afterwards.
# T-G: options-only change (Posters - EPG) is saved without a design change; restored afterwards.
. ~/cineview-mla/p6lib.sh
L=/usr/share/enigma2/CineView_FHD_MLA/layouts/infobar
$R "mkdir -p $L/zz_brokentest $L/zz_xmlerror && cd $L && for d in zz_brokentest zz_xmlerror; do sed -e \"s/\\\"classic\\\"/\\\"\$d\\\"/; s/CineView Classic/TEST \$d (Slot 8 fixture)/\" classic/manifest.json > \$d/manifest.json; done && echo '<skin><screen name=\"NotTheInfoBar\" position=\"0,0\" size=\"10,10\" /></skin>' > zz_brokentest/screens.openatv.xml && echo '<skin><screen name=\"InfoBar\"><widget ' > zz_xmlerror/screens.openatv.xml && ls $L"
st
openui; $RC 108; sleep 1; $RC 106; sleep 1.5; g F01_broken_selected; $RC 399; sleep 4; g F02_apply_refused; st; $RC 352; sleep 2
$RC 106; sleep 1.5; g F03_xmlerror_selected; $RC 399; sleep 4; g F04_apply_refused2; st; $RC 352; sleep 2
$RC 398; sleep 2
$R "rm -rf $L/zz_brokentest $L/zz_xmlerror; ls $L"
e2log 8
# T-G
openui; for i in 1 2 3 4 5 6 7 8 9 10; do $RC 108; sleep 0.5; done; sleep 1; g G01_posters_epg_row; $RC 106; sleep 1; g G02_posters_epg_no
$RC 399; sleep 3; g G03_saved_msg; $R 'grep "cineviewmla.poster_epg" /etc/enigma2/settings || echo "poster_epg not in settings"'
sleep 5; X; openui; for i in 1 2 3 4 5 6 7 8 9 10; do $RC 108; sleep 0.5; done; $RC 106; sleep 1; g G04_restore_yes; $RC 399; sleep 3; $R 'grep "cineviewmla.poster_epg" /etc/enigma2/settings || echo "poster_epg default (True)"'
X; st; e2log 8
echo DONE-FG
