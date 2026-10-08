#!/usr/bin/env python3
"""Smart Installer 1.2.1 = 1.2.0 (final/dist/cineview-install.sh, SHA 9fe790cf...) with the user's pre-publication
conditions (2026-10-08 21:52) only:
  1. no package list / addresses in the public script: packages come from the protected distribution service
  2. no image compatibility rules in the public script: the service decides (the script sends the image facts)
  3. no automatic HTTPS certificate bypass: Python (always installed) with certificate verification; missing root
     certificates are updated from the image's own feed (ca-certificates), verification stays on
  4./5. same visible stages; the temporary package is removed silently on every exit (unchanged trap)
Everything else of 1.2.0 is kept.  usage: mkinstaller_svc.py <installer 1.2.0> <client helper> <out> [service url]"""
import hashlib
import sys

src, helper, dst = sys.argv[1:4]
service = sys.argv[4] if len(sys.argv) > 4 else ""
s = open(src).read()
if hashlib.sha256(s.encode()).hexdigest() != "9fe790cf14ca253532cf6937ce9f4847503cc02cf68773f6d4b66f2c9f21c04e":
    sys.exit("source is not Smart Installer 1.2.0 (9fe790cf)")
if service and not service.startswith("https://"):
    sys.exit("the service address must be https")
h = open(helper).read()
assert "PYEOF" not in h


def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor found %d times: %r" % (n, old[:80]))
    s = s.replace(old, new)


def between(start, end, new, keep_end=True):
    global s
    for a in (start, end):
        if s.count(a) != 1:
            sys.exit("anchor found %d times: %r" % (s.count(a), a[:80]))
    i, j = s.index(start), s.index(end)
    assert i < j
    s = s[:i] + new + (s[j:] if keep_end else s[j + len(end):])


rep('INSTALLER_VERSION="1.2.0"', 'INSTALLER_VERSION="1.2.1"')
rep('#   wget -qO /tmp/cineview-install.sh "<distribution point>/cineview-install.sh" && sh /tmp/cineview-install.sh',
    '#   wget -qO /tmp/cineview-install.sh "<installer address>" && sh /tmp/cineview-install.sh')
rep('#           PKG_DIR=<folder>  install from package files copied to the receiver (USB / local), same SHA256 check',
    '#           PKG_DIR=<folder>  install from a package file copied to the receiver (USB / local), same SHA256 check')
between('# One package per image, built from the same CineView MLA source', 'RT="${CVMLA_ROOT:-}"',
        '''# The packages are not in a public place.  The CineView MLA distribution service decides which package fits this
# receiver and returns its version, its SHA256 and a short-lived HTTPS link; the file must match that SHA256 or
# nothing is installed.  HTTPS certificates are always verified.  No account, key or login is needed.
SERVICE="%s"  # empty until the distribution service is in operation
''' % service)

# ---- Image: facts here, decision by the service
between("# Second, independent evidence: files that only that image's own enigma2 ships",
        'ok "$IMG $IVER detected (image information and the image\'s own files agree)"\n',
        r'''[ -n "$DISTRO" ] || fail "This image does not name itself in /usr/lib/enigma.info: it cannot be identified."
# The installer sends the image facts (enigma.info, Python, which of the files the service asks about exist); the
# service answers with the image, the tested-version decision and the package.  No rules are kept in this script.
E="$RT/usr/lib/enigma2/python"
SVC="${CVMLA_SERVICE:-$SERVICE}"  # CVMLA_SERVICE: test hook only
[ -n "$SVC" ] || fail "The CineView MLA distribution service is not available yet. Please try again later."
command -v python3 >/dev/null 2>&1 || fail "Python 3 was not found."
cat > "$TMPD/cvsvc.py" <<'PYEOF'
''' + h + r'''PYEOF
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
''', keep_end=False)

# ---- Version: the service's decision is shown
between('section "Version"\n', 'section "Python"\n', r'''section "Version"
ok "$SUPPORT"
if [ "${ROLLBACK:-0}" = "1" ]; then FORCE=1; info "Rollback requested: CineView MLA $VERSION (previous release for $IMG)"; fi
[ -n "${PKG_DIR:-}" ] && PKG_URL="${PKG_DIR%/}/$PKG_FILE"
case "$PKG_URL" in
	/*) ok "Package source: $PKG_URL (local file)" ;;
	*) ok "Package source: CineView MLA distribution service" ;;
esac

''')

# ---- Package: verified HTTPS download (Python), resume, retries, SHA256; one new link if the link expired
between('	[ -n "$PKG_URL" ] || fail "CineView MLA is not published yet', '	ok "Package verified (SHA256)"\n', r'''	case "$PKG_URL" in
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
''')

for gone in ("OPENATV_", "OPENBH_", "OPENVIX_", "M_OPENATV", "no-check-certificate", "DIST_BASE", "4709881b", "Components/International"):
    assert gone not in s, gone
open(dst, "w").write(s)
print("written %s (%s)" % (dst, hashlib.sha256(s.encode()).hexdigest()))
