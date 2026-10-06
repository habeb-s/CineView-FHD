#!/bin/bash
# t86: package lifecycle on Slot 8 (user list 2026-10-06 06:13: "install / upgrade / reboot / uninstall").
#  0. backup (USB) of settings, MLA state, MLA files, runtime.json; poster cache file count
#  1. UPGRADE with Enigma2 RUNNING (as a user does over telnet): Modern selected first -> opkg install <ipk> ->
#     GUI restart -> the selection must still be Modern (postinst re-applies it), skin still CineView MLA
#  2. REBOOT of the receiver (Slot 8 is the STARTUP slot: rootsubdir=linuxrootfs8 checked before and after) ->
#     Enigma2 up, skin, selection, guardian, 0 tracebacks
#  3. UNINSTALL (release/rc/uninstall-mla.sh, normal): package gone, skin dir gone, Enigma2 runs on the image's
#     default skin, /etc/enigma2/cineview_mla KEPT, poster cache untouched
#  4. FRESH INSTALL (opkg install <ipk>): factory Classic navy; skin selected again -> GUI restart -> CineView MLA
#  5. PURGE (uninstall-mla.sh purge): /etc/enigma2/cineview_mla deleted, poster cache untouched
#  6. RESTORE: install <ipk>, settings + MLA state + runtime.json back from the backup, Classic navy, skin selected
# Only Slot 8; nothing on the HDD is opened or written; no Multiboot change (STARTUP is only read).
exec 9>~/cineview-mla/t86.lock; flock -n 9 || { echo "t86 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
IPK=${1:?ipk}; TAG=${2:?tag}
S=~/cineview-mla/shots/t86_$TAG; rm -rf $S; mkdir -p $S
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
B=/media/usb/cineview-mla/state/backup-t86-$TAG
echo "== 0. backup $B"
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings && tar -C /etc/enigma2 -czf $B/cineview_mla-state.tgz cineview_mla && opkg status $PKG | grep Version > $B/version && ls $B"
state
cat $IPK | $R 'cat > /tmp/t86.ipk'; $R 'ls -l /tmp/t86.ipk; sha256sum /tmp/t86.ipk'

echo "== 1. upgrade with Enigma2 running (selection Modern first)"
ap --theme navy --set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern
restart ""
$R 'opkg install /tmp/t86.ipk 2>&1 | tail -4; pidof enigma2 >/dev/null && echo "   enigma2 kept running during opkg"'
restart ""; state; errs
curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=1:0:19:784:C6D4:16E:A00000:0:0:0:"; sleep 8; X; $RC 352; sleep 2.5; ga 1_upgrade_ib

echo "== 2. reboot"
$R 'grep -o "rootsubdir=[^ ]*" /proc/cmdline; uptime'
$R 'sync; (sleep 2; reboot) >/dev/null 2>&1 &'; echo "   reboot issued $(date +%T)"
waitup; state; errs
$R 'uptime; ls -l /usr/bin/enigma2_pre_start.sh; grep -a "CineView MLA guardian" /home/root/logs/*.log 2>/dev/null | tail -1 | cut -c1-150'
X; $RC 352; sleep 2.5; ga 2_reboot_ib

echo "== 3. uninstall (normal)"
cat ~/cineview-mla/repo/release/rc/uninstall-mla.sh | $R 'cat > /tmp/uninstall-mla.sh'
o=$(pid); $R 'sh /tmp/uninstall-mla.sh 2>&1 | tail -4'; newe2 $o; sleep 30; state; errs
X; $RC 352; sleep 2.5; ga 3_uninstalled_ib

echo "== 4. fresh install + skin selected"
$R 'opkg install /tmp/t86.ipk 2>&1 | tail -4'
restart 'grep -q "^config.skin.primary_skin=" /etc/enigma2/settings && sed -i "s#^config.skin.primary_skin=.*#config.skin.primary_skin=CineView_FHD_MLA/skin.xml#" /etc/enigma2/settings || echo "config.skin.primary_skin=CineView_FHD_MLA/skin.xml" >> /etc/enigma2/settings;'
state; errs
X; $RC 352; sleep 2.5; ga 4_fresh_ib

echo "== 5. purge"
o=$(pid); $R 'sh /tmp/uninstall-mla.sh purge 2>&1 | tail -4'; newe2 $o; sleep 30; state; errs

echo "== 6. restore"
$R 'opkg install /tmp/t86.ipk 2>&1 | tail -2'
restart "tar -C /etc/enigma2 -xzf $B/cineview_mla-state.tgz; cp -p $B/settings /etc/enigma2/settings;"
ap --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines
restart ""; state; errs
X; $RC 352; sleep 2.5; ga 6_restored_ib
$R 'rm -f /tmp/t86.ipk /tmp/uninstall-mla.sh'
echo T86_DONE
