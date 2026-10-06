#!/bin/bash
# t94b: re-record the SecondInfoBar frames of t94 (t94 pressed OK while the InfoBar was still open, so the
# SIB never opened).  Installed 1.0.0, nothing else repeated.  Restore: Classic navy.
exec 9>~/cineview-mla/t94b.lock; flock -n 9 || { echo "t86 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
TAG=final100
S=~/cineview-mla/shots/t94_$TAG; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
PKG=enigma2-plugin-skins-cineview-fhd-mla
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error" $f | grep -v "progressPercentWidth\|piconMargin" | tail -3 | cut -c1-170'; }
ap() { local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"; }
CACHE=$($R 'python3 -c "import json;print(json.load(open(\"/etc/enigma2/cineview_mla/runtime.json\")).get(\"poster_cache\",\"\"))" 2>/dev/null')
state() {
  $R "echo \"   package: \$(opkg status $PKG 2>/dev/null | grep -E '^(Version|Status)' | tr '\n' ' ')\"; echo \"   skin: \$(grep '^config.skin.primary_skin' /etc/enigma2/settings || echo '(image default)')\"; echo \"   skin dir: \$(ls -d /usr/share/enigma2/CineView_FHD_MLA 2>/dev/null || echo absent) | state dir: \$(ls -d /etc/enigma2/cineview_mla 2>/dev/null || echo absent) | runtime.json: \$(ls /etc/enigma2/cineview_mla/runtime.json 2>/dev/null || echo absent)\"; echo \"   active: \$(readlink /usr/share/enigma2/CineView_FHD_MLA/active 2>/dev/null) selection: \$(python3 -c 'import json;print(json.load(open(\"/etc/enigma2/cineview_mla/selection.json\"))[\"layouts\"].get(\"infobar\"))' 2>/dev/null)\"; echo \"   poster cache $CACHE: \$(find '$CACHE' -type f 2>/dev/null | wc -l) files\"; echo \"   boot: \$(grep -o 'rootsubdir=[^ ]*' /proc/cmdline) e2pid=\$(pidof enigma2)\""
}
waitup() { sleep 50; for i in $(seq 1 120); do sleep 4; curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; done; echo "   webif up $(date +%T)"; sleep 25; }
fr() {  # fr <name> <seconds>: receiver frames (OSD + video) for the video
  local end=$(( $(date +%s) + $2 )) i=0; mkdir -p $S/frames
  while [ $(date +%s) -lt $end ]; do curl -s -m 10 -o $S/frames/$(printf "%s_%03d" $1 $i).jpg "http://192.168.1.250/grab?format=jpg&r=1280&mode=all"; i=$((i+1)); done
  echo "   frames $1: $i"
}
model() {
  case $1 in
    details) echo "--set infobar=details --set secondinfobar=details --set channelselection=posterlist --set epg=graphicalplus --set pvr=cover --set eventview=detailscard";;
    cinema)  echo "--set infobar=cinema --set secondinfobar=cinema --set channelselection=videofirst --set epg=graphicalplus --set pvr=cinema --set eventview=feature";;
    modern)  echo "--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern";;
    minimal) echo "--set infobar=minimal --set secondinfobar=minimal --set channelselection=minimal --set epg=minimal --set pvr=minimal --set eventview=minimal";;
    classic) echo "--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines";;
  esac
}
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"

echo "== SecondInfoBar frames, five models (installed $($R "opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version"))"
for m in classic details cinema modern minimal; do
  echo "-- $m"; ap --theme navy $(model $m); restart ""; errs
  curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$HBO"; sleep 8; X; sleep 2
  rm -f $S/frames/3_${m}_2sib_*.jpg
  $RC 352; sleep 1.5; $RC 352; fr 3_${m}_2sib 6; X; sleep 1.5
  errs
done
echo "== restore Classic navy"; ap --theme navy $(model classic); restart ""; state; errs
echo T94B_DONE
