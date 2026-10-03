#!/bin/sh
# Installed as /usr/bin/enigma2_pre_start.sh (native OpenATV hook, run by enigma2.sh before each start).
# Only calls the CineView MLA guardian; never blocks Enigma2 startup.
G=/usr/share/enigma2/CineView_FHD_MLA/mla/guardian/guardian.sh
[ -x "$G" ] && "$G" || true
exit 0
