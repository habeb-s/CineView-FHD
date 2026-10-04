#!/bin/bash
# Device run (Slot 8) for the user's 2026-10-04 20:12 requests:
#  A. core screens BEFORE the z-order fix (build32): Plugin Browser, Quick Menu, removal screen, PackageActionLog
#  B. build33: the same screens AFTER + regression grabs (InfoBar, SIB, EventView, Channel list, EPGs, EventViews)
#  C. D1: long-name clip (Video First L/R), opaque Poster List, stale-poster test (warm-up, slow reference, fast nav)
#  D. accelAlloc study: gAccel debug log (posters on / off), enigma2 CPU and memory during channel-list navigation
#  E. restore (Classic, classic-lines, posters on, show_second_infobar=2, dev plugin removed)
# Screens are opened through their native entry points by the dev-only trigger plugin (removed at the end).
exec 9>~/cineview-mla/t34.lock; flock -n 9 || { echo "t34 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build33}
S=~/cineview-mla/shots/t34; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
U=/media/usb/cineview-mla/tmp
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
ALL="poster_infobar poster_secondinfobar poster_channelselection poster_epg poster_eventview"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
log() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo $f'; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accelAlloc=$(grep -a -c "accelAlloc failed" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|name clip\|ScreenOpen\] error" $f | tail -4'; }
cfg() { for k in $ALL; do printf 'config.plugins.cineviewmla.%s=%s ' $k $1; done; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
recstart() { $R "nohup sh /tmp/cvmla/grabloop.sh $1 /tmp/cvmla/rec >/dev/null 2>&1 &"; sleep 1; }
recget() { sleep 2; $R 'for i in $(seq 1 90); do [ -f /tmp/cvmla/rec.done ] && break; sleep 1; done; cd /tmp/cvmla && tar -cf - rec' | tar -C $S -xf - && mv $S/rec $S/rec_$1; $R 'rm -rf /tmp/cvmla/rec /tmp/cvmla/rec.done'; echo "   $1 recorded $(ls $S/rec_$1 | wc -l) frames"; }
core() {  # $1 tag
  zap $HBO; X
  op pluginbrowser 6; ga $1_pluginbrowser; X
  op quickmenu 6; ga $1_quickmenu; X
  op pkgremove 12; ga $1_pkgremove; X
  op pkglog 6; ga $1_pkglog; X
}
# e2 CPU time (ms) and RSS (kB)
cpu() { $R 'p=$(pidof enigma2); set -- $(cut -d" " -f14,15 /proc/$p/stat); echo $(( ($1 + $2) * 10 )) $(grep VmRSS /proc/$p/status | tr -s " " | cut -d" " -f2)'; }
navloop() {  # $1 rounds: open list, 6 down, 6 up, exit
  for r in $(seq 1 $1); do $RC 108; sleep 3; for i in 1 2 3 4 5 6; do $RC 108; sleep 0.6; done; for i in 1 2 3 4 5 6; do $RC 103; sleep 0.6; done; X; done
}

echo "== 0. setup"
cat ~/cineview-mla/setcfg.py | $R 'cat > /tmp/cvmla/setcfg.py'
$R 'cat > /tmp/cvmla/grabloop.sh' <<'SH'
#!/bin/sh
end=$(( $(date +%s) + $1 )); rm -rf $2; mkdir -p $2
rm -f $2.done
while [ $(date +%s) -lt $end ]; do grab -q -j 75 -r 1280 $2/$(date +%s%N).jpg; done
touch $2.done
SH
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py && rm -f /tmp/cvmla/acceldebug"
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings"

echo "== A. core screens BEFORE (installed build)"
restart ""; errs
core before; errs

echo "== B. deploy $NEW, core screens AFTER + regression"
~/cineview-mla/deploy_b.sh $NEW
$R "$E apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set eventview=classic-lines --set pvr=classic 2>&1 | tail -1"
restart ""; st; errs
core after; errs
zap $HBO; X; $RC 352; sleep 2; ga reg_infobar; $RC 352; sleep 2.5; ga reg_sib; X
$RC 358; sleep 5; ga reg_eventview; X
$RC 108; sleep 5; ga reg_chsel; X
$RC 365; sleep 7; ga reg_epg_default; X
op multi 7; ga reg_epg_multi; X
op quick 7; ga reg_quickepg; X
op infobarepg 7; ga reg_infobarepg; $RC 358; sleep 5; ga reg_infobareventview; X
op evsimple 6; ga reg_eventviewsimple; X
errs

echo "== C. D1 designs (name clip, opaque Poster List, stale-poster test)"
for d in videofirst videofirst-right posterlist; do
  $R "$E apply --set channelselection=$d 2>&1 | tail -1"; restart ""; errs
  zap $HBO; X; $RC 108; sleep 5; ga d1_${d}; $RC 108; sleep 3; ga d1_${d}_down1; X
done
# posterlist is active now
echo "-- warm-up (fills the poster cache for rows 146..154)"
zap $HBO; X; $RC 108; sleep 4; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 4; done; X
echo "-- slow reference"
zap $HBO; X; recstart 44; $RC 108; sleep 4; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 4; done; sleep 2; X; recget pl_slow
echo "-- fast (0.35 s per step) down 8, hold, up 8, hold"
zap $HBO; X; recstart 30; $RC 108; sleep 4; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 0.35; done; sleep 6; for i in 1 2 3 4 5 6 7 8; do $RC 103; sleep 0.35; done; sleep 6; X; recget pl_fast
echo "-- very fast (key repeat, 0.15 s per step) down 8, hold"
zap $HBO; X; recstart 20; $RC 108; sleep 4; for i in 1 2 3 4 5 6 7 8; do $RC 108; sleep 0.15; done; sleep 7; X; recget pl_vfast
for r in pl_fast pl_vfast; do echo "   $r $(python3 ~/cineview-mla/postercheck.py $S/rec_pl_slow $S/rec_$r | tail -1)"; done
errs

echo "== D. accelAlloc study"
echo "-- D1 CPU / memory, posters ON (Poster List, navigation 5 rounds), no debug"
a=$(cpu); navloop 5; b=$(cpu); echo "   posters ON : cpu_ms ${a% *}->${b% *} rss_kB ${a#* }->${b#* }"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_channelselection=False;"; errs
a=$(cpu); navloop 5; b=$(cpu); echo "   posters OFF: cpu_ms ${a% *}->${b% *} rss_kB ${a#* }->${b#* }"
echo "-- accel debug from session start, posters ON (Classic)"
$R "$E apply --set channelselection=classic 2>&1 | tail -1"
restart "python3 /tmp/cvmla/setcfg.py $(cfg True); touch /tmp/cvmla/acceldebug;"; errs
zap $HBO; X; $RC 352; sleep 3; X; $RC 358; sleep 5; X; $RC 108; sleep 5; X
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); cp $f /media/usb/cineview-mla/tmp/accel_on.log'; $R 'cat /media/usb/cineview-mla/tmp/accel_on.log' > $S/accel_on.log
echo "-- accel debug, posters OFF"
restart "python3 /tmp/cvmla/setcfg.py $(cfg False);"; errs
zap $HBO; X; $RC 352; sleep 3; X; $RC 358; sleep 5; X; $RC 108; sleep 5; X
$R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); cp $f /media/usb/cineview-mla/tmp/accel_off.log'; $R 'cat /media/usb/cineview-mla/tmp/accel_off.log' > $S/accel_off.log
echo "-- memory over 10 minutes of use, posters ON, no debug"
restart "python3 /tmp/cvmla/setcfg.py $(cfg True); rm -f /tmp/cvmla/acceldebug;"; errs
for k in 1 2 3 4 5; do a=$(cpu); navloop 3; $RC 358; sleep 5; X; $RC 352; sleep 2; $RC 352; sleep 3; X; echo "   round $k: rss_kB ${a#* } cpu_ms ${a% *}"; done
b=$(cpu); echo "   end: rss_kB ${b#* } cpu_ms ${b% *}"; $R 'free; f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "accel fails this run: $(grep -a -c "accelAlloc failed" $f)"'

echo "== E. restore"
$R "rm -rf $P /tmp/cvmla/acceldebug /media/usb/cineview-mla/tmp/accel_*.log; $E apply --set channelselection=classic --set eventview=classic-lines 2>&1 | tail -1"
restart "python3 /tmp/cvmla/setcfg.py $(cfg True) config.usage.show_second_infobar=2;"; st; errs
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings; ls /usr/lib/enigma2/python/Plugins/Extensions | grep -c ScreenOpen"
echo T34_DONE
