#!/bin/bash
# Slot 4 (OpenViX 6.9) cleanup after the CineView MLA tests: project test files only.
# Kept: the MLA package, the user's design selection and state (/etc/enigma2/cineview_mla), the settings backup
# (/home/root/mla-backup-20261008-openvix).  Settings lines added by the tests are removed with the GUI stopped.
# HDD never used.  No reboot.
R=~/cineview-mla/r4.sh
B=/home/root/mla-backup-20261008-openvix
$R 'grep -q "rootsubdir=duo4kse/linuxrootfs4" /proc/cmdline' || { echo "NOT Slot 4"; exit 1; }
LS=$($R "sed -n 's/^config.tv.lastservice=//p' $B/settings"); echo "lastservice before the tests: $LS"
[ -n "$LS" ] && curl -s -m 10 -o /dev/null "http://192.168.1.250/api/zap?sRef=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$LS")"; sleep 8
mkdir -p ~/cineview-mla/vixlogs/final
$R 'cd /home/root/logs && tar -czf - Enigma2_debug_*.log' > ~/cineview-mla/vixlogs/final/e2logs_final.tgz; echo "logs archived: $(tar -tzf ~/cineview-mla/vixlogs/final/e2logs_final.tgz | wc -l)"
o=$($R pidof enigma2)
$R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done
S=/etc/enigma2/settings
for k in config.crash.enabledebug config.usage.last_movie_played config.usage.show_event_progress_in_servicelist; do
  grep -q \"^\$k=\" $B/settings || sed -i \"/^\$k=/d\" \$S
done
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen /tmp/cvmla /tmp/cvmla-test.ipk /tmp/cvmla_rb.ipk /tmp/timers.xml.before-t107p /home/root/cvmla-testmedia
rm -f /home/root/logs/Enigma2_debug_2026-10-08_*.log
echo '--- settings vs backup:'; diff $B/settings \$S | grep '^[<>]' | cut -c1-120
init 3"
for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done; echo "new e2 pid=$p"
for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30
$R "opkg status enigma2-plugin-skins-cineview-fhd-mla | grep 'Version\|Status'; grep primary_skin /etc/enigma2/settings; readlink /usr/share/enigma2/CineView_FHD_MLA/active; ls /etc/enigma2/cineview_mla; ls -d /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen 2>&1; ls /home/root/logs; ls $B"
curl -s -m 10 http://192.168.1.250/api/getcurrent | python3 -c "import json,sys;d=json.load(sys.stdin)['info'];print('playing:', d.get('name'))"
curl -s -m 60 -o ~/cineview-mla/vixchk/final_after_cleanup.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"
echo CLEANUP_DONE
