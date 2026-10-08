#!/bin/bash
cd "$(dirname "$0")"
for s in dash bash "busybox sh"; do echo "== $s: $(SIMSH="$s" bash svc_sim.sh ../svc_dist_install.sh 2>&1 | tee svc_sim_$(echo $s|tr -d ' ').log | grep TOTAL)"; done
bash svc_net_sim.sh ../svc_dist_install.sh > svc_net_sim.log 2>&1; grep TOTAL svc_net_sim.log
PYBIN=$(cd ../py313shim && pwd) bash svc_net_sim.sh ../svc_dist_install.sh > svc_net_sim_py313.log 2>&1; grep TOTAL svc_net_sim_py313.log
echo DONE
