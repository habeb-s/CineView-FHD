#!/bin/sh
# Guardian crash-loop tests on an isolated copy.  usage: test_guardian.sh <built CineView_FHD_MLA dir> <scratch dir>
SRC=$1; T=$2; PASS=0; FAIL=0
export MLA_SKIN_DIR=$T/skin MLA_STATE_DIR=$T/state MLA_SETTINGS=$T/settings
G=$T/skin/mla/guardian/guardian.sh; E="python3 $T/skin/mla/engine/composer.py"
ok() { if [ "$1" = "$2" ]; then PASS=$((PASS+1)); echo "PASS $3"; else FAIL=$((FAIL+1)); echo "FAIL $3 (got '$1' want '$2')"; fi; }
fresh() { rm -rf "$T"; mkdir -p "$T/state"; cp -a "$SRC" "$T/skin"; printf 'config.skin.primary_skin=CineView_FHD_MLA/skin.xml\nconfig.misc.x=1\n' > "$T/settings"; echo "MetrixHD/skin.MySkin.xml" > "$T/state/previous_skin"; }
act() { basename "$(readlink "$T/skin/active")"; }

fresh; $E apply --theme graphite >/dev/null 2>&1; LKG=$(act); $E apply --theme purple --trial >/dev/null 2>&1; TRIAL=$(act)
sh "$G"; ok "$(cat $T/state/boot.count)" 1 "start 1 counts 1"
sh "$G"; ok "$(act)" "$TRIAL" "start 2 (1 crash) keeps trial"
sh "$G"; ok "$(act)" "$LKG" "start 3 (2 crashes) -> last-known-good"
sh "$G"; sh "$G"; ok "$(act)" "g000000" "start 5 -> factory"
sh "$G"; sh "$G"; ok "$(grep primary_skin $T/settings)" "config.skin.primary_skin=MetrixHD/skin.MySkin.xml" "start 7 -> previous skin restored"
ok "$(grep -c config.misc.x=1 $T/settings)" 1 "other settings preserved"
sh "$G"; ok "$(cat $T/state/boot.count)" 0 "guardian inert once MLA is not the active skin"

fresh; sh "$G"; sh "$G"; touch "$T/state/clean_exit"; sh "$G"; ok "$(cat $T/state/boot.count)" 1 "clean exit resets the counter"

fresh; printf 'config.skin.primary_skin=MetrixHD/skin.xml\n' > "$T/settings"; sh "$G"; ok "$(cat $T/state/boot.count 2>/dev/null || echo none)" none "not active -> no action"

fresh; mv "$T/skin/mla/engine/composer.py" "$T/skin/mla/engine/composer.py.off"; rm "$T/skin/active"; ln -s generations/gBROKEN "$T/skin/active"; sh "$G"; ok "$(act)" g000000 "python engine unavailable -> shell fallback to factory"

fresh; mkdir "$T/skin/generations/g000042"; echo '<skin><scr' > "$T/skin/generations/g000042/infobar.xml"; echo '{"state":"PREPARING","gid":"g000042"}' > "$T/state/txn.json"; sh "$G"; ok "$(ls $T/skin/generations | grep -c g000042)" 0 "interrupted write cleaned at boot"

echo "RESULT: $PASS/$((PASS+FAIL)) passed"; [ $FAIL = 0 ]
