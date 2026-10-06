#!/bin/sh
# CineView FHD MLA 1.0.0~rc8 — test install on an OpenATV 7.6 / 8.0 receiver, any model (release candidate, NOT final).
# Package: enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc8_all.ipk = build79 (No Poster audit fixes, t85/t85b; lifecycle t86): posters shown from a
# widget-size copy made without fast graphics memory (no accelAlloc warnings from CineView, device t83), No Poster
# layout instead of a placeholder (t82 / t84), poster cache order HDD real mount -> USB -> /tmp (see "poster cache"
# below: no HDD writes unless HDD_CACHE=1).  Device-tested on Vu+ Duo 4K SE / OpenATV 8.0.1 (t77_rc8, t86 rc8).
# Image check from tools/mla/compat_image.py evidence: OpenATV 7.6 and 8.0; 7.5 and older lack required widgets.
# Every check runs BEFORE anything is installed; any failure stops with a reason and changes nothing.
#   usage (telnet/ssh on the receiver):
#   wget -q -O /tmp/install-mla.sh "https://raw.githubusercontent.com/habeb-s/CineView-FHD/dev/mla-openatv/release/rc/install-mla.sh" && sh /tmp/install-mla.sh
#   checks only:            ... && DRYRUN=1 sh /tmp/install-mla.sh
#   poster cache on the HDD: ... && HDD_CACHE=1 sh /tmp/install-mla.sh
set -u
PKG=enigma2-plugin-skins-cineview-fhd-mla
URL="https://raw.githubusercontent.com/habeb-s/CineView-FHD/dev/mla-openatv/release/rc/enigma2-plugin-skins-cineview-fhd-mla_1.0.0%7Erc8_all.ipk"
SHA=cd3bfbe59889d3cbedfa55b1583eebb8492c95a2cc7162a50f1c0aa439459bc1
NEED_KB=40960   # unpacked 8.7 MB + design generations built on the receiver + margin
IPK=/tmp/cineview-mla-rc8.ipk
stop() { echo "CineView MLA rc8: NOT installed - $*"; rm -f "$IPK"; exit 1; }

echo "== CineView MLA 1.0.0~rc8: compatibility checks"
INFO=/usr/lib/enigma.info
[ -r "$INFO" ] || stop "$INFO missing: the image cannot be identified."
val() { sed -n "s/^$1='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" "$INFO" | head -1; }
DISTRO=$(val distro); VER=$(val imageversion); MODEL=$(val machinebuild); ARCH=$(val architecture)
echo "   image: ${DISTRO:-?} ${VER:-?} | model: ${MODEL:-?} | architecture: ${ARCH:-?}"
[ "$DISTRO" = "openatv" ] || stop "image '$DISTRO' is not OpenATV (the package uses OpenATV-only screen contracts)."
case "$VER" in
  7.6|7.6.*|8.0|8.0.*) ;;
  7.[0-5]|7.[0-5].*|6.*|5.*) stop "OpenATV '$VER' lacks skin features the package needs ('addon' widgets, MovieInfo FullDescription); 7.6 or 8.0 required.";;
  *) stop "OpenATV '$VER' has not been checked against this package yet (checked: 7.6, 8.0).";;
esac
[ -n "$MODEL" ] || stop "machinebuild is empty in $INFO: the receiver model cannot be identified."
# architecture: the package is architecture-independent ('all', Python + skin files) and needs Python 3 + enigma2
opkg print-architecture 2>/dev/null | grep -q "^arch all " || stop "opkg does not accept 'all' packages on this receiver."
command -v python3 >/dev/null 2>&1 || stop "python3 is missing."
python3 -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 and sys.version_info[1] >= 9 else 1)' 2>/dev/null \
  || stop "Python $(python3 -V 2>&1) is older than 3.9 (the package's code needs 3.9+)."
[ -d /usr/lib/enigma2/python/Components ] && [ -x /usr/bin/enigma2 ] || stop "enigma2 is not installed where expected."
H=/usr/bin/enigma2_pre_start.sh
if [ -e "$H" ] && ! grep -q "CineView MLA guardian" "$H"; then stop "$H belongs to another plugin (not replaced)."; fi
FREE=$(df -k / | awk 'NR==2 {print $4}')
[ -n "$FREE" ] && [ "$FREE" -ge "$NEED_KB" ] || stop "only ${FREE:-?} kB free on / (needs $NEED_KB kB)."
TFREE=$(df -k /tmp | awk 'NR==2 {print $4}')
[ -n "$TFREE" ] && [ "$TFREE" -ge 12000 ] || stop "only ${TFREE:-?} kB free in /tmp for the download."
echo "   free on /: ${FREE} kB, /tmp: ${TFREE} kB - OK"
INST=$(opkg status $PKG 2>/dev/null | sed -n 's/^Version: //p')
echo "   installed now: ${INST:-none}"

if [ "${DRYRUN:-0}" = "1" ]; then echo "DRYRUN: all checks passed - nothing downloaded or installed."; exit 0; fi

echo "== download + checksum"
rm -f "$IPK"
wget -q -O "$IPK" "$URL" || stop "download failed ($URL)."
GOT=$(sha256sum "$IPK" | cut -d' ' -f1)
[ "$GOT" = "$SHA" ] || stop "SHA256 mismatch (got $GOT)."
echo "   sha256 OK"

echo "== backup of the current state (for rollback)"
B=/tmp/cineview-mla-backup-$(date +%Y%m%d%H%M%S)
mkdir -p "$B" && cp -p /etc/enigma2/settings "$B/settings" 2>/dev/null
[ -d /etc/enigma2/cineview_mla ] && tar -C /etc/enigma2 -czf "$B/cineview_mla-state.tgz" cineview_mla 2>/dev/null
echo "   $B (settings + MLA state)"

echo "== install"
opkg install "$IPK" || stop "opkg refused the package (see the lines above); nothing was changed by this script."
rm -f "$IPK"
opkg status $PKG | grep -E "^(Version|Status):"

echo "== poster cache"
# rc8 carries the release cache order (1. /media/hdd/poster on a real HDD mount, 2. USB, 3. /tmp).  During the
# release-candidate tests nothing is written to an HDD unless asked for: without HDD_CACHE=1 the cache is pinned
# in /etc/enigma2/cineview_mla/runtime.json to a real USB mount (or /tmp).  An existing "poster_cache" is kept.
python3 - "${HDD_CACHE:-0}" <<'PYEOF'
import json, os, sys
p = "/etc/enigma2/cineview_mla/runtime.json"
try:
    rt = json.load(open(p))
except Exception:
    rt = {}
if rt.get("poster_cache"):
    print("   kept: %s (runtime.json)" % rt["poster_cache"]); sys.exit(0)
if sys.argv[1] == "1":
    print("   HDD_CACHE=1: release order (HDD real mount -> USB -> /tmp), decided by the skin"); sys.exit(0)
root = os.stat("/").st_dev
hdd = set()
mounts = [l.split()[:4] for l in open("/proc/mounts") if len(l.split()) >= 4]
for src, mp, fs, opts in mounts:
    if mp in ("/media/hdd", "/hdd"):
        try: hdd.add(os.stat(mp).st_dev)
        except OSError: pass
cand = []
for src, mp, fs, opts in mounts:
    if not mp.startswith("/media/") or mp == "/media/hdd" or not src.startswith("/dev/") or "rw" not in opts.split(","):
        continue
    try:
        d = os.stat(mp).st_dev
    except OSError:
        continue
    if d == root or d in hdd or not os.path.ismount(mp):
        continue
    if os.path.exists(os.path.join(mp, "STARTUP")) or any(n.startswith("linuxrootfs") for n in os.listdir(mp)):
        continue  # multiboot media
    cand.append((0 if "usb" in mp else 1, mp))
path = os.path.join(sorted(cand)[0][1], "cineview-mla", "poster") if cand else "/tmp/CINEVIEW-MLA/poster"
rt["poster_cache"] = path
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(rt, open(p, "w"), indent=1)
print("   pinned: %s (%s; no HDD writes - run with HDD_CACHE=1 to use /media/hdd/poster)" % (path, "USB" if cand else "no USB stick: /tmp, lost at reboot"))
PYEOF
echo "CineView MLA rc8 installed. Select 'CineView_FHD_MLA' in Menu > Setup > User Interface > Skin, then restart the GUI."
echo "Uninstall / rollback: see release/rc/uninstall-mla.sh (select another skin first)."
