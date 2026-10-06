#!/bin/bash
# t90 (user 2026-10-06 14:31): Minimal / SecondInfoBar description-area leak (one t87e capture, not in 24 t88 retakes).
# Long targeted test on the INSTALLED package: 3 receiver reboots (Slot 8 = STARTUP slot, only read); after each:
# Purple and Navy x posters ON and OFF; SIB opened and closed 6 times each on HBO, OSD grabbed 2 / 4 / 6 s after
# opening.  Every grab: alpha of the description band (60..1860 x 780..920) must be 255 everywhere.
# Nothing on the HDD is opened or written.  Restore: Classic, navy, posters ON.
exec 9>~/cineview-mla/t87.lock; flock -n 9 || { echo "t87 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-rc9}
S=~/cineview-mla/shots/t90; rm -rf $S; mkdir -p $S
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
waitup() { sleep 50; for i in $(seq 1 120); do sleep 4; curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; done; echo "   webif up $(date +%T)"; sleep 25; }
g() { curl -s -m 30 -o $S/$1_osd.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; python3 - $S/$1_osd.png $1 <<'PY'
import sys
from PIL import Image
try:
    a = Image.open(sys.argv[1]).getchannel("A").crop((60, 780, 1860, 920)); h = a.histogram(); n = sum(h)
    print("   %-36s band opaque %6.2f%%  alpha<255 px %6d  min %3d%s" % (sys.argv[2], 100.0 * h[255] / n, n - h[255], a.getextrema()[0], "  LEAK" if h[255] != n else ""))
except Exception as e:
    print("   %-36s GRAB-BAD %s" % (sys.argv[2], e))
PY
}
echo "== using the INSTALLED package: $($R "opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version")"
for b in 1 2 3; do
  echo "== reboot $b"
  $R 'grep -o "rootsubdir=[^ ]*" /proc/cmdline'
  $R 'sync; (sleep 2; reboot) >/dev/null 2>&1 &'; echo "   reboot issued $(date +%T)"
  waitup; $R 'grep -o "rootsubdir=[^ ]*" /proc/cmdline'; errs
  cat ~/cineview-mla/repo/tools/mla/devtools/device/setcfg.py | $R "mkdir -p /tmp/cvmla && cat > /tmp/cvmla/setcfg.py"
  for t in purple navy; do
    for p in True False; do
      echo "== reboot $b minimal $t posters $p"; ap --theme $t $(model minimal); restart "$(pset $p)"; errs
      zap $HBO; X; sleep 2
      for o in 1 2 3 4 5 6; do
        $RC 352; sleep 1.5; $RC 352; T0=$(date +%s.%N)
        for d in 2 4 6; do now=$(date +%s.%N); w=$(echo "$T0 + $d - $now" | bc); [ "${w:0:1}" != "-" ] && sleep $w; g b${b}_${t}_p${p}_o${o}_t$d; done
        X; sleep 2
      done
      errs
    done
  done
done
echo "== restore"; ap --theme navy $(model classic); restart "$(pset True)"; errs
echo T90_DONE
