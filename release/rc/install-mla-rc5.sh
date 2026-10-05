#!/bin/sh
# CineView FHD MLA 1.0.0~rc5 — test install for another OpenATV 8.0.x receiver (release candidate, NOT final).
# Package: enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc5_all.ipk  (build70, branch dev/mla-openatv)
# Every check runs BEFORE anything is installed; any failure stops with a reason and changes nothing.
#   usage (telnet/ssh on the receiver):
#   wget -q -O /tmp/install-mla-rc5.sh "https://raw.githubusercontent.com/habeb-s/CineView-FHD/dev/mla-openatv/release/rc/install-mla-rc5.sh" && sh /tmp/install-mla-rc5.sh
set -u
PKG=enigma2-plugin-skins-cineview-fhd-mla
URL="https://raw.githubusercontent.com/habeb-s/CineView-FHD/dev/mla-openatv/release/rc/enigma2-plugin-skins-cineview-fhd-mla_1.0.0%7Erc5_all.ipk"
SHA=c8b6220e7a16004fef283cd4ce5bd8aa250a97f2784360ffd62185f1ac6664e5
NEED_KB=40960   # unpacked 8.7 MB + design generations built on the receiver + margin
IPK=/tmp/cineview-mla-rc5.ipk
stop() { echo "CineView MLA rc5: NOT installed - $*"; rm -f "$IPK"; exit 1; }

echo "== CineView MLA 1.0.0~rc5: compatibility checks"
INFO=/usr/lib/enigma.info
[ -r "$INFO" ] || stop "$INFO missing: the image cannot be identified."
val() { sed -n "s/^$1='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" "$INFO" | head -1; }
DISTRO=$(val distro); VER=$(val imageversion); MODEL=$(val machinebuild); ARCH=$(val architecture)
echo "   image: ${DISTRO:-?} ${VER:-?} | model: ${MODEL:-?} | architecture: ${ARCH:-?}"
[ "$DISTRO" = "openatv" ] || stop "image '$DISTRO' is not OpenATV (this package is OpenATV 8.0.x only)."
case "$VER" in 8.0|8.0.*) ;; *) stop "OpenATV '$VER' is not 8.0.x (verified on 8.0.1).";; esac
[ -n "$MODEL" ] || stop "machinebuild is empty in $INFO: the receiver model cannot be identified."
# architecture: the package is architecture-independent ('all', Python + skin files) and needs Python 3 + enigma2
opkg print-architecture 2>/dev/null | grep -q "^arch all " || stop "opkg does not accept 'all' packages on this receiver."
command -v python3 >/dev/null 2>&1 || stop "python3 is missing."
python3 -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 and sys.version_info[1] >= 11 else 1)' 2>/dev/null \
  || stop "Python $(python3 -V 2>&1) is older than 3.11 (OpenATV 8.0 ships 3.12+)."
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
echo "CineView MLA rc5 installed. Select 'CineView_FHD_MLA' in Menu > Setup > User Interface > Skin, then restart the GUI."
echo "Uninstall / rollback: see release/rc/uninstall-mla.sh (select another skin first)."
