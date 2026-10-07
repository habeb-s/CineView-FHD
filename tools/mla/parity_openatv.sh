#!/bin/bash
# OpenATV parity gate (multi-image work): build the OpenATV tree from the current checkout and compare it file by
# file with the golden 1.0.0 build (build94).  Every difference must be listed in ALLOWED (shared code changed on
# purpose, each with its own equivalence test) - anything else fails the gate.
# usage (agent, ~/cineview-mla): parity_openatv.sh <checkout dir> [out dir]
set -u
CO=${1:?checkout}; OUT=${2:-build_parity}
cd ~/cineview-mla
G=candidates/golden0926/usr
rm -rf "$OUT"
MLA_CS_MOCKS=$PWD/csmock/out MLA_PREVIEWS=$PWD/previews python3 "$CO/tools/mla/build.py" $G/share/enigma2/CineView_FHD \
	$G/lib/enigma2/python/Components $G/lib/enigma2/python/Plugins/Extensions/CineViewControl "$OUT" > "$OUT.log" 2>&1 \
	|| { echo "PARITY: build failed"; tail -5 "$OUT.log"; exit 2; }
ALLOWED='usr/lib/enigma2/python/Components/Converter/CineViewMLAServiceInfo.py
usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/plugin.py
usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/image_adapter.py
usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py
usr/share/enigma2/CineView_FHD_MLA/mla/image.py'
diff -rq build94 "$OUT" | sed -e "s|^Files build94/\([^ ]*\) and .* differ$|\1|" -e "s|^Only in $OUT/*\([^:]*\): \(.*\)$|\1/\2|" \
	-e "s|^Only in build94/*\([^:]*\): \(.*\)$|REMOVED \1/\2|" | sed 's|//|/|g' > "$OUT.diff"
BAD=$(grep -v -x -F "$ALLOWED" "$OUT.diff")
echo "PARITY: $(wc -l < "$OUT.diff") differing files vs golden build94"
sed 's/^/   /' "$OUT.diff"
if [ -n "$BAD" ]; then echo "PARITY: FAIL - not allowed:"; echo "$BAD" | sed 's/^/   /'; exit 1; fi
echo "PARITY: PASS (skin XML, layouts, themes, previews, assets identical; only the listed shared code changed)"
