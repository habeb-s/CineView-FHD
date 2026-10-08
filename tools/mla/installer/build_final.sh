#!/bin/bash
# Final packages (not published) from mi HEAD for OpenATV / OpenBH / OpenViX.  .pyc compiled on this PC with the
# image's Python minor version (3.14 / 3.13 / 3.14), hash-based unchecked - proven byte-identical below against the
# approved packages for every module whose source did not change.
set -e
cd ~/cineview-mla
CO=~/cineview-mla/mi; F=final
G=candidates/golden0926/usr
git -C mi log --oneline -1 | tee $F/SOURCE_COMMIT
git -C mi status --porcelain | grep -v '^??' && { echo "mi has uncommitted changes - stop"; exit 2; } || true
bash mi/tools/mla/parity_openatv.sh $CO build_fatv > $F/parity.log 2>&1 || { echo PARITY_FAILED; tail -8 $F/parity.log; exit 3; }
tail -2 $F/parity.log
pyc() {  # pyc <build> <out> <python>
	local B=$1 O=$2 PY=$3; rm -rf $O; mkdir -p $O
	(cd $B && { find usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA -name '*.py'; find usr/lib/enigma2/python/Components -name 'CineViewMLA*.py'; }) | sort -u > $O.list
	while read f; do mkdir -p $O/$(dirname $f); $PY -c "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], dfile='/'+sys.argv[3], doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)" $B/$f $O/${f}c $f; done < $O.list
	$PY -c 'import sys;print("%d.%d"%sys.version_info[:2],end="")' > $O/PYVER
	echo "  pyc: $(wc -l < $O.list) modules, Python $($PY -V)"
}
P14=~/cineview-mla/py314/python/bin/python3.14; P13=~/cineview-mla/py313/python/bin/python3.13
for img in openbh openvix; do
	rm -rf build_f$img
	MLA_IMAGE=$img MLA_CS_MOCKS=$PWD/csmock/out MLA_PREVIEWS=$PWD/previews python3 mi/tools/mla/build.py $G/share/enigma2/CineView_FHD \
		$G/lib/enigma2/python/Components $G/lib/enigma2/python/Plugins/Extensions/CineViewControl build_f$img > $F/build_$img.log 2>&1 \
		|| { echo "$img build failed"; tail -8 $F/build_$img.log; exit 2; }
	grep -c "BUILD OK" $F/build_$img.log >/dev/null && echo "  $img: BUILD OK"
done
pyc build_fatv $F/pyc_atv $P14; pyc build_fopenbh $F/pyc_bh $P13; pyc build_fopenvix $F/pyc_vix $P14
rm -rf $F/pkg; mkdir -p $F/pkg
MLA_RELEASE=1 MLA_TARGET=openatv MLA_HOMEPAGE=https://github.com/habeb-s/CineView-MLA python3 mi/tools/mla/package_ipk.py build_fatv 1.0.1 $F/pkg --pyc $F/pyc_atv | tail -1
MLA_RELEASE=1 MLA_TARGET=openbh MLA_HOMEPAGE=https://github.com/habeb-s/CineView-MLA python3 mi/tools/mla/package_ipk.py build_fopenbh 1.0.1~openbh1 $F/pkg --pyc $F/pyc_bh | tail -1
MLA_RELEASE=1 MLA_TARGET=openvix MLA_HOMEPAGE=https://github.com/habeb-s/CineView-MLA python3 mi/tools/mla/package_ipk.py build_fopenvix 1.0.1~openvix1 $F/pkg --pyc $F/pyc_vix | tail -1
(cd $F/pkg && sha256sum *.ipk | tee ../SHA256SUMS)
