#!/bin/bash
# OpenATV parity gate (multi-image work): build the OpenATV tree from the current checkout and compare it file by
# file with the golden 1.0.0 build (build94).  Every difference must be listed in ALLOWED (shared code changed on
# purpose, each with its own equivalence test) - anything else fails the gate.
# PVR classic / cover + generation g000000/pvr.xml: header icons moved off the date line (build.py
# apply_pvr_header_icons, user 2026-10-07 "common UI defect"); the gate also checks that ONLY the two icon positions
# changed in those files (pvr_icons_only below).
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
usr/lib/enigma2/python/Components/Converter/CineViewMLAShowIf.py
usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/plugin.py
usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/image_adapter.py
usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py
usr/share/enigma2/CineView_FHD_MLA/mla/guardian/guardian.sh
usr/share/enigma2/CineView_FHD_MLA/layouts/pvr/classic/screens.openatv.xml
usr/share/enigma2/CineView_FHD_MLA/layouts/pvr/cover/screens.openatv.xml
usr/share/enigma2/CineView_FHD_MLA/generations/g000000/pvr.xml'
diff -rq build94 "$OUT" | sed -e "s|^Files build94/\([^ ]*\) and .* differ$|\1|" -e "s|^Only in $OUT/*\([^:]*\): \(.*\)$|\1/\2|" \
	-e "s|^Only in build94/*\([^:]*\): \(.*\)$|REMOVED \1/\2|" | sed 's|//|/|g' > "$OUT.diff"
BAD=$(grep -v -x -F "$ALLOWED" "$OUT.diff")
echo "PARITY: $(wc -l < "$OUT.diff") differing files vs golden build94"
sed 's/^/   /' "$OUT.diff"
if [ -n "$BAD" ]; then echo "PARITY: FAIL - not allowed:"; echo "$BAD" | sed 's/^/   /'; exit 1; fi
for f in usr/share/enigma2/CineView_FHD_MLA/layouts/pvr/classic/screens.openatv.xml usr/share/enigma2/CineView_FHD_MLA/layouts/pvr/cover/screens.openatv.xml usr/share/enigma2/CineView_FHD_MLA/generations/g000000/pvr.xml; do
	[ -f "build94/$f" ] || continue
	CH=$(diff <(sed -e 's/position="1600,8"/position="1740,45"/' -e 's/position="1660,8"/position="1800,45"/' "$OUT/$f") "build94/$f" | wc -l)
	[ "$CH" = 0 ] || { echo "PARITY: FAIL - $f changed beyond the PVR header icon positions"; exit 1; }
done
echo "PARITY: PASS (skin XML, layouts, themes, previews, assets identical; only the listed shared code changed)"
