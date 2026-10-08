#!/bin/bash
# Download behaviour of the installer (CVMLA_FETCH_ONLY=1: download + SHA256 only, nothing installed) against a
# faulty test server, with GNU wget and BusyBox wget; temporary files and the lock must be gone after every run.
INST=$(readlink -f "${1:?installer}")
H=$(cd "$(dirname "$0")" && pwd); W=$H/work
[ -d "$W/atv" ] || { echo "run run_sim.sh first"; exit 2; }
mkdir -p $W/bb && ln -sf /usr/bin/busybox $W/bb/wget
python3 $H/netserver.py $H/../dist 18765 2>$W/server.log & SRV=$!; sleep 1; kill -0 $SRV 2>/dev/null || { echo "test server did not start"; cat $W/server.log; exit 2; }
N=0; NP=0; NF=0
one() {  # one <variant gnu|bb> <mode> <expect>
	local v=$1 m=$2 exp=$3 P="$W/bin:/usr/bin:/bin"; [ $v = bb ] && P="$W/bb:$W/bin:/usr/bin:/bin"
	local t0=$(date +%s)
	local out; out=$(env -i PATH="$P" HOME=/tmp CVMLA_ROOT=$W/atv CVMLA_PYV=3.14 FAKE_CUR=1.0.0 CVMLA_FETCH_ONLY=1 CVMLA_TIMEOUT=10 \
		CVMLA_DIST_BASE=$( [ $m = refused ] && echo http://127.0.0.1:18799/x || echo http://127.0.0.1:18765/$m-$v ) sh "$INST" 2>&1)
	local dt=$(( $(date +%s) - t0 )) left=$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l)
	local got; got=$(echo "$out" | grep -m1 -o "fetch-only test: package downloaded and verified\|failed the SHA256 check\|not found at the distribution point\|could not be downloaded")
	local retries=$(echo "$out" | grep -c "trying again")
	N=$((N+1))
	if echo "$got" | grep -qF "$exp" && [ "$left" = 0 ] && ! echo "$out" | grep -qi "clean\|temporary\|removing"; then
		NP=$((NP+1)); printf 'PASS  %-4s %-12s %3ss retries=%s -> %s\n' $v $m $dt $retries "$got"
	else
		NF=$((NF+1)); printf 'FAIL  %-4s %-12s expected [%s] got [%s] leftovers=%s\n' $v $m "$exp" "$got" $left; echo "$out" | tail -8 | sed 's/^/      | /'
	fi
}
for v in gnu bb; do
	one $v ok "verified"; one $v slow "verified"; one $v drop "verified"; one $v stall "verified"
	one $v dropnorange "verified"; one $v corruptonce "verified"; one $v flaky "verified"
	one $v corrupt "failed the SHA256 check"; one $v 404 "not found at the distribution point"; one $v dead "could not be downloaded"; one $v refused "could not be downloaded"
done
# interrupted by the user (Ctrl-C / lost session): temporary files removed
for sig in INT HUP; do
	env -i PATH="$W/bin:/usr/bin:/bin" HOME=/tmp CVMLA_ROOT=$W/atv CVMLA_PYV=3.14 FAKE_CUR=1.0.0 CVMLA_FETCH_ONLY=1 \
		CVMLA_DIST_BASE=http://127.0.0.1:18765/slow-sig$sig sh "$INST" > $W/sig$sig.out 2>&1 & P=$!
	sleep 4; kill -$sig $P; wait $P 2>/dev/null; sleep 1; pkill -f "slow-sig$sig" 2>/dev/null
	left=$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l); N=$((N+1))
	[ "$left" = 0 ] && { NP=$((NP+1)); echo "PASS  $sig during download: no temporary files or lock left"; } || { NF=$((NF+1)); echo "FAIL  $sig: $left leftovers"; ls -d /tmp/.cvmla.*; }
done
# killed hard (power loss / kill -9): leftovers are removed silently by the next run
env -i PATH="$W/bin:/usr/bin:/bin" HOME=/tmp CVMLA_ROOT=$W/atv CVMLA_PYV=3.14 FAKE_CUR=1.0.0 CVMLA_FETCH_ONLY=1 \
	CVMLA_DIST_BASE=http://127.0.0.1:18765/slow-kill sh "$INST" > $W/kill.out 2>&1 & P=$!
sleep 4; kill -9 $P; sleep 1; pkill -f "slow-kill" 2>/dev/null; before=$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l)
one gnu ok-afterkill "verified"
echo "      (leftovers after kill -9: $before -> after the next run: $(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l))"
# a second installer while one is running: refused, the running one is not disturbed
env -i PATH="$W/bin:/usr/bin:/bin" HOME=/tmp CVMLA_ROOT=$W/atv CVMLA_PYV=3.14 FAKE_CUR=1.0.0 CVMLA_FETCH_ONLY=1 \
	CVMLA_DIST_BASE=http://127.0.0.1:18765/slow-first sh "$INST" > $W/first.out 2>&1 & P=$!
sleep 3
second=$(env -i PATH="$W/bin:/usr/bin:/bin" HOME=/tmp CVMLA_ROOT=$W/atv CVMLA_PYV=3.14 FAKE_CUR=1.0.0 CVMLA_FETCH_ONLY=1 \
	CVMLA_DIST_BASE=http://127.0.0.1:18765/ok-second sh "$INST" 2>&1 | grep -o "Another CineView MLA installation is running")
wait $P; N=$((N+1))
if [ -n "$second" ] && grep -q "downloaded and verified" $W/first.out && [ "$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l)" = 0 ]; then
	NP=$((NP+1)); echo "PASS  second installer refused while the first runs; the first completed; nothing left"
else NF=$((NF+1)); echo "FAIL  concurrency: second='$second'"; tail -3 $W/first.out; fi
kill $SRV
echo "NET TOTAL $N  PASS $NP  FAIL $NF"
