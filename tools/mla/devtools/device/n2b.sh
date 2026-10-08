#!/bin/sh
# runs ON the receiver: enigma.info edited to say OpenBH 5.6 (a supported OpenBH version) on the OpenViX image
T=/tmp/cvmla-it2
cd $T || exit 1
sed -e "s/^distro=.*/distro='openbh'/" -e "s/^imageversion=.*/imageversion='5.6'/" /usr/lib/enigma.info > bh56.info
grep -E "^(distro|imageversion)=" bh56.info
DRYRUN=1 CVMLA_INFO=$T/bh56.info sh $T/i.sh 2>&1 | sed -e 's/\x1b\[[0-9;]*m//g' | grep -v "^$"
echo "pkg after: $(opkg status enigma2-plugin-skins-cineview-fhd-mla | sed -n 's/^Version: //p')"
