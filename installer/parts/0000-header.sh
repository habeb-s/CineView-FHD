#!/bin/sh
# CineView FHD 2.0 Smart Universal Installer
# Designed by habeb-s
set -u
SELF="$0"
RESTART=1
DRY=0
for a in "$@"; do
  case "$a" in --restart) RESTART=1;; --dry-run) DRY=1;; --no-restart) RESTART=0;; esac
done
say(){ echo "[CineView] $*"; }
fail(){ echo "[CineView] ERROR: $*" >&2; exit 1; }
[ "$(id -u 2>/dev/null)" = 0 ] || fail "run as root"
TMP=$(mktemp -d /tmp/cineview-smart.XXXXXX 2>/dev/null || echo /tmp/cineview-smart.$$)
mkdir -p "$TMP" || fail "cannot create temporary directory"
trap 'rm -rf "$TMP"' EXIT INT TERM

# Receiver/image fingerprint.
IMG=$(cat /etc/image-version /etc/issue /etc/os-release /etc/hostname 2>/dev/null | tr '\n' ' ')
LOW=$(echo "$IMG" | tr 'A-Z' 'a-z')
case "$LOW" in
  *openpli*) FAMILY=openpli;;
  *dreamos*|*dreambox*|*gemini*|*merlin*) FAMILY=dreamos;;
  *openatv*|*openvix*|*openbh*|*openblackhole*|*opendroid*|*openspa*|*pure2*|*puree2*|*egami*|*teamblue*|*openhdf*|*nonsolosat*|*opentr*|*cobralib*|*satlodge*|*foxbob*|*pkteam*|*hyperion*|*vti*) FAMILY=oealliance;;
  *) FAMILY=generic;;
esac
if command -v opkg >/dev/null 2>&1; then PM=opkg; elif command -v apt-get >/dev/null 2>&1; then PM=apt; else PM=none; fi
if command -v python3 >/dev/null 2>&1; then PY=python3; elif command -v python >/dev/null 2>&1; then PY=python; else fail "Python is required by Enigma2 but was not found"; fi
PYVER=$($PY -V 2>&1 | head -n1)
ARCH=$(uname -m 2>/dev/null || echo unknown)
say "image-family=$FAMILY package-manager=$PM python=$PYVER arch=$ARCH"

# Space check: payload is small, but keep a conservative safety margin.
FREE=$(df -Pk /usr 2>/dev/null | awk 'NR==2{print $4}')
[ -z "$FREE" ] && FREE=999999
[ "$FREE" -ge 15360 ] 2>/dev/null || fail "less than 15 MB free on /usr"

# Decode embedded payload.
LINE=$(awk '/^__CINEVIEW_PAYLOAD_BELOW__$/{print NR+1; exit}' "$SELF")
[ -n "$LINE" ] || fail "embedded payload marker missing"
sed -n "${LINE},\$p" "$SELF" > "$TMP/payload.b64"
if command -v base64 >/dev/null 2>&1; then
  base64 -d "$TMP/payload.b64" > "$TMP/payload.tar.gz" 2>/dev/null || fail "payload decode failed"
elif command -v openssl >/dev/null 2>&1; then
  openssl base64 -d -in "$TMP/payload.b64" -out "$TMP/payload.tar.gz" >/dev/null 2>&1 || fail "payload decode failed"
else
  "$PY" - "$TMP/payload.b64" "$TMP/payload.tar.gz" <<'PY'
import sys,base64
open(sys.argv[2],'wb').write(base64.b64decode(open(sys.argv[1],'rb').read()))
PY
fi
mkdir -p "$TMP/stage"
tar -xzf "$TMP/payload.tar.gz" -C "$TMP/stage" || fail "payload extract failed"
PLUGSTAGE="$TMP/stage/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"
SKINSTAGE="$TMP/stage/usr/share/enigma2/CineView_FHD"
[ -f "$SKINSTAGE/skin.xml" ] || fail "skin payload incomplete"

# First install required/optional components from the receiver image's own feed only.
if [ "$DRY" = 0 ] && [ -x "$PLUGSTAGE/smartdeps.sh" ]; then
  say "checking dependencies from the image feed"
  CINEVIEW_LOG="$TMP/dependencies.log" sh "$PLUGSTAGE/smartdeps.sh" --install >/dev/null 2>&1 || true
else
  : > "$TMP/dependencies.log"
fi

# Patch the staged skin BEFORE copying it to the receiver.
say "adapting CineView to installed Enigma2 components"
"$PY" "$PLUGSTAGE/compat.py" "$SKINSTAGE" /usr/lib/enigma2/python "$TMP/compat.json" >/dev/null 2>&1 || fail "compatibility adaptation failed"

# Validate every XML file before installation.
"$PY" - "$SKINSTAGE" <<'PY'
from __future__ import print_function
import os,sys
try:
    import xml.etree.ElementTree as ET
except Exception:
    sys.exit(2)
root=sys.argv[1]; bad=[]; n=0
for base,dirs,files in os.walk(root):
    for name in files:
        if name.endswith('.xml'):
            n+=1
            p=os.path.join(base,name)
            try: ET.parse(p)
            except Exception as e: bad.append('%s: %s' % (p,e))
if bad:
    print('\n'.join(bad)); sys.exit(1)
print('validated %d XML files' % n)
PY
[ $? = 0 ] || fail "XML validation failed"

if [ "$DRY" = 1 ]; then
  say "dry-run passed: payload, dependency logic and compatibility adaptation are valid"
  cat "$TMP/compat.json" 2>/dev/null || true
  exit 0
fi

# Persistent safety backup without touching HDD/USB media.
STAMP=$(date +%Y%m%d-%H%M%S 2>/dev/null || echo now)
BACK=/etc/enigma2/cineview-backup-$STAMP.tar.gz
if [ -d /usr/share/enigma2/CineView_FHD ] || [ -d /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl ]; then
  tar -czf "$BACK" /usr/share/enigma2/CineView_FHD /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl /etc/enigma2/settings 2>/dev/null || true
  say "backup=$BACK"
fi

# Build a temporary native package AFTER compatibility adaptation.
# The package is deliberately created in /tmp, installed, then removed.
PKGROOT="$TMP/pkg"
mkdir -p "$PKGROOT/CONTROL" || fail "cannot create package metadata"
cat > "$PKGROOT/CONTROL/control" <<'EOF'
Package: enigma2-plugin-skins-cineview-fhd
Version: 2.0
Architecture: all
Maintainer: habeb-s
Description: CineView FHD 2.0 Smart Enigma2 Skin
EOF
printf '2.0\n' > "$TMP/debian-binary"
tar -C "$PKGROOT/CONTROL" -czf "$TMP/control.tar.gz" . || fail "control package creation failed"
tar -C "$TMP/stage" -czf "$TMP/data.tar.gz" . || fail "data package creation failed"

if [ "$PM" = apt ]; then
  PKGFILE="/tmp/cineview-fhd-2.0-smart-$$.deb"
else
  PKGFILE="/tmp/cineview-fhd-2.0-smart-$$.ipk"
fi

"$PY" - "$PKGFILE" "$TMP/debian-binary" "$TMP/control.tar.gz" "$TMP/data.tar.gz" <<'PY'
from __future__ import print_function
import os, sys, time
out = sys.argv[1]
members = sys.argv[2:]
def b(x):
    return x if isinstance(x, bytes) else x.encode("ascii")
with open(out, "wb") as f:
    f.write(b("!<arch>\n"))
    for p in members:
        name = os.path.basename(p) + "/"
        data = open(p, "rb").read()
        header = ("%-16s%-12d%-6d%-6d%-8o%-10d`\n" %
                  (name, int(time.time()), 0, 0, 0o100644, len(data)))
        f.write(b(header))
        f.write(data)
        if len(data) & 1:
            f.write(b("\n"))
PY
[ -s "$PKGFILE" ] || fail "temporary package creation failed"
say "temporary package=$PKGFILE"

say "installing CineView FHD 2.0"
if [ "$PM" = opkg ]; then
  opkg install "$PKGFILE" || fail "opkg installation failed"
elif [ "$PM" = apt ]; then
  if command -v dpkg >/dev/null 2>&1; then
    dpkg -i "$PKGFILE" || fail "dpkg installation failed"
  else
    fail "dpkg not found on apt image"
  fi
else
  cp -a "$TMP/stage/usr/." /usr/ 2>/dev/null || cp -Rpf "$TMP/stage/usr/." /usr/ || fail "file installation failed"
fi
chmod 755 /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/*.sh 2>/dev/null || true

SETTINGS=/etc/enigma2/settings
[ -f "$SETTINGS" ] || touch "$SETTINGS"
set_key(){ key="$1"; val="$2"; if grep -q "^${key}=" "$SETTINGS" 2>/dev/null; then sed -i "s|^${key}=.*|${key}=${val}|" "$SETTINGS"; else echo "${key}=${val}" >> "$SETTINGS"; fi; }
get_key(){ grep "^$1=" "$SETTINGS" 2>/dev/null | tail -1 | cut -d= -f2-; }
[ -n "$(get_key config.plugins.cineview.theme)" ] || set_key config.plugins.cineview.theme black
[ -n "$(get_key config.plugins.cineview.poster_infobar)" ] || set_key config.plugins.cineview.poster_infobar True
[ -n "$(get_key config.plugins.cineview.poster_second)" ] || set_key config.plugins.cineview.poster_second True
[ -n "$(get_key config.plugins.cineview.poster_channels)" ] || set_key config.plugins.cineview.poster_channels True
[ -n "$(get_key config.plugins.cineview.weatherprovider)" ] || set_key config.plugins.cineview.weatherprovider oa
[ -n "$(get_key config.plugins.cineview.timeformat)" ] || set_key config.plugins.cineview.timeformat 24
[ -n "$(get_key config.plugins.cineview.servermode)" ] || set_key config.plugins.cineview.servermode profile
[ -n "$(get_key config.plugins.cineview.secondtimeout)" ] || set_key config.plugins.cineview.secondtimeout 20
set_key config.skin.primary_skin CineView_FHD/skin.xml
/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/activate.sh >/dev/null 2>&1 || true

REPORT=/etc/enigma2/cineview-smart-report.txt
{
  echo "CineView FHD 2.0 Smart Installer"
  echo "family=$FAMILY"
  echo "package_manager=$PM"
  echo "python=$PYVER"
  echo "arch=$ARCH"
  echo "installed=$(date 2>/dev/null || true)"
  echo "--- compatibility ---"
  cat "$TMP/compat.json" 2>/dev/null || true
  echo "--- dependencies ---"
  cat "$TMP/dependencies.log" 2>/dev/null || true
} > "$REPORT"
say "installed successfully; report=$REPORT"
say "Second InfoBar uses CineView fixed transparent overlay on every theme."

if [ -n "${PKGFILE:-}" ] && [ -f "$PKGFILE" ]; then
  rm -f "$PKGFILE"
  say "removed temporary install package"
fi

if [ "$RESTART" = 1 ]; then
  say "restarting Enigma2 GUI"
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
    systemctl restart enigma2.service || true
  elif command -v init >/dev/null 2>&1; then
    init 4; sleep 3; init 3
  elif command -v killall >/dev/null 2>&1; then
    killall -9 enigma2 2>/dev/null || true
  else
    say "automatic GUI restart is not supported on this image; restart Enigma2 manually"
  fi
else
  say "Enigma2 restart skipped by --no-restart."
fi
say "CineView FHD 2.0 installation complete"
exit 0
__CINEVIEW_PAYLOAD_BELOW__
