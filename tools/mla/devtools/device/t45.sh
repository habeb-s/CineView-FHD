#!/bin/bash
# accelAlloc failures in Poster List (t38 soak: ~1 per key press with posters ON, none with posters OFF).
# gAccel debug from session start (dev trigger, logging only), Poster List posters ON, HBO rows (cached), 15 DOWN
# presses 1.5 s apart; the log is analysed for: sizes of failed allocations, pool free map at that moment, which
# surfaces stay allocated.  Restore: Classic channel selection, accel debug off, dev trigger removed.
exec 9>~/cineview-mla/t45.lock; flock -n 9 || { echo "t45 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t45; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
$R "$E apply --set channelselection=posterlist 2>&1 | tail -1"
restart "touch /tmp/cvmla/acceldebug;"
zap $HBO; X; sleep 2
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "MARK nav start $(date +%T)"; grep -a -c "accelAlloc failed" $f'
$RC 108; sleep 3
for i in $(seq 1 15); do $RC 108; sleep 1.5; done
X; sleep 2
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); cp $f /media/usb/cineview-mla/tmp/t45_accel.log'; $R 'cat /media/usb/cineview-mla/tmp/t45_accel.log' > $S/accel.log; $R 'rm -f /media/usb/cineview-mla/tmp/t45_accel.log'
python3 - $S/accel.log <<'PY'
import re, sys, collections
L = open(sys.argv[1], errors="replace").read().splitlines()
allocs = collections.Counter(); fails = collections.Counter(); last_free = None
for i, l in enumerate(L):
    m = re.search(r"\[accelAlloc\] \S+ size=(\d+) (\d+x\d+)", l)
    if m:
        allocs[m.group(2)] += 1
        if i + 1 < len(L) and "accel alloc failed" in L[i + 1]:
            fails[m.group(2)] += 1
            # pool map printed just before (last 'free:' line)
            print("FAIL %s size=%s  last pool free: %s" % (m.group(2), m.group(1), last_free))
    m2 = re.search(r"free: (.*)", l)
    if m2:
        last_free = m2.group(1)
print("ALLOCS", dict(allocs.most_common(12)))
print("FAILS", dict(fails))
PY
$R "rm -rf $P /tmp/cvmla/acceldebug"
$R "$E apply --set channelselection=classic 2>&1 | tail -1"
restart ""; st
echo T45_DONE
