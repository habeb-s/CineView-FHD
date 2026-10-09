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
if cv_recording_active; then
  cv_recording_warn
  warn "The safe skin becomes active at the next Enigma2 restart"
elif command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
  say "Restarting Enigma2 only after recovery checks passed"
  systemctl restart enigma2.service || true
elif command -v init >/dev/null 2>&1; then
  say "Restarting Enigma2 only after recovery checks passed"
  init 4
  sleep 3
  init 3
else
  killall -9 enigma2 2>/dev/null || true
fi

ok "Recovery completed"
