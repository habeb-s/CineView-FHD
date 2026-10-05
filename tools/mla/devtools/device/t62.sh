#!/bin/bash
# accelAlloc with the Modern model (t60: Modern soak 639 failures in 15 rounds, Classic 1 in 6 rounds, both with
# stable RSS / threads / CPU).  Which Modern screen and which surface sizes cause them: gAccel debug from session
# start (dev trigger, logging only), failures counted after each step (InfoBar, SecondInfoBar, Channel Selection
# + 10 moves, EventView, Graphical EPG + moves), posters ON, then the same with posters OFF.  build55.
# Restore: Classic, navy, posters ON, debug off.
exec 9>~/cineview-mla/t62.lock; flock -n 9 || { echo "t62 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build55}
S=~/cineview-mla/shots/t62; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
cnt() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); grep -a -c "accel alloc failed\|accelAlloc failed" $f'; }
step() { local a=$(cnt); eval "$2"; local b=$(cnt); echo "   step $1: +$((b - a)) failures"; }
steps() {
  zap $HBO; X; sleep 2
  step infobar '$RC 352; sleep 3; X; sleep 2'
  step secondinfobar '$RC 352; sleep 1.5; $RC 352; sleep 4; X; sleep 2'
  step chsel_open '$RC 108; sleep 5'
  step chsel_10moves 'for k in 1 2 3 4 5 6 7 8 9 10; do $RC 108; sleep 1.5; done'
  step chsel_close 'X; sleep 2'
  step eventview '$RC 358; sleep 5; X; sleep 2'
  step epg_open 'op graph 9'
  step epg_moves 'for k in 1 2 3 4 5; do $RC 106; sleep 1.5; done; $RC 108; sleep 2'
  step epg_close 'X; sleep 2; X; sleep 2'
}
analyse() {  # $1 tag
  $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); cat $f' > $S/accel_$1.log
  python3 - $S/accel_$1.log <<'PY'
import re, sys, collections
L = open(sys.argv[1], errors="replace").read().splitlines()
allocs = collections.Counter(); fails = collections.Counter()
for i, l in enumerate(L):
    m = re.search(r"\[accelAlloc\] \S+ size=(\d+) (\d+x\d+)", l)
    if m:
        allocs[m.group(2)] += 1
        if i + 1 < len(L) and ("accel alloc failed" in L[i + 1] or "accelAlloc failed" in L[i + 1]):
            fails[m.group(2)] += 1
print("   ALLOCS", dict(allocs.most_common(10)))
print("   FAILS by surface size", dict(fails.most_common(10)))
PY
}
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "$E apply --theme navy --set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set eventview=modern 2>&1 | tail -1"
echo "== Modern, posters ON"
restart "touch /tmp/cvmla/acceldebug;"; steps; analyse on
echo "== Modern, posters OFF"
restart "touch /tmp/cvmla/acceldebug; for s in infobar secondinfobar channelselection epg eventview; do python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_\$s=False; done;"; steps; analyse off
restart "rm -f /tmp/cvmla/acceldebug; for s in infobar secondinfobar channelselection epg eventview; do python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_\$s=True; done;"
$R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set eventview=classic-lines 2>&1 | tail -1"
$R "rm -rf $P"; restart ""; st
echo T62_DONE
