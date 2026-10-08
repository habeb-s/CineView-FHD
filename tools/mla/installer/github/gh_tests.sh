#!/bin/bash
cd "$(dirname "$0")"
echo "== decisions: $(SIMSH=sh bash run_sim.sh ../gh/cineview-install.sh 2>&1 | tee gh_sim.log | grep TOTAL)"
grep -q "Package source: CineView MLA distribution point" work/atv_8.0_fresh.out && echo "   (package source: distribution point)"
bash net_sim.sh ../gh/cineview-install.sh > gh_net.log 2>&1; grep "NET TOTAL" gh_net.log
# HTTPS certificate not trusted: one ca-certificates update from the image feed, then a clear stop - never a bypass
SV=../svc; W=work
python3 $SV/cvmla_dist.py --catalog $SV/catalog.json --store $SV/store --secret-file $SV/secret --port 18444 --bind 127.0.0.1 --cert $SV/tls/bad.crt --key $SV/tls/bad.key 2>/dev/null & B=$!; sleep 1.5
rm -f $W/opkg.calls
out=$(env -i PATH="$W/bin:/usr/bin:/bin" HOME=/tmp CVMLA_ROOT=$W/atv CVMLA_PYV=3.14 FAKE_CUR=1.0.0 CVMLA_FETCH_ONLY=1 CVMLA_TIMEOUT=10 CVMLA_DIST_BASE=https://127.0.0.1:18444 sh ../gh/cineview-install.sh 2>&1)
kill $B
echo "$out" | grep -q "could not be verified (HTTPS certificate)" && grep -q "install ca-certificates" $W/opkg.calls 2>/dev/null && [ "$(ls -d /tmp/.cvmla.* 2>/dev/null | wc -l)" = 0 ] && echo "PASS  untrusted certificate: ca-certificates update once, then stop (no bypass)" || { echo "FAIL cert"; echo "$out" | tail -5; cat $W/opkg.calls; }
