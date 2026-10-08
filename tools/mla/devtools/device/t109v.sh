#!/bin/bash
# t109v - OpenViX 6.9 (Slot 4): CineView MLA Smart Installer 1.1.0 + uninstaller, run on the receiver exactly as a
# user runs them (sh <script>).  Package files are given through the installer's test overrides (CVMLA_PKG_URL /
# CVMLA_PKG_SHA / CVMLA_VERSION) because the OpenViX package has no public address yet.  HDD never used, no reboot.
#   I1 default run (package not released)   I1b check-only run (DRYRUN) with the package file
#   N1-N7 detection: enigma.info says openatv / openbh / nothing / openvix 6.8 / openvix 7.0 / another Vu+ model,
#         and no enigma.info at all -> must stop, nothing changed
#   I2 same version        I3 SHA256 mismatch     I4 upgrade openvix1 -> openvix2 (test build) + GUI restart
#   I5 image shell crash during the package script, twice -> stops, no loop     I6 next run repairs the package entry
#   I7 return to openvix1 (FORCE=1, --force-downgrade) + GUI restart   I8 uninstaller with MLA selected
#   I9 fresh install with the installer, MLA selected again            I10 preinst x100 with a per-run record
R=~/cineview-mla/r4.sh
S=~/cineview-mla/shots/vix_t109; rm -rf $S; mkdir -p $S
P1=~/cineview-mla/pkg_vix/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openvix1_all.ipk
P2=~/cineview-mla/pkg_vix2/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openvix2_all.ipk
PC=~/cineview-mla/crash_test.ipk
SHA1=$(sha256sum $P1 | cut -c1-64); SHA2=$(sha256sum $P2 | cut -c1-64); SHAC=$(sha256sum $PC | cut -c1-64)
T=/tmp/cvmla-it
PK=enigma2-plugin-skins-cineview-fhd-mla
$R 'grep -q "rootsubdir=duo4kse/linuxrootfs4" /proc/cmdline' || { echo "NOT Slot 4"; exit 1; }
$R "rm -rf $T; mkdir -p $T"
cat ~/cineview-mla/installer_vix/cineview-install.sh | $R "cat > $T/cineview-install.sh"
cat ~/cineview-mla/installer_vix/cineview-uninstall.sh | $R "cat > $T/cineview-uninstall.sh"
for p in $P1 $P2 $PC; do cat $p | $R "cat > $T/$(basename $p)"; done
I=/usr/lib/enigma.info
$R "cd $T; cp $I real.info
sed 's/^distro=.*/distro='\''openatv'\''/' $I > atv.info
sed 's/^distro=.*/distro='\''openbh'\''/' $I > bh.info
grep -v '^distro=' $I > nodistro.info
sed 's/^imageversion=.*/imageversion='\''6.8'\''/' $I > vix68.info
sed 's/^imageversion=.*/imageversion='\''7.0'\''/' $I > vix70.info
sed 's/^machinebuild=.*/machinebuild='\''vuuno4kse'\''/' $I > othermodel.info
ls"
state() { $R "echo \"pkg: \$(opkg status $PK | sed -n 's/^Version: //p') / \$(opkg status $PK | sed -n 's/^Status: //p')\"; echo \"settings: \$(sha256sum /etc/enigma2/settings | cut -c1-16) skin=\$(sed -n 's/^config.skin.primary_skin=//p' /etc/enigma2/settings)\"; echo \"selection: \$(python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print(d['theme'], ','.join('%s=%s'%kv for kv in sorted(d['layouts'].items())))\" 2>/dev/null) active=\$(readlink /usr/share/enigma2/CineView_FHD_MLA/active 2>/dev/null)\"; echo \"restore points: \$(ls /etc/enigma2/cineview_mla/backup 2>/dev/null | tr '\n' ' ')\""; }
run() { local name=$1; shift; echo; echo "################ $name"; $R "cd $T; $* sh $T/cineview-install.sh 2>&1; echo \"exit=\$?\"" | sed -E 's/\x1b\[[0-9;]*m//g' | tee $S/$name.txt; }
alive() { for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && return 0; sleep 3; done; return 1; }
newgui() { local o=$1; for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done; alive && sleep 30; echo "   GUI pid $o -> $p, webif $(alive && echo up || echo DOWN), crash logs today: $($R 'ls /home/root/logs | grep -i crash | grep -c 2026-10-08')"; }
ib() { for i in 1 2 3; do ~/cineview-mla/rc.sh 174; sleep 0.5; done; ~/cineview-mla/rc.sh 352; sleep 2; curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ~/cineview-mla/rc.sh 174; }
echo "== start"; state | tee $S/state_start.txt
OV="CVMLA_PKG_URL=$T/$(basename $P1) CVMLA_PKG_SHA=$SHA1"
run I1_default_not_released ""
run I1b_dryrun "DRYRUN=1 $OV"
run N1_info_openatv "DRYRUN=1 $OV CVMLA_INFO=$T/atv.info"
run N2_info_openbh "DRYRUN=1 $OV CVMLA_INFO=$T/bh.info"
run N3_info_nodistro "DRYRUN=1 $OV CVMLA_INFO=$T/nodistro.info"
run N4_info_vix68 "DRYRUN=1 $OV CVMLA_INFO=$T/vix68.info"
run N5_info_vix70 "DRYRUN=1 $OV CVMLA_INFO=$T/vix70.info"
run N6_info_othermodel "DRYRUN=1 $OV CVMLA_INFO=$T/othermodel.info"
run N7_info_missing "DRYRUN=1 $OV CVMLA_INFO=$T/none.info"
echo; echo "== state after the check-only and refusal runs (must equal the start)"; state | tee $S/state_after_N.txt
run I2_same_version "$OV"
run I3_sha_mismatch "CVMLA_PKG_URL=$T/$(basename $P2) CVMLA_PKG_SHA=$SHA1 CVMLA_VERSION=1.0.0~openvix2"
state | tee $S/state_after_I3.txt
o=$($R pidof enigma2)
run I4_upgrade_restart "RESTART=1 CVMLA_PKG_URL=$T/$(basename $P2) CVMLA_PKG_SHA=$SHA2 CVMLA_VERSION=1.0.0~openvix2"
newgui $o; state | tee $S/state_after_I4.txt; ib I4_infobar
run I5_shell_crash_twice "FORCE=1 CVMLA_PKG_URL=$T/crash_test.ipk CVMLA_PKG_SHA=$SHAC CVMLA_VERSION=1.0.0~openvix2"
state | tee $S/state_after_I5.txt
run I6_repair "CVMLA_PKG_URL=$T/$(basename $P2) CVMLA_PKG_SHA=$SHA2 CVMLA_VERSION=1.0.0~openvix2"
state | tee $S/state_after_I6.txt
o=$($R pidof enigma2)
run I7_return_to_openvix1 "FORCE=1 RESTART=1 $OV"
newgui $o; state | tee $S/state_after_I7.txt; ib I7_infobar
echo; echo "################ I8_uninstall (MLA selected)"
o=$($R pidof enigma2)
$R "sh $T/cineview-uninstall.sh 2>&1; echo exit=\$?" | tee $S/I8_uninstall.txt
newgui $o; state | tee $S/state_after_I8.txt
$R "ls -d /usr/share/enigma2/CineView_FHD_MLA /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA 2>&1; ls /etc/enigma2/cineview_mla" | tee -a $S/state_after_I8.txt
curl -s -m 60 -o $S/I8_after_uninstall.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"
run I9_fresh_install "$OV"
o=$($R pidof enigma2)
$R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; grep -q '^config.skin.primary_skin=' /etc/enigma2/settings && sed -i 's#^config.skin.primary_skin=.*#config.skin.primary_skin=CineView_FHD_MLA/skin.xml#' /etc/enigma2/settings || echo config.skin.primary_skin=CineView_FHD_MLA/skin.xml >> /etc/enigma2/settings; init 3"
newgui $o; state | tee $S/state_after_I9.txt; ib I9_infobar
run I9b_verify_same "$OV"
echo; echo "################ I10 preinst x100"
$R 'P=/var/lib/opkg/info/enigma2-plugin-skins-cineview-fhd-mla.preinst; head -2 $P | tail -1 | cut -c1-70; rm -f /tmp/cvmla-it/preinst_runs.txt; t0=$(date +%s); for i in $(seq 1 100); do $P upgrade >/dev/null 2>&1; echo "$i $?" >> /tmp/cvmla-it/preinst_runs.txt; done; t1=$(date +%s); echo "runs recorded: $(wc -l < /tmp/cvmla-it/preinst_runs.txt), seconds: $((t1 - t0))"; echo "exit codes:"; cut -d" " -f2 /tmp/cvmla-it/preinst_runs.txt | sort | uniq -c; echo "crashes (exit >= 128): $(awk "\$2 >= 128" /tmp/cvmla-it/preinst_runs.txt | wc -l)/100"' | tee $S/I10_preinst100.txt
$R "cat $T/preinst_runs.txt" > $S/I10_preinst_runs.txt
echo; echo "== end"; state | tee $S/state_end.txt
$R "rm -rf $T"
echo T109V_DONE
