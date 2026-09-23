#!/bin/sh
set -eu

SNAP_COMMIT='8d4e843706785ae691c7ad09e2d9cab9b4d34bb4'
SNAP_SHA256='935f63b0865f8209169dae5a5e9d36734957971967e536a677a38075014dc6ad'
SNAP_REL='snapshots/openatv-final-20260923/cineview-live-openatv-final-20260923.tar.gz'
SNAP_URL="https://raw.githubusercontent.com/habeb-s/CineView-FHD/$SNAP_COMMIT/$SNAP_REL"
TMP="/tmp/cineview-openatv-final.$$"
ARCHIVE="$TMP/cineview-openatv-final.tar.gz"
STAGE="$TMP/stage"

cleanup(){ rm -rf "$TMP"; }
trap cleanup EXIT INT TERM
fail(){ echo "[CineView][FAIL] $*" >&2; exit 1; }
ok(){ echo "[CineView][OK] $*"; }

iv_get(){
  key="$1"
  [ -f /etc/image-version ] || return 0
  awk -F '=' -v wanted="$key" '{
    k=$1
    gsub(/^[ \t]+|[ \t]+$/, "", k)
    if (tolower(k)==tolower(wanted)) {
      v=substr($0,index($0,"=")+1)
      gsub(/^[ \t]+|[ \t]+$/, "", v)
      print v
      exit
    }
  }' /etc/image-version 2>/dev/null
}

[ "$(id -u 2>/dev/null)" = 0 ] || fail "run as root"
DISTRO="$(iv_get distro | tr 'A-Z' 'a-z' | tr -d ' ')"
VERSION="$(iv_get Version)"
[ -n "$VERSION" ] || VERSION="$(iv_get imageversion)"
[ "$DISTRO" = openatv ] || fail "this snapshot is for OpenATV; detected: ${DISTRO:-unknown}"
case "$VERSION" in
  7.4*|7.5*|7.6*|8.0*) ;;
  *) fail "unsupported OpenATV version: ${VERSION:-unknown}; supported: 7.4 / 7.5 / 7.6 / 8.0" ;;
esac
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required"

mkdir -p "$STAGE"
echo "[CineView] Downloading pinned final OpenATV snapshot..."
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
ok "Snapshot checksum verified"

tar -tzf "$ARCHIVE" > "$TMP/list.txt" || fail "snapshot archive is invalid"
grep -qx 'usr/share/enigma2/CineView_FHD/skin.xml' "$TMP/list.txt" || fail "skin.xml missing"
grep -qx 'usr/share/enigma2/CineView_FHD/openatv_skin.xml' "$TMP/list.txt" || fail "openatv_skin.xml missing"
grep -qx 'usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py' "$TMP/list.txt" || fail "CineViewPosterX missing"
grep -qx 'usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py' "$TMP/list.txt" || fail "LukaPosterXEMC missing"
tar -xzf "$ARCHIVE" -C "$STAGE" || fail "snapshot extraction failed"

python3 - "$STAGE" <<'PY' || fail "snapshot validation failed"
import os,sys,ast,xml.etree.ElementTree as ET
root=sys.argv[1]
skin=os.path.join(root,'usr/share/enigma2/CineView_FHD')
n=0
for base,dirs,files in os.walk(skin):
    for name in files:
        if name.endswith('.xml'):
            ET.parse(os.path.join(base,name)); n+=1
for rel in (
 'usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_left_pig.xml',
 'usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_left_pig_1080.xml'):
    p=os.path.join(root,rel)
    if os.path.exists(p): ET.parse(p)
for rel in (
 'usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py',
 'usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py'):
    p=os.path.join(root,rel)
    with open(p,'r',encoding='utf-8',errors='ignore') as f: ast.parse(f.read(), filename=p)
# Enforce the accepted true Full-HD GraphicalEPG contract.
sp=os.path.join(skin,'skin.xml')
rr=ET.parse(sp).getroot()
ge=[x for x in rr.findall('.//screen') if x.get('name')=='GraphicalEPG']
if not ge or ge[0].get('position')!='0,0' or ge[0].get('size')!='1920,1080':
    raise SystemExit('GraphicalEPG is not true 1920x1080')
print('[CineView][OK] GraphicalEPG verified at 1920x1080')
print('[CineView][OK] validated %d skin XML files' % n)
PY

STAMP="$(date +%Y%m%d-%H%M%S 2>/dev/null || echo now)"
BACKUP="/tmp/cineview-before-openatv-final-$STAMP.tar.gz"
tar -C / -czf "$BACKUP" \
  usr/share/enigma2/CineView_FHD \
  usr/lib/enigma2/python/Plugins/Extensions/CineViewControl \
  usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py \
  usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py \
  usr/lib/enigma2/python/Components/Converter/CineViewBitrate.py \
  usr/lib/enigma2/python/Components/Converter/CineViewCPUTemp.py \
  usr/lib/enigma2/python/Components/Converter/CineViewCamInfo.py \
  usr/lib/enigma2/python/Components/Converter/CineViewIMDb.py \
  usr/lib/enigma2/python/Components/Converter/CineViewTransponder.py \
  usr/lib/enigma2/python/Components/Converter/CineViewTransponderInfo.py \
  usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_left_pig.xml \
  usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_left_pig_1080.xml \
  usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/img_fhd/red_cineview.png \
  usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/img_fhd/green_cineview.png \
  usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/img_fhd/yellow_cineview.png \
  usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/img_fhd/blue_cineview.png \
  2>/dev/null || true
ok "Rollback backup: $BACKUP"

mkdir -p /usr/share/enigma2
rm -rf /usr/share/enigma2/CineView_FHD
cp -a "$STAGE/usr/share/enigma2/CineView_FHD" /usr/share/enigma2/

mkdir -p /usr/lib/enigma2/python/Plugins/Extensions
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl
cp -a "$STAGE/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl" /usr/lib/enigma2/python/Plugins/Extensions/

mkdir -p /usr/lib/enigma2/python/Components/Renderer /usr/lib/enigma2/python/Components/Converter
cp -af "$STAGE/usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py" /usr/lib/enigma2/python/Components/Renderer/
cp -af "$STAGE/usr/lib/enigma2/python/Components/Converter/." /usr/lib/enigma2/python/Components/Converter/

EMC="/usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter"
if [ -d "$EMC" ]; then
  mkdir -p "$EMC/CoolSkin" "$EMC/img_fhd"
  cp -af "$STAGE/usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_left_pig.xml" "$EMC/CoolSkin/"
  cp -af "$STAGE/usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_left_pig_1080.xml" "$EMC/CoolSkin/"
  cp -af "$STAGE/usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/img_fhd/"*_cineview.png "$EMC/img_fhd/"
  if [ -f /usr/lib/enigma2/python/Components/Renderer/LukaPosterXDownloadThread.py ]; then
    cp -af "$STAGE/usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py" /usr/lib/enigma2/python/Components/Renderer/
    ok "EnhancedMovieCenter CineView integration installed"
  else
    echo "[CineView][WARN] EMC poster dependency missing; EMC poster renderer skipped"
  fi
else
  echo "[CineView][INFO] EnhancedMovieCenter not installed; EMC extras skipped"
fi

chmod 755 /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/*.sh 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Components/Renderer/CineViewPosterX.py 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Components/Renderer/LukaPosterXEMC.py 2>/dev/null || true
chmod 644 /usr/lib/enigma2/python/Components/Converter/CineView*.py 2>/dev/null || true

SETTINGS=/etc/enigma2/settings
touch "$SETTINGS"
if grep -q '^config.skin.primary_skin=' "$SETTINGS"; then
  sed -i 's|^config.skin.primary_skin=.*|config.skin.primary_skin=CineView_FHD/skin.xml|' "$SETTINGS"
else
  echo 'config.skin.primary_skin=CineView_FHD/skin.xml' >> "$SETTINGS"
fi

sync
ok "Final OpenATV snapshot installed"
ok "Pinned source commit: $SNAP_COMMIT"
ok "Snapshot SHA256: $SNAP_SHA256"
ok "No /media/hdd data was modified"

if [ "${CINEVIEW_NO_RESTART:-0}" != 1 ]; then
  echo "[CineView] Restarting Enigma2..."
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
    systemctl restart enigma2.service || true
  else
    ( sleep 1; killall -9 enigma2 >/dev/null 2>&1 || true ) &
  fi
fi
exit 0
