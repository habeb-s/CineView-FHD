#!/bin/bash
# Smart Installer 1.2.2 (official GitHub link) on the receiver's OpenBH 5.6 - DRYRUN, upgrade 1.0.0~openbh17 -> 1.0.1~openbh1 (
# SHA256, GUI restart by the installer), version line check in CineView Designs, 'same' run, ROLLBACK=1 back to
# Golden 1.0.0, then every Golden package file verified against the published 1.0.0 and the user state restored.
# Poster cache pinned to /tmp for the test (the HDD is never used); pin, devtool and test files removed at the end.
cd ~/cineview-mla
R=~/cineview-mla/r5.sh; F=final; L=$F/openbhgh; rm -rf $L; mkdir -p $L/shots
B=/home/root/inst122-backup-20261008; T=/tmp/cvmla-dist
PK=enigma2-plugin-skins-cineview-fhd-mla
DT=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
log() { echo "$(date -u +%T) $*" | tee -a $L/status; }
# health = a new enigma2 process + the CineView guardian's 'healthy' mark written by that session (no debug log on this image)
newe2() { local o=$1; for i in $(seq 1 120); do p=$($R pidof enigma2 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 50); do sleep 4; $R "[ \$(stat -c %Y /etc/enigma2/cineview_mla/healthy 2>/dev/null || echo 0) -gt $T0 ]" && return 0; done; return 1; }
errs() { $R 'echo "enigma2 pid=$(pidof enigma2) crash logs=$(ls /home/root/logs /media/*/logs 2>/dev/null | grep -ic crash) boot.count=$(cat /etc/enigma2/cineview_mla/boot.count 2>/dev/null) skin=$(sed -n "s/^config.skin.primary_skin=//p" /etc/enigma2/settings)"'; }
X() { for i in 1 2 3 4; do ./rc.sh 174; sleep 0.6; done; }
log "== R0 identity + golden"
$R 'grep -q "^distro=.openbh" /usr/lib/enigma.info && grep -q "^imageversion=.5\.6" /usr/lib/enigma.info' || { log "the receiver is not running OpenBH 5.6 - stop"; exit 1; }
$R "opkg status $PK | grep -E '^(Version|Status)'" | tee -a $L/status
$R "opkg status $PK | grep -q '^Version: 1.0.0~openbh17$'" || { log "1.0.0~openbh17 is not the installed version - stop"; exit 1; }
log "== R1 backup"
$R "mkdir -p $B && cp -p /etc/enigma2/settings $B/settings && tar -C /etc/enigma2 -czf $B/cineview_mla.tgz cineview_mla && ls /etc/enigma2/cineview_mla/backup > $B/restorepoints.before 2>/dev/null; sha256sum $B/settings $B/cineview_mla.tgz" | tee -a $L/status
log "== R2 official command: installer downloaded from GitHub on the receiver"
$R "rm -rf $T; mkdir -p $T; wget -qO $T/cineview-install.sh https://raw.githubusercontent.com/habeb-s/CineView-MLA-Install/main/cineview-install.sh && sha256sum $T/cineview-install.sh" | tee -a $L/status
log "== R3 test setup (GUI stopped): screen-open devtool (the poster cache is already on /tmp by the user's own setting)"
T0=$($R date +%s); o=$($R pidof enigma2)
cat mi/tools/mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done
mkdir -p $DT && cat > $DT/plugin.py && touch $DT/__init__.py; init 3"
newe2 $o && log "GUI healthy" || log "GUI NOT healthy"
log "== R4 DRYRUN"
$R "DRYRUN=1 sh $T/cineview-install.sh" > $L/R4_dryrun.txt 2>&1; tail -4 $L/R4_dryrun.txt | tee -a $L/status
log "== R5 upgrade 1.0.0~openbh17 -> 1.0.1~openbh1 downloaded from the GitHub release, GUI restarted by the installer"
T0=$($R date +%s); o=$($R pidof enigma2)
$R "RESTART=1 sh $T/cineview-install.sh" > $L/R5_install.txt 2>&1; echo "installer rc=$?" | tee -a $L/status
newe2 $o && log "GUI healthy after upgrade" || log "GUI NOT healthy after upgrade"
$R "opkg status $PK | grep -E '^(Version|Status)'; cat /etc/enigma2/cineview_mla/selection.json" | tee -a $L/status
errs | tee -a $L/status
log "== R6 CineView Designs (version line)"
$R "mkdir -p /tmp/cvmla; echo designs > /tmp/cvmla/open.txt"; sleep 7
curl -s -m 60 -o $L/shots/designs_1.0.1_openbh1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; X; sleep 2
$R "cat /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/version.json | tr -d '\n'" | tee -a $L/status
errs | tee -a $L/status
log "== R7 same version again"
$R "sh $T/cineview-install.sh" > $L/R7_same.txt 2>&1; echo "installer rc=$?" | tee -a $L/status
grep -a "already installed and verified" $L/R7_same.txt | tee -a $L/status
log "== R8 ROLLBACK=1 -> 1.0.0~openbh17 (SHA256-pinned previous release)"
T0=$($R date +%s); o=$($R pidof enigma2)
$R "ROLLBACK=1 RESTART=1 sh $T/cineview-install.sh" > $L/R8_rollback.txt 2>&1; echo "installer rc=$?" | tee -a $L/status
newe2 $o && log "GUI healthy after rollback" || log "GUI NOT healthy after rollback"
$R "opkg status $PK | grep -E '^(Version|Status)'; cat /etc/enigma2/cineview_mla/selection.json" | tee -a $L/status
errs | tee -a $L/status
log "== R9 cleanup (GUI stopped): devtool, test files, installer restore points made by this test, last service"
T0=$($R date +%s); o=$($R pidof enigma2)
$R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done
rm -rf $DT /tmp/cvmla $T
for d in \$(ls /etc/enigma2/cineview_mla/backup 2>/dev/null); do grep -qx \"\$d\" $B/restorepoints.before 2>/dev/null || { echo \"removed test restore point \$d\"; rm -rf /etc/enigma2/cineview_mla/backup/\$d; }; done
python3 - <<EOF
b = {l.split('=', 1)[0]: l for l in open('$B/settings').read().splitlines() if '=' in l}
p = '/etc/enigma2/settings'
out = [b[l.split('=', 1)[0]] if l.split('=', 1)[0] in ('config.tv.lastservice', 'config.tv.lastroot') and l.split('=', 1)[0] in b else l for l in open(p).read().splitlines()]
open(p, 'w').write('\n'.join(out) + '\n')
EOF
init 3" | tee -a $L/status
newe2 $o && log "GUI healthy after cleanup" || log "GUI NOT healthy after cleanup"
log "== R10 1.0.0~openbh17 verification"
$R "opkg files $PK | sed 1d | while read f; do if [ -L \"\$f\" ]; then echo \"L \$f -> \$(readlink \$f)\"; elif [ -f \"\$f\" ]; then echo \"F \$(sha256sum \"\$f\")\"; fi; done" | sort > $L/golden_receiver.txt
(cd final/bh17x && { find . -type l | sed 's#^\.##' | sort | while read f; do echo "L $f -> $(readlink ".$f")"; done; find . -type f | sed 's#^\.##' | sort | while read f; do echo "F $(sha256sum ".$f" | cut -d' ' -f1)  $f"; done; }) | sort > $L/golden_published.txt
echo "receiver: $(grep -c '^F' $L/golden_receiver.txt) files + $(grep -c '^L' $L/golden_receiver.txt) links; published: $(grep -c '^F' $L/golden_published.txt) files + $(grep -c '^L' $L/golden_published.txt) links" | tee -a $L/status
diff $L/golden_published.txt $L/golden_receiver.txt > $L/golden_diff.txt && log "1.0.0~openbh17: ALL FILES AND LINKS IDENTICAL TO THE APPROVED PACKAGE" || { log "GOLDEN DIFFERENCES:"; head -20 $L/golden_diff.txt | tee -a $L/status; }
echo "selection now:    $($R 'cat /etc/enigma2/cineview_mla/selection.json')" | tee -a $L/status
echo "selection backup: $($R "tar -xzOf $B/cineview_mla.tgz cineview_mla/selection.json")" | tee -a $L/status
$R "diff $B/settings /etc/enigma2/settings | grep '^[+-]config' | cut -c1-110" | tee -a $L/status
echo "playing: $(curl -s -m 10 http://192.168.1.250/api/getcurrent | python3 -c "import json,sys;print(json.load(sys.stdin)['info']['name'])")" | tee -a $L/status
$R "cat /etc/enigma2/cineview_mla/runtime.json | tr -d '\n '; echo; ls -d $DT $T /tmp/.cvmla* /tmp/*.ipk 2>&1 | sed 's/^/  /'" | tee -a $L/status
log "OPENBH_DONE"
