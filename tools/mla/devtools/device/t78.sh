#!/bin/bash
# Poster quality and fast-graphics-memory A/B: Modern "Large" (build63, as before the accelAlloc work) vs the current
# build (build71).  Same screens, same items, minutes apart:
#  * EMC (PVR key path, USB test folder): Harry Potter (local cover file) and Ples malog pingvina (identity poster);
#  * live EventView on HBO HD / HBO 2 HD / HBO 3 HD (whichever has a poster now).
# The poster area of each grab is cut out and compared pixel by pixel (A vs B).  With gAccel debug on (logging only),
# the accelerated pool content after the same steps is summarised for both builds.
# USB test folder only; the HDD is not opened.  Restore: Classic, navy, posters ON, movielist folder as before.
exec 9>~/cineview-mla/t78.lock; flock -n 9 || { echo "t78 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
A=${1:-build63}; B=${2:-build71}
S=~/cineview-mla/shots/t78; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accel=$(grep -a -c "accelAlloc failed" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 9; }
ap() { local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"; }
MODERN="--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern"
CLASSIC="--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines"
pool() {  # last pool dump of the current session: used kB, surfaces by size
  $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); cat $f' > $S/accel_$1.log
  python3 - $S/accel_$1.log <<'PY'
import re, sys, collections
L = open(sys.argv[1], errors="replace").read().splitlines()
idx = [i for i, l in enumerate(L) if "[gAccel] info --" in l]
if not idx:
    print("   no pool dump"); sys.exit()
used = collections.Counter(); n = 0; free = 0
for l in L[idx[-1] + 1:]:
    m = re.search(r"surface: \(\d+ \(\d+k\), \d+ \((\d+)k\)\) \S+ (\d+)x(\d+)", l)
    if m:
        used["%dx%s" % (int(m.group(2)) // 4, m.group(3))] += int(m.group(1)); n += 1; continue
    m = re.search(r"free: \(\d+ \(\d+k\), \d+ \((\d+)k\)\)", l)
    if m:
        free += int(m.group(1)); continue
    if l.rstrip().endswith("--") and n:
        break
print("   pool: used %dk in %d surfaces, free %dk | by size: %s" % (sum(used.values()), n, free, dict(used.most_common(8))))
PY
}
ROUNDS() {  # $1 tag
  op movies 9; $RC 108; sleep 3; $RC 108; sleep 6; ga ${1}_emc_hp; $RC 108; sleep 6; ga ${1}_emc_ples; X; sleep 3
  for sr in 784 785 786; do zap "1:0:19:$sr:C6D4:16E:A00000:0:0:0:"; X; $RC 358; sleep 7; ga ${1}_ev_$sr; X; sleep 2; done
  $RC 108; sleep 4; for k in 1 2 3 4 5 6; do $RC 108; sleep 1; done; sleep 3; ga ${1}_cs; X; sleep 2
}
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh >/dev/null
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')
for v in A B; do
  BLD=$([ $v = A ] && echo $A || echo $B)
  echo "== $v = $BLD (Modern, navy, posters ON, accel debug)"
  ~/cineview-mla/deploy_b.sh $BLD >/dev/null 2>&1
  cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
  ap --theme navy $MODERN; restart "touch /tmp/cvmla/acceldebug;"; errs
  ROUNDS $v; errs; pool $v
done
python3 - $S <<'PY'
import sys, os
from PIL import Image, ImageChops, ImageStat
S = sys.argv[1]
boxes = {"emc_hp": (1412, 128, 1712, 578), "emc_ples": (1412, 128, 1712, 578)}
for sr in ("784", "785", "786"):
    boxes["ev_" + sr] = (100, 100, 500, 700)
for k, box in boxes.items():
    a, b = os.path.join(S, "A_%s.png" % k), os.path.join(S, "B_%s.png" % k)
    if not (os.path.exists(a) and os.path.exists(b)):
        print("   %-9s missing" % k); continue
    ia, ib = Image.open(a).convert("RGB").crop(box), Image.open(b).convert("RGB").crop(box)
    d = ImageChops.difference(ia, ib)
    st = ImageStat.Stat(d)
    import math
    mse = sum(v * v for v in ImageStat.Stat(d).rms) / 3.0
    psnr = 99.0 if mse == 0 else 10 * math.log10(255 * 255 / mse)
    pair = Image.new("RGB", (ia.width * 2 + 10, ia.height), (128, 128, 128)); pair.paste(ia, (0, 0)); pair.paste(ib, (ia.width + 10, 0))
    pair.save(os.path.join(S, "AB_%s.png" % k))
    print("   %-9s mean abs diff %s  PSNR %.1f dB" % (k, [round(v, 2) for v in st.mean], psnr))
PY
ap --theme navy $CLASSIC
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "rm -f /tmp/cvmla/acceldebug; $R2"; st; errs
echo T78_DONE
