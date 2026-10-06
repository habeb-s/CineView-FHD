#!/bin/bash
# t91 (user 2026-10-06 14:31) on the INSTALLED package, no deploy:
#  A. No Poster pairs, all five models incl. Classic (navy, posters ON): InfoBar / EPG / EMC / MovieSelection on HBO
#     (film, poster) and HRT1 (news, no poster); every PVR row of the USB test folder.
#  B. SecondInfoBarECM (config.usage.show_second_infobar = 3, set while Enigma2 is stopped, ORIGINAL VALUE RESTORED):
#     poster (HBO) / no poster (HRT1) / posters OFF -> no placeholder, no empty frame, no overlap.
#  C. Picons under fast channel switching: CH+ / CH- bursts, OSD+video grabs 0.3 / 1 / 2.5 s after each zap, plus the
#     channel list cursor; picon areas cut out to one sheet per model (one picon per place).
# HDD not opened; USB test media only; nothing played, deleted or moved.  Restore: Classic navy, posters ON.
exec 9>~/cineview-mla/t91.lock; flock -n 9 || { echo "t84 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
cat ~/cineview-mla/repo/tools/mla/devtools/device/setcfg.py | $R "mkdir -p /tmp/cvmla && cat > /tmp/cvmla/setcfg.py"
NEW=${1:-installed}
S=~/cineview-mla/shots/t91; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
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
$R 'sh -s' < ~/cineview-mla/repo/tools/mla/devtools/device/tmedia_pvr.sh | tail -2
echo "== using the INSTALLED package: $($R "opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version")"
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
OLDDIR=$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-'); echo "movielist folder before: '$OLDDIR'"
OLDSIB=$($R 'grep "^config.usage.show_second_infobar=" /etc/enigma2/settings | cut -d= -f2-'); echo "show_second_infobar before: '$OLDSIB'"
POSTERS="infobar secondinfobar channelselection epg pvr eventview"
pset() { local c=""; for s in $POSTERS; do c="$c python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_$s=$1;"; done; echo "$c"; }
cur() { curl -s -m 5 http://192.168.1.250/api/getcurrent | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['info'].get('name'))" 2>/dev/null; }
for m in ${MODELS:-classic details cinema modern minimal}; do
  echo "== A $m navy posters ON"; ap --theme navy $(model $m); restart "$(pset True)"; errs
  zap $HBO; X; $RC 352; sleep 2.5; ga ${m}_ib_hbo; X; sleep 2
  zap $HRT1; X; $RC 352; sleep 2.5; ga ${m}_ib_hrt1; X; sleep 2
  zap $HBO; X; op graph 8; ga ${m}_epg_hbo; $RC 106; sleep 4; ga ${m}_epg_hbo_r1; X; sleep 2; X; sleep 2
  zap $HRT1; X; op graph 8; ga ${m}_epg_hrt1; $RC 106; sleep 4; ga ${m}_epg_hrt1_r1; X; sleep 2; X; sleep 2
  op movies 9; ga ${m}_emc_0; for k in 1 2 3 4; do $RC 108; sleep 4; ga ${m}_emc_$k; done; X; sleep 3
  op nativemovies 9; ga ${m}_ms_0; for k in 1 2 3 4; do $RC 108; sleep 4; ga ${m}_ms_$k; done; X; sleep 3
  errs
  echo "== C $m fast zapping"
  zap $HBO 5; X
  for burst in 1 2 3; do
    for k in 402 402 402 403 402 403 403 402; do $RC $k; sleep 0.3; done
    ga ${m}_zap_b${burst}_t03; sleep 0.7; ga ${m}_zap_b${burst}_t1; sleep 1.5; ga ${m}_zap_b${burst}_t25; echo "   on: $(cur)"
    $RC 402; sleep 0.3; ga ${m}_zap_b${burst}_s03; sleep 1.0; ga ${m}_zap_b${burst}_s13
  done
  X; $RC 108; sleep 3; for i in $(seq 1 8); do $RC 108; sleep 0.25; done; ga ${m}_csfast_t0; sleep 1.5; ga ${m}_csfast_t15; X; sleep 2
  errs
  echo "== B $m SecondInfoBarECM"
  restart "python3 /tmp/cvmla/setcfg.py config.usage.show_second_infobar=3;"; errs
  zap $HBO; X; $RC 352; sleep 1.5; $RC 352; sleep 4; ga ${m}_ecm_hbo; X; sleep 2
  zap $HRT1; X; $RC 352; sleep 1.5; $RC 352; sleep 4; ga ${m}_ecm_hrt1; X; sleep 2
  restart "$(pset False)"; errs
  zap $HBO; X; $RC 352; sleep 1.5; $RC 352; sleep 4; ga ${m}_ecm_off; X; sleep 2
  if [ -n "$OLDSIB" ]; then RS="python3 /tmp/cvmla/setcfg.py config.usage.show_second_infobar=$OLDSIB;"; else RS="sed -i '/^config.usage.show_second_infobar=/d' /etc/enigma2/settings;"; fi
  restart "$RS $(pset True)"; errs
  echo "   show_second_infobar now: '$($R 'grep "^config.usage.show_second_infobar=" /etc/enigma2/settings | cut -d= -f2-')'"
done
ap --theme navy $(model classic)
if [ -n "$OLDDIR" ]; then R2="python3 /tmp/cvmla/setcfg.py config.movielist.last_videodir=$OLDDIR;"; else R2="sed -i '/^config.movielist.last_videodir=/d' /etc/enigma2/settings;"; fi
$R "rm -rf $P"; restart "$R2 $(pset True)"; st; errs
echo "movielist folder after: '$($R 'grep "^config.movielist.last_videodir=" /etc/enigma2/settings | cut -d= -f2-')'"
echo "show_second_infobar after: '$($R 'grep "^config.usage.show_second_infobar=" /etc/enigma2/settings | cut -d= -f2-')' (before '$OLDSIB')"
echo T91_DONE
