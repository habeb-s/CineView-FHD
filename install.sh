#!/bin/sh
set -eu
# >>> cineview recording guard >>>
# Canonical copy: packaging/recording_guard.sh (tools/sync_recording_guard.py copies it into every script that
# restarts Enigma2; tools/tests/test_recording_guard.sh checks the copies).  POSIX / BusyBox sh.
# cv_recording_active returns 0 while Enigma2 is recording:
#   1. OpenWebif /api/statusinfo reports "isRecording": "true" (when OpenWebif is installed and answers), or
#   2. the enigma2 process holds a recording file (*.ts) open for writing (timeshift files are ignored).
# CV_STATUS_URL / CV_PROC exist only for the tests.
cv_recording_active(){
  _cv_s=""
  if command -v wget >/dev/null 2>&1; then
    _cv_s="$(wget -q -T 3 -O - "${CV_STATUS_URL:-http://127.0.0.1/api/statusinfo}" 2>/dev/null || true)"
  elif command -v curl >/dev/null 2>&1; then
    _cv_s="$(curl -fsS -m 3 "${CV_STATUS_URL:-http://127.0.0.1/api/statusinfo}" 2>/dev/null || true)"
  fi
  case "$_cv_s" in
    *'"isRecording": "true"'*|*'"isRecording":"true"'*|*'"isRecording": true'*|*'"isRecording":true'*) return 0 ;;
  esac
  _cv_p="${CV_PROC:-/proc}"
  for _cv_c in "$_cv_p"/[0-9]*/comm; do
    [ -r "$_cv_c" ] || continue
    [ "$(cat "$_cv_c" 2>/dev/null)" = enigma2 ] || continue
    _cv_d="${_cv_c%/comm}"
    for _cv_f in "$_cv_d"/fd/*; do
      _cv_t="$(readlink "$_cv_f" 2>/dev/null)" || continue
      case "$_cv_t" in
        *timeshift*) continue ;;
        *.ts|*.ts.*) ;;
        *) continue ;;
      esac
      _cv_fl="$(sed -n 's/^flags:[[:space:]]*//p' "$_cv_d/fdinfo/${_cv_f##*/}" 2>/dev/null || true)"
      case "$_cv_fl" in
        *1|*2|*3|*5|*6|*7) return 0 ;;  # O_WRONLY / O_RDWR
      esac
    done
  done
  return 1
}
cv_recording_warn(){
  echo "[CineView][WARN] A recording is in progress - Enigma2 was NOT restarted."
  echo "[CineView][WARN] Restart Enigma2 after the recording has finished to activate the changes."
}
# <<< cineview recording guard <<<

# CineView FHD 2.3.5 Smart Multi-Image Installer
# Designed by habeb-s

SELF="$0"
PIN='main'
TMP="/tmp/cineview-smart-installer.$$"

ESC="$(printf '\033')"
RESET="${ESC}[0m"
BOLD="${ESC}[1m"
GREEN="${ESC}[32m"
YELLOW="${ESC}[33m"
BLUE="${ESC}[34m"
CYAN="${ESC}[36m"
RED="${ESC}[31m"

say(){ printf "%s[CineView]%s %s\n" "$CYAN" "$RESET" "$*"; }
ok(){ printf "%s[OK]%s %s\n" "$GREEN" "$RESET" "$*"; }
info(){ printf "%s[INFO]%s %s\n" "$BLUE" "$RESET" "$*"; }
warn(){ printf "%s[WARN]%s %s\n" "$YELLOW" "$RESET" "$*"; }
fail(){ printf "%s[FAIL]%s %s\n" "$RED" "$RESET" "$*" >&2; exit 1; }

cleanup(){
  rm -f "$TMP" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

printf "\n%s%s============================================================%s\n" "$BOLD" "$CYAN" "$RESET"
printf "%s%s        CineView FHD 2.3.5 Smart Installer%s\n" "$BOLD" "$GREEN" "$RESET"
printf "%s              Designed by habeb-s%s\n" "$CYAN" "$RESET"
printf "%s%s============================================================%s\n" "$BOLD" "$CYAN" "$RESET"
printf "%sInstallation requirements / شروط التثبيت:%s\n" "$BOLD" "$RESET"
printf "  %s•%s Root access and Python 3\n" "$YELLOW" "$RESET"
printf "  %s•%s Supported: OpenATV 7.4/7.5/7.6/8.0, OpenViX 6.7+, OpenBH 5.6+\n" "$YELLOW" "$RESET"
printf "  %s•%s A rollback backup is created before CineView files are replaced\n" "$YELLOW" "$RESET"
printf "  %s•%s Poster cache prefers persistent storage (/media/hdd/poster), then local media storage; /tmp is fallback only\n" "$YELLOW" "$RESET"
printf "  %s•%s Multiboot storage is excluded from poster cache\n" "$YELLOW" "$RESET"
printf "  %s•%s Temporary installer files are removed after completion\n\n" "$YELLOW" "$RESET"

[ "$(id -u 2>/dev/null)" = 0 ] || fail "Run installer as root"
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required"

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

IMG="$(cat /etc/image-version /etc/issue /etc/os-release /etc/hostname 2>/dev/null | tr 'A-Z' 'a-z' | tr '\n' ' ')"
VERSION="$(iv_get Version)"
[ -n "$VERSION" ] || VERSION="$(iv_get imageversion)"
BUILD="$(iv_get Build)"
[ -n "$BUILD" ] || BUILD="$(iv_get imagebuild)"
DISTRO="$(iv_get distro | tr 'A-Z' 'a-z' | tr -d ' ')"

case "$IMG" in
  *openvix*) DISTRO=openvix ;;
  *openatv*) DISTRO=openatv ;;
  *openbh*|*openblackhole*) DISTRO=openbh ;;
esac

printf "%sReceiver / Image information:%s\n" "$BOLD" "$RESET"
MODEL="$(cat /proc/stb/info/model /proc/stb/info/boxtype 2>/dev/null | head -n 1 || true)"
MACHINE="$(iv_get machinebuild)"
[ -n "$MACHINE" ] || MACHINE="$(iv_get machine)"
printf "  %sImage:%s   %s\n" "$CYAN" "$RESET" "${DISTRO:-unknown}"
printf "  %sVersion:%s %s\n" "$CYAN" "$RESET" "${VERSION:-unknown}"
printf "  %sBuild:%s   %s\n" "$CYAN" "$RESET" "${BUILD:-unknown}"
printf "  %sModel:%s   %s\n" "$CYAN" "$RESET" "${MODEL:-${MACHINE:-unknown}}"
printf "  %sPython:%s  %s\n\n" "$CYAN" "$RESET" "$(python3 -V 2>&1)"
BASE="https://raw.githubusercontent.com/habeb-s/CineView-FHD/$PIN"

case "$DISTRO" in
  openatv)
    case "$VERSION" in
      7.4*|7.5*|7.6*|8.0*) ;;
      *) fail "Unsupported OpenATV version: ${VERSION:-unknown}" ;;
    esac
    URL="$BASE/install-openatv-live.sh"
    info "Detected: OpenATV ${VERSION:-unknown}"
    ;;
  openvix)
    case "$VERSION" in 6.7*|6.8*|6.9*|7.*|8.*|9.*|[1-9][0-9].*) ;; *) fail "Unsupported OpenViX version: ${VERSION:-unknown}; minimum is 6.7" ;; esac
    URL="$BASE/install-openvix-live.sh"
    info "Detected: OpenViX ${VERSION:-unknown} build ${BUILD:-unknown}"
    ;;
  openbh|openblackhole)
    case "$VERSION" in 5.6*|5.7*|5.8*|5.9*|6.*|7.*|8.*|9.*|[1-9][0-9].*) ;; *) fail "Unsupported OpenBH version: ${VERSION:-unknown}; minimum is 5.6" ;; esac
    URL="$BASE/install-openbh-live.sh"
    info "Detected: OpenBH ${VERSION:-unknown} build ${BUILD:-unknown}"
    ;;
  *)
    fail "Unsupported image: ${DISTRO:-unknown}"
    ;;
esac

say "Downloading the verified image-specific CineView installer..."
if command -v wget >/dev/null 2>&1; then
  wget -q --no-check-certificate -O "$TMP" "$URL" || fail "Installer download failed"
elif command -v curl >/dev/null 2>&1; then
  curl -fsSLk "$URL" -o "$TMP" || fail "Installer download failed"
else
  fail "wget/curl not found"
fi

[ -s "$TMP" ] || fail "Downloaded installer is empty"
chmod 755 "$TMP"
ok "Image-specific installer downloaded"

if CINEVIEW_NO_RESTART=1 /bin/sh "$TMP"; then
  RC=0
else
  RC=$?
fi

rm -f "$TMP" 2>/dev/null || true
trap - EXIT INT TERM
ok "Temporary image-specific installer removed"

if [ "$RC" -ne 0 ]; then
  fail "Installation failed with exit code $RC"
fi

# Install the CineView 2.3.5 update layer (CineView Control + receiver-temperature converter) without replacing
# the accepted image-specific skin/layout files.  The package is pinned by SHA256.
UPDATE_TAG="v2.3.5"
UPDATE_TMP="${TMP}.control"
UPDATE_IPK="$UPDATE_TMP/cineview-control.ipk"
UPDATE_STAGE="$UPDATE_TMP/stage"
mkdir -p "$UPDATE_STAGE"
cleanup_update(){ rm -rf "$UPDATE_TMP" 2>/dev/null || true; }
trap cleanup_update EXIT INT TERM

case "$DISTRO" in
  openatv) UPDATE_PKG="enigma2-plugin-skins-cineview-openatv_2.3.5_all.ipk"; UPDATE_SHA="8befd18388aad0d6fc0e07d553bdc90d70709eb23e5583228e545c3f60a81f7d" ;;
  openvix) UPDATE_PKG="enigma2-plugin-skins-cineview-openvix_2.3.5_all.ipk"; UPDATE_SHA="d2b2bbe2399485d5621f996c2d77a04d78d4f25b8426145f4f38c1aef9c7fdff" ;;
  openbh|openblackhole) UPDATE_PKG="enigma2-plugin-skins-cineview-openbh_2.3.5_all.ipk"; UPDATE_SHA="0954dfcb262d5010a2ca6cb602c014ff3bbd8864669a67c28d8e1d2abccb707c" ;;
  *) UPDATE_PKG=""; UPDATE_SHA="" ;;
esac

if [ -n "$UPDATE_PKG" ]; then
  UPDATE_URL="https://github.com/habeb-s/CineView-FHD/releases/download/$UPDATE_TAG/$UPDATE_PKG?cv=20261009"
  info "Applying CineView 2.3.5 update layer..."
  if command -v wget >/dev/null 2>&1; then
    wget -q --no-check-certificate -O "$UPDATE_IPK" "$UPDATE_URL" || fail "CineView Control update download failed"
  elif command -v curl >/dev/null 2>&1; then
    curl -fsSLk "$UPDATE_URL" -o "$UPDATE_IPK" || fail "CineView Control update download failed"
  else
    fail "wget/curl not found"
  fi
  [ -s "$UPDATE_IPK" ] || fail "Downloaded CineView Control update is empty"
  if command -v sha256sum >/dev/null 2>&1; then
    UPDATE_ACTUAL="$(sha256sum "$UPDATE_IPK" | awk '{print $1}')"
  else
    UPDATE_ACTUAL="$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$UPDATE_IPK")"
  fi
  [ "$UPDATE_ACTUAL" = "$UPDATE_SHA" ] || fail "CineView update package SHA256 mismatch: $UPDATE_ACTUAL"
  ok "CineView 2.3.5 update package checksum verified"

  if command -v dpkg-deb >/dev/null 2>&1; then
    dpkg-deb -x "$UPDATE_IPK" "$UPDATE_STAGE" || fail "Unable to extract CineView Control update"
  else
    mkdir -p "$UPDATE_TMP/ar"
    (cd "$UPDATE_TMP/ar" && ar x "$UPDATE_IPK") || fail "Unable to unpack update package"
    DATA_ARCHIVE="$(find "$UPDATE_TMP/ar" -maxdepth 1 -type f -name 'data.tar*' | head -n 1)"
    [ -n "$DATA_ARCHIVE" ] || fail "Update package data archive missing"
    tar -xf "$DATA_ARCHIVE" -C "$UPDATE_STAGE" || fail "Unable to extract update data"
  fi

  CONTROL_SRC="$UPDATE_STAGE/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"
  [ -f "$CONTROL_SRC/plugin.py" ] || fail "CineView Control plugin.py missing from update"
  [ -f "$CONTROL_SRC/updater.py" ] || fail "CineView Control updater.py missing from update"
  [ -f "$CONTROL_SRC/plugin.png" ] || fail "CineView Control plugin icon missing from update"
  TEMP_SRC="$UPDATE_STAGE/usr/lib/enigma2/python/Components/Converter/CineViewCPUTemp.py"
  [ -f "$TEMP_SRC" ] || fail "CineViewCPUTemp converter missing from update"

  python3 - "$CONTROL_SRC/plugin.py" "$CONTROL_SRC/updater.py" "$TEMP_SRC" <<'PY' || fail "CineView update validation failed"
import ast,sys
for p in sys.argv[1:]:
    with open(p,'r',encoding='utf-8',errors='ignore') as f:
        ast.parse(f.read(), filename=p)
with open(sys.argv[3],'r',encoding='utf-8') as f:
    assert 'class CineViewCPUTemp(Poll, Converter)' in f.read()
print('[CineView][OK] CineView 2.3.5 Python validation passed')
PY

  CONTROL_DST="/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"
  mkdir -p "$CONTROL_DST"
  cp -af "$CONTROL_SRC/plugin.py" "$CONTROL_DST/plugin.py"
  cp -af "$CONTROL_SRC/updater.py" "$CONTROL_DST/updater.py"
  cp -af "$CONTROL_SRC/plugin.png" "$CONTROL_DST/plugin.png"
  chmod 644 "$CONTROL_DST/plugin.py" "$CONTROL_DST/updater.py" "$CONTROL_DST/plugin.png" 2>/dev/null || true
  ok "CineView Control 2.3.5 installed; image-specific skin design preserved"
  TEMP_DST="/usr/lib/enigma2/python/Components/Converter"
  mkdir -p "$TEMP_DST"
  cp -af "$TEMP_SRC" "$TEMP_DST/CineViewCPUTemp.py"
  chmod 644 "$TEMP_DST/CineViewCPUTemp.py" 2>/dev/null || true
  ok "Receiver temperature converter 2.3.5 installed"
fi

rm -rf "$UPDATE_TMP" 2>/dev/null || true
trap - EXIT INT TERM
ok "CineView Control temporary update files removed"

sync
ok "All CineView files installed and temporary files cleaned"
if cv_recording_active; then
  cv_recording_warn
else
  info "Restarting Enigma2 to activate CineView FHD 2.3.5..."
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
    systemctl restart enigma2.service || true
  else
    ( sleep 1; killall -9 enigma2 >/dev/null 2>&1 || true ) &
  fi
fi

case "$SELF" in
  /*|./*|../*)
    if [ -f "$SELF" ] && [ "$SELF" != "/bin/sh" ]; then
      rm -f "$SELF" 2>/dev/null || true
      ok "Downloaded smart installer file removed"
    fi
    ;;
esac

printf "\n%s%s============================================================%s\n" "$BOLD" "$GREEN" "$RESET"
printf "%s%s       CineView FHD 2.3.5 installation complete%s\n" "$BOLD" "$GREEN" "$RESET"
printf "%s              Designed by habeb-s%s\n" "$CYAN" "$RESET"
printf "%s%s============================================================%s\n\n" "$BOLD" "$GREEN" "$RESET"
exit 0
