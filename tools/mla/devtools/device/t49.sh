#!/bin/bash
# Truly UNCACHED posters at 0.15 s on MOVIE rows (t44 page 2 were kids series = placeholders only) (§3c), Poster List, Slot 8: CineView's own runtime.json poster_cache is pointed at a NEW EMPTY
# directory on USB (dev cache), so every row's identity lookup + download happens live while the cursor moves.
# Network / system settings are NOT touched (no throttling: slower networks cannot be simulated without changing the
# network, which is out of bounds); downloads that finish after the cursor has left are exercised naturally.
#  cold page 1 (HBO movie rows): very fast 0.15 s down 8 + hold + up 8 + hold -> later slow reference (same rows)
#  runs after t48, i.e. on build41 (poster.log one entry per line -> identity lookups countable)
#  postercheck(slow, fast) = valid method (reference = settled frames of the SAME rows); poster.log of the cold run.
# Restore: runtime.json from the backup, cold cache removed, Classic channel selection, posters on.
exec 9>~/cineview-mla/t49.lock; flock -n 9 || { echo "t49 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t49; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
COLD=/media/usb/cineview-mla/dev-cache/t49cold/poster
RT=/etc/enigma2/cineview_mla/runtime.json
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
recstart() { $R "nohup sh /tmp/cvmla/grabloop.sh $1 /tmp/cvmla/rec >/dev/null 2>&1 &"; sleep 1; }
recget() { sleep 2; $R 'for i in $(seq 1 90); do [ -f /tmp/cvmla/rec.done ] && break; sleep 1; done; cd /tmp/cvmla && tar -cf - rec' | tar -C $S -xf - && mv $S/rec $S/rec_$1; $R 'rm -rf /tmp/cvmla/rec /tmp/cvmla/rec.done'; echo "   $1 recorded $(ls $S/rec_$1 | wc -l) frames"; }
$R 'cat > /tmp/cvmla/grabloop.sh' <<'SH'
#!/bin/sh
end=$(( $(date +%s) + $1 )); rm -rf $2; mkdir -p $2
rm -f $2.done
while [ $(date +%s) -lt $end ]; do grab -q -j 75 -r 1280 $2/$(date +%s%N).jpg; done
touch $2.done
SH
$R "cp $RT /tmp/cvmla/runtime.json.t49bak && cp $RT /media/usb/cineview-mla/state/runtime.json.t49bak && echo runtime-backed-up"
$R "$E apply --set channelselection=posterlist 2>&1 | tail -1"
restart "mkdir -p $COLD && python3 -c \"import json; p='$RT'; d=json.load(open(p)); d['poster_cache']='$COLD'; json.dump(d, open(p,'w'), indent=1, sort_keys=True)\" && echo cold-cache-set;"
errs; $R "grep poster_cache $RT; ls $COLD | wc -l; : > /tmp/CINEVIEW-MLA/poster.log 2>/dev/null; true"
echo "== cold page 1 (HBO movie rows): very fast 0.15 s down 8, hold, up 8, hold"
zap $HBO; X; recstart 30; $RC 108; sleep 4; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 0.15; done; sleep 7; for i in 1 2 3 4 5 6 7 8; do $RC 103; sleep 0.15; done; sleep 7; X; recget cold1_vfast
$R 'cat /tmp/CINEVIEW-MLA/poster.log' > $S/poster_log_cold.txt; echo "   identity lines: $(grep -c 'identity key' $S/poster_log_cold.txt)  matches: $(grep -c -- '-> match' $S/poster_log_cold.txt)  cold files now: $($R "find $COLD -type f | wc -l")"
echo "== slow references (same rows, now cached)"
zap $HBO; X; recstart 44; $RC 108; sleep 4; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 4; done; sleep 2; X; recget slow1
echo "   cold1_vfast $(python3 ~/cineview-mla/postercheck.py $S/rec_slow1 $S/rec_cold1_vfast | tail -1)"
python3 ~/cineview-mla/postercheck.py $S/rec_slow1 $S/rec_cold1_vfast > $S/check_cold1.txt 2>&1
errs
echo "== restore"
$R "$E apply --set channelselection=classic 2>&1 | tail -1"
restart "cp /tmp/cvmla/runtime.json.t49bak $RT && rm -rf /media/usb/cineview-mla/dev-cache/t49cold && echo runtime-restored;"
$R "grep poster_cache $RT"; st; errs
echo T49_DONE
