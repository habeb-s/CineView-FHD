#!/usr/bin/env python3
"""Smart Installer 1.1.0 = the OpenBH-release installer (CineView-MLA 08f09b9) + OpenViX 6.9 support.
Every edit is an exact, unique replacement; the script stops if a source line is not found exactly once."""
import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()


def rep(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("replacement target found %d times: %r" % (n, old[:80]))
    s = s.replace(old, new)


rep('INSTALLER_VERSION="1.0.0"', 'INSTALLER_VERSION="1.1.0"')
rep('OPENBH_PY="3.13"\n', '''OPENBH_PY="3.13"
#   openvix: OpenViX 6.9, Python 3.14 - tested on OpenViX 6.9.002; NOT RELEASED YET: no package address until the
#   OpenViX package is published (the package SHA256 is fixed: only that exact file is ever installed)
OPENVIX_VERSION="1.0.0~openvix1"
OPENVIX_URL="@OPENVIX_URL@"
OPENVIX_SHA="955d102826bf30854003a7f5cd8e5d75b4f9e808b783bfe1fb53571acfa76d87"
OPENVIX_PY="3.14"
''')
# model: enigma.info, cross-checked with the Vu+ driver's own model file when it exists.  /proc/stb/info/model is
# never used: on Vu+ receivers it reports a fixed legacy value (dm8000 on a Duo 4K SE).
rep('[ -n "$MB" ] || fail "The receiver model cannot be identified."\n', '''[ -n "$MB" ] || fail "The receiver model cannot be identified."
VUM=$(cat /proc/stb/info/vumodel 2>/dev/null)
if [ -n "$VUM" ] && [ "$MB" != "vu$VUM" ]; then
	fail "The receiver model is ambiguous (image: $MB, Vu+ driver: $VUM): nothing is installed."
fi
''')
rep('''# second, independent evidence: the image's own Plugin Browser contract (OpenATV: PackageAction; OpenBH:
# PluginDownloadBrowser and no PackageAction).  Disagreement with enigma.info = the image is not identified.''',
    '''# second, independent evidence: the image's own Plugin Browser contract (OpenATV: PackageAction; OpenBH:
# PluginDownloadBrowser and no PackageAction; OpenViX: PluginDownloadBrowser, no PackageAction and no key_menu).
# Disagreement with enigma.info = the image is not identified.''')
rep('''	"") fail "This image does not name itself''', '''	openvix)
		IMG="OpenViX"; VERSION="$OPENVIX_VERSION"; PKG_URL="$OPENVIX_URL"; PKG_SHA="$OPENVIX_SHA"; PY_NEED="$OPENVIX_PY"
		{ has PluginDownloadBrowser && ! has PackageAction && ! has key_menu; } || fail "enigma.info names OpenViX, but the image's screens are not OpenViX's: the image cannot be identified reliably." ;;
	"") fail "This image does not name itself''')
rep('''*) fail "This image is '$DISTRO'. CineView MLA supports OpenATV and OpenBH." ;;''',
    '''*) fail "This image is '$DISTRO'. CineView MLA supports OpenATV, OpenBH and OpenViX." ;;''')
rep('''	*) fail "$IMG $IVER has not been checked with CineView MLA yet." ;;''',
    '''	openvix:6.9|openvix:6.9.*) ok "OpenViX $IVER is supported (tested on OpenViX 6.9)" ;;
	openvix:[0-5]|openvix:[0-5].*|openvix:6.[0-8]|openvix:6.[0-8].*) fail "OpenViX $IVER is too old: CineView MLA for OpenViX is built and tested for OpenViX 6.9." ;;
	*) fail "$IMG $IVER has not been checked with CineView MLA yet." ;;''')
# rollback: an older package only with FORCE=1, installed with --force-downgrade (opkg refuses a downgrade otherwise)
rep('''	elif [ "${FORCE:-0}" = "1" ]; then
		MODE=reinstall; warn "Reinstall requested"''', '''	elif [ "${FORCE:-0}" = "1" ] && [ "$CUR" = "$VERSION" ]; then
		MODE=reinstall; warn "Reinstall requested"
	elif [ "${FORCE:-0}" = "1" ]; then
		MODE=downgrade; warn "Return to the earlier version $VERSION requested (your design, theme and profiles are kept)"''')
rep('''OPT=""; case "$MODE" in reinstall|repair) OPT="--force-reinstall" ;; esac''',
    '''OPT=""; case "$MODE" in reinstall|repair) OPT="--force-reinstall" ;; downgrade) OPT="--force-downgrade" ;; esac''')
# OpenBH and OpenViX share PluginDownloadBrowser; OpenBH 5.6 has key_menu, OpenViX 6.9 has not (both enigma2 sources).
# Without this, an OpenViX image whose enigma.info says openbh would be taken for OpenBH.
rep('''{ has PluginDownloadBrowser && ! has PackageAction; } || fail "enigma.info names OpenBH''',
    '''{ has PluginDownloadBrowser && ! has PackageAction && has key_menu; } || fail "enigma.info names OpenBH''')
open(dst, "w").write(s)
print("written", dst)
