#!/bin/bash
# Modern Optimized v5 (build68): v4 + posters shown from widget-size PNGs outside the accelerated pool.
# 1. Diagnostic: gAccel debug from session start (dev trigger, logging only), 3 navigation rounds; at every failure
#    enigma2 dumps the whole accelerated pool -> which surfaces were resident, free blocks (fragmentation).
# 2. The same 25-min soak as t67 (Large 741, Optimized v1 see t67.log) without debug.
# USB test folder only; nothing played / deleted / moved.  Restore: Classic, navy, posters ON, debug off.
exec 9>~/cineview-mla/t74.lock; flock -n 9 || { echo "t74 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build68}
S=~/cineview-mla/shots/t74; rm -rf $S; mkdir -p $S
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
soak() {
  local end=$(( $(date +%s) + $2 * 60 )) next=0 r=0
  sample "$1 start"
  while [ $(date +%s) -lt $end ]; do
    round; r=$((r + 1))
    if [ $(date +%s) -ge $next ]; then [ $r -gt 1 ] && sample "$1 r$r"; next=$(( $(date +%s) + 180 )); fi
  done
  sample "$1 end r$r"
}
analyse() {
  $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); cat $f' > $S/accel_$1.log
  python3 - $S/accel_$1.log <<'PY'
import re, sys, collections
L = open(sys.argv[1], errors="replace").read().splitlines()
dump, last, nfail, fails = [], None, 0, collections.Counter()
req = None
for l in L:
    m = re.search(r"\[gAccel\] \[accelAlloc\] \S+ size=(\d+) (\d+)x(\d+):(\d+)", l)
    if m:
        req = "%sx%s" % (m.group(2), m.group(3)); continue
    if "[gAccel] info --" in l:
        dump = []; continue
    m = re.search(r"\[gAccel\] surface: \(\d+ \((\d+)k\), \d+ \((\d+)k\)\) \S+ (\d+)x(\d+):(\d+)", l)
    if m:
        dump.append(("used", int(m.group(2)), "%dx%d" % (int(m.group(3)) // 4, int(m.group(4))))); continue
    m = re.search(r"\[gAccel\]    free: \(\d+ \((\d+)k\), \d+ \((\d+)k\)\)", l)
    if m:
        dump.append(("free", int(m.group(2)), "")); continue
    if "accel alloc failed" in l:
        nfail += 1; fails[req] += 1; last = (req, list(dump))
print("   failures:", nfail, "by requested surface:", dict(fails.most_common(8)))
if last:
    req, d = last
    used = [x for x in d if x[0] == "used"]; free = [x for x in d if x[0] == "free"]
    print("   last failure: requested %s; pool used %d kB in %d surfaces, free %d kB in %d blocks (largest %d kB)" % (
        req, sum(x[1] for x in used), len(used), sum(x[1] for x in free), len(free), max([x[1] for x in free] or [0])))
    print("   resident:", ", ".join("%s=%dk" % (x[2], x[1]) for x in sorted(used, key=lambda x: -x[1])[:16]))
PY
}
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
ap --theme navy $MODERN
echo "== 1. diagnostic (accel debug), 3 rounds"
restart "touch /tmp/cvmla/acceldebug; for s in infobar secondinfobar channelselection epg pvr eventview; do python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_\$s=True; done;"; errs
for i in 1 2 3; do round; done; errs; analyse v5
echo "== 2. v5 soak 25 min"
restart "rm -f /tmp/cvmla/acceldebug;"; errs
soak v5 25; errs
zap $HBO; X; $RC 352; sleep 4; ga ib_v5; X; sleep 2
$RC 352; sleep 1.5; $RC 352; sleep 4; ga sib_v5; X; sleep 2
$RC 108; sleep 4; $RC 108; sleep 3; ga cs_v5; X; sleep 2
op graph 7; $RC 106; sleep 3; ga epg_v5; X; sleep 2; X; sleep 2
$RC 358; sleep 5; ga ev_v5; X; sleep 2
op movies 8; for k in 1 2 3; do $RC 108; sleep 3; done; sleep 2; ga emc_v5; $RC 108; sleep 4; ga emc_v5_generic; X; sleep 3
errs
ap --theme navy $CLASSIC
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "rm -f /tmp/cvmla/acceldebug; $R2"; st; errs
echo T74_DONE
