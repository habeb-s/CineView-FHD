#!/bin/sh
# CineView MLA Smart Installer - Design & Development by habeb-s (c) 2026
# One installer for OpenATV, OpenBH and OpenViX.  Usage on the receiver (telnet / ssh):
#   wget -qO /tmp/cineview-install.sh "<distribution point>/cineview-install.sh" && sh /tmp/cineview-install.sh
# options:  DRYRUN=1  checks only      HDD_CACHE=0  keep the poster cache off the hard disk
#           RESTART=1 restart the GUI at the end without asking
#           ROLLBACK=1  return to the previous released version for this image (SHA256-verified, settings kept)
#           PKG_DIR=<folder>  install from package files copied to the receiver (USB / local), same SHA256 check
# Every check runs before anything is changed; any failure stops the installer and nothing is changed.
INSTALLER_VERSION="1.2.0"
PKG="enigma2-plugin-skins-cineview-fhd-mla"
# One package per image, built from the same CineView MLA source (Common Core + image adapter).  Only these exact
# files are ever installed: each is pinned by its SHA256 here, in the installer itself (a download is never trusted
# by its address).  Tested image versions only: OpenATV 8.0, OpenBH 5.6, OpenViX 6.9 (user decision 2026-10-08).
# Distribution point: ONE address for every image - <DIST_BASE>/cineview-install.sh and
# <DIST_BASE>/packages/<image>/<file>.  Empty = not published yet: then only PKG_DIR (local copies) can be used;
# no address is ever guessed.
DIST_BASE=""
OPENATV_VERSION="1.0.1"; OPENATV_FILE="enigma2-plugin-skins-cineview-fhd-mla_1.0.1_all.ipk"
OPENATV_SHA="80808b77c716c912366ce10f948aa5e3270e7730b61c0e9ed9b4d717ad60fab3"
OPENATV_PREV_VERSION="1.0.0"; OPENATV_PREV_FILE="enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk"
OPENATV_PREV_SHA="4709881b66ae9e5b8cc8dfa7f5b7e3fafdfb57d779431709b8c5c1b48c4cb0a8"
OPENATV_PY="3.14"
OPENBH_VERSION="1.0.1~openbh1"; OPENBH_FILE="enigma2-plugin-skins-cineview-fhd-mla_1.0.1~openbh1_all.ipk"
OPENBH_SHA="9fe54774c82b122f7be189e7e065b1c35fea4390358871c23f866c8e665bb2b6"
OPENBH_PREV_VERSION="1.0.0~openbh17"; OPENBH_PREV_FILE="enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openbh17_all.ipk"
OPENBH_PREV_SHA="deee7938c13325ecd18ff40b1ec0b5fbe5780d7c5458608bbde3d0c357c7ee39"
OPENBH_PY="3.13"
OPENVIX_VERSION="1.0.1~openvix1"; OPENVIX_FILE="enigma2-plugin-skins-cineview-fhd-mla_1.0.1~openvix1_all.ipk"
OPENVIX_SHA="5b99135e2f27c888061b61b9d667d8a0c56423ed1e764479c103f2ac4fe06793"
OPENVIX_PREV_VERSION="1.0.0~openvix1"; OPENVIX_PREV_FILE="enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openvix1_all.ipk"
OPENVIX_PREV_SHA="955d102826bf30854003a7f5cd8e5d75b4f9e808b783bfe1fb53571acfa76d87"
OPENVIX_PY="3.14"
RT="${CVMLA_ROOT:-}"  # CVMLA_ROOT: test hook only (a simulated receiver root for the identification checks)
INFO="${CVMLA_INFO:-$RT/usr/lib/enigma.info}"  # CVMLA_INFO: test hook only (another enigma.info)
NEED_ROOT_KB=40960
NEED_TMP_KB=12000
SKIN_NAME="CineView_FHD_MLA"
SKIN_DIR="/usr/share/enigma2/$SKIN_NAME"
PLG_DIR="/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA"
STATE="/etc/enigma2/cineview_mla"

if [ -t 1 ] || [ "${CVMLA_COLOR:-0}" = "1" ]; then
	B=$(printf '\033[1m'); N=$(printf '\033[0m'); G=$(printf '\033[32m'); Y=$(printf '\033[33m'); R=$(printf '\033[31m'); C=$(printf '\033[36m'); W=$(printf '\033[37m')
else
	B=""; N=""; G=""; Y=""; R=""; C=""; W=""
fi
TMPD=$(mktemp -d /tmp/.cvmla.XXXXXX 2>/dev/null || echo /tmp/.cvmla.$$)
mkdir -p "$TMPD"
IPK="$TMPD/cineview-mla.ipk"
LOG="$TMPD/opkg.log"
SELF="$0"
cleanup() {  # silent: temporary files and this script only - never the poster cache, profiles, settings or backups
	rm -rf "$TMPD" 2>/dev/null
	[ "${HAVELOCK:-0}" = "1" ] && rm -rf /tmp/.cvmla.lock 2>/dev/null
	case "$SELF" in /tmp/cineview-install*.sh) rm -f "$SELF" 2>/dev/null ;; esac
}
trap cleanup EXIT
trap 'exit 130' INT TERM HUP

section() { printf '\n%s%s%s\n' "$B$C" "$1" "$N"; }
ok()   { printf '  %s[OK]%s %s\n' "$G" "$N" "$1"; }
info() { printf '  %s[..]%s %s\n' "$C" "$N" "$1"; }
warn() { printf '  %s[!!]%s %s\n' "$Y" "$N" "$1"; }
fail() { printf '  %s[XX]%s %s\n' "$R" "$N" "$1"; printf '\n%s%sCineView MLA was not installed.%s Nothing was changed on this receiver.\n\n' "$B" "$R" "$N"; exit 1; }
kv()   { sed -n "s/^$1='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" "$INFO" 2>/dev/null | head -1; }

printf '\n%s%s  CineView MLA Smart Installer  %s  %sversion %s%s\n' "$B" "$W" "$N" "$C" "$INSTALLER_VERSION" "$N"
printf '  %sDesign & Development by habeb-s (c) 2026%s\n' "$W" "$N"

LOCK=/tmp/.cvmla.lock  # one installer at a time; a lock left by a run that was killed is taken over
if ! mkdir "$LOCK" 2>/dev/null; then
	OP=$(cat "$LOCK/pid" 2>/dev/null)
	if [ -n "$OP" ] && [ "$OP" != "$$" ] && kill -0 "$OP" 2>/dev/null && grep -q "cineview" "/proc/$OP/cmdline" 2>/dev/null; then
		fail "Another CineView MLA installation is running. Please wait until it has finished."
	fi
	rm -rf "$LOCK"; mkdir "$LOCK" 2>/dev/null || fail "/tmp is not writable."
fi
echo $$ > "$LOCK/pid"; HAVELOCK=1
for d in /tmp/.cvmla.*; do [ -d "$d" ] && [ "$d" != "$LOCK" ] && [ "$d" != "$TMPD" ] && rm -rf "$d" 2>/dev/null; done

section "Device"
[ -x "$RT/usr/bin/enigma2" ] && [ -d "$RT/usr/lib/enigma2/python/Components" ] || fail "Enigma2 was not found on this receiver."
[ -r "$INFO" ] || fail "The image information (/usr/lib/enigma.info) is missing: the image cannot be identified."
BRAND=$(kv displaybrand); MODEL=$(kv displaymodel); MB=$(kv machinebuild); BR=$(kv brand)
# The package is the same for every receiver model (architecture 'all'), so the model never decides or blocks the
# installation (a legitimate receiver of any brand must not be refused).  It is shown as the image reports it and
# cross-checked with the receiver driver's own model file, read in the order the image itself uses (OpenATV
# Tools/StbHardware.getBoxProc).  Vu+: vu<vumodel>; /proc/stb/info/model is never used on Vu+ (its driver reports a
# fixed legacy value there: dm8000 on a Duo 4K SE).  No model is ever invented: an unknown model is shown as unknown.
SI="$RT/proc/stb/info"
rd() { [ -f "$1" ] && head -n 1 "$1" 2>/dev/null | tr 'A-Z' 'a-z' | tr -d '\r\000' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }
lc() { printf '%s' "$1" | tr 'A-Z' 'a-z' | tr -cd 'a-z0-9'; }
VUM=$(rd "$SI/vumodel"); DRV=""; DSRC=""; SAME=0
if [ -n "$VUM" ]; then
	DRV="$VUM"; DSRC="vumodel"; [ "$MB" = "vu$VUM" ] && SAME=1
else
	for f in hwmodel gbmodel boxtype; do v=$(rd "$SI/$f"); [ -n "$v" ] && { DRV="$v"; DSRC="$f"; break; }; done
	[ -z "$DRV" ] && [ -f "$SI/azmodel" ] && { DRV=$(rd "$SI/model"); DSRC="model"; }
	[ -z "$DRV" ] && { DRV=$(rd "$RT/proc/boxtype"); [ -n "$DRV" ] && DSRC="/proc/boxtype"; }
	[ -z "$DRV" ] && { DRV=$(rd "$SI/model"); [ -n "$DRV" ] && DSRC="model"; }
	A=$(lc "$MB"); D=$(lc "$DRV")
	if [ -n "$A" ] && [ -n "$D" ]; then
		case "$A" in *"$D"*) SAME=1 ;; *) case "$D" in *"$A"*) SAME=1 ;; esac ;; esac
	fi
fi
NAME="${BRAND:+$BRAND }${MODEL:-${MB:-unknown model}}"
if [ -z "$MB" ]; then
	info "Receiver: ${DRV:+$DRV (receiver driver) - }the image does not report its model (not needed: one package fits every model)"
elif [ "$SAME" = "1" ]; then
	ok "$NAME ($MB, confirmed by the receiver driver)"
elif [ -n "$DRV" ]; then
	info "$NAME ($MB; the receiver driver reports '$DRV' - not needed: one package fits every model)"
else
	ok "$NAME ($MB)"
fi

section "Image"
DISTRO=$(kv distro); IVER=$(kv imageversion)
# Second, independent evidence: files that only that image's own enigma2 ships, taken from the enigma2 source of every
# checked version (OpenATV 8.0.1 57b7a51 + current; OpenBH 5.6.008 52dedddc, 6.0.003 c06a87e + current; OpenViX
# 6.9.002 d3f089a + current) and present on the tested receivers.  The image named by enigma.info must have its own
# files (two per image, either is enough) and NONE of the other images' files - no single button or screen decides.
E="$RT/usr/lib/enigma2/python"
M_OPENATV="Components/International Components/Opkg"
M_OPENBH="Screens/BpBlue Plugins/SystemPlugins/OBH/plugin"
M_OPENVIX="Plugins/SystemPlugins/ViX/plugin Plugins/SystemPlugins/ViX/ImageManager"
many() { for m in "$@"; do ls "$E/$m.py" "$E/$m.pyc" 2>/dev/null | grep -q . && return 0; done; return 1; }
FOUND=""
for i in openatv openbh openvix; do
	case $i in openatv) L="$M_OPENATV" ;; openbh) L="$M_OPENBH" ;; openvix) L="$M_OPENVIX" ;; esac
	many $L && FOUND="$FOUND $i"
done
FOUND="${FOUND# }"
case "$DISTRO" in
	openatv) IMG="OpenATV"; L="$M_OPENATV" ;;
	openbh) IMG="OpenBH"; L="$M_OPENBH" ;;
	openvix) IMG="OpenViX"; L="$M_OPENVIX" ;;
	"") fail "This image does not name itself in /usr/lib/enigma.info: it cannot be identified." ;;
	*) fail "This image is '$DISTRO'. CineView MLA supports OpenATV, OpenBH and OpenViX." ;;
esac
[ "$FOUND" = "$DISTRO" ] \
	|| fail "enigma.info names $IMG, but the image's own files point to '${FOUND:-no known image}': the image cannot be identified reliably."
eval "VERSION=\$$(echo $DISTRO | tr a-z A-Z)_VERSION; PKG_FILE=\$$(echo $DISTRO | tr a-z A-Z)_FILE; PKG_SHA=\$$(echo $DISTRO | tr a-z A-Z)_SHA"
eval "PREV_VERSION=\$$(echo $DISTRO | tr a-z A-Z)_PREV_VERSION; PREV_FILE=\$$(echo $DISTRO | tr a-z A-Z)_PREV_FILE; PREV_SHA=\$$(echo $DISTRO | tr a-z A-Z)_PREV_SHA; PY_NEED=\$$(echo $DISTRO | tr a-z A-Z)_PY"
ok "$IMG $IVER detected (image information and the image's own files agree)"

section "Version"
case "$DISTRO:$IVER" in
	openatv:8.0|openatv:8.0.*) ok "OpenATV $IVER is supported (tested on OpenATV 8.0)" ;;
	openbh:5.6|openbh:5.6.*) ok "OpenBH $IVER is supported (tested on OpenBH 5.6)" ;;
	openvix:6.9|openvix:6.9.*) ok "OpenViX $IVER is supported (tested on OpenViX 6.9)" ;;
	*) fail "$IMG $IVER has not been tested with CineView MLA, so it is not installed (tested: OpenATV 8.0, OpenBH 5.6, OpenViX 6.9)." ;;
esac
if [ "${ROLLBACK:-0}" = "1" ]; then  # the previous released package of this image, pinned by its SHA256 like the current one
	VERSION="$PREV_VERSION"; PKG_FILE="$PREV_FILE"; PKG_SHA="$PREV_SHA"; FORCE=1
	info "Rollback requested: CineView MLA $VERSION (previous release for $IMG)"
fi
if [ -n "${PKG_DIR:-}" ]; then PKG_URL="${PKG_DIR%/}/$PKG_FILE"
elif [ -n "${CVMLA_DIST_BASE:-$DIST_BASE}" ]; then PKG_URL="${CVMLA_DIST_BASE:-$DIST_BASE}/packages/$DISTRO/$PKG_FILE"  # CVMLA_DIST_BASE: test hook only
else PKG_URL=""; fi
# the package for this image (CVMLA_PKG_URL / CVMLA_PKG_SHA / CVMLA_VERSION: test overrides)
PKG_URL="${CVMLA_PKG_URL:-$PKG_URL}"; PKG_SHA="${CVMLA_PKG_SHA:-$PKG_SHA}"; VERSION="${CVMLA_VERSION:-$VERSION}"
case "$PKG_SHA:$VERSION:$PKG_FILE" in *@*|:*|*::*|*:) fail "This installer is incomplete (package table). Please download the official installer again." ;; esac
case "$PKG_URL" in
	"") warn "Package source: none - CineView MLA is not published yet (copy the package to the receiver and use PKG_DIR=<folder>)" ;;
	/*) ok "Package source: $PKG_URL (local file)" ;;
	*) ok "Package source: CineView MLA distribution point" ;;
esac

section "Python"
PYV=${CVMLA_PYV:-$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)}  # CVMLA_PYV: test hook only
[ -n "$PYV" ] || fail "Python 3 was not found."
[ "$PYV" = "$PY_NEED" ] || fail "Python $PYV found; this package is built for Python $PY_NEED ($IMG)."
ok "Python $PYV compatible"

section "Architecture"
ARCH=$(kv architecture); [ -n "$ARCH" ] || ARCH=$(uname -m)
opkg print-architecture 2>/dev/null | grep -q "^arch all " || fail "This receiver does not accept architecture-independent packages."
ok "Architecture: $ARCH (CineView MLA is architecture-independent)"

section "Compatibility"
H="$RT/usr/bin/enigma2_pre_start.sh"
if [ -e "$H" ] && ! grep -q "CineView MLA guardian" "$H" 2>/dev/null; then
	fail "$H belongs to another add-on; CineView MLA does not replace it."
fi
MISSING=""
for d in python3-requests python3-pillow; do
	opkg status "$d" 2>/dev/null | grep -q "^Status:.* installed" || MISSING="$MISSING $d"
done
if [ -n "$MISSING" ]; then
	opkg list 2>/dev/null | grep -q "^python3-pillow \|^python3-requests " || opkg update >/dev/null 2>&1
	for d in $MISSING; do opkg list 2>/dev/null | grep -q "^$d " || fail "Required component '$d' is not installed and not available from the image feed."; done
	warn "Required components will be installed from the image feed:$MISSING"
else
	ok "Required components present (python3-pillow, python3-requests)"
fi
ok "Package matches this receiver"

section "Storage"
FREE=$(df -Pk / | awk 'NR==2 {print $4}')
TFREE=$(df -Pk /tmp | awk 'NR==2 {print $4}')
[ -n "$FREE" ] && [ "$FREE" -ge "$NEED_ROOT_KB" ] || fail "Not enough free space: $(( ${FREE:-0} / 1024 )) MB free, $(( NEED_ROOT_KB / 1024 )) MB needed."
[ -n "$TFREE" ] && [ "$TFREE" -ge "$NEED_TMP_KB" ] || fail "Not enough free space in /tmp for the download."
ok "Free space: $(( FREE / 1024 )) MB"
CACHE=$(python3 - "${HDD_CACHE:-1}" <<'PYEOF'
import json, os, sys
try:
    pinned = json.load(open("/etc/enigma2/cineview_mla/runtime.json")).get("poster_cache")
except Exception:
    pinned = None
mounts = [l.split()[:4] for l in open("/proc/mounts") if len(l.split()) >= 4]
root = os.stat("/").st_dev
def real(mp, src, opts):
    try:
        return "rw" in opts.split(",") and os.path.ismount(mp) and os.stat(mp).st_dev != root and src.startswith("/dev/")
    except OSError:
        return False
def on_storage(path):  # a pinned cache is shown only when it is on /tmp or on real external storage, never the flash
    if path.startswith("/tmp/"):
        return True
    best = None
    for src, mp, fs, opts in mounts:
        if (path == mp or path.startswith(mp.rstrip("/") + "/")) and (best is None or len(mp) > len(best[1])):
            best = (src, mp, opts)
    return bool(best) and best[1] != "/" and real(best[1], best[0], best[2])
if pinned and on_storage(pinned):
    print("kept|" + pinned); sys.exit(0)
if sys.argv[1] != "0":
    for src, mp, fs, opts in mounts:
        if mp == "/media/hdd" and real(mp, src, opts):
            print("hdd|/media/hdd/poster"); sys.exit(0)
for src, mp, fs, opts in mounts:
    if mp.startswith("/media/") and mp != "/media/hdd" and real(mp, src, opts):
        try:
            names = os.listdir(mp)
        except OSError:
            continue
        if "STARTUP" in names or any(n.startswith("linuxrootfs") for n in names):
            continue  # multiboot media
        print("usb|" + os.path.join(mp, "cineview-mla", "poster")); sys.exit(0)
print(("tmpopt|" if sys.argv[1] == "0" else "tmp|") + "/tmp/CINEVIEW-MLA/poster")
PYEOF
)
case "$CACHE" in
	hdd\|*) ok "Poster cache: ${CACHE#*|} (hard disk)" ;;
	usb\|*) ok "Poster cache: ${CACHE#*|} (USB storage)" ;;
	kept\|*) ok "Poster cache: ${CACHE#*|} (your setting, kept)" ;;
	tmpopt\|*) warn "Poster cache: /tmp (HDD_CACHE=0 and no USB storage - posters are fetched again after a reboot)" ;;
	*) warn "Poster cache: /tmp (no hard disk or USB storage found - posters are fetched again after a reboot)" ;;
esac

section "Existing installation"
CUR=$(opkg status "$PKG" 2>/dev/null | sed -n 's/^Version: //p')
PST=$(opkg status "$PKG" 2>/dev/null | sed -n 's/^Status: //p')
MODE=install
# A maintainer script that failed leaves CineView's package entry incomplete (half-installed / unpacked /
# half-configured): the database names the new version while the old files are still in place.  Repair = one
# reinstall of the verified package; only CineView's own entry is involved.
case "$PST" in
	*half-installed*|*unpacked*|*half-configured*)
		warn "An earlier CineView MLA installation was not completed (package state: $PST)"
		MODE=repair ;;
esac
if [ "$MODE" = "repair" ]; then
	info "It is repaired with a verified reinstall of CineView MLA $VERSION"
elif [ -z "$CUR" ]; then
	info "No earlier CineView MLA installation"
else
	info "Current version: $CUR"
	info "New version:     $VERSION"
	if [ "$CUR" = "$VERSION" ] && [ "${FORCE:-0}" != "1" ]; then
		MODE=same
	elif opkg compare-versions "$CUR" '<<' "$VERSION" 2>/dev/null; then
		MODE=upgrade; ok "Upgrade: your design, theme, profiles, settings and poster cache are kept"
	elif [ "${FORCE:-0}" = "1" ] && [ "$CUR" = "$VERSION" ]; then
		MODE=reinstall; warn "Reinstall requested"
	elif [ "${FORCE:-0}" = "1" ]; then
		MODE=downgrade; warn "Return to the earlier version $VERSION requested (your design, theme and profiles are kept)"
	else
		fail "A newer CineView MLA ($CUR) is already installed."
	fi
fi
[ -d /usr/share/enigma2/CineView_FHD ] && info "CineView FHD (classic edition) found - it stays installed and independent"

if [ "${DRYRUN:-0}" = "1" ]; then
	printf '\n%s%sAll checks passed.%s Check-only run: nothing was downloaded or installed.\n\n' "$B" "$G" "$N"
	exit 0
fi

if [ "$MODE" != "same" ]; then
	section "Package"
	[ -n "$PKG_URL" ] || fail "CineView MLA is not published yet: no download address. Copy the package file to the receiver and run the installer with PKG_DIR=<folder>."
	case "$PKG_URL" in
		/*)  # a package file already on the receiver (PKG_DIR)
			cp "$PKG_URL" "$IPK" 2>/dev/null || fail "The package file cannot be read: $PKG_URL"
			[ "$(sha256sum "$IPK" 2>/dev/null | cut -d' ' -f1)" = "$PKG_SHA" ] \
				|| fail "The package file failed the SHA256 check (damaged or not the official file)." ;;
		*)  # GNU or BusyBox wget: idle timeout per attempt (a slow but moving download is never cut), up to 3
			# attempts that resume an interrupted download, SHA256 checked after each complete download
			command -v wget >/dev/null 2>&1 || fail "wget is not available on this receiver."
			TRIES=${CVMLA_TRIES:-3}; TMO=${CVMLA_TIMEOUT:-30}; NOCERT=""; n=0; WHY=""
			WOPT=""; wget --version 2>/dev/null | grep -q "GNU Wget" && WOPT="-t 3 --waitretry=3"  # GNU: bounded own retries
			rm -f "$IPK"
			while [ "$n" -lt "$TRIES" ]; do
				n=$((n + 1))
				wget -c -T "$TMO" $WOPT $NOCERT -O "$IPK" "$PKG_URL" >"$TMPD/wget.err" 2>&1; RC=$?
				if [ "$RC" -eq 0 ]; then
					[ "$(sha256sum "$IPK" 2>/dev/null | cut -d' ' -f1)" = "$PKG_SHA" ] && { WHY=""; break; }
					WHY=sha; rm -f "$IPK"  # complete but not the official file: the next attempt starts from zero
				else
					WHY=net
					if [ -z "$NOCERT" ] && { [ "$RC" -eq 5 ] || grep -qi "certificate\|ssl\|tls" "$TMPD/wget.err"; }; then
						# an image without current CA certificates: the file's integrity comes from the SHA256 above
						NOCERT="--no-check-certificate"; n=$((n - 1)); continue
					fi
					grep -q "ERROR 404\|404 Not Found" "$TMPD/wget.err" && { WHY=missing; break; }  # GNU / BusyBox wording
				fi
				[ "$n" -lt "$TRIES" ] && { info "Download interrupted - trying again ($((n + 1)) of $TRIES)"; sleep $((n * 3)); }
			done
			case "$WHY" in
				sha) fail "The downloaded package failed the SHA256 check (damaged or not the official file). Please try again later." ;;
				missing) fail "The package was not found at the distribution point (${PKG_URL##*/}). Please try again later." ;;
				net) fail "The package could not be downloaded. Please check the internet connection and run the installer again." ;;
			esac ;;
	esac
	ok "Package verified (SHA256)"
	[ "${CVMLA_FETCH_ONLY:-0}" = "1" ] && { printf '\nfetch-only test: package downloaded and verified; nothing was installed.\n'; exit 0; }  # test hook only

	section "Installing"
	if [ -d "$STATE" ] || [ -f /etc/enigma2/settings ]; then  # small restore point (settings + CineView state)
		BK="$STATE/backup/$(date +%Y%m%d-%H%M%S)"
		mkdir -p "$BK" 2>/dev/null && cp -p /etc/enigma2/settings "$BK/settings" 2>/dev/null
		if [ -d "$STATE" ]; then
			tar -C /etc/enigma2 --exclude=cineview_mla/backup -czf "$BK/cineview_mla.tgz" cineview_mla 2>/dev/null \
				|| tar -C "$STATE" -czf "$BK/cineview_mla.tgz" $(ls "$STATE" | grep -v '^backup$') 2>/dev/null
		fi
		ok "Restore point saved"
	fi
	for i in $(seq 1 30); do pidof opkg >/dev/null 2>&1 || break; sleep 2; done  # another package operation: wait for it
	OPT=""; case "$MODE" in reinstall|repair) OPT="--force-reinstall" ;; downgrade) OPT="--force-downgrade" ;; esac
	if ! opkg install $OPT "$IPK" >"$LOG" 2>&1; then
		PST=$(opkg status "$PKG" 2>/dev/null | sed -n 's/^Status: //p')
		if grep -q "killed by signal 11\|Segmentation fault" "$LOG" && ! grep -q "CineView MLA: .*Stopped\|installation stopped" "$LOG"; then
			# The image's shell crashed while running a package script - not a refusal by CineView's own checks.
			# CineView's preinst only checks (it changes nothing), so ONE reinstall of the same verified package
			# is safe.  Never a loop.
			warn "The image's shell crashed during the installation (signal 11) - one more attempt"
			if ! opkg install --force-reinstall "$IPK" >"$LOG.2" 2>&1; then
				PST=$(opkg status "$PKG" 2>/dev/null | sed -n 's/^Status: //p')
				printf '  %s[XX]%s The package manager stopped the installation twice (package state: %s).\n' "$R" "$N" "${PST:-none}"
				printf '\n%s%sCineView MLA was not installed.%s Run the installer again: it repairs the incomplete installation first.\n\n' "$B" "$R" "$N"
				exit 1
			fi
			cat "$LOG.2" >> "$LOG"
			ok "Second attempt completed"
		else
			REASON=$(grep -h "CineView MLA:\|Collected errors\|cannot\|Cannot\|error" "$LOG" | grep -v "^ \* opkg_" | head -3)
			case "$PST" in
				*half-installed*|*unpacked*|*half-configured*)
					# never leave CineView half-installed: one repair with the same, already verified package
					warn "The installation was interrupted - repairing it with the verified package"
					if opkg install --force-reinstall "$IPK" >"$LOG.r" 2>&1 && opkg status "$PKG" 2>/dev/null | grep -q "^Status: .* installed$"; then
						cat "$LOG.r" >> "$LOG"; ok "Installation repaired"
					else
						PST=$(opkg status "$PKG" 2>/dev/null | sed -n 's/^Status: //p')
						printf '  %s[XX]%s The package manager stopped the installation.%s\n' "$R" "$N" "${REASON:+ $REASON}"
						printf '\n%s%sCineView MLA was not installed%s and its package entry is incomplete (%s). Run the installer again to repair it.\n\n' "$B" "$R" "$N" "${PST:-none}"
						exit 1
					fi ;;
				*) fail "The package manager stopped the installation.${REASON:+ $REASON}" ;;
			esac
		fi
	fi
	PST=$(opkg status "$PKG" 2>/dev/null | sed -n 's/^Status: //p')
	case "$PST" in *" installed") ;; *) fail "The package state after installing is '${PST:-none}' (expected: installed)." ;; esac
	grep -q "factory design (Classic, Navy) is active" "$LOG" && warn "The previous design could not be kept: the factory design (Classic, Navy) is active"
	ok "CineView MLA $VERSION installed"
	if [ "${HDD_CACHE:-1}" = "0" ] && [ "${CACHE%%|*}" != "kept" ]; then
		python3 - "${CACHE#*|}" <<'PYEOF'
import json, os, sys
p = "/etc/enigma2/cineview_mla/runtime.json"
try:
    rt = json.load(open(p))
except Exception:
    rt = {}
rt["poster_cache"] = sys.argv[1]
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(rt, open(p, "w"), indent=1)
PYEOF
	fi
fi

section "Verification"
V=$(opkg status "$PKG" 2>/dev/null | sed -n 's/^Version: //p')
[ "$V" = "$VERSION" ] && ok "Package version $V" || fail "Installed version is '${V:-none}', expected $VERSION."
[ -f "$SKIN_DIR/skin.xml" ] && [ -e "$SKIN_DIR/active/theme.xml" ] && ok "Skin files present" || fail "Skin files are incomplete."
if python3 - "$PLG_DIR/plugin.pyc" "$PLG_DIR/plugin.py" <<'PYEOF'
import importlib.util, marshal, os, sys
for f in sys.argv[1:]:
    if os.path.isfile(f):
        if f.endswith(".pyc"):
            data = open(f, "rb").read()
            if data[:4] != importlib.util.MAGIC_NUMBER:
                sys.exit(1)
            marshal.loads(data[16:])
        else:
            compile(open(f).read(), f, "exec")
        sys.exit(0)
sys.exit(1)
PYEOF
then ok "Plugin loadable"; else fail "The CineView Designs plugin cannot be loaded by this Python."; fi
[ -s "$PLG_DIR/plugin.png" ] && ok "Plugin icon present" || fail "Plugin icon is missing."
grep -aq "CineView Designs" "$PLG_DIR"/plugin.py* 2>/dev/null && ok "CineView Designs available in the Plugin Browser" || fail "CineView Designs entry not found."

section "Result"
SKIN=$(sed -n 's/^config.skin.primary_skin=//p' /etc/enigma2/settings 2>/dev/null)
if [ "$MODE" = "same" ]; then
	printf '  %s%sCineView MLA %s is already installed and verified.%s\n' "$B" "$G" "$VERSION" "$N"
else
	printf '  %s%sCineView MLA %s installed successfully.%s\n' "$B" "$G" "$VERSION" "$N"
fi
case "$SKIN" in
	$SKIN_NAME/*)
		[ "$MODE" = "same" ] && { printf '\n'; exit 0; }
		printf '\n  %s+-----------------------------------------------------+%s\n' "$C" "$N"
		printf '  %s|%s  Restart the GUI to load CineView MLA %-13s %s|%s\n' "$C" "$N" "$VERSION." "$C" "$N"
		printf '  %s+-----------------------------------------------------+%s\n' "$C" "$N"
		DO="${RESTART:-}"
		if [ -z "$DO" ] && [ -t 0 ]; then printf '  Restart the GUI now? [y/N] '; read -r A; case "$A" in y|Y|yes|YES) DO=1 ;; esac; fi
		if [ "$DO" = "1" ]; then
			info "Restarting the GUI ..."
			wget -qO /dev/null "http://127.0.0.1/api/powerstate?newstate=3" 2>/dev/null || { init 4; sleep 4; init 3; }
		else
			info "Later: Menu > Standby / Restart > Restart GUI"
		fi ;;
	*)
		printf '\n  %sNext step:%s Menu > Setup > User Interface > Skin > %s%s%s, then restart the GUI.\n' "$C" "$N" "$B" "$SKIN_NAME" "$N"
		info "Then open CineView Designs from the Plugin Browser to choose designs and themes." ;;
esac
printf '\n'
exit 0
