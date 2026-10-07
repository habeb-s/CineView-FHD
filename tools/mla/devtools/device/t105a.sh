#!/bin/bash
# t105a - OpenBH 5.6 (Slot 5) first compatibility run, step 1: install the OpenBH TEST build (golden build94 skin,
# .pyc compiled by OpenBH's Python 3.13) and start Enigma2 with CineView MLA selected.
# HDD safety: the poster cache is pinned to /tmp BEFORE the first GUI start that loads CineView (with no pin the
# release policy would choose /media/hdd/poster).  Nothing on /media/hdd is written, read for content, or mounted.
# usage: t105a.sh <ipk>
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r5.sh
IPK=${1:?ipk}; S=~/cineview-mla/shots/t105; rm -rf $S; mkdir -p $S
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1"; }
log() { $R 'ls -t /home/root/logs/Enigma2_debug_*.log | head -1'; }
errs() { $R 'f=$(ls -t /home/root/logs/Enigma2_debug_*.log | head -1); echo "   log=$f tracebacks=$(grep -a -c Traceback $f) skin_errors=$(grep -a -c "\[Skin\] Error\|SkinError" $f) crashlogs=$(ls /home/root/logs | grep -c -i crash)"'; }
$R 'grep -q "rootsubdir=duo4kse/linuxrootfs5" /proc/cmdline' || { echo "NOT Slot 5"; exit 1; }
$R 'xr() { grep -q "^$1=" /etc/enigma2/settings && sed -n "s/^$1=//p" /etc/enigma2/settings || echo "(default)"; }; echo "skin before: $(xr config.skin.primary_skin)"'
X; ga 0_openbh_default_infobar_before; $RC 358; sleep 2; ga 0_openbh_default_infobar; X

echo "== install"
cat $IPK | $R "cat > /tmp/cvmla-test.ipk"
$R "opkg install /tmp/cvmla-test.ipk 2>&1; rm -f /tmp/cvmla-test.ipk; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep -E 'Version|Status'"
echo "== pin poster cache to /tmp (HDD protection) BEFORE the GUI loads CineView"
$R "python3 - <<'PYEOF'
import json, os
p = '/etc/enigma2/cineview_mla/runtime.json'
try:
    rt = json.load(open(p))
except Exception:
    rt = {}
rt['poster_cache'] = '/tmp/CINEVIEW-MLA/poster'
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(rt, open(p, 'w'), indent=1)
print('pin:', rt)
PYEOF"
echo "== select skin (GUI stopped, same as Menu > Skin) and start"
o=$($R 'pidof enigma2')
$R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; sed -i '/^config.skin.primary_skin=/d' /etc/enigma2/settings; echo config.skin.primary_skin=CineView_FHD_MLA/skin.xml >> /etc/enigma2/settings; init 3"
for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30
echo "   enigma2 pid=$($R 'pidof enigma2')"
$R 'f=$(ls -t /home/root/logs/Enigma2_debug_*.log | head -1); grep -a "\[Skin\] Loading skin file\|primary skin\|falling back\|EMERGENCY\|CineViewMLA\]" $f | grep -v "complete\." | head -25 | cut -c1-200'
errs
$R 'f=$(ls -t /home/root/logs/Enigma2_debug_*.log | head -1); grep -a -B2 -A12 "Traceback" $f | head -80 | cut -c1-220; grep -a "\[Skin\] Error\|SkinError" $f | sort | uniq -c | sort -rn | head -40 | cut -c1-220' > $S/first_start_errors.txt
wc -l < $S/first_start_errors.txt | sed 's/^/   error lines: /'
ga 1_first_start
$R "readlink /usr/share/enigma2/CineView_FHD_MLA/active; cat /etc/enigma2/cineview_mla/runtime.json; ls /tmp/CINEVIEW-MLA 2>/dev/null | head -3"
echo T105A_DONE
