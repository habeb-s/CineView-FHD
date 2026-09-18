#!/bin/sh
set -eu

ESC="$(printf '\033')"
GREEN="${ESC}[32m"; YELLOW="${ESC}[33m"; RED="${ESC}[31m"; CYAN="${ESC}[36m"; RESET="${ESC}[0m"
say(){ printf "%s[CineView Recovery]%s %s\n" "$CYAN" "$RESET" "$*"; }
ok(){ printf "%s[OK]%s %s\n" "$GREEN" "$RESET" "$*"; }
warn(){ printf "%s[WARN]%s %s\n" "$YELLOW" "$RESET" "$*"; }
fail(){ printf "%s[FAIL]%s %s\n" "$RED" "$RESET" "$*" >&2; exit 1; }

[ "$(id -u 2>/dev/null)" = 0 ] || fail "Run as root"

IMG="$(cat /etc/image-version /etc/issue /etc/os-release 2>/dev/null | tr 'A-Z' 'a-z')"
case "$IMG" in
  *openatv*8.0*|*openatv*8.1*|*openatv*8-beta*|*openatv*8.0.0-beta*) ;;
  *) fail "This recovery is only for OpenATV 8.x" ;;
esac
ok "OpenATV 8 detected"

STAMP="$(date +%Y%m%d-%H%M%S 2>/dev/null || echo now)"
SETTINGS=/etc/enigma2/settings
[ -f "$SETTINGS" ] || fail "/etc/enigma2/settings not found"
cp -p "$SETTINGS" "/etc/enigma2/settings.cineview-recovery-$STAMP.bak"
ok "Settings backup created"

WP=/usr/lib/enigma2/python/Plugins/Extensions/WeatherPlugin
if [ -d "$WP" ]; then
  if [ -f "$WP/__init__.py" ] && grep -Fq 'language.addCallback(localeInit())' "$WP/__init__.py" 2>/dev/null; then
    QBASE=/usr/lib/enigma2/python/CineViewQuarantine
    QDST="$QBASE/WeatherPlugin-openatv8-$STAMP"
    mkdir -p "$QBASE" || fail "Cannot create quarantine directory"
    mv "$WP" "$QDST" || fail "Cannot quarantine legacy WeatherPlugin"
    [ ! -e "$WP" ] || fail "WeatherPlugin is still inside Plugins; refusing to restart"
    [ -f "$QDST/__init__.py" ] || fail "WeatherPlugin quarantine verification failed"
    ok "Legacy WeatherPlugin quarantined safely"
    say "Backup location: $QDST"
  else
    warn "WeatherPlugin exists but the known legacy callback was not found; leaving it untouched"
  fi
else
  ok "WeatherPlugin is not present in active Plugins path"
fi

find /usr/lib/enigma2/python/Plugins/Extensions -type d -name __pycache__ -path '*/WeatherPlugin/*' -exec rm -rf {} + 2>/dev/null || true

SAFE=""
for candidate in MetrixHD/skin.xml MetrixFHD/skin.xml skin.xml; do
  if [ -f "/usr/share/enigma2/$candidate" ]; then SAFE="$candidate"; break; fi
done
if [ -z "$SAFE" ]; then
  SAFE="$(find /usr/share/enigma2 -mindepth 2 -maxdepth 2 -type f -name skin.xml 2>/dev/null | grep -v '/CineView_FHD/' | head -n1 | sed 's#^/usr/share/enigma2/##')"
fi
[ -n "$SAFE" ] || fail "No safe fallback skin found; refusing to restart"

if grep -q '^config.skin.primary_skin=' "$SETTINGS"; then
  sed -i "s#^config.skin.primary_skin=.*#config.skin.primary_skin=$SAFE#" "$SETTINGS"
else
  printf 'config.skin.primary_skin=%s\n' "$SAFE" >> "$SETTINGS"
fi
grep -q "^config.skin.primary_skin=$SAFE$" "$SETTINGS" || fail "Could not set safe fallback skin"
ok "Safe skin selected temporarily: $SAFE"

sync
say "Restarting Enigma2 only after recovery checks passed"
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
  systemctl restart enigma2.service || true
elif command -v init >/dev/null 2>&1; then
  init 4
  sleep 3
  init 3
else
  killall -9 enigma2 2>/dev/null || true
fi

ok "Recovery completed"
