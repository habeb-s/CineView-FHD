#!/bin/sh
set -eu

# CineView FHD 2.1 Smart Multi-Image Installer
# Designed by habeb-s

SELF="$0"
PIN='3c1aae4fe2b22299346b78cb77a930a51fd3d141'
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
printf "%s%s        CineView FHD 2.1 Smart Installer%s\n" "$BOLD" "$GREEN" "$RESET"
printf "%s              Designed by habeb-s%s\n" "$CYAN" "$RESET"
printf "%s%s============================================================%s\n" "$BOLD" "$CYAN" "$RESET"
printf "%sInstallation requirements / شروط التثبيت:%s\n" "$BOLD" "$RESET"
printf "  %s•%s Root access and Python 3\n" "$YELLOW" "$RESET"
printf "  %s•%s Supported: OpenATV 7.4/7.5/7.6/8.0, OpenViX 6.9 build 002, OpenBH 6.0 build 001\n" "$YELLOW" "$RESET"
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
    case "$VERSION" in 6.9*) ;; *) fail "Unsupported OpenViX version: ${VERSION:-unknown}" ;; esac
    [ "$BUILD" = "002" ] || fail "OpenViX build 002 required; detected: ${BUILD:-unknown}"
    URL="$BASE/install-openvix-live.sh"
    info "Detected: OpenViX ${VERSION:-unknown} build ${BUILD:-unknown}"
    ;;
  openbh|openblackhole)
    case "$VERSION" in 6.0*) ;; *) fail "Unsupported OpenBH version: ${VERSION:-unknown}" ;; esac
    [ "$BUILD" = "001" ] || fail "OpenBH build 001 required; detected: ${BUILD:-unknown}"
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

if /bin/sh "$TMP"; then
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

case "$SELF" in
  /*|./*|../*)
    if [ -f "$SELF" ] && [ "$SELF" != "/bin/sh" ]; then
      rm -f "$SELF" 2>/dev/null || true
      ok "Downloaded smart installer file removed"
    fi
    ;;
esac

printf "\n%s%s============================================================%s\n" "$BOLD" "$GREEN" "$RESET"
printf "%s%s       CineView FHD 2.1 installation complete%s\n" "$BOLD" "$GREEN" "$RESET"
printf "%s              Designed by habeb-s%s\n" "$CYAN" "$RESET"
printf "%s%s============================================================%s\n\n" "$BOLD" "$GREEN" "$RESET"
exit 0
