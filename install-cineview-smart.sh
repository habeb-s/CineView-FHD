#!/bin/sh
set -eu
OWNER="habeb-s/CineView-FHD"
TMP="/tmp/cineview-install"
mkdir -p "$TMP"
rm -f "$TMP"/*.ipk 2>/dev/null || true
printf "\033[1;36m\n  CineView FHD Smart Installer\033[0m\n"

IMAGE="$(tr '[:upper:]' '[:lower:]' < /etc/image-version 2>/dev/null || true)"
case "$IMAGE" in
  *openbh*) TAG="v2.1.1-openbh6"; PKG="enigma2-plugin-skins-cineview-openbh_2.3.3_all.ipk" ;;
  *openvix*) TAG="openvix-6.9-cineview-2.3.2"; PKG="enigma2-plugin-skins-cineview-openvix_2.3.3_all.ipk" ;;
  *openatv*) TAG="openatv-7.6-cineview-final"; PKG="enigma2-plugin-skins-cineview-openatv_2.3.3_all.ipk" ;;
  *) printf "\033[1;31mUnsupported Enigma2 image.\033[0m\n"; exit 1 ;;
esac
URL="https://github.com/$OWNER/releases/download/$TAG/$PKG"
printf "\033[1;33mDownloading %s...\033[0m\n" "$PKG"
if command -v wget >/dev/null 2>&1; then wget -q -O "$TMP/$PKG" "$URL"; else curl -LfsS -o "$TMP/$PKG" "$URL"; fi
[ -s "$TMP/$PKG" ] || { printf "\033[1;31mDownload failed.\033[0m\n"; exit 1; }
printf "\033[1;32mInstalling CineView FHD 2.3.3...\033[0m\n"
opkg install --force-reinstall "$TMP/$PKG"
rm -rf "$TMP"
rm -f /tmp/CineView-* /tmp/cineview-* /tmp/AglareBitrate.log 2>/dev/null || true
printf "\033[1;32mInstallation completed successfully.\033[0m\n"
exit 0
