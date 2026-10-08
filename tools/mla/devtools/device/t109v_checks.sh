#!/bin/bash
# t109v_checks - rerun of the non-changing installer cases with the final installer 1.1.0 (OpenBH contract now also
# requires key_menu): I1, I1b, I2, N1-N7 and N2b (enigma.info says OpenBH 5.6 on this OpenViX image).
R=~/cineview-mla/r4.sh
S=~/cineview-mla/shots/vix_t109/final_checks; rm -rf $S; mkdir -p $S
P1=~/cineview-mla/pkg_vix/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openvix1_all.ipk
SHA1=$(sha256sum $P1 | cut -c1-64)
T=/tmp/cvmla-it
$R 'grep -q "rootsubdir=duo4kse/linuxrootfs4" /proc/cmdline' || { echo "NOT Slot 4"; exit 1; }
$R "rm -rf $T; mkdir -p $T"
cat ~/cineview-mla/installer_vix/cineview-install.sh | $R "cat > $T/cineview-install.sh"
cat $P1 | $R "cat > $T/$(basename $P1)"
cat > /tmp/mkinfo.sh <<'EOF'
I=/usr/lib/enigma.info; cd /tmp/cvmla-it
sed "s/^distro=.*/distro='openatv'/" $I > atv.info
sed "s/^distro=.*/distro='openbh'/" $I > bh.info
sed -e "s/^distro=.*/distro='openbh'/" -e "s/^imageversion=.*/imageversion='5.6'/" $I > bh56.info
grep -v '^distro=' $I > nodistro.info
sed "s/^imageversion=.*/imageversion='6.8'/" $I > vix68.info
sed "s/^imageversion=.*/imageversion='7.0'/" $I > vix70.info
sed "s/^machinebuild=.*/machinebuild='vuuno4kse'/" $I > othermodel.info
EOF
cat /tmp/mkinfo.sh | $R "cat > $T/mkinfo.sh; sh $T/mkinfo.sh; ls $T"
before=$($R "opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E 'Version|Status'; sha256sum /etc/enigma2/settings | cut -c1-16")
run() { local name=$1; shift; echo "################ $name"; $R "cd $T; $* sh $T/cineview-install.sh 2>&1; echo \"exit=\$?\"" | sed -E 's/\x1b\[[0-9;]*m//g' | grep -v '^$' > $S/$name.txt; grep "\[XX\]\|All checks passed\|already installed\|exit=" $S/$name.txt; }
OV="CVMLA_PKG_URL=$T/$(basename $P1) CVMLA_PKG_SHA=$SHA1"
run I1_default_not_released ""
run I1b_dryrun "DRYRUN=1 $OV"
run I2_same_version "$OV"
for c in atv bh bh56 nodistro vix68 vix70 othermodel none; do run N_info_$c "DRYRUN=1 $OV CVMLA_INFO=$T/$c.info"; done
after=$($R "opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E 'Version|Status'; sha256sum /etc/enigma2/settings | cut -c1-16")
echo "before: $before" | tr '\n' ' '; echo; echo "after:  $after" | tr '\n' ' '; echo
[ "$before" = "$after" ] && echo "UNCHANGED" || echo "CHANGED"
$R "rm -rf $T"
echo CHECKS_DONE
