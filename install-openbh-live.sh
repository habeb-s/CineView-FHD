#!/bin/sh
set -eu

SNAP_COMMIT='0d5c9b884244ba1ea0235fe9d668c2581f843abd'
SNAP_SHA256='9017ab3455632ef5f93d46def51a8d26738f6bd8ce24ddacedabaad31bcadf3c'
SNAP_REL='snapshots/openbh-final-20260923/cineview-live-openbh-final-20260923.tar.gz'
SNAP_URL="https://raw.githubusercontent.com/habeb-s/CineView-FHD/$SNAP_COMMIT/$SNAP_REL"
TMP="/tmp/cineview-openbh-final.$$"
ARCHIVE="$TMP/cineview-openbh-final.tar.gz"
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
      v=substr($0,index($0,"=")+1)
      gsub(/^[ \t]+|[ \t]+$/, "", v)
      print v; exit
    }
  }' /etc/image-version 2>/dev/null
}

[ "$(id -u 2>/dev/null)" = 0 ] || fail "run as root"
DISTRO="$(iv_get distro | tr 'A-Z' 'a-z' | tr -d ' ')"
VERSION="$(iv_get Version)"
BUILD="$(iv_get Build)"
case "$DISTRO" in
  openbh|openblackhole) ;;
  *) fail "this final snapshot is for OpenBH; detected: \${DISTRO:-unknown}" ;;
esac
[ "$VERSION" = 6.0 ] || fail "this final snapshot requires OpenBH 6.0; detected: \${VERSION:-unknown}"
[ "$BUILD" = 001 ] || fail "this final snapshot requires OpenBH build 001; detected: \${BUILD:-unknown}"
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required"

mkdir -p "$STAGE"
echo "[CineView] Downloading pinned final OpenBH snapshot..."
if command -v wget >/dev/null 2>&1; then
  wget -q --no-check-certificate -O "$ARCHIVE" "$SNAP_URL" || fail "snapshot download failed"
elif command -v curl >/dev/null 2>&1; then
  curl -fsSLk "$SNAP_URL" -o "$ARCHIVE" || fail "snapshot download failed"
else
  fail "wget/curl not found"
fi
[ -s "$ARCHIVE" ] || fail "downloaded snapshot is empty"

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
else
  ACTUAL="$(python3 - "$ARCHIVE" <<'PY'
import hashlib,sys
h=hashlib.sha256()
with open(sys.argv[1],'rb') as f:
    for b in iter(lambda:f.read(1024*1024), b''):
        h.update(b)
print(h.hexdigest())
PY
)"
fi
[ "$ACTUAL" = "$SNAP_SHA256" ] || fail "SHA256 mismatch: $ACTUAL"
ok "Snapshot checksum verified: $ACTUAL"

tar -tzf "$ARCHIVE" > "$TMP/list.txt" || fail "snapshot archive is invalid"
for req in \
  usr/share/enigma2/CineView_FHD/skin.xml \
  usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/openbh_compat.py \
  usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/activate.sh \
  usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py \
  usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py \
  usr/lib/enigma2/python/Components/Converter/CineViewMoviePath.py
do
  grep -qx "$req" "$TMP/list.txt" || fail "required file missing: $req"
done
tar -xzf "$ARCHIVE" -C "$STAGE" || fail "snapshot extraction failed"

python3 - "$STAGE" <<'PY' || fail "snapshot validation failed"
import os,sys,ast,xml.etree.ElementTree as ET
root=sys.argv[1]
skin=os.path.join(root,'usr/share/enigma2/CineView_FHD')
n=0
for base,dirs,files in os.walk(skin):
    for name in files:
        if name.endswith('.xml'):
            ET.parse(os.path.join(base,name)); n += 1
for rel in (
 'usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/openbh_compat.py',
 'usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py',
 'usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py',
 'usr/lib/enigma2/python/Components/Converter/CineViewMoviePath.py'):
    p=os.path.join(root,rel)
    with open(p,'r',encoding='utf-8',errors='ignore') as f:
        ast.parse(f.read(), filename=p)
print('[CineView][OK] validated %d CineView XML files' % n)
PY

python3 "$STAGE/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/openbh_compat.py" \
  "$STAGE/usr/share/enigma2/CineView_FHD" >/dev/null 2>&1 || fail "OpenBH compatibility validation failed"

STAMP="$(date +%Y%m%d-%H%M%S 2>/dev/null || echo now)"
BACKUP="/tmp/cineview-before-openbh-final-$STAMP.tar.gz"
tar -C / -czf "$BACKUP" \
  usr/share/enigma2/CineView_FHD \
  usr/lib/enigma2/python/Plugins/Extensions/CineViewControl \
  usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py \
  usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py \
  usr/lib/enigma2/python/Components/Converter/CineViewMoviePath.py \
  2>/dev/null || true
ok "Rollback backup: $BACKUP"

tar -C "$STAGE" -cf - . | tar -C / -xf - || fail "install copy failed"
chmod 755 /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/*.sh 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/*.py 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Components/Converter/CineViewMoviePath.py 2>/dev/null || true

SETTINGS=/etc/enigma2/settings
touch "$SETTINGS"
if grep -q '^config.skin.primary_skin=' "$SETTINGS"; then
  sed -i 's|^config.skin.primary_skin=.*|config.skin.primary_skin=CineView_FHD/skin.xml|' "$SETTINGS"
else
  echo 'config.skin.primary_skin=CineView_FHD/skin.xml' >> "$SETTINGS"
fi

if [ -x /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/activate.sh ]; then
  /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/activate.sh || fail "CineView OpenBH activation failed"
fi

python3 - <<'PY' || fail "installed OpenBH validation failed"
import os,ast,xml.etree.ElementTree as ET
root='/usr/share/enigma2/CineView_FHD'
n=0
for base,dirs,files in os.walk(root):
    for name in files:
        if name.endswith('.xml'):
            ET.parse(os.path.join(base,name)); n += 1
for p in (
 '/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/openbh_compat.py',
 '/usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py',
 '/usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py',
 '/usr/lib/enigma2/python/Components/Converter/CineViewMoviePath.py'):
    with open(p,'r',encoding='utf-8',errors='ignore') as f:
        ast.parse(f.read(), filename=p)
print('[CineView][OK] installed validation passed (%d XML files)' % n)
PY

sync
ok "Final OpenBH CineView snapshot installed"
ok "Pinned source commit: $SNAP_COMMIT"
ok "Snapshot SHA256: $SNAP_SHA256"
ok "No /media/hdd data was modified"

if [ "\${CINEVIEW_NO_RESTART:-0}" != 1 ]; then
  echo "[CineView] Restarting Enigma2..."
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
    systemctl restart enigma2.service || true
  else
    ( sleep 1; killall -9 enigma2 >/dev/null 2>&1 || true ) &
  fi
fi
exit 0
