#!/bin/bash
# Compare each final package with the approved / tested package it replaces: data files (content), control,
# maintainer scripts.  Every difference is listed; unchanged .pyc being byte-identical proves the local compiler
# produces what the receiver's own Python produced.
cd ~/cineview-mla
F=final; X=$F/x; rm -rf $X; mkdir -p $X
ex() { mkdir -p $X/$1/c $X/$1/d; (cd $X/$1 && ar x ../../../$2 && tar xzf control.tar.gz -C c && tar xzf data.tar.gz -C d); }
ex atv_new $F/pkg/*_1.0.1_all.ipk;            ex atv_gold pkg_pub/*_1.0.0_all.ipk;   ex atv_cand atv8/cand/pkg/*.ipk
ex bh_new $F/pkg/*~openbh1_all.ipk;           ex bh_old pkg_bh/*~openbh17_all.ipk
ex vix_new $F/pkg/*~openvix1_all.ipk;         ex vix_old release_openvix/*~openvix1_all.ipk
cmpp() {  # cmpp <new> <old> <label>
	echo "== $3"
	diff <(cd $X/$2/d && find . \( -type f -o -type l \) | sort) <(cd $X/$1/d && find . \( -type f -o -type l \) | sort) | sed 's/^/   list: /' | grep -v "^   list: [0-9]" 
	n=0; (cd $X/$1/d && find . -type f | sort) | while read f; do
		[ -f $X/$2/d/$f ] && ! cmp -s $X/$1/d/$f $X/$2/d/$f && echo "   changed: ${f#./}"
	done
	for s in control preinst postinst prerm postrm; do cmp -s $X/$1/c/$s $X/$2/c/$s || echo "   script/control differs: $s"; done
	echo "   pyc identical: $(cd $X/$1/d && find . -name '*.pyc' | while read f; do cmp -s $f ../../$2/d/$f && echo x; done | wc -l) of $(cd $X/$1/d && find . -name '*.pyc' | wc -l)"
}
cmpp atv_new atv_cand "OpenATV 1.0.1 vs runtime-tested candidate 1.0.1~atv1"
cmpp atv_new atv_gold "OpenATV 1.0.1 vs Golden 1.0.0"
cmpp bh_new bh_old "OpenBH 1.0.1~openbh1 vs approved 1.0.0~openbh17"
cmpp vix_new vix_old "OpenViX 1.0.1~openvix1 vs approved 1.0.0~openvix1"
echo "== plugin.pyc: version line"
for p in atv_new bh_new vix_new atv_gold bh_old vix_old; do
	f=$X/$p/d/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/plugin.pyc
	printf '   %-9s old-format(version on screen)=%s  new-format(name only)=%s\n' $p "$(grep -c -a 'CineView MLA %s' $f)" "$(grep -c -a -F 'CineView MLA
%s: %s' $f)"
done
echo "== control (new)"; for p in atv_new bh_new vix_new; do grep -E "^(Version|Description)" $X/$p/c/control | sed "s/^/   $p /"; done
echo "== preinst version gate (new)"; for p in atv_new bh_new vix_new; do grep -E "^\s+[0-9].*\) ;;$" $X/$p/c/preinst | sed "s/^/   $p /"; done
