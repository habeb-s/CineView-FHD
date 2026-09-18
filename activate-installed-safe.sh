#!/bin/sh
set -eu

SETTINGS=/etc/enigma2/settings
SKIN=/usr/share/enigma2/CineView_FHD
ACT=/usr/lib/enigma2/python/Plugins/Extensions/CineViewControl/activate.sh
STAMP=$(date +%Y%m%d-%H%M%S 2>/dev/null || echo now)
BACK="/etc/enigma2/settings.cineview-activate-$STAMP.bak"

say(){ echo "[CineView Activate] $*"; }
fail(){ echo "[CineView Activate] FAIL: $*" >&2; exit 1; }
set_key(){
  key="$1"; val="$2"
  if grep -q "^$key=" "$SETTINGS" 2>/dev/null; then
    sed -i "s|^$key=.*|$key=$val|" "$SETTINGS"
  else
    echo "$key=$val" >> "$SETTINGS"
  fi
}
start_e2(){
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
    systemctl start enigma2.service || true
  else
    init 3 || true
  fi
}
stop_e2(){
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q '^enigma2.service'; then
    systemctl stop enigma2.service || true
  else
    init 4 || true
  fi
}
wait_webif(){
  n=0
  while [ "$n" -lt 30 ]; do
    if command -v wget >/dev/null 2>&1; then
      wget -qO- http://127.0.0.1/web/about >/dev/null 2>&1 && return 0
    elif command -v curl >/dev/null 2>&1; then
      curl -fsS -m 2 http://127.0.0.1/web/about >/dev/null 2>&1 && return 0
    else
      pidof enigma2 >/dev/null 2>&1 && return 0
    fi
    n=$((n+1))
    sleep 1
  done
  return 1
}

[ "$(id -u)" = 0 ] || fail "run as root"
[ -f "$SETTINGS" ] || fail "settings file missing"
[ -f "$SKIN/skin.xml" ] || fail "CineView skin is not installed"
[ -f "$ACT" ] || fail "CineView activation helper missing"

cp -p "$SETTINGS" "$BACK" || fail "cannot back up settings"
say "Backup: $BACK"

say "Stopping Enigma2 before changing persistent settings..."
stop_e2
sleep 3

set_key config.skin.primary_skin CineView_FHD/skin.xml
grep -q '^config.plugins.cineview.theme=' "$SETTINGS" 2>/dev/null || set_key config.plugins.cineview.theme black
grep -q '^config.plugins.cineview.poster_infobar=' "$SETTINGS" 2>/dev/null || set_key config.plugins.cineview.poster_infobar True
grep -q '^config.plugins.cineview.poster_second=' "$SETTINGS" 2>/dev/null || set_key config.plugins.cineview.poster_second True
grep -q '^config.plugins.cineview.poster_channels=' "$SETTINGS" 2>/dev/null || set_key config.plugins.cineview.poster_channels True
grep -q '^config.plugins.cineview.weatherprovider=' "$SETTINGS" 2>/dev/null || set_key config.plugins.cineview.weatherprovider oa
grep -q '^config.plugins.cineview.timeformat=' "$SETTINGS" 2>/dev/null || set_key config.plugins.cineview.timeformat 24
grep -q '^config.plugins.cineview.servermode=' "$SETTINGS" 2>/dev/null || set_key config.plugins.cineview.servermode profile
grep -q '^config.plugins.cineview.secondtimeout=' "$SETTINGS" 2>/dev/null || set_key config.plugins.cineview.secondtimeout 20

grep -q '^config.skin.primary_skin=CineView_FHD/skin.xml$' "$SETTINGS" || {
  cp -p "$BACK" "$SETTINGS"
  start_e2
  fail "skin setting verification failed"
}

chmod 755 "$ACT" 2>/dev/null || true
"$ACT" >/tmp/cineview-activate.log 2>&1 || {
  cp -p "$BACK" "$SETTINGS"
  start_e2
  fail "CineView activation preparation failed"
}

sync
say "Starting Enigma2 with CineView..."
start_e2

if wait_webif; then
  say "DONE: Enigma2 is back and CineView activation persisted."
  exit 0
fi

say "Enigma2 did not return in time. Rolling back automatically..."
stop_e2
sleep 2
cp -p "$BACK" "$SETTINGS"
sync
start_e2
if wait_webif; then
  fail "CineView activation rolled back safely; previous skin restored."
fi

fail "rollback attempted but Enigma2/OpenWebif is still unavailable"
