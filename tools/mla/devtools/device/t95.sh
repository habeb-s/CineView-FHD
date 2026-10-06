#!/bin/bash
# t95 (2026-10-06 21:01): final 1.0.0 package = build88 (plugin icon A, rights + version line, version.json) with the
# importable modules as sourceless .pyc (receiver Python 3.14).  Only what the change touches:
#  1. install over the staged 1.0.0 with Enigma2 RUNNING (opkg --force-reinstall, same version) -> GUI restart
#  2. files: no .py left in the plugin / Components CineViewMLA*, .pyc present, version.json; plugin load errors
#  3. Plugin Browser (icon) + CineView Designs (version / rights line) - receiver frames + PNG grabs
#  4. quick pass, five models (InfoBar, SecondInfoBar, channel list) - the converters / renderers are .pyc now
#  5. receiver REBOOT -> Plugin Browser again
#  6. preinst Python check with a fake python3 (3.12) in /tmp only -> must refuse; then the real one -> must pass
# Restore: Classic navy; the development screen-open tool is removed at the end.  Only Slot 8; HDD not opened.
exec 9>~/cineview-mla/t95.lock; flock -n 9 || { echo "t86 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
IPK=${1:?ipk}; TAG=${2:?tag}
S=~/cineview-mla/shots/t95_$TAG; rm -rf $S; mkdir -p $S
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
B=/media/usb/cineview-mla/state/backup-t95-$TAG
echo "== 0. backup $B"
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings && tar -C /etc/enigma2 -czf $B/cineview_mla-state.tgz cineview_mla && opkg status $PKG | grep Version > $B/version && ls $B"
state
# the package is kept in /home/root/cvmla, not /tmp: /tmp is cleared by the reboot (t86 rc8 run 1)
cat $IPK | $R 'mkdir -p /home/root/cvmla && cat > /home/root/cvmla/t95.ipk'; $R 'ls -l /home/root/cvmla/t95.ipk; sha256sum /home/root/cvmla/t95.ipk'


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
PLG=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
plog() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   plugin load errors: $(grep -a -c "PluginComponent\] Error" $f) ($(grep -a "PluginComponent\] Error" $f | grep -c CineViewMLA) CineView)"; grep -a "PluginComponent\] Error\|CineViewMLA.*rror" $f | tail -3 | cut -c1-160'; }
pb() {  # Plugin Browser -> CineView Designs
  op pluginbrowser 6; ga ${1}_pluginbrowser; fr ${1}_pluginbrowser 3
  $RC 106; sleep 0.8; $RC 106; sleep 0.8; $RC 106; sleep 1; fr ${1}_pb_select 2
  $RC 352; sleep 5; ga ${1}_cineviewdesigns; fr ${1}_cineviewdesigns 4
  X; sleep 2; X; sleep 1
}
echo "== 1. install the final 1.0.0 with Enigma2 running"
ap --theme navy $(model classic); restart ""
$R 'opkg install --force-reinstall /home/root/cvmla/t95.ipk 2>&1 | tail -4; pidof enigma2 >/dev/null && echo "   enigma2 kept running during opkg"'
restart ""; state; errs; plog
echo "== 2. files"
$R "ls $PLG; echo -n '   .py left in plugin / components: '; (ls $PLG/*.py /usr/lib/enigma2/python/Components/CineViewMLA*.py /usr/lib/enigma2/python/Components/*/CineViewMLA*.py 2>/dev/null | wc -l); echo -n '   CineViewMLA .pyc: '; ls /usr/lib/enigma2/python/Components/CineViewMLA*.pyc /usr/lib/enigma2/python/Components/*/CineViewMLA*.pyc $PLG/*.pyc 2>/dev/null | wc -l; cat $PLG/version.json; echo; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E 'Version|Status'"
echo "== 3. Plugin Browser + CineView Designs"
pb 3
echo "== 4. quick pass, five models"
for m in classic details cinema modern minimal; do
  echo "-- $m"; ap --theme navy $(model $m); restart ""; errs
  curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$HBO"; sleep 8; X; sleep 1.5
  $RC 352; fr 4_${m}_1ib 3; X; sleep 2
  $RC 352; sleep 1.5; $RC 352; fr 4_${m}_2sib 5; X; sleep 2
  $RC 108; fr 4_${m}_3cs 4; X; sleep 1.5
  errs
done
ap --theme navy $(model classic); restart ""
echo "== 5. reboot"
$R 'grep -o "rootsubdir=[^ ]*" /proc/cmdline'
$R 'sync; (sleep 2; reboot) >/dev/null 2>&1 &'; echo "   reboot issued $(date +%T)"
waitup; state; errs; plog
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
restart ""; pb 5
echo "== 6. preinst Python check"
$R 'cd /tmp && rm -rf t95p && mkdir t95p && cd t95p && ar x /home/root/cvmla/t95.ipk && tar -xzf control.tar.gz && mkdir fake && printf "#!/bin/sh\necho 3.12\n" > fake/python3 && chmod +x fake/python3 && echo "   with python3 = 3.12 (fake, /tmp only):" && (PATH=/tmp/t95p/fake:$PATH sh ./preinst; echo "   exit $?") && echo "   with the real python3:" && (sh ./preinst; echo "   exit $?"); cd /tmp && rm -rf t95p'
echo "== restore"; $R "rm -rf $P"; restart ""; state; errs; plog
$R 'rm -f /home/root/cvmla/t95.ipk; rmdir /home/root/cvmla 2>/dev/null'
echo T95_DONE
