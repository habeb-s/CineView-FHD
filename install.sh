#!/bin/sh
set -eu

# CineView FHD smart entry point.
# - OpenATV 7.4/7.5/7.6/8.0 -> final live OpenATV snapshot (2026-09-23)
# - OpenViX 6.9 build 002      -> pinned live OpenViX snapshot
# Other images are intentionally not routed until their image-specific port is completed.

TMP="/tmp/cineview-smart-installer.$$"
cleanup(){ rm -f "$TMP"; }
trap cleanup EXIT INT TERM

fail(){ echo "[CineView][FAIL] $*" >&2; exit 1; }

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

case "$DISTRO" in
  openvix)
    URL='https://raw.githubusercontent.com/habeb-s/CineView-FHD/3c4519ba47ba59444ff2392507e67d9c133f14ec/install-openvix-live.sh'
    echo "[CineView] OpenViX detected -> pinned live OpenViX installer"
    ;;
  openatv)
    case "$VERSION" in
      7.4*|7.5*|7.6*|8.0*) ;;
      *) fail "unsupported OpenATV version: \${VERSION:-unknown}; supported: 7.4 / 7.5 / 7.6 / 8.0" ;;
    esac
    URL='https://raw.githubusercontent.com/habeb-s/CineView-FHD/main/install-openatv-live.sh'
    echo "[CineView] OpenATV \${VERSION:-unknown} detected -> final 2026-09-23 live snapshot"
    ;;
  openbh)
    fail "OpenBH port is not published yet; use the saved OpenATV engineering reference when the OpenBH port is ready"
    ;;
  *)
    fail "unsupported image: \${DISTRO:-unknown}"
    ;;
esac

if command -v wget >/dev/null 2>&1; then
  wget -q --no-check-certificate -O "$TMP" "$URL" || fail "installer download failed"
elif command -v curl >/dev/null 2>&1; then
  curl -fsSLk "$URL" -o "$TMP" || fail "installer download failed"
else
  fail "wget/curl not found"
fi

[ -s "$TMP" ] || fail "downloaded installer is empty"
chmod 755 "$TMP"
/bin/sh "$TMP"
RC=$?
rm -f "$TMP"
trap - EXIT INT TERM
exit "$RC"
