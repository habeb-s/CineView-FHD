#!/bin/sh
set -eu

# CineView live OpenViX snapshot installer
# Final snapshot captured from the user's Vu+ Duo 4K SE on 2026-09-23.
SNAP_COMMIT='26d1390db22d41a1de29920a8d7a0cc446848a9c'
SNAP_SHA256='06e08ab6498832680645f2eb29c44f47bed984148d786bc08a2def042ebe3ffa'
SNAP_REL='snapshots/openvix-final-20260923/cineview-live-openvix-final-20260923.tar.gz'
SNAP_URL="https://raw.githubusercontent.com/habeb-s/CineView-FHD/$SNAP_COMMIT/$SNAP_REL"
TMP="/tmp/cineview-live-openvix.$$"
ARCHIVE="$TMP/cineview-live.tar.gz"
STAGE="$TMP/stage"
cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

fail(){ echo "[CineView][FAIL] $*" >&2; exit 1; }
ok(){ echo "[CineView][OK] $*"; }
iv_get(){
  key="$1"
  [ -f /etc/image-version ] || return 0
  awk -F '=' -v wanted="$key" '{
    k=$1; gsub(/^[ \t]+|[ \t]+$/, "", k)
    if (tolower(k)==tolower(wanted)) {
      v=substr($0,index($0,"=")+1); gsub(/^[ \t]+|[ \t]+$/, "", v); print v; exit
    }
  }' /etc/image-version 2>/dev/null
}

[ "$(id -u 2>/dev/null)" = 0 ] || fail 'run as root'
DISTRO="$(iv_get distro | tr 'A-Z' 'a-z' | tr -d ' ')"
VERSION="$(iv_get Version)"
BUILD="$(iv_get Build)"
[ "$DISTRO" = openvix ] || fail "this live snapshot is for OpenViX; detected: $DISTRO"
[ "$VERSION" = 6.9 ] || fail "this live snapshot requires OpenViX 6.9; detected: $VERSION"
[ "$BUILD" = 002 ] || fail "this live snapshot requires OpenViX build 002; detected: $BUILD"

mkdir -p "$STAGE"
echo '[CineView] Downloading pinned final OpenViX snapshot...'
if command -v wget >/dev/null 2>&1; then
  wget -q --no-check-certificate -O "$ARCHIVE" "$SNAP_URL" || fail 'snapshot download failed'
elif command -v curl >/dev/null 2>&1; then
  curl -fsSLk "$SNAP_URL" -o "$ARCHIVE" || fail 'snapshot download failed'
else
  fail 'wget/curl not found'
fi
[ -s "$ARCHIVE" ] || fail 'downloaded snapshot is empty'

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
elif command -v python3 >/dev/null 2>&1; then
  ACTUAL="$(python3 - "$ARCHIVE" <<'PY'
import hashlib,sys
h=hashlib.sha256()
with open(sys.argv[1],'rb') as f:
    for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
print(h.hexdigest())
PY
)"
else
  fail 'no SHA256 tool available'
fi
[ "$ACTUAL" = "$SNAP_SHA256" ] || fail "SHA256 mismatch: $ACTUAL"
ok "Snapshot checksum verified: $ACTUAL"

tar -tzf "$ARCHIVE" > "$TMP/list.txt" || fail 'snapshot archive is invalid'
grep -q '^usr/share/enigma2/CineView_FHD/skin.xml$' "$TMP/list.txt" || fail 'skin.xml missing from snapshot'
grep -q '^usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/plugin.py$' "$TMP/list.txt" || fail 'CineViewControl missing from snapshot'
grep -q '^usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/openvix_final.py$' "$TMP/list.txt" || fail 'OpenViX final compatibility helper missing from snapshot'
grep -q '^usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py$' "$TMP/list.txt" || fail 'CineViewPosterX missing from snapshot'
grep -q '^usr/lib/enigma2/python/Components/Converter/CineViewTransponderInfo.py$' "$TMP/list.txt" || fail 'CineViewTransponderInfo missing from snapshot'
tar -xzf "$ARCHIVE" -C "$STAGE" || fail 'snapshot extraction failed'
grep -q '_cineview_poster_cache_root' "$STAGE/usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py" || fail 'persistent poster-cache policy missing'
ok 'Persistent poster-cache policy verified'

if command -v python3 >/dev/null 2>&1; then
  python3 - "$STAGE/usr/share/enigma2/CineView_FHD" <<'PY' || fail 'XML validation failed'
import os,sys,xml.etree.ElementTree as ET
root=sys.argv[1]
n=0
for base,dirs,files in os.walk(root):
    for name in files:
        if name.endswith('.xml'):
            ET.parse(os.path.join(base,name)); n+=1
print('[CineView][OK] validated %d XML files' % n)
PY
fi

STAMP="$(date +%Y%m%d-%H%M%S 2>/dev/null || echo now)"
BACKUP="/tmp/cineview-before-live-$STAMP.tar.gz"
tar -C / -czf "$BACKUP" \
  usr/share/enigma2/CineView_FHD \
  usr/lib/enigma2/python/Plugins/Extensions/CineViewControl \
  usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py \
  usr/lib/enigma2/python/Components/Converter/CineViewBitrate.py \
  usr/lib/enigma2/python/Components/Converter/CineViewCPUTemp.py \
  usr/lib/enigma2/python/Components/Converter/CineViewCamInfo.py \
  usr/lib/enigma2/python/Components/Converter/CineViewIMDb.py \
  usr/lib/enigma2/python/Components/Converter/CineViewTransponder.py \
  usr/lib/enigma2/python/Components/Converter/CineViewTransponderInfo.py \
  usr/lib/enigma2/python/Plugins/Extensions/OAWeather \
  etc/enigma2/settings 2>/dev/null || true
ok "Temporary rollback backup: $BACKUP"

tar -C "$STAGE" -cf - . | tar -C / -xf - || fail 'install copy failed'
chmod 755 /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/*.sh 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Components/Converter/CineView*.py 2>/dev/null || true

SETTINGS=/etc/enigma2/settings
if [ -f "$SETTINGS" ] && grep -q '^config.skin.primary_skin=' "$SETTINGS"; then
  sed -i 's|^config.skin.primary_skin=.*|config.skin.primary_skin=CineView_FHD/skin.xml|' "$SETTINGS"
else
  echo 'config.skin.primary_skin=CineView_FHD/skin.xml' >> "$SETTINGS"
fi
sync
ok 'Final OpenViX CineView snapshot installed exactly from pinned GitHub commit.'
ok "Source commit: $SNAP_COMMIT"
ok "Rollback backup: $BACKUP"

if [ "${CINEVIEW_NO_RESTART:-0}" != 1 ]; then
  echo '[CineView] Restarting Enigma2...'
  ( sleep 1; killall -9 enigma2 >/dev/null 2>&1 || true ) &
fi
exit 0
