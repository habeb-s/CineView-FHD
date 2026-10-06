#!/bin/bash
# t93 (2026-10-06): focused A/B of the t90 trigger - Minimal / Purple / posters ON, the FIRST SecondInfoBar opening
# after an Enigma2 restart, OSD grabbed densely around the RunningText scroll start (3.6 / 3.9 / 4.2 / 4.5 / 5.0 s).
#   A: build86 (= rc9 layouts)   B: build87 (scrolling text with its own fill)   N restarts each (default 15).
# Each build is deployed and verified by md5; the receiver ends on build87.  HDD not opened.
exec 9>~/cineview-mla/t87.lock; flock -n 9 || { echo "t87 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-rc9}
S=~/cineview-mla/shots/t93; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }  # /tmp is cleared by a reboot
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accel=$(grep -a -c "accelAlloc failed" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|ShowIf\]\|PosterState" $f | grep -v "progressPercentWidth\|piconMargin" | tail -4 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
ap() { local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"; }
model() {
  case $1 in
    details) echo "--set infobar=details --set secondinfobar=details --set channelselection=posterlist --set epg=graphicalplus --set pvr=cover --set eventview=detailscard";;
    cinema)  echo "--set infobar=cinema --set secondinfobar=cinema --set channelselection=videofirst --set epg=graphicalplus --set pvr=cinema --set eventview=feature";;
    modern)  echo "--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern";;
    minimal) echo "--set infobar=minimal --set secondinfobar=minimal --set channelselection=minimal --set epg=minimal --set pvr=minimal --set eventview=minimal";;
    classic) echo "--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines";;
  esac
}


POSTERS="infobar secondinfobar channelselection epg pvr eventview"
pset() { local c=""; for s in $POSTERS; do c="$c python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_$s=$1;"; done; echo "$c"; }
g() { curl -s -m 30 -o $S/$1_osd.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; python3 - $S/$1_osd.png $1 <<'PY'
import sys
from PIL import Image
try:
    a = Image.open(sys.argv[1]).getchannel("A").crop((60, 780, 1860, 920)); h = a.histogram(); n = sum(h)
    print("   %-28s band opaque %6.2f%%  alpha<255 px %6d  min %3d%s" % (sys.argv[2], 100.0 * h[255] / n, n - h[255], a.getextrema()[0], "  LEAK" if h[255] != n else ""))
except Exception as e:
    print("   %-28s GRAB-BAD %s" % (sys.argv[2], e))
PY
}
CK=usr/share/enigma2/CineView_FHD_MLA/layouts/secondinfobar/minimal/screens.openatv.xml
for B in build86 build87; do
  echo "== $B"
  ~/cineview-mla/deploy_b.sh $B >/dev/null 2>&1
  [ "$($R "md5sum /$CK" | cut -d' ' -f1)" = "$(md5sum ~/cineview-mla/$B/$CK | cut -d' ' -f1)" ] || { echo "DEPLOY MISMATCH $B"; exit 2; }
  echo "   deploy verified $B"
  ap --theme purple $(model minimal)
  for i in $(seq 1 ${N:-15}); do
    restart "$(pset True)"; [ $i = 1 ] && errs
    zap $HBO; X; sleep 1
    $RC 352; sleep 1.5; $RC 352; T0=$(date +%s.%N)
    for d in 3.6 3.9 4.2 4.5 5.0; do now=$(date +%s.%N); w=$(echo "$T0 + $d - $now" | bc); [ "${w:0:1}" != "-" ] && sleep $w; g ${B}_r${i}_t$d; done
    X; sleep 1
  done
  errs
done
echo "== restore"; ap --theme navy $(model classic); restart "$(pset True)"; errs
echo T93_DONE
