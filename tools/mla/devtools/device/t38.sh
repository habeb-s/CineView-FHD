#!/bin/bash
# Soak + poster behaviour (Slot 8, build35), autonomous order 2026-10-04 22:06 §3c/§3f:
#  1. Poster List, posters ON: 60 s fast-navigation recording (start), 30 min continuous navigation with samples
#     every ~3 min (RSS, peak RSS, threads, open fds, CPU, poster cache files/size, /tmp/CINEVIEW-MLA, accel fails),
#     60 s recording at the end (degradation check: same lag/postercheck metrics).
#  2. Uncached posters: page down to channels not visited before, step while posters download, hold; recording.
#  3. Same 10-min navigation with Channel Selection posters OFF, and with the Classic design (baselines).
#  restore: Classic, posters on.
exec 9>~/cineview-mla/t38.lock; flock -n 9 || { echo "t38 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t38; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
apply() { $R "$E apply $* 2>&1 | tail -1"; }
sample() {  # $1 label
  $R 'p=$(pidof enigma2); set -- $(cut -d" " -f14,15 /proc/$p/stat); cpu=$(( ($1 + $2) * 10 ));
      rss=$(grep VmRSS /proc/$p/status | tr -s " " | cut -d" " -f2); hwm=$(grep VmHWM /proc/$p/status | tr -s " " | cut -d" " -f2);
      thr=$(grep Threads /proc/$p/status | tr -s "\t " " " | cut -d" " -f2); fds=$(ls /proc/$p/fd | wc -l);
      pc=$(python3 -c "import json; print(json.load(open(\"/etc/enigma2/cineview_mla/runtime.json\")).get(\"poster_cache\",\"/media/usb/cineview-mla/dev-cache/mla/poster\"))"); files=$(find $pc -type f 2>/dev/null | wc -l); kb=$(du -sk $pc 2>/dev/null | cut -f1);
      tmp=$(du -sk /tmp/CINEVIEW-MLA 2>/dev/null | cut -f1); f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1);
      echo "$(date +%T) cpu_ms=$cpu rss_kB=$rss hwm_kB=$hwm threads=$thr fds=$fds cache_files=$files cache_kB=$kb tmp_kB=$tmp accel_fails=$(grep -a -c "accelAlloc failed" $f) tb=$(grep -a -c Traceback $f)"' | sed "s/^/   [$1] /"
}
navround() {  # one round of mixed-speed navigation in the open-and-close channel list + EventView
  $RC 108; sleep 3
  for i in $(seq 1 10); do $RC 108; sleep 0.35; done
  for i in $(seq 1 10); do $RC 103; sleep 0.15; done
  for i in $(seq 1 12); do $RC 108; sleep 0.6; done
  sleep 2; X; $RC 358; sleep 4; X
}
soak() {  # $1 label, $2 minutes
  local end=$(( $(date +%s) + $2 * 60 )) next=0 r=0
  sample "$1 start"
  while [ $(date +%s) -lt $end ]; do
    navround; r=$((r + 1))
    if [ $(date +%s) -ge $next ]; then [ $r -gt 1 ] && sample "$1 r$r"; next=$(( $(date +%s) + 180 )); fi
  done
  sample "$1 end r$r"
}
recwin() {  # $1 tag: 60 s fast navigation recording (grab loop on the receiver)
  $R "nohup sh /tmp/cvmla/grabloop.sh 50 /tmp/cvmla/rec >/dev/null 2>&1 &"; sleep 1
  $RC 108; sleep 4; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 0.35; done; sleep 6; for i in 1 2 3 4 5 6 7 8; do $RC 103; sleep 0.15; done; sleep 6
  for i in 1 2 3 4 5 6; do $RC 108; sleep 1.2; done; sleep 5; X
  sleep 2; $R 'for i in $(seq 1 90); do [ -f /tmp/cvmla/rec.done ] && break; sleep 1; done; cd /tmp/cvmla && tar -cf - rec' | tar -C $S -xf - && mv $S/rec $S/rec_$1; $R 'rm -rf /tmp/cvmla/rec /tmp/cvmla/rec.done'
  echo "   $1 recorded $(ls $S/rec_$1 | wc -l) frames"
}
$R 'cat > /tmp/cvmla/grabloop.sh' <<'SH'
#!/bin/sh
end=$(( $(date +%s) + $1 )); rm -rf $2; mkdir -p $2
rm -f $2.done
while [ $(date +%s) -lt $end ]; do grab -q -j 75 -r 1280 $2/$(date +%s%N).jpg; done
touch $2.done
SH

echo "== 1. Poster List, posters ON: soak 30 min"
apply --set channelselection=posterlist; restart ""; errs
zap $HBO; X
recwin start
soak posterlist_on 30
recwin end
for r in start end; do echo "   $r $(python3 ~/cineview-mla/postercheck.py $S/rec_start $S/rec_$r 2>/dev/null | tail -1)"; echo "   $r $(python3 ~/cineview-mla/lagcheck.py $S/rec_$r 300,560,70,560 680,92,1000,122 48,50,63 | tail -1)"; done
errs

echo "== 2. uncached posters (pages not visited)"
zap $HBO; X
$R "nohup sh /tmp/cvmla/grabloop.sh 45 /tmp/cvmla/rec >/dev/null 2>&1 &"; sleep 1
$RC 108; sleep 3; for i in 1 2 3; do $RC 106; sleep 0.3; done; sleep 1
for i in 1 2 3 4 5 6 7 8 9 10; do $RC 108; sleep 0.35; done; sleep 8; for i in 1 2 3 4 5; do $RC 103; sleep 0.15; done; sleep 8
for i in 1 2 3; do $RC 108; sleep 3; done; X
sleep 2; $R 'for i in $(seq 1 90); do [ -f /tmp/cvmla/rec.done ] && break; sleep 1; done; cd /tmp/cvmla && tar -cf - rec' | tar -C $S -xf - && mv $S/rec $S/rec_uncached; $R 'rm -rf /tmp/cvmla/rec /tmp/cvmla/rec.done'
echo "   uncached recorded $(ls $S/rec_uncached | wc -l) frames  $(python3 ~/cineview-mla/postercheck.py $S/rec_start $S/rec_uncached 2>/dev/null | tail -1)"
$R 'tail -40 /tmp/CINEVIEW-MLA/poster.log' > $S/poster_log_tail.txt

echo "== 3a. baseline: Poster List, Channel Selection posters OFF, 10 min"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=False;"; errs
zap $HBO; X; soak posterlist_off 10
echo "== 3b. baseline: Classic, posters ON, 10 min"
apply --set channelselection=classic
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=True;"; errs
zap $HBO; X; soak classic_on 10
errs
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings"
echo T38_DONE
