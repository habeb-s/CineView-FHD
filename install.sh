#!/bin/sh
set -eu

# CineView FHD 2.3.4 Smart Multi-Image Installer
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
printf "%s%s        CineView FHD 2.3.4 Smart Installer%s\n" "$BOLD" "$GREEN" "$RESET"
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

# Install CineView Control 2.3.4 update layer without replacing accepted image-specific skin/layout files.
UPDATE_TAG="v2.3.4"
UPDATE_TMP="${TMP}.control"
UPDATE_IPK="$UPDATE_TMP/cineview-control.ipk"
UPDATE_STAGE="$UPDATE_TMP/stage"
mkdir -p "$UPDATE_STAGE"
cleanup_update(){ rm -rf "$UPDATE_TMP" 2>/dev/null || true; }
trap cleanup_update EXIT INT TERM

case "$DISTRO" in
  openatv) UPDATE_PKG="enigma2-plugin-skins-cineview-openatv_2.3.4_all.ipk" ;;
  openvix) UPDATE_PKG="enigma2-plugin-skins-cineview-openvix_2.3.4_all.ipk" ;;
  openbh|openblackhole) UPDATE_PKG="enigma2-plugin-skins-cineview-openbh_2.3.4_all.ipk" ;;
  *) UPDATE_PKG="" ;;
esac

if [ -n "$UPDATE_PKG" ]; then
  UPDATE_URL="https://github.com/habeb-s/CineView-FHD/releases/download/$UPDATE_TAG/$UPDATE_PKG?cv=20260925-1827"
  info "Applying CineView Control 2.3.4 update layer..."
  if command -v wget >/dev/null 2>&1; then
    wget -q --no-check-certificate -O "$UPDATE_IPK" "$UPDATE_URL" || fail "CineView Control update download failed"
  elif command -v curl >/dev/null 2>&1; then
    curl -fsSLk "$UPDATE_URL" -o "$UPDATE_IPK" || fail "CineView Control update download failed"
  else
    fail "wget/curl not found"
  fi
  [ -s "$UPDATE_IPK" ] || fail "Downloaded CineView Control update is empty"

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

  python3 - "$CONTROL_SRC/plugin.py" "$CONTROL_SRC/updater.py" <<'PY' || fail "CineView Control update validation failed"
import ast,sys
for p in sys.argv[1:]:
    with open(p,'r',encoding='utf-8',errors='ignore') as f:
        ast.parse(f.read(), filename=p)
print('[CineView][OK] CineView Control 2.3.4 Python validation passed')
PY

  CONTROL_DST="/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"
  mkdir -p "$CONTROL_DST"
  cp -af "$CONTROL_SRC/plugin.py" "$CONTROL_DST/plugin.py"
  cp -af "$CONTROL_SRC/updater.py" "$CONTROL_DST/updater.py"
  cp -af "$CONTROL_SRC/plugin.png" "$CONTROL_DST/plugin.png"
  chmod 644 "$CONTROL_DST/plugin.py" "$CONTROL_DST/updater.py" "$CONTROL_DST/plugin.png" 2>/dev/null || true
  ok "CineView Control 2.3.4 installed; image-specific skin design preserved"
fi

rm -rf "$UPDATE_TMP" 2>/dev/null || true
trap - EXIT INT TERM
ok "CineView Control temporary update files removed"

sync
ok "All CineView files installed and temporary files cleaned"
info "Restarting Enigma2 to activate CineView FHD 2.3.4..."
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
  systemctl restart enigma2.service || true
else
  ( sleep 1; killall -9 enigma2 >/dev/null 2>&1 || true ) &
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
printf "%s%s       CineView FHD 2.3.4 installation complete%s\n" "$BOLD" "$GREEN" "$RESET"
printf "%s              Designed by habeb-s%s\n" "$CYAN" "$RESET"
printf "%s%s============================================================%s\n\n" "$BOLD" "$GREEN" "$RESET"
exit 0
