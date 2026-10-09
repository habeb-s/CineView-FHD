#!/bin/bash
# Rebuild the three image trees from mi (working tree) exactly as build_final.sh does; compare with the trees the
# approved 1.0.1 packages were made from.  Expected differences: CineViewMLACPUTemp.py (1.0.2), and for 1.0.3
# CineViewMLAPosterMatch.py + CineViewMLAPosterX.py only.
cd ~/cineview-mla
G=candidates/golden0926/usr
for img in openatv openbh openvix; do
	O=oct/c_$img; rm -rf $O
	if [ $img = openatv ]; then E=""; REF=build_fatv; else E="MLA_IMAGE=$img"; REF=build_f$img; fi
	env $E MLA_CS_MOCKS=$PWD/csmock/out MLA_PREVIEWS=$PWD/previews python3 mi/tools/mla/build.py $G/share/enigma2/CineView_FHD \
		$G/lib/enigma2/python/Components $G/lib/enigma2/python/Plugins/Extensions/CineViewControl $O > oct/build103_$img.log 2>&1 \
		|| { echo "$img BUILD FAILED"; tail -5 oct/build103_$img.log; continue; }
	echo "== $img vs $REF:"; diff -rq --exclude=__pycache__ $REF $O | sed "s#$REF/##;s#$O/##"
	cmp -s $O/usr/lib/enigma2/python/Components/CineViewMLAPosterMatch.py mi/mla/components/_lib/CineViewMLAPosterMatch.py && echo "   PosterMatch = mla/components/_lib"
done
md5sum oct/c_*/usr/lib/enigma2/python/Components/Renderer/CineViewMLAPosterX.py
echo DONE
