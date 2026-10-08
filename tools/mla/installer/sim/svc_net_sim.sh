#!/bin/bash
# Smart Installer 1.2.1 (service mode): download, certificate and cleanup behaviour against the reference service
# over HTTPS (test CA via SSL_CERT_FILE).  CVMLA_FETCH_ONLY=1: download + SHA256 only, nothing installed.
INST=$(readlink -f "${1:?installer}"); H=$(cd "$(dirname "$0")" && pwd); W=$H/work; SV=$H/../svc
[ -d "$W/atv" ] || { echo "run svc_sim.sh first"; exit 2; }
python3 $SV/cvmla_dist.py --catalog $SV/catalog.json --store $SV/store --secret-file $SV/secret --port 18443 --bind 127.0.0.1 \
	--cert $SV/tls/srv.crt --key $SV/tls/srv.key --test-faults 2>$W/service.log & SRV=$!
python3 $SV/cvmla_dist.py --catalog $SV/catalog.json --store $SV/store --secret-file $SV/secret --port 18444 --bind 127.0.0.1 \
	--cert $SV/tls/bad.crt --key $SV/tls/bad.key 2>$W/service_bad.log & BAD=$!
python3 $SV/cvmla_dist.py --catalog $SV/catalog.json --store $SV/store --secret-file $SV/secret --port 18445 --bind 127.0.0.1 \
	--cert $SV/tls/srv.crt --key $SV/tls/srv.key --ttl -10 2>$W/service_exp.log & EXP=$!
sleep 2; trap 'kill $SRV $BAD $EXP 2>/dev/null' EXIT
N=0; NP=0; NF=0
inst() {  # inst <service> <ca> [VAR=value ...]
	local svc=$1 ca=$2; shift 2
	env -i PATH="${PYBIN:+$PYBIN:}$W/bin:/usr/bin:/bin" HOME=/tmp CVMLA_ROOT=$W/atv CVMLA_PYV=3.14 FAKE_CUR=1.0.0 CVMLA_FETCH_ONLY=1 CVMLA_TIMEOUT=10 \
		CVMLA_SERVICE=$svc ${ca:+SSL_CERT_FILE=$ca} "$@" sh "$INST" 2>&1
}
check() {  # check <id> <expect> <output> [extra condition result]
	local id=$1 exp=$2 out=$3 extra=${4:-0}
	local got; got=$(echo "$out" | grep -m1 -o "fetch-only test: package downloaded and verified\|failed the SHA256 check\|not available from the CineView MLA service\|could not be downloaded\|could not be verified (HTTPS certificate)\|service cannot be reached\|service is not available yet")
	local left; left=$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l)
	N=$((N+1))
	if echo "$got" | grep -qF "$exp" && [ "$left" = 0 ] && [ "$extra" = 0 ] && ! echo "$out" | grep -qi "clean\|temporary\|removing\|deleting"; then
		NP=$((NP+1)); printf 'PASS  %-24s retries=%s -> %s\n' "$id" "$(echo "$out" | grep -c 'trying again')" "$got"
	else
		NF=$((NF+1)); printf 'FAIL  %-24s expected [%s] got [%s] leftovers=%s extra=%s\n' "$id" "$exp" "$got" "$left" "$extra"; echo "$out" | tail -6 | sed 's/^/      | /'
	fi
}
OK=https://127.0.0.1:18443; CA=$SV/tls/ca.crt
for f in none slow drop stall norange corruptonce flaky; do
	out=$(inst $OK $CA CVMLA_SVC_QUERY=fault=$f); check "fault:$f" "downloaded and verified" "$out"
done
out=$(inst $OK $CA CVMLA_SVC_QUERY=fault=corrupt); check "fault:corrupt" "failed the SHA256 check" "$out"
out=$(inst $OK $CA CVMLA_SVC_QUERY=fault=dead);    check "fault:dead" "could not be downloaded" "$out"
out=$(inst $OK $CA CVMLA_SVC_QUERY=fault=gone);    check "link expired -> new link" "downloaded and verified" "$out"
out=$(inst https://127.0.0.1:18445 $CA);           check "link always expired" "not available from the CineView MLA service" "$out"
out=$(inst https://127.0.0.1:18799 $CA);           check "service down" "service cannot be reached" "$out"
out=$(inst "" "");                                 check "no service configured" "service is not available yet" "$out"
# certificates: never bypassed.  Untrusted certificate -> the image's ca-certificates are updated once, then a clear stop
rm -f $W/opkg.calls
out=$(inst https://127.0.0.1:18444 $CA); c=0; grep -q "^install ca-certificates" $W/opkg.calls 2>/dev/null || c=1
check "untrusted certificate" "could not be verified (HTTPS certificate)" "$out" $c
echo "      (opkg calls: $(tr '\n' ';' < $W/opkg.calls 2>/dev/null))"
out=$(inst $OK "");                                check "test CA not trusted (system CAs)" "could not be verified (HTTPS certificate)" "$out"
grep -q "no-check-certificate\|CERT_NONE\|_create_unverified_context\|check_hostname *= *False" "$INST" && { NF=$((NF+1)); echo "FAIL  a certificate bypass exists in the installer"; } || { NP=$((NP+1)); echo "PASS  no certificate bypass anywhere in the installer"; }; N=$((N+1))
# interrupted / killed / concurrent
for sig in INT HUP; do
	inst $OK $CA CVMLA_SVC_QUERY=fault=slow > $W/sig.out & P=$!; sleep 4; pkill -$sig -f "^sh $INST" ; wait $P 2>/dev/null; sleep 1
	left=$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l); N=$((N+1))
	[ "$left" = 0 ] && { NP=$((NP+1)); echo "PASS  $sig during download: nothing left"; } || { NF=$((NF+1)); echo "FAIL  $sig: $left left"; }
done
inst $OK $CA CVMLA_SVC_QUERY=fault=slow > $W/kill.out & P=$!; sleep 4; pkill -9 -f "^sh $INST"; pkill -9 -f "cvsvc.py fetch"; sleep 1
before=$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l)
out=$(inst $OK $CA); check "next run after kill -9" "downloaded and verified" "$out"
echo "      (leftovers after kill -9: $before -> after the next run: $(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l))"
inst $OK $CA CVMLA_SVC_QUERY=fault=slow > $W/first.out & P=$!; sleep 3
second=$(inst $OK $CA | grep -o "Another CineView MLA installation is running"); wait $P; N=$((N+1))
if [ -n "$second" ] && grep -q "downloaded and verified" $W/first.out && [ "$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l)" = 0 ]; then
	NP=$((NP+1)); echo "PASS  second installer refused while the first runs; first completed; nothing left"
else NF=$((NF+1)); echo "FAIL  concurrency ($second)"; fi
echo "SVC NET TOTAL $N  PASS $NP  FAIL $NF"
