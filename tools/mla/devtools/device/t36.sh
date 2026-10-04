#!/bin/bash
# build34 poster regression (ePicLoad at widget size): Classic InfoBar, SIB, EventView, Channel list, default EPG.
exec 9>~/cineview-mla/t36.lock; flock -n 9 || exit 1
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t36; rm -rf $S; mkdir -p $S
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
for ch in "1:0:19:784:C6D4:16E:A00000:0:0:0:|hbo" "1:0:19:786:C6D4:16E:A00000:0:0:0:|cinemax"; do
  ref=${ch%%|*}; n=${ch##*|}
  curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ref"; sleep 8; X
  $RC 352; sleep 2; ga ${n}_infobar; $RC 352; sleep 2.5; ga ${n}_sib; X
  $RC 358; sleep 5; ga ${n}_eventview; X
  $RC 108; sleep 5; ga ${n}_chsel; X
  $RC 365; sleep 7; ga ${n}_epg; X
done
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "tracebacks=$(grep -a -c Traceback $f) accel_fails=$(grep -a -c "accelAlloc failed" $f) picload_fallback=$(grep -a -c "picload fallback" /tmp/CINEVIEW-MLA/poster.log 2>/dev/null)"'
echo T36_DONE
