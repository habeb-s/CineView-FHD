#!/bin/bash
# 1) every range package: public download (the installer's own address rule: ~ -> .) + SHA256 = installer table
# 2) real receiver (OpenATV 8.0.1, Slot 8): installer 1.3.0 from the GitHub test branch, check-only (DRYRUN=1)
cd ~/cineview-mla/rangecheck
I=https://raw.githubusercontent.com/habeb-s/CineView-MLA-Install/installer-1.3.0/cineview-install.sh
curl -fsSL "$I" -o inst130.sh || { echo "installer download failed"; exit 1; }
BASE=$(sed -n 's/^DIST_BASE="\(.*\)"$/\1/p' inst130.sh)
grep -oE '[A-Z]+_R3[0-9]{2}_FILE="[^"]+"; [A-Z]+_R3[0-9]{2}_SHA="[0-9a-f]{64}"' inst130.sh | while read -r line; do
	F=$(echo "$line" | sed 's/.*_FILE="\([^"]*\)".*/\1/'); S=$(echo "$line" | sed 's/.*_SHA="\([^"]*\)".*/\1/')
	A=$(printf '%s' "$F" | tr '~' '.')
	G=$(curl -fsSL "$BASE/$A" | sha256sum | cut -d' ' -f1)
	[ "$G" = "$S" ] && echo "DL-OK   $F" || echo "DL-FAIL $F ($G)"
done
echo "--- receiver: check-only run of installer 1.3.0 (nothing is downloaded or installed)"
cd ~/cineview-mla && ./r.sh "wget -qO /tmp/cineview-install.sh '$I' && DRYRUN=1 CVMLA_COLOR=0 sh /tmp/cineview-install.sh; echo RC=\$?; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version; ls /tmp/cineview-install.sh 2>&1 | tail -1"
