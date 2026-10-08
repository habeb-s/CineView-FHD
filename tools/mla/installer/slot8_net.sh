#!/bin/bash
# Installer 1.2.0 download behaviour on the real receiver (Slot 8, its own GNU wget 1.25) against the faulty test
# server on this PC.  CVMLA_FETCH_ONLY=1: download + SHA256 only - nothing is installed, Golden 1.0.0 is not touched.
cd ~/cineview-mla
R=~/cineview-mla/r.sh; F=final; L=$F/slot8net; rm -rf $L; mkdir -p $L
T=/tmp/cvmla-net; SRVURL=http://127.0.0.1:18765
# the PC's firewall does not accept connections from the receiver: the faulty test server runs on the receiver
# itself (its own Python, loopback, files in /tmp only) - the receiver's own wget is what is tested
$R 'grep -q "rootsubdir=linuxrootfs8" /proc/cmdline' || { echo "NOT Slot 8"; exit 1; }
echo "leftovers before (a run killed with SIGKILL): $($R 'ls -d /tmp/.cvmla.* 2>/dev/null | tr "\n" " "')"
$R "rm -rf $T; mkdir -p $T/dist/packages/openatv"
cat $F/sim/netserver.py | $R "cat > $T/netserver.py"
cat $F/dist/packages/openatv/enigma2-plugin-skins-cineview-fhd-mla_1.0.1_all.ipk | $R "cat > $T/dist/packages/openatv/enigma2-plugin-skins-cineview-fhd-mla_1.0.1_all.ipk"
$R "cd $T && (nohup python3 netserver.py $T/dist 18765 > $T/server.log 2>&1 &) ; sleep 2; wget -q -T 5 -t 1 -O /dev/null $SRVURL/ok-probe/packages/openatv/enigma2-plugin-skins-cineview-fhd-mla_1.0.1_all.ipk && echo server ok"
echo "golden before: $($R 'opkg status enigma2-plugin-skins-cineview-fhd-mla | grep ^Version')"
cat $F/dist/cineview-install.sh | $R "cat > $T/cineview-install.sh"
N=0; NP=0; NF=0
one() {  # one <mode> <expect>
	local m=$1 exp=$2 t0=$(date +%s)
	$R "CVMLA_FETCH_ONLY=1 CVMLA_TIMEOUT=10 CVMLA_DIST_BASE=$SRVURL/$m-r8 sh $T/cineview-install.sh" > $L/$m.out 2>&1
	local dt=$(( $(date +%s) - t0 ))
	local got=$(grep -m1 -o "fetch-only test: package downloaded and verified\|failed the SHA256 check\|not found at the distribution point\|could not be downloaded" $L/$m.out)
	local left=$($R 'ls -d /tmp/.cvmla.* 2>/dev/null | wc -l')
	N=$((N+1))
	if echo "$got" | grep -qF "$exp" && [ "$left" = 0 ]; then NP=$((NP+1)); printf 'PASS  %-12s %3ss retries=%s -> %s\n' $m $dt "$(grep -c 'trying again' $L/$m.out)" "$got"
	else NF=$((NF+1)); printf 'FAIL  %-12s expected [%s] got [%s] leftovers=%s\n' $m "$exp" "$got" $left; tail -6 $L/$m.out | sed 's/^/      | /'; fi
}
one ok verified; one slow verified; one drop verified; one stall verified; one dropnorange verified
one corruptonce verified; one flaky verified; one corrupt "failed the SHA256 check"; one 404 "not found"; one dead "could not be downloaded"
# hard kill (kill -9, as a power loss would leave it) during a download, then a normal run: leftovers cleaned silently
$R "(CVMLA_FETCH_ONLY=1 CVMLA_DIST_BASE=$SRVURL/slow-kill sh $T/cineview-install.sh > $T/kill.out 2>&1 &); sleep 4; kill -9 \$(cat /tmp/.cvmla.lock/pid) \$(pidof wget) 2>/dev/null; sleep 1"
echo "after kill -9: $($R 'ls -d /tmp/.cvmla.* 2>/dev/null | tr "\n" " "')"
one ok-afterkill verified
$R "DRYRUN=1 sh $T/cineview-install.sh" > $L/dryrun.out 2>&1; grep -E "^\s+\[(OK|!!|\.\.|XX)\]|All checks" $L/dryrun.out | head -20
$R "kill \$(pgrep -f 'python3 netserver.py') 2>/dev/null; sleep 1; rm -rf $T; ls -d /tmp/.cvmla.* /tmp/cvmla-net 2>&1 | head -3"
echo "golden after: $($R 'opkg status enigma2-plugin-skins-cineview-fhd-mla | grep ^Version')"
$R "ls /etc/enigma2/cineview_mla/backup" > $L/restorepoints_after.txt
echo "SLOT8 NET TOTAL $N  PASS $NP  FAIL $NF"
