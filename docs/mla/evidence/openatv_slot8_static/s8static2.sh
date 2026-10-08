set -u
cd ~/cineview-mla
PY=~/cineview-mla/py314/python/bin/python3.14
OUT=s8static; S8=slot8ro; INFO8=$S8/usr/lib/enigma.info
W=$(mktemp -d /tmp/s8w.XXXX)
# E. composer: golden vs candidate engine, every layout of every section and every theme, image from Slot 8's
#    enigma.info; the generated screen files must be identical except the allowed PVR icon / CAM wrap lines
cat > $W/comp.py <<'EOF'
import json, os, shutil, subprocess, sys, hashlib
W, which, info = sys.argv[1], sys.argv[2], sys.argv[3]
src = {"golden": "build94", "cand": "build_s8cand"}[which]
skin = os.path.join(W, which, "skin"); state = os.path.join(W, which, "state")
shutil.copytree(os.path.join(src, "usr/share/enigma2/CineView_FHD_MLA"), skin, symlinks=True)
os.makedirs(state)
comp = os.path.join(skin, "mla/engine/composer.py")
s = open(comp).read()
if "ENIGMA_INFO = " in s:
	s = s.replace('ENIGMA_INFO = "/usr/lib/enigma.info"', 'ENIGMA_INFO = %r' % os.path.abspath(info))
open(comp, "w").write(s)
env = dict(os.environ, MLA_SKIN_DIR=skin, MLA_STATE_DIR=state)
env.pop("MLA_IMAGE", None)
secs = json.load(open(os.path.join(skin, "mla/sections.json")))["sections"]
lays = {sec: sorted(d for d in os.listdir(os.path.join(skin, "layouts", sec)) if os.path.isdir(os.path.join(skin, "layouts", sec, d))) for sec in secs}
themes = sorted(d for d in os.listdir(os.path.join(skin, "themes")) if os.path.isdir(os.path.join(skin, "themes", d)))
runs = [["--set", "%s=%s" % (sec, l)] for sec in secs for l in lays[sec]] + [["--theme", t] for t in themes]
out = {}
for i, a in enumerate(runs):
	r = subprocess.run([sys.executable, comp, "apply"] + a, env=env, capture_output=True, text=True)
	act = os.path.realpath(os.path.join(skin, "active"))
	files = {}
	for f in sorted(os.listdir(act)):
		p = os.path.join(act, f)
		if os.path.isfile(p) and f.endswith(".xml"):
			files[f] = open(p).read()
	out[" ".join(a)] = {"rc": r.returncode, "files": files}
json.dump(out, open(os.path.join(W, which + ".json"), "w"))
print(which, len(runs), "applies, failures:", sum(1 for v in out.values() if v["rc"]))
EOF
python3 $W/comp.py $W golden $INFO8
python3 $W/comp.py $W cand $INFO8
python3 - $W > $OUT/E_composer_equivalence.txt <<'EOF'
import json, re, sys
W = sys.argv[1]
g = json.load(open(W + "/golden.json")); c = json.load(open(W + "/cand.json"))
norm = lambda t: re.sub(r',wrap"', '"', t.replace('position="1600,8"', 'position="1740,45"').replace('position="1660,8"', 'position="1800,45"'))
same = allowed = bad = 0
for k in g:
	for f, t in g[k]["files"].items():
		u = c[k]["files"].get(f)
		if u == t: same += 1
		elif u is not None and norm(u) == t: allowed += 1
		else: bad += 1; print("DIFF", k, f)
	if g[k]["rc"] != c[k]["rc"]: bad += 1; print("RC", k, g[k]["rc"], c[k]["rc"])
print("applies: %d; generated screen files identical: %d, differing only by PVR icon position / CAM wrap: %d, other differences: %d" % (len(g), same, allowed, bad))
EOF
tail -1 $OUT/E_composer_equivalence.txt
# F. guardian crash-loop tests, golden and candidate scripts (isolated copies)
for t in build94 build_s8cand; do sh mi/tools/mla/test_guardian.sh $t/usr/share/enigma2/CineView_FHD_MLA $W/g_$t > $OUT/F_guardian_$t.txt 2>&1; echo "guardian $t: $(grep -c ^PASS $OUT/F_guardian_$t.txt) PASS, $(grep -c ^FAIL $OUT/F_guardian_$t.txt) FAIL"; done
# G. ImageAdapter with Slot 8's own enigma.info
$PY - $INFO8 > $OUT/G_image_adapter.txt <<'EOF'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("ia", "build_s8cand/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA/image_adapter.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.ENIGMA_INFO = sys.argv[1]
class U:  # config.usage stand-in with the two OpenATV settings
	show_second_infobar = "SIB"; second_infobar_timeout = "SIBT"
print("image:", m.image())
print("native rows:", [(r[0], r[2]) for r in m.native_rows(U)])
print("shutdown hook:", m.shutdown_hook(), "| ChoiceBox:", m.choice_list(["x"]), "| package wait:", m.package_wait(), "| name clip:", m.name_clip(), "| label overrides:", m.label_overrides())
EOF
cat $OUT/G_image_adapter.txt
# H. candidate OpenATV package (structure only, NOT a release): .pyc with Python 3.14 as mkpyc.sh does
rm -rf $W/pyc; mkdir -p $W/pyc
(cd build_s8cand && find usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA -name '*.py'; cd ~/cineview-mla/build_s8cand && find usr/lib/enigma2/python/Components -name 'CineViewMLA*.py') | sort -u > $W/pylist
while read f; do mkdir -p $W/pyc/$(dirname $f); $PY -c "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], dfile='/'+sys.argv[3], doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)" build_s8cand/$f $W/pyc/${f}c $f; done < $W/pylist
echo 3.14 > $W/pyc/PYVER
python3 mi/tools/mla/package_ipk.py build_s8cand 1.0.0~s8static $W/pkg --pyc $W/pyc > $OUT/H_package.txt 2>&1; tail -2 $OUT/H_package.txt
mkdir -p $W/cx && (cd $W/cx && ar x $W/pkg/*.ipk && mkdir c d && tar xzf control.tar.gz -C c && tar xzf data.tar.gz -C d)
{ echo "control scripts vs published 1.0.0:"; for s in preinst postinst prerm postrm; do cmp -s pub100/x/control/$s $W/cx/c/$s && echo "  $s identical" || { echo "  $s DIFFERS:"; diff pub100/x/control/$s $W/cx/c/$s | head -20; }; done
  diff <(cd pub100/x/data && find . -type f | sort) <(cd $W/cx/d && find . -type f | sort) > $W/fl.txt && echo "file list: identical ($(cd $W/cx/d && find . -type f | wc -l) files)" || { echo "file list differs:"; cat $W/fl.txt; }
  echo "files with different content:"; (cd pub100/x/data && find . -type f) | while read f; do cmp -s pub100/x/data/$f $W/cx/d/$f || echo "  $f"; done; } > $OUT/H_package_vs_published.txt
cat $OUT/H_package_vs_published.txt | head -50
# I. Smart Installer image detection (dev/openbh-installer) on Slot 8's files - detection part only, nothing installed
git -C ~/cineview-mla/prodrepo fetch -q 2>/dev/null
gh api repos/habeb-s/CineView-MLA/contents/install/cineview-install.sh?ref=dev/openbh-installer -q .content | base64 -d > $W/inst.sh
gh api repos/habeb-s/CineView-MLA/contents/install/cineview-install.sh?ref=main -q .content | base64 -d > $W/inst_pub.sh
for v in inst inst_pub; do
	n=$(grep -n '^section "Python"' $W/$v.sh | cut -d: -f1)
	head -$((n - 1)) $W/$v.sh | sed -e 's#\[ -x /usr/bin/enigma2 \] && \[ -d /usr/lib/enigma2/python/Components \]#true#' -e "s#/usr/lib/enigma2/python/Screens/PluginBrowser.py\*#$PWD/$S8/usr/lib/enigma2/python/Screens/PluginBrowser.py*#" -e "s#/usr/lib/enigma.info#$PWD/$INFO8#" > $W/$v.head.sh
	echo 'echo "DECISION image=$IMG version=$VERSION url=$PKG_URL sha=$PKG_SHA python=$PY_NEED"' >> $W/$v.head.sh
	CVMLA_INFO=$PWD/$INFO8 sh $W/$v.head.sh > $OUT/I_installer_$v.txt 2>&1; echo "== $v"; grep -v "^$" $OUT/I_installer_$v.txt | sed 's/\x1b\[[0-9;]*m//g' | tail -8
done
echo "Slot 8 Python: $(ls $S8/../ 2>/dev/null >/dev/null; grep -A1 '^Package: python3-core$' $S8/var/lib/opkg/status | sed -n 's/^Version: //p')"
rm -rf $W
echo S8STATIC2_DONE
