#!/bin/bash
# Build the OpenBH test package from a checkout (agent, ~/cineview-mla):
#   OpenATV parity gate first (must PASS), then the OpenBH build (MLA_IMAGE=openbh overlay), .pyc compiled by the
#   OpenBH receiver's own Python (Slot 5, r5.sh), package with the OpenBH preinst (MLA_TARGET=openbh).
# usage: build_openbh.sh <checkout> <version>      e.g. build_openbh.sh ~/cineview-mla/mi 1.0.0~openbh2
set -e
CO=${1:?checkout}; VER=${2:?version}
cd ~/cineview-mla
bash "$CO/tools/mla/parity_openatv.sh" "$CO" build_parity | tail -3
grep -q "PARITY: PASS" build_parity.log 2>/dev/null || true
G=candidates/golden0926/usr
rm -rf build_bh
MLA_IMAGE=openbh MLA_CS_MOCKS=$PWD/csmock/out MLA_PREVIEWS=$PWD/previews python3 "$CO/tools/mla/build.py" $G/share/enigma2/CineView_FHD \
	$G/lib/enigma2/python/Components $G/lib/enigma2/python/Plugins/Extensions/CineViewControl build_bh > build_bh.log 2>&1 \
	|| { echo "OpenBH build failed"; tail -8 build_bh.log; exit 2; }
grep "IMAGE-OVERLAY\|VALIDATION\|BUILD OK" build_bh.log
sed -n '/VALIDATION/,/BUILD OK/p' build_bh.log | head -20
MKPYC_R=~/cineview-mla/r5.sh bash "$CO/tools/mla/devtools/device/mkpyc.sh" build_bh pyc_bh | tail -1
rm -rf pkg_bh
MLA_TARGET=openbh MLA_HOMEPAGE=https://github.com/habeb-s/CineView-MLA python3 "$CO/tools/mla/package_ipk.py" build_bh "$VER" pkg_bh --pyc pyc_bh | tail -1
sha256sum pkg_bh/*.ipk
