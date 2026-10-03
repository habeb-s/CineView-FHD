#!/bin/bash
# P5 identity poster engine — device test (Slot 8, 16.0E only).  Engine opt-in via runtime.json.
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/p5; mkdir -p $S
CH="1:0:19:784:C6D4:16E:A00000:0:0:0:|HBO 1:0:19:786:C6D4:16E:A00000:0:0:0:|Cinemax 1:0:19:787:C6D4:16E:A00000:0:0:0:|Cinemax2 1:0:19:458:526C:16E:A00000:0:0:0:|EpicDrama 1:0:19:D49:C738:16E:A00000:0:0:0:|HRT1 1:0:19:D4A:C738:16E:A00000:0:0:0:|HRT2 1:0:16:123:3:40:A00000:0:0:0:|RTL 1:0:16:125:3:40:A00000:0:0:0:|RTL2 1:0:16:126:3:40:A00000:0:0:0:|Doma 1:0:1:6E8:C544:16E:A00000:0:0:0:|N1 1:0:1:8:CB2B:16E:A00000:0:0:0:|PinkMovies 1:0:1:7:CB2B:16E:A00000:0:0:0:|PinkAction"
ga() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; }
if [ "$1" = "enable" ]; then
  $R 'cp -p /etc/enigma2/cineview_mla/runtime.json /media/usb/cineview-mla/state/runtime.json.pre-p5 && python3 -c "
import json; p=\"/etc/enigma2/cineview_mla/runtime.json\"; d=json.load(open(p)); d[\"poster_engine\"]=\"identity\"; open(p+\".tmp\",\"w\").write(json.dumps(d)); import os; os.replace(p+\".tmp\",p)" && cat /etc/enigma2/cineview_mla/runtime.json'
  o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; init 3'; newe2 $o; sleep 30
  $R 'python3 /tmp/cvmla/plog.py engine= | tail -2'
fi
for pass in 1 2; do
 for c in $CH; do
  ref=${c%%|*}; n=${c##*|}
  curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ref"; sleep 9
  X; $RC 352; sleep 1; ga p${pass}_${n}_ib
  $RC 352; sleep $([ $pass = 1 ] && echo 12 || echo 4); ga p${pass}_${n}_sib
  X; $RC 358; sleep 4; ga p${pass}_${n}_ev; X
  t=$(curl -s -m 5 -o /dev/null -w "%{time_total}" "http://192.168.1.250/api/statusinfo"); echo "pass$pass $n webif=${t}s"
 done
done
$R 'top -bn1 | head -12; python3 /tmp/cvmla/plog.py identity' > $S/poster_identity_log.txt
$R 'cd /media/usb/cineview-mla/dev-cache/reference/poster/id 2>/dev/null && ls -la | head -80; cat *.json 2>/dev/null' > $S/cache_id.txt
echo P5_DONE
