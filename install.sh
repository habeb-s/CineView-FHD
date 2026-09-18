#!/bin/sh
set -eu
RAW="https://raw.githubusercontent.com/habeb-s/CineView-FHD/4b158ec6e6787a2afb1e9691b8d68e5b38d1574a"
TMP="/tmp/cineview-smart-installer.$$.sh"
ESC="$(printf '\033')"
GREEN="${ESC}[32m"; CYAN="${ESC}[36m"; RED="${ESC}[31m"; RESET="${ESC}[0m"
cleanup(){ rm -f "$TMP"; }
trap cleanup EXIT INT TERM
# OPENATV8_PUBLIC_HOLD: do not expose unverified OpenATV 8 installs publicly.
IMG="$(cat /etc/image-version /etc/issue /etc/os-release 2>/dev/null | tr 'A-Z' 'a-z')"
case "$IMG" in
  *openatv*8.0*|*openatv*8.1*|*openatv*8-beta*|*openatv*8.0.0-beta*)
    printf "%s[HOLD]%s OpenATV 8 installation is temporarily paused pending live verification.\n" "$CYAN" "$RESET"
    printf "Use the dedicated OpenATV 8 recovery first; CineView will not modify this receiver.\n"
    exit 2
    ;;
esac

printf "%s[CineView]%s Downloading CineView FHD 2.0 Smart Installer...\n" "$CYAN" "$RESET"
if command -v wget >/dev/null 2>&1; then
  wget -q --no-check-certificate -O "$TMP" "$RAW/cineview-smart-install.sh"
elif command -v curl >/dev/null 2>&1; then
  curl -fsSLk "$RAW/cineview-smart-install.sh" -o "$TMP"
else
  printf "%s[FAIL]%s wget/curl not found\n" "$RED" "$RESET" >&2
  exit 1
fi
[ -s "$TMP" ] || { printf "%s[FAIL]%s download failed\n" "$RED" "$RESET" >&2; exit 1; }
chmod 755 "$TMP"
printf "%s[CineView]%s Installer downloaded. Starting smart preflight...\n" "$CYAN" "$RESET"
/bin/sh "$TMP" --restart
RC=$?
rm -f "$TMP"
trap - EXIT INT TERM
[ "$RC" -eq 0 ] && printf "%s[DONE]%s Installer file removed.\n" "$GREEN" "$RESET"
exit "$RC"
