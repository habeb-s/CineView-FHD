#!/bin/bash
# Build the OpenViX test package from a checkout (agent, ~/cineview-mla):
#   OpenATV parity gate first (must PASS), then the OpenBH build (MLA_IMAGE=openvix overlay), .pyc compiled by the
#   OpenViX receiver's own Python (Slot 4, r4.sh), package with the OpenBH preinst (MLA_TARGET=openvix).
# usage: build_openvix.sh <checkout> <version>      e.g. build_openvix.sh ~/cineview-mla/mi 1.0.0~openvix1
set -e
CO=${1:?checkout}; VER=${2:?version}
cd ~/cineview-mla
bash "$CO/tools/mla/parity_openatv.sh" "$CO" build_parity > parity_last.log 2>&1 || { echo "PARITY FAILED - no OpenViX build"; tail -8 parity_last.log; exit 3; }
tail -3 parity_last.log
G=candidates/golden0926/usr
rm -rf build_vix
MLA_IMAGE=openvix MLA_CS_MOCKS=$PWD/csmock/out MLA_PREVIEWS=$PWD/previews python3 "$CO/tools/mla/build.py" $G/share/enigma2/CineView_FHD \
	$G/lib/enigma2/python/Components $G/lib/enigma2/python/Plugins/Extensions/CineViewControl build_vix > build_vix.log 2>&1 \
	|| { echo "OpenViX build failed"; tail -8 build_vix.log; exit 2; }
grep "IMAGE-OVERLAY\|VALIDATION\|BUILD OK" build_vix.log
sed -n '/VALIDATION/,/BUILD OK/p' build_vix.log | head -20
MKPYC_R=~/cineview-mla/r4.sh bash "$CO/tools/mla/devtools/device/mkpyc.sh" build_vix pyc_vix | tail -1
rm -rf pkg_vix
MLA_TARGET=openvix MLA_HOMEPAGE=https://github.com/habeb-s/CineView-MLA python3 "$CO/tools/mla/package_ipk.py" build_vix "$VER" pkg_vix --pyc pyc_vix | tail -1
sha256sum pkg_vix/*.ipk
