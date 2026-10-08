#!/usr/bin/env python3
"""Smart Installer 1.2.0 = Smart Installer 1.1.0 (installer_vix/cineview-install.sh, SHA 40e4ccca...) + unified package
table with one distribution point, image identification by image-owned files (from each image's enigma2 source),
multi-brand receiver model check, tested-versions-only gate, ROLLBACK=1, PKG_DIR= local install, CVMLA_ROOT test hook.
Every edit is anchored on exact 1.1.0 text (each anchor must occur exactly once); the rest of 1.1.0 is kept as is.
usage: mkinstaller.py <installer 1.1.0> <out> <manifest.json> <package dir>"""
import hashlib
import json
import os
import sys

src, dst, manifest, pkgdir = sys.argv[1:5]
s = open(src).read()
if hashlib.sha256(s.encode()).hexdigest() != "40e4cccacbd433202539db6fab94932c7155fa7d0dac4e657fac98019c258709":
    sys.exit("source is not Smart Installer 1.1.0")


def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor found %d times: %r" % (n, old[:80]))
    s = s.replace(old, new)


def between(start, end, new):
    """replace the text from start (inclusive) to end (exclusive); both anchors must be unique"""
    global s
    for a in (start, end):
        if s.count(a) != 1:
            sys.exit("anchor found %d times: %r" % (s.count(a), a[:80]))
    i, j = s.index(start), s.index(end)
    assert i < j
    s = s[:i] + new + s[j:]


# ---------------------------------------------------------------- package table from the manifest (verified files)
m = json.load(open(manifest))
table = []
for key in ("openatv", "openbh", "openvix"):
    e = m["images"][key]
    for slot, pfx in (("current", ""), ("previous", "PREV_")):
        p = e[slot]
        path = os.path.join(pkgdir, key, p["file"])
        got = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if got != p["sha256"]:
            sys.exit("%s %s: SHA256 mismatch (%s)" % (key, p["file"], got))
        table.append('%s_%sVERSION="%s"; %s_%sFILE="%s"\n%s_%sSHA="%s"' % (
            key.upper(), pfx, p["version"], key.upper(), pfx, p["file"], key.upper(), pfx, p["sha256"]))
    table.append('%s_PY="%s"' % (key.upper(), e["python"]))
dist = m.get("dist_base", "")
if dist and not dist.startswith("https://"):
    sys.exit("dist_base must be an https address or empty")

rep('INSTALLER_VERSION="1.1.0"', 'INSTALLER_VERSION="%s"' % m["installer_version"])
rep('''# usage on the receiver (telnet / ssh):
#   wget -qO /tmp/cineview-install.sh "<raw url of this file>" && sh /tmp/cineview-install.sh
# options:  DRYRUN=1  checks only      HDD_CACHE=0  keep the poster cache off the hard disk
#           RESTART=1 restart the GUI at the end without asking''',
    '''# One installer for OpenATV, OpenBH and OpenViX.  Usage on the receiver (telnet / ssh):
#   wget -qO /tmp/cineview-install.sh "<distribution point>/cineview-install.sh" && sh /tmp/cineview-install.sh
# options:  DRYRUN=1  checks only      HDD_CACHE=0  keep the poster cache off the hard disk
#           RESTART=1 restart the GUI at the end without asking
#           ROLLBACK=1  return to the previous released version for this image (SHA256-verified, settings kept)
#           PKG_DIR=<folder>  install from package files copied to the receiver (USB / local), same SHA256 check''')

between('# One package per image, built from the same CineView MLA source', 'INFO="${CVMLA_INFO:-/usr/lib/enigma.info}"',
    '''# One package per image, built from the same CineView MLA source (Common Core + image adapter).  Only these exact
# files are ever installed: each is pinned by its SHA256 here, in the installer itself (a download is never trusted
# by its address).  Tested image versions only: OpenATV 8.0, OpenBH 5.6, OpenViX 6.9 (user decision 2026-10-08).
# Distribution point: ONE address for every image - <DIST_BASE>/cineview-install.sh and
# <DIST_BASE>/packages/<image>/<file>.  Empty = not published yet: then only PKG_DIR (local copies) can be used;
# no address is ever guessed.
DIST_BASE="%s"
%s
''' % (dist, "\n".join(table)))
rep('INFO="${CVMLA_INFO:-/usr/lib/enigma.info}"  # CVMLA_INFO: test hook only (another enigma.info)',
    '''RT="${CVMLA_ROOT:-}"  # CVMLA_ROOT: test hook only (a simulated receiver root for the identification checks)
INFO="${CVMLA_INFO:-$RT/usr/lib/enigma.info}"  # CVMLA_INFO: test hook only (another enigma.info)''')

# ---------------------------------------------------------------- Device + Image
between('section "Device"\n', 'section "Version"\n', r'''LOCK=/tmp/.cvmla.lock  # one installer at a time; a lock left by a run that was killed is taken over
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

''')

# ---------------------------------------------------------------- Version: tested versions only + package source
between('section "Version"\n', 'section "Python"\n', r'''section "Version"
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

''')

rep('''PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)''',
    '''PYV=${CVMLA_PYV:-$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)}  # CVMLA_PYV: test hook only''')
rep('H=/usr/bin/enigma2_pre_start.sh\n', 'H="$RT/usr/bin/enigma2_pre_start.sh"\n')
rep('''	case "$PKG_URL$PKG_SHA" in *@*) fail "This installer has no package address. Please download the official installer again." ;; esac''',
    '''	[ -n "$PKG_URL" ] || fail "CineView MLA is not published yet: no download address. Copy the package file to the receiver and run the installer with PKG_DIR=<folder>."''')
rep('''	case "$PKG_URL" in
		/*) cp "$PKG_URL" "$IPK" 2>/dev/null ;;  # a package file already on the receiver
		*) wget -q -T 60 -t 2 -O "$IPK" "$PKG_URL" 2>/dev/null ;;
	esac || fail "The package could not be downloaded. Please check the internet connection."
	GOT=$(sha256sum "$IPK" 2>/dev/null | cut -d' ' -f1)
	[ "$GOT" = "$PKG_SHA" ] || fail "The package failed the SHA256 check (damaged or not the official file)."
''', r'''	case "$PKG_URL" in
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
''')

# free space: POSIX output (-P) - a long device name (LVM, by-uuid) wraps the default df output onto two lines
rep("""FREE=$(df -k / | awk 'NR==2 {print $4}')
TFREE=$(df -k /tmp | awk 'NR==2 {print $4}')""", """FREE=$(df -Pk / | awk 'NR==2 {print $4}')
TFREE=$(df -Pk /tmp | awk 'NR==2 {print $4}')""")

rep('''	ok "Package verified (SHA256)"
''', '''	ok "Package verified (SHA256)"
	[ "${CVMLA_FETCH_ONLY:-0}" = "1" ] && { printf '\\nfetch-only test: package downloaded and verified; nothing was installed.\\n'; exit 0; }  # test hook only
''')
rep('''	OPT=""; case "$MODE" in reinstall|repair) OPT="--force-reinstall" ;; downgrade) OPT="--force-downgrade" ;; esac
''', '''	for i in $(seq 1 30); do pidof opkg >/dev/null 2>&1 || break; sleep 2; done  # another package operation: wait for it
	OPT=""; case "$MODE" in reinstall|repair) OPT="--force-reinstall" ;; downgrade) OPT="--force-downgrade" ;; esac
''')
rep('''			case "$PST" in
				*half-installed*|*unpacked*|*half-configured*)
					printf '  %s[XX]%s The package manager stopped the installation.%s\\n' "$R" "$N" "${REASON:+ $REASON}"
					printf '\\n%s%sCineView MLA was not installed%s and its package entry is incomplete (%s). Run the installer again to repair it.\\n\\n' "$B" "$R" "$N" "$PST"
					exit 1 ;;
			esac
			fail "The package manager stopped the installation.${REASON:+ $REASON}"''', '''			case "$PST" in
				*half-installed*|*unpacked*|*half-configured*)
					# never leave CineView half-installed: one repair with the same, already verified package
					warn "The installation was interrupted - repairing it with the verified package"
					if opkg install --force-reinstall "$IPK" >"$LOG.r" 2>&1 && opkg status "$PKG" 2>/dev/null | grep -q "^Status: .* installed$"; then
						cat "$LOG.r" >> "$LOG"; ok "Installation repaired"
					else
						PST=$(opkg status "$PKG" 2>/dev/null | sed -n 's/^Status: //p')
						printf '  %s[XX]%s The package manager stopped the installation.%s\\n' "$R" "$N" "${REASON:+ $REASON}"
						printf '\\n%s%sCineView MLA was not installed%s and its package entry is incomplete (%s). Run the installer again to repair it.\\n\\n' "$B" "$R" "$N" "${PST:-none}"
						exit 1
					fi ;;
				*) fail "The package manager stopped the installation.${REASON:+ $REASON}" ;;
			esac''')
# lock released on every exit (only by the run that holds it); HUP (lost telnet / ssh session) cleans up as well
rep('''	rm -rf "$TMPD" 2>/dev/null
	case "$SELF" in''', '''	rm -rf "$TMPD" 2>/dev/null
	[ "${HAVELOCK:-0}" = "1" ] && rm -rf /tmp/.cvmla.lock 2>/dev/null
	case "$SELF" in''')
rep("trap 'exit 130' INT TERM\n", "trap 'exit 130' INT TERM HUP\n")

assert "@" not in "".join(table) and "has key_menu" not in s and "PluginBrowser.py" not in s
open(dst, "w").write(s)
print("written %s (%s)" % (dst, hashlib.sha256(s.encode()).hexdigest()))
