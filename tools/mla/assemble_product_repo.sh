#!/bin/sh
# Assemble the CineView-MLA product repository tree from product/ and a packaged ipk.
# usage: assemble_product_repo.sh <ipk> <out-dir> [version]
# Fills the installer's package URL and SHA256 and the release notes' SHA256. Nothing is published here.
set -e
IPK=${1:?ipk}; OUT=${2:?out dir}; VER=${3:-1.0.0}
HERE=$(cd "$(dirname "$0")/../.." && pwd); P=$HERE/product
OWNER_REPO=${MLA_REPO:-habeb-s/CineView-MLA}
F=$(basename "$IPK")
SHA=$(sha256sum "$IPK" | cut -c1-64)
URL="https://raw.githubusercontent.com/$OWNER_REPO/main/release/$VER/$F"
mkdir -p "$OUT"
# keep .git if the out dir is already a clone; replace everything else
find "$OUT" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp "$P/README.md" "$P/LICENSE" "$P/RELEASE_NOTES.md" "$OUT/"
mkdir -p "$OUT/images" "$OUT/install" "$OUT/release/$VER"
cp "$P"/images/*.png "$P"/images/*.jpg "$OUT/images/"
sed -e "s|@PKG_URL@|$URL|" -e "s|@PKG_SHA@|$SHA|" "$P/install/cineview-install.sh" > "$OUT/install/cineview-install.sh"
cp "$P/install/cineview-uninstall.sh" "$OUT/install/"
sed -i "s|@PKG_SHA@|$SHA|" "$OUT/RELEASE_NOTES.md"
cp "$IPK" "$OUT/release/$VER/$F"
(cd "$OUT/release/$VER" && sha256sum "$F" > SHA256SUMS)
# guards: no placeholders, no development paths or internal words in anything published
if grep -rn "@PKG_\|dev-cache\|dev/mla\|/home/\|cineview-mla/repo" "$OUT" --exclude-dir=.git --exclude=*.ipk; then
	echo "ASSEMBLE: forbidden text found" >&2; exit 1
fi
sh -n "$OUT/install/cineview-install.sh"; sh -n "$OUT/install/cineview-uninstall.sh"
echo "assembled $OUT  url=$URL  sha=$SHA"
