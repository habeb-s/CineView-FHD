#!/bin/sh
set -eu
RAW="https://raw.githubusercontent.com/habeb-s/CineView-FHD/a2ef71c02b9cc841c87876884d9849b89cfc67ce"
TMP="/tmp/cineview-smart-installer.$$.sh"
ESC="$(printf '\033')"
GREEN="${ESC}[32m"; CYAN="${ESC}[36m"; RED="${ESC}[31m"; RESET="${ESC}[0m"
cleanup(){ rm -f "$TMP"; }
trap cleanup EXIT INT TERM
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
