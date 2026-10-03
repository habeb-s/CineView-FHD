#!/bin/sh
# CineView MLA boot guardian (busybox sh; no Enigma2, no skin, no UI needed).
# Called by /usr/bin/enigma2_pre_start.sh, which OpenATV's enigma2.sh runs before EVERY
# Enigma2 start (including the automatic respawn after a crash).
#
# Escalation (boot.count = consecutive starts without a "healthy"/"clean" signal):
#   >=3  rollback to last-known-good generation
#   >=5  rollback to factory generation g000000 (approved Classic)
#   >=7  switch config.skin.primary_skin back to the skin used before MLA
# Env overrides for tests: MLA_SKIN_DIR MLA_STATE_DIR MLA_SETTINGS MLA_PY

SKIN_DIR=${MLA_SKIN_DIR:-/usr/share/enigma2/CineView_FHD_MLA}
STATE=${MLA_STATE_DIR:-/etc/enigma2/cineview_mla}
SETTINGS=${MLA_SETTINGS:-/etc/enigma2/settings}
PY=${MLA_PY:-python3}
ENGINE="$SKIN_DIR/mla/engine/composer.py"

grep -q '^config.skin.primary_skin=CineView_FHD_MLA/' "$SETTINGS" 2>/dev/null || exit 0
mkdir -p "$STATE"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') guardian: $*" >> "$STATE/history.log"; }
put() { echo "$2" > "$1.tmp" && sync && mv -f "$1.tmp" "$1"; }

shell_point_factory() {
	ln -s generations/g000000 "$SKIN_DIR/active.tmp" 2>/dev/null || { rm -f "$SKIN_DIR/active.tmp"; ln -s generations/g000000 "$SKIN_DIR/active.tmp"; }
	mv -f "$SKIN_DIR/active.tmp" "$SKIN_DIR/active" && sync
	log "shell fallback: active -> g000000"
}

# 1) Structural recovery (interrupted transactions, unsealed/corrupt generations).
if ! MLA_SKIN_DIR="$SKIN_DIR" MLA_STATE_DIR="$STATE" "$PY" "$ENGINE" recover >/dev/null 2>&1; then
	log "engine recover failed (rc=$?)"
	shell_point_factory
fi

# 2) Crash-loop counter.
if [ -f "$STATE/clean_exit" ]; then
	rm -f "$STATE/clean_exit"
	n=0
else
	n=$(cat "$STATE/boot.count" 2>/dev/null)
	case "$n" in ''|*[!0-9]*) n=0 ;; esac
fi
n=$((n + 1))
put "$STATE/boot.count" "$n"

if [ "$n" -ge 7 ]; then
	prev=$(cat "$STATE/previous_skin" 2>/dev/null)
	[ -n "$prev" ] || prev="MetrixHD/skin.xml"
	cp -p "$SETTINGS" "$STATE/settings.before-guardian-skin-switch" 2>/dev/null
	if grep -q '^config.skin.primary_skin=' "$SETTINGS"; then
		sed "s|^config.skin.primary_skin=.*|config.skin.primary_skin=$prev|" "$SETTINGS" > "$SETTINGS.mla.tmp" && sync && mv -f "$SETTINGS.mla.tmp" "$SETTINGS"
	fi
	put "$STATE/boot.count" 0
	log "count=$n: primary_skin -> $prev (last resort)"
elif [ "$n" -ge 5 ]; then
	MLA_SKIN_DIR="$SKIN_DIR" MLA_STATE_DIR="$STATE" "$PY" "$ENGINE" rollback --to factory >/dev/null 2>&1 || shell_point_factory
	log "count=$n: rollback to factory"
elif [ "$n" -ge 3 ]; then
	MLA_SKIN_DIR="$SKIN_DIR" MLA_STATE_DIR="$STATE" "$PY" "$ENGINE" rollback >/dev/null 2>&1 || shell_point_factory
	log "count=$n: rollback to last-known-good"
fi
exit 0
