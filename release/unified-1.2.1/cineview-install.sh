#!/bin/sh
# CineView MLA Smart Installer - Design & Development by habeb-s (c) 2026
# One installer for OpenATV, OpenBH and OpenViX.  Usage on the receiver (telnet / ssh):
#   wget -qO /tmp/cineview-install.sh "<installer address>" && sh /tmp/cineview-install.sh
# options:  DRYRUN=1  checks only      HDD_CACHE=0  keep the poster cache off the hard disk
#           RESTART=1 restart the GUI at the end without asking
#           ROLLBACK=1  return to the previous released version for this image (SHA256-verified, settings kept)
#           PKG_DIR=<folder>  install from a package file copied to the receiver (USB / local), same SHA256 check
# Every check runs before anything is changed; any failure stops the installer and nothing is changed.
INSTALLER_VERSION="1.2.1"
PKG="enigma2-plugin-skins-cineview-fhd-mla"
# The packages are not in a public place.  The CineView MLA distribution service decides which package fits this
# receiver and returns its version, its SHA256 and a short-lived HTTPS link; the file must match that SHA256 or
# nothing is installed.  HTTPS certificates are always verified.  No account, key or login is needed.
SERVICE=""  # empty until the distribution service is in operation
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
[ -n "$DISTRO" ] || fail "This image does not name itself in /usr/lib/enigma.info: it cannot be identified."
# The installer sends the image facts (enigma.info, Python, which of the files the service asks about exist); the
# service answers with the image, the tested-version decision and the package.  No rules are kept in this script.
E="$RT/usr/lib/enigma2/python"
SVC="${CVMLA_SERVICE:-$SERVICE}"  # CVMLA_SERVICE: test hook only
[ -n "$SVC" ] || fail "The CineView MLA distribution service is not available yet. Please try again later."
command -v python3 >/dev/null 2>&1 || fail "Python 3 was not found."
cat > "$TMPD/cvsvc.py" <<'PYEOF'
import hashlib, json, os, re, ssl, sys, time, urllib.error, urllib.request
# CineView MLA installer helper: HTTPS with certificate verification ALWAYS on (never disabled).
# exit: 0 ok | 2 SHA256 mismatch | 3 refused / not found / link expired | 4 network | 5 certificate not verifiable


def ctx():
    c = ssl.create_default_context()
    if not c.cert_store_stats().get("x509_ca"):  # image CA bundle not in OpenSSL's default place: add it, still verified
        for f in ("/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt", "/etc/ssl/cert.pem"):
            if os.path.isfile(f):
                try:
                    c.load_verify_locations(f)
                except Exception:
                    pass
        try:
            import certifi
            c.load_verify_locations(certifi.where())
        except Exception:
            pass
    return c


def code(e):
    r = getattr(e, "reason", None)
    if isinstance(e, ssl.SSLCertVerificationError) or isinstance(r, ssl.SSLCertVerificationError):
        return 5
    if isinstance(e, urllib.error.HTTPError):
        return 3 if e.code in (403, 404, 410) else 4
    return 4


def get(url):
    last = 4
    for n in range(3):
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=20, context=ctx()).read().decode())
            break
        except Exception as e:
            last = code(e)
            if last == 5:
                return 5
            time.sleep(2 * (n + 1))
    else:
        return last
    for p in d.get("paths", []):
        if re.match(r"^[A-Za-z0-9_/]+$", p):
            print("P=" + p)
    for k, v in d.items():
        if k != "paths" and re.match(r"^[a-z0-9_]+$", k):
            print("%s=%s" % (k.upper(), str(int(v) if isinstance(v, bool) else v).replace("\n", " ")))
    return 0


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def fetch(url, out, want, tries, tmo):
    last = 4
    for n in range(1, tries + 1):
        try:
            have = os.path.getsize(out) if os.path.exists(out) else 0
            req = urllib.request.Request(url, headers={"Range": "bytes=%d-" % have} if have else {})
            try:
                r = urllib.request.urlopen(req, timeout=tmo, context=ctx())  # timeout = idle time, not total time
            except urllib.error.HTTPError as e:
                if e.code != 416:
                    raise
                r = None  # the file is already complete
            if r is not None:
                mode = "ab" if have and r.status == 206 else "wb"
                expect = int(r.headers.get("Content-Length") or -1)
                got = 0
                with open(out, mode) as f:
                    for b in iter(lambda: r.read(1 << 16), b""):
                        f.write(b)
                        got += len(b)
                if expect >= 0 and got < expect:  # connection closed early: keep the part, the next attempt resumes
                    raise ConnectionError("incomplete")
            if sha(out) == want:
                return 0
            os.remove(out)  # complete but not the official file: the next attempt starts from zero
            last = 2
        except Exception as e:
            last = code(e)
            if last in (3, 5):
                return last
        if n < tries:
            sys.stderr.write("  [..] Download interrupted - trying again (%d of %d)\n" % (n + 1, tries))
            sys.stderr.flush()
            time.sleep(3 * n)
    return last


if __name__ == "__main__":
    if sys.argv[1] == "get":
        sys.exit(get(sys.argv[2]))
    sys.exit(fetch(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6])))
PYEOF
CAFIX=0
svc() {  # svc <url>: one request to the service -> $TMPD/svc.out (KEY=value lines)
	python3 "$TMPD/cvsvc.py" get "$1" > "$TMPD/svc.out" 2>/dev/null; SR=$?
	if [ "$SR" -eq 5 ] && [ "$CAFIX" -eq 0 ]; then
		# the image's root certificates are missing or out of date: update them from the image's own package feed
		# (verification is never switched off), then try once more
		CAFIX=1; opkg update >/dev/null 2>&1; opkg install ca-certificates >/dev/null 2>&1
		python3 "$TMPD/cvsvc.py" get "$1" > "$TMPD/svc.out" 2>/dev/null; SR=$?
	fi
	case "$SR" in
		0) ;;
		5) fail "The secure connection to the CineView MLA service could not be verified (HTTPS certificate). Please update the image's root certificates (ca-certificates) and try again." ;;
		*) fail "The CineView MLA service cannot be reached. Please check the internet connection and try again." ;;
	esac
}
val() { sed -n "s/^$1=//p" "$TMPD/svc.out" | head -n 1; }
svc "$SVC/v1/probe"
FOUND=""
for p in $(sed -n 's/^P=//p' "$TMPD/svc.out"); do
	if ls "$E/$p.py" "$E/$p.pyc" 2>/dev/null | grep -q .; then FOUND="${FOUND}1"; else FOUND="${FOUND}0"; fi
done
PYV=${CVMLA_PYV:-$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)}
CH=current; [ "${ROLLBACK:-0}" = "1" ] && CH=previous
Q="distro=$(printf '%s' "$DISTRO" | tr -cd 'A-Za-z0-9._-')&version=$(printf '%s' "$IVER" | tr -cd 'A-Za-z0-9._-')&python=$PYV&found=$FOUND&channel=$CH${CVMLA_SVC_QUERY:+&$CVMLA_SVC_QUERY}"  # CVMLA_SVC_QUERY: test hook only
svc "$SVC/v1/resolve?$Q"
[ "$(val OK)" = "1" ] || fail "$(val MESSAGE)"
IMG=$(val IMAGE); SUPPORT=$(val SUPPORT); PY_NEED=$(val PYTHON); VERSION=$(val VERSION)
PKG_FILE=$(val FILE); PKG_SHA=$(val SHA256); PKG_URL="$SVC$(val URL)"
case "$PKG_SHA" in *[!0-9a-f]*|"") fail "The CineView MLA service sent an incomplete answer. Please try again later." ;; esac
[ ${#PKG_SHA} -eq 64 ] && [ -n "$VERSION" ] && [ -n "$PKG_FILE" ] && [ -n "$PY_NEED" ] \
	|| fail "The CineView MLA service sent an incomplete answer. Please try again later."
ok "$IMG $IVER detected (image information and the image's own files agree)"

section "Version"
ok "$SUPPORT"
if [ "${ROLLBACK:-0}" = "1" ]; then FORCE=1; info "Rollback requested: CineView MLA $VERSION (previous release for $IMG)"; fi
[ -n "${PKG_DIR:-}" ] && PKG_URL="${PKG_DIR%/}/$PKG_FILE"
case "$PKG_URL" in
	/*) ok "Package source: $PKG_URL (local file)" ;;
	*) ok "Package source: CineView MLA distribution service" ;;
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
	case "$PKG_URL" in
		/*)  # a package file already on the receiver (PKG_DIR)
			cp "$PKG_URL" "$IPK" 2>/dev/null || fail "The package file cannot be read: $PKG_URL"
			[ "$(sha256sum "$IPK" 2>/dev/null | cut -d' ' -f1)" = "$PKG_SHA" ] \
				|| fail "The package file failed the SHA256 check (damaged or not the official file)." ;;
		*)  # idle timeout per attempt (a slow but moving download is never cut), up to 3 attempts resuming an
			# interrupted download, SHA256 after each complete download, HTTPS certificate always verified
			python3 "$TMPD/cvsvc.py" fetch "$PKG_URL" "$IPK" "$PKG_SHA" "${CVMLA_TRIES:-3}" "${CVMLA_TIMEOUT:-30}"; FR=$?
			if [ "$FR" -eq 3 ]; then  # the short-lived link expired or was refused: one new link from the service
				svc "$SVC/v1/resolve?$Q"; PKG_URL="$SVC$(val URL)"; rm -f "$IPK"
				python3 "$TMPD/cvsvc.py" fetch "$PKG_URL" "$IPK" "$PKG_SHA" "${CVMLA_TRIES:-3}" "${CVMLA_TIMEOUT:-30}"; FR=$?
			fi
			case "$FR" in
				0) ;;
				2) fail "The downloaded package failed the SHA256 check (damaged or not the official file). Please try again later." ;;
				3) fail "The package is not available from the CineView MLA service right now. Please try again later." ;;
				5) fail "The secure connection to the CineView MLA service could not be verified (HTTPS certificate). Please update the image's root certificates (ca-certificates) and try again." ;;
				*) fail "The package could not be downloaded. Please check the internet connection and run the installer again." ;;
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
