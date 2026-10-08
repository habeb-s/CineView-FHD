#!/bin/sh
# CineView MLA Smart Installer - Design & Development by habeb-s (c) 2026
# usage on the receiver (telnet / ssh):
#   wget -qO /tmp/cineview-install.sh "<raw url of this file>" && sh /tmp/cineview-install.sh
# options:  DRYRUN=1  checks only      HDD_CACHE=0  keep the poster cache off the hard disk
#           RESTART=1 restart the GUI at the end without asking
# Every check runs before anything is changed; any failure stops the installer and nothing is changed.
INSTALLER_VERSION="1.1.0"
PKG="enigma2-plugin-skins-cineview-fhd-mla"
# One package per image, built from the same CineView MLA source (Common Core + image adapter).  The image is taken
# from the image's own build information (/usr/lib/enigma.info "distro"), cross-checked with a native screen
# contract of that image; a receiver model list is never used.
#   openatv: OpenATV 8.0 (7.6 when its Python matches), Python 3.14 - the published 1.0.0 package
OPENATV_VERSION="1.0.0"
OPENATV_URL="https://raw.githubusercontent.com/habeb-s/CineView-MLA/main/release/1.0.0/enigma2-plugin-skins-cineview-fhd-mla_1.0.0_all.ipk"
OPENATV_SHA="4709881b66ae9e5b8cc8dfa7f5b7e3fafdfb57d779431709b8c5c1b48c4cb0a8"
OPENATV_PY="3.14"
#   openbh: OpenBH 5.6, Python 3.13 - NOT RELEASED YET: no package address until the OpenBH package is published
OPENBH_VERSION="@OPENBH_VERSION@"
OPENBH_URL="@OPENBH_URL@"
OPENBH_SHA="@OPENBH_SHA@"
OPENBH_PY="3.13"
#   openvix: OpenViX 6.9, Python 3.14 - tested on OpenViX 6.9.002; NOT RELEASED YET: no package address until the
#   OpenViX package is published (the package SHA256 is fixed: only that exact file is ever installed)
OPENVIX_VERSION="1.0.0~openvix1"
OPENVIX_URL="@OPENVIX_URL@"
OPENVIX_SHA="955d102826bf30854003a7f5cd8e5d75b4f9e808b783bfe1fb53571acfa76d87"
OPENVIX_PY="3.14"
INFO="${CVMLA_INFO:-/usr/lib/enigma.info}"  # CVMLA_INFO: test hook only (another enigma.info)
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
	case "$SELF" in /tmp/cineview-install*.sh) rm -f "$SELF" 2>/dev/null ;; esac
}
trap cleanup EXIT
trap 'exit 130' INT TERM

section() { printf '\n%s%s%s\n' "$B$C" "$1" "$N"; }
ok()   { printf '  %s[OK]%s %s\n' "$G" "$N" "$1"; }
info() { printf '  %s[..]%s %s\n' "$C" "$N" "$1"; }
warn() { printf '  %s[!!]%s %s\n' "$Y" "$N" "$1"; }
fail() { printf '  %s[XX]%s %s\n' "$R" "$N" "$1"; printf '\n%s%sCineView MLA was not installed.%s Nothing was changed on this receiver.\n\n' "$B" "$R" "$N"; exit 1; }
kv()   { sed -n "s/^$1='\{0,1\}\([^']*\)'\{0,1\}$/\1/p" "$INFO" 2>/dev/null | head -1; }

printf '\n%s%s  CineView MLA Smart Installer  %s  %sversion %s%s\n' "$B" "$W" "$N" "$C" "$INSTALLER_VERSION" "$N"
printf '  %sDesign & Development by habeb-s (c) 2026%s\n' "$W" "$N"

section "Device"
[ -x /usr/bin/enigma2 ] && [ -d /usr/lib/enigma2/python/Components ] || fail "Enigma2 was not found on this receiver."
[ -r "$INFO" ] || fail "The image information (/usr/lib/enigma.info) is missing: the image cannot be identified."
BRAND=$(kv displaybrand); MODEL=$(kv displaymodel); MB=$(kv machinebuild)
[ -n "$MB" ] || fail "The receiver model cannot be identified."
VUM=$(cat /proc/stb/info/vumodel 2>/dev/null)
if [ -n "$VUM" ] && [ "$MB" != "vu$VUM" ]; then
	fail "The receiver model is ambiguous (image: $MB, Vu+ driver: $VUM): nothing is installed."
fi
ok "${BRAND:+$BRAND }${MODEL:-$MB}"

section "Image"
DISTRO=$(kv distro); IVER=$(kv imageversion)
# second, independent evidence: the image's own Plugin Browser contract (OpenATV: PackageAction; OpenBH:
# PluginDownloadBrowser and no PackageAction; OpenViX: PluginDownloadBrowser, no PackageAction and no key_menu).
# Disagreement with enigma.info = the image is not identified.
PB=$(ls /usr/lib/enigma2/python/Screens/PluginBrowser.py* 2>/dev/null | head -1)
has() { [ -n "$PB" ] && python3 -c 'import sys; sys.exit(0 if sys.argv[2].encode() in open(sys.argv[1], "rb").read() else 1)' "$PB" "$1" 2>/dev/null; }
case "$DISTRO" in
	openatv)
		IMG="OpenATV"; VERSION="$OPENATV_VERSION"; PKG_URL="$OPENATV_URL"; PKG_SHA="$OPENATV_SHA"; PY_NEED="$OPENATV_PY"
		has PackageAction || fail "enigma.info names OpenATV, but the image's screens are not OpenATV's: the image cannot be identified reliably." ;;
	openbh)
		IMG="OpenBH"; VERSION="$OPENBH_VERSION"; PKG_URL="$OPENBH_URL"; PKG_SHA="$OPENBH_SHA"; PY_NEED="$OPENBH_PY"
		{ has PluginDownloadBrowser && ! has PackageAction && has key_menu; } || fail "enigma.info names OpenBH, but the image's screens are not OpenBH's: the image cannot be identified reliably." ;;
	openvix)
		IMG="OpenViX"; VERSION="$OPENVIX_VERSION"; PKG_URL="$OPENVIX_URL"; PKG_SHA="$OPENVIX_SHA"; PY_NEED="$OPENVIX_PY"
		{ has PluginDownloadBrowser && ! has PackageAction && ! has key_menu; } || fail "enigma.info names OpenViX, but the image's screens are not OpenViX's: the image cannot be identified reliably." ;;
	"") fail "This image does not name itself in /usr/lib/enigma.info: it cannot be identified." ;;
	*) fail "This image is '$DISTRO'. CineView MLA supports OpenATV, OpenBH and OpenViX." ;;
esac
ok "$IMG $IVER detected"

section "Version"
case "$DISTRO:$IVER" in
	openatv:8.0|openatv:8.0.*) ok "OpenATV $IVER is supported (fully tested on OpenATV 8.0)" ;;
	openatv:7.6|openatv:7.6.*) warn "OpenATV $IVER: the screens are compatible; the Python check below decides" ;;
	openatv:7.[0-5]|openatv:7.[0-5].*|openatv:6.*|openatv:5.*) fail "OpenATV $IVER is too old: it lacks skin features CineView MLA needs. Please update to OpenATV 8.0." ;;
	openbh:5.6|openbh:5.6.*) ok "OpenBH $IVER is supported (tested on OpenBH 5.6)" ;;
	openbh:[0-4]|openbh:[0-4].*|openbh:5.[0-5]|openbh:5.[0-5].*) fail "OpenBH $IVER is too old: CineView MLA needs OpenBH 5.6 or newer." ;;
	openvix:6.9|openvix:6.9.*) ok "OpenViX $IVER is supported (tested on OpenViX 6.9)" ;;
	openvix:[0-5]|openvix:[0-5].*|openvix:6.[0-8]|openvix:6.[0-8].*) fail "OpenViX $IVER is too old: CineView MLA for OpenViX is built and tested for OpenViX 6.9." ;;
	*) fail "$IMG $IVER has not been checked with CineView MLA yet." ;;
esac
# the package for this image (CVMLA_PKG_URL / CVMLA_PKG_SHA / CVMLA_VERSION: test overrides)
PKG_URL="${CVMLA_PKG_URL:-$PKG_URL}"; PKG_SHA="${CVMLA_PKG_SHA:-$PKG_SHA}"; VERSION="${CVMLA_VERSION:-$VERSION}"
case "$PKG_URL$PKG_SHA$VERSION" in *@*) fail "The $IMG package of CineView MLA is not released yet." ;; esac

section "Python"
PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)
[ -n "$PYV" ] || fail "Python 3 was not found."
[ "$PYV" = "$PY_NEED" ] || fail "Python $PYV found; this package is built for Python $PY_NEED ($IMG)."
ok "Python $PYV compatible"

section "Architecture"
ARCH=$(kv architecture); [ -n "$ARCH" ] || ARCH=$(uname -m)
opkg print-architecture 2>/dev/null | grep -q "^arch all " || fail "This receiver does not accept architecture-independent packages."
ok "Architecture: $ARCH (CineView MLA is architecture-independent)"

section "Compatibility"
H=/usr/bin/enigma2_pre_start.sh
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
FREE=$(df -k / | awk 'NR==2 {print $4}')
TFREE=$(df -k /tmp | awk 'NR==2 {print $4}')
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
	case "$PKG_URL$PKG_SHA" in *@*) fail "This installer has no package address. Please download the official installer again." ;; esac
	case "$PKG_URL" in
		/*) cp "$PKG_URL" "$IPK" 2>/dev/null ;;  # a package file already on the receiver
		*) wget -q -T 60 -t 2 -O "$IPK" "$PKG_URL" 2>/dev/null ;;
	esac || fail "The package could not be downloaded. Please check the internet connection."
	GOT=$(sha256sum "$IPK" 2>/dev/null | cut -d' ' -f1)
	[ "$GOT" = "$PKG_SHA" ] || fail "The package failed the SHA256 check (damaged or not the official file)."
	ok "Package verified (SHA256)"

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
					printf '  %s[XX]%s The package manager stopped the installation.%s\n' "$R" "$N" "${REASON:+ $REASON}"
					printf '\n%s%sCineView MLA was not installed%s and its package entry is incomplete (%s). Run the installer again to repair it.\n\n' "$B" "$R" "$N" "$PST"
					exit 1 ;;
			esac
			fail "The package manager stopped the installation.${REASON:+ $REASON}"
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
