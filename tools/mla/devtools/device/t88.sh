#!/bin/bash
# t88 (2026-10-06): is the Minimal/Purple SIB description band (alpha 210 at y 796-848, t87e) timing-dependent?
# Minimal SIB in purple and navy, OSD grabbed 2 / 4 / 5 / 6 / 8 / 12 s after opening (RunningText startdelay 4000).
# Uses the build already deployed (build85, checked by md5).  Restores Classic navy.
# t84: No Poster arrangement on the list screens with a fixed layout (build77): GraphicalEPG (Modern, Graphical Plus)
# and the PVR cards (Modern, Cinema Shelf, Cover Library; EMC + native MovieSelection) follow the poster of the
# HIGHLIGHTED event / SELECTED recording: poster card with a real poster, No Poster card otherwise; no placeholder.
# EPG: highlighted event on HBO (film, poster) and on HRT1 (news, generic).  PVR: USB test folder only (tmedia_pvr.sh:
# A identity lookup, B local cover, C generic news); every row of the list is grabbed.  HDD not opened; nothing played,
# deleted or moved.  Restore: Classic navy, posters ON, movielist folder as before.
exec 9>~/cineview-mla/t87.lock; flock -n 9 || { echo "t87 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build85}
S=~/cineview-mla/shots/t88; rm -rf $S; mkdir -p $S
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
CK=usr/share/enigma2/CineView_FHD_MLA/layouts/secondinfobar/classic/screens.openatv.xml
[ "$($R "md5sum /$CK" | cut -d' ' -f1)" = "$(md5sum ~/cineview-mla/$NEW/$CK | cut -d' ' -f1)" ] || { echo "DEPLOY MISMATCH"; exit 2; }
g() { curl -s -m 30 -o $S/$1_osd.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; echo "cap $1"; }
for t in purple navy; do
  for rep in 1 2; do
    echo "== minimal $t rep $rep"; ap --theme $t $(model minimal); restart ""; errs
    zap $HBO; X; sleep 2
    $RC 352; sleep 1.5; $RC 352; T0=$(date +%s.%N)
    for d in 2 4 5 6 8 12; do
      now=$(date +%s.%N); w=$(echo "$T0 + $d - $now" | bc); [ "${w:0:1}" != "-" ] && sleep $w
      g minimal_${t}_r${rep}_sib_t$d
    done
    X; sleep 2
  done
done
ap --theme navy $(model classic); restart ""; errs
echo T88_DONE
