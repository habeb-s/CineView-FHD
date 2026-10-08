#!/usr/bin/env python3
"""Smart Installer 1.2.2 = 1.2.0 (9fe790cf) for GitHub-only distribution (user decision 2026-10-08 22:34):
packages are GitHub release assets (one tag), never in the repository tree; no HTTPS certificate bypass (missing
root certificates are updated from the image's own feed once, verification stays on).  Nothing else changes."""
import hashlib, sys
src, dst, base = sys.argv[1:4]
s = open(src).read()
assert hashlib.sha256(s.encode()).hexdigest() == "9fe790cf14ca253532cf6937ce9f4847503cc02cf68773f6d4b66f2c9f21c04e"
assert base.startswith("https://github.com/habeb-s/")
def rep(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:70]); s = s.replace(a, b)
rep('INSTALLER_VERSION="1.2.0"', 'INSTALLER_VERSION="1.2.2"')
rep('''# Distribution point: ONE address for every image - <DIST_BASE>/cineview-install.sh and
# <DIST_BASE>/packages/<image>/<file>.  Empty = not published yet: then only PKG_DIR (local copies) can be used;''',
'''# Distribution point: the packages are assets of one GitHub release, <DIST_BASE>/<file> (not in any repository
# tree).  Empty = not published: then only PKG_DIR (local copies) can be used;''')
rep('DIST_BASE=""', 'DIST_BASE="%s"' % base)
rep('PKG_URL="${CVMLA_DIST_BASE:-$DIST_BASE}/packages/$DISTRO/$PKG_FILE"', 'PKG_URL="${CVMLA_DIST_BASE:-$DIST_BASE}/$(printf \'%s\' "$PKG_FILE" | tr \'~\' \'.\')"  # GitHub stores ~ as . in asset names')
rep('TRIES=${CVMLA_TRIES:-3}; TMO=${CVMLA_TIMEOUT:-30}; NOCERT=""; n=0; WHY=""', 'TRIES=${CVMLA_TRIES:-3}; TMO=${CVMLA_TIMEOUT:-30}; CAFIX=0; n=0; WHY=""')
rep('wget -c -T "$TMO" $WOPT $NOCERT -O "$IPK"', 'wget -c -T "$TMO" $WOPT -O "$IPK"')
rep('''					if [ -z "$NOCERT" ] && { [ "$RC" -eq 5 ] || grep -qi "certificate\\|ssl\\|tls" "$TMPD/wget.err"; }; then
						# an image without current CA certificates: the file's integrity comes from the SHA256 above
						NOCERT="--no-check-certificate"; n=$((n - 1)); continue
					fi''', '''					if [ "$CAFIX" = "0" ] && { [ "$RC" -eq 5 ] || grep -qi "certificate" "$TMPD/wget.err"; }; then
						# the image's root certificates are missing or out of date: update them from the image's own
						# package feed once - certificate verification is never switched off
						CAFIX=1; opkg update >/dev/null 2>&1; opkg install ca-certificates >/dev/null 2>&1; n=$((n - 1)); continue
					fi
					[ "$CAFIX" = "1" ] && { [ "$RC" -eq 5 ] || grep -qi "certificate" "$TMPD/wget.err"; } && { WHY=cert; break; }''')
rep('''				net) fail "The package could not be downloaded.''', '''				cert) fail "The secure connection could not be verified (HTTPS certificate). Please update the image's root certificates (ca-certificates) and try again." ;;
				net) fail "The package could not be downloaded.''')
assert "no-check-certificate" not in s
open(dst, "w").write(s); print(hashlib.sha256(s.encode()).hexdigest())
