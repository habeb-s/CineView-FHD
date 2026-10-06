#!/bin/bash
# Modern accelAlloc: "Large" (build63, as measured in t60: 639 failures / 25 min) vs "Optimized" (build64: no
# default-poster PNG pinned in the 5400 kB accelerated pool, poster widgets release their picture when empty).
# Identical 25-min soak for each: Modern on all six sections, navy, posters ON; each round = channel list fast/slow
# + EventView, SecondInfoBar, Graphical EPG open/move/close, EMC (PVR key path, USB test folder only) open/move/close,
# and a channel change (HBO HD / HRT1).  Samples every ~3 min: RSS, peak RSS, threads, fds, CPU, accelAlloc
# failures, tracebacks.  Then Optimized only: posters OFF 8 min, green and burgundy 5 min each, and grabs of every
# section for the visual check.  Nothing is played, deleted or moved; the HDD is not opened.
# Restore: Classic on every section, navy, posters ON, movielist folder as before.
exec 9>~/cineview-mla/t67.lock; flock -n 9 || { echo "t67 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
LARGE=${1:-build63}; OPT=${2:-build64}
S=~/cineview-mla/shots/t67; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accel=$(grep -a -c "accelAlloc failed" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|release:" $f | grep -v "progressPercentWidth\|piconMargin" | tail -4 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep ${2:-8}; }
ap() { local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | sed "s/^/   apply: /"; echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"; }
MODERN="--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern"
CLASSIC="--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines"
sample() {
  $R 'p=$(pidof enigma2); set -- $(cut -d" " -f14,15 /proc/$p/stat); cpu=$(( ($1 + $2) * 10 ));
      rss=$(grep VmRSS /proc/$p/status | tr -s " " | cut -d" " -f2); hwm=$(grep VmHWM /proc/$p/status | tr -s " " | cut -d" " -f2);
      thr=$(grep Threads /proc/$p/status | tr -s "\t " " " | cut -d" " -f2); fds=$(ls /proc/$p/fd | wc -l);
      f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1);
      echo "$(date +%T) cpu_ms=$cpu rss_kB=$rss hwm_kB=$hwm threads=$thr fds=$fds accel_fails=$(grep -a -c "accelAlloc failed" $f) tb=$(grep -a -c Traceback $f)"' | sed "s/^/   [$1] /"
}
round() {
  zap $([ $(( RANDOM % 2 )) -eq 0 ] && echo $HBO || echo $HRT1) 6; X
  $RC 108; sleep 3
  for i in $(seq 1 10); do $RC 108; sleep 0.35; done
  for i in $(seq 1 10); do $RC 103; sleep 0.15; done
  for i in $(seq 1 12); do $RC 108; sleep 0.6; done
  sleep 2; X; $RC 358; sleep 4; X
  $RC 352; sleep 1.5; $RC 352; sleep 4; X; sleep 1.5
  op graph 7; for i in 1 2 3 4; do $RC 106; sleep 0.5; done; $RC 108; sleep 1; $RC 108; sleep 2; X; sleep 2; X; sleep 1.5
  op movies 8; for i in 1 2 3; do $RC 108; sleep 1.5; done; X; sleep 3
}
soak() {  # $1 label, $2 minutes
  local end=$(( $(date +%s) + $2 * 60 )) next=0 r=0
  sample "$1 start"
  while [ $(date +%s) -lt $end ]; do
    round; r=$((r + 1))
    if [ $(date +%s) -ge $next ]; then [ $r -gt 1 ] && sample "$1 r$r"; next=$(( $(date +%s) + 180 )); fi
  done
  sample "$1 end r$r"
}
shots() {  # $1 tag: every Modern section once (live grabs)
  zap $HBO; X; $RC 352; sleep 4; ga ib_$1; X; sleep 2
  $RC 352; sleep 1.5; $RC 352; sleep 4; ga sib_$1; X; sleep 2
  $RC 108; sleep 4; $RC 108; sleep 3; ga cs_$1; X; sleep 2
  op graph 7; $RC 106; sleep 3; ga epg_$1; X; sleep 2; X; sleep 2
  $RC 358; sleep 5; ga ev_$1; X; sleep 2
  op movies 8; $RC 108; sleep 3; $RC 108; sleep 3; $RC 108; sleep 4; ga emc_$1; $RC 108; sleep 4; ga emc_$1_generic; X; sleep 3
  zap $HRT1; X; $RC 358; sleep 5; ga ev_$1_hrt; X; sleep 2
}
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
for v in large opt; do
  B=$([ $v = large ] && echo $LARGE || echo $OPT)
  echo "== $v ($B): Modern, navy, posters ON — 25 min"
  ~/cineview-mla/deploy_b.sh $B
  cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
  ap --theme navy $MODERN; restart ""; errs
  soak $v 25; errs
  shots ${v}_navy_on; errs
done
echo "== opt: posters OFF — 8 min"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_infobar=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_secondinfobar=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_pvr=False; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=False;"; errs
soak opt_off 8; errs
shots opt_navy_off; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_infobar=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_secondinfobar=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_pvr=True; python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_eventview=True;"
for t in green burgundy; do
  echo "== opt: $t, posters ON — 5 min"
  ap --theme $t $MODERN; restart ""; errs
  soak opt_$t 5; errs
  shots opt_${t}_on; errs
done
ap --theme navy $CLASSIC
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "$R2"; st; errs
echo "movielist folder after: '$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')'"
echo T67_DONE
