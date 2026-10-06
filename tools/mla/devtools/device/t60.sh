#!/bin/bash
# Performance retest after the new designs (user decision 2026-10-05 05:23, accelAlloc accepted only while there is
# no picture loss, no memory leak and no noticeable slowdown).  build52, Modern model on every section it has
# (InfoBar, SIB, Channel Selection, EPG, EventView): 25-min soak of mixed navigation (channel list fast/slow +
# EventView, SecondInfoBar, Graphical EPG open/move/close) with samples every ~3 min (RSS, peak RSS, threads, fds,
# CPU, poster cache, /tmp, accelAlloc failures, tracebacks); then the same 10 min with Classic as the baseline.
# Restore: Classic, navy.
exec 9>~/cineview-mla/t60.lock; flock -n 9 || { echo "t60 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build52}
S=~/cineview-mla/shots/t60; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
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
navround_cs() {  # channel list fast/slow + EventView
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
navround() {
  navround_cs
  $RC 352; sleep 1.5; $RC 352; sleep 4; X; sleep 1.5
  op graph 7; for i in 1 2 3 4; do $RC 106; sleep 0.5; done; $RC 108; sleep 1; $RC 108; sleep 2; X; sleep 2; X; sleep 1.5
}
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
echo "== 1. Modern model: soak 25 min"
apply --theme navy --set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set eventview=modern; restart ""; errs
zap $HBO; X
soak modern 25; errs
echo "== 2. Classic baseline: 10 min"
apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set eventview=classic-lines; restart ""; errs
zap $HBO; X
soak classic 10; errs
$R "rm -rf $P"; restart ""; st; errs
echo T60_DONE
