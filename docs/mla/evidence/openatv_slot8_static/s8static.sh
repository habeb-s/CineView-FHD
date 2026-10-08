set -u
cd ~/cineview-mla
PY=~/cineview-mla/py314/python/bin/python3.14
OUT=s8static; rm -rf $OUT; mkdir -p $OUT
# 0. enigma2 57b7a5127d source (= Slot 8, proven by the .pyc source hashes)
rm -rf e2_57b; mkdir -p e2_57b; git -C e2git archive 57b7a5127d lib/python lib/gdi lib/gui lib/service | tar x -C e2_57b
echo "== 57b7a5127d python files: $(find e2_57b/lib/python -name '*.py' | wc -l)"
# 1. published package .pyc <-> build94 sources (hash-based pyc)
$PY - <<'EOF' > $OUT/1_pub_pyc_vs_build94.txt
import importlib.util, os
pub, src = "pub100/x/data", "build94"
ok = bad = 0
for d, _, fs in os.walk(pub):
	for f in fs:
		if f.endswith(".pyc"):
			p = os.path.join(d, f); rel = os.path.relpath(p, pub)[:-1]
			h = open(p, "rb").read(16)
			s = os.path.join(src, rel)
			flags = int.from_bytes(h[4:8], "little")
			if not os.path.exists(s):
				print("NO SOURCE", rel); bad += 1; continue
			if flags & 1 and importlib.util.source_hash(open(s, "rb").read()) == h[8:16]:
				ok += 1
			else:
				print("MISMATCH", rel, "flags", flags); bad += 1
print("published .pyc matching build94 sources: %d, other: %d" % (ok, bad))
EOF
cat $OUT/1_pub_pyc_vs_build94.txt | tail -1
# 2. candidate OpenATV build from the current dev branch + parity gate
(cd mi && git checkout -q -- . && git fetch -q origin dev/mla-multiimage && git checkout -q FETCH_HEAD && git log --oneline -1) > $OUT/2_candidate_commit.txt
bash mi/tools/mla/parity_openatv.sh ~/cineview-mla/mi build_s8cand > $OUT/2_parity.txt 2>&1; tail -1 $OUT/2_parity.txt
# 3. Python 3.14 compile of every candidate .py (in memory, nothing written)
$PY - <<'EOF' > $OUT/3_py314_compile.txt
import os
n = bad = 0
for d, _, fs in os.walk("build_s8cand"):
	for f in fs:
		if f.endswith(".py"):
			p = os.path.join(d, f); n += 1
			try:
				compile(open(p, "rb").read(), p, "exec")
			except SyntaxError as e:
				bad += 1; print("SYNTAX", p, e)
print("compiled with Python 3.14.8: %d files, %d errors" % (n, bad))
EOF
tail -1 $OUT/3_py314_compile.txt
# 4. XML well-formedness of every candidate skin file
$PY - <<'EOF' > $OUT/4_xml.txt
import os, xml.etree.ElementTree as ET
n = bad = 0
for d, _, fs in os.walk("build_s8cand/usr/share/enigma2/CineView_FHD_MLA"):
	for f in fs:
		if f.endswith(".xml"):
			n += 1
			try: ET.parse(os.path.join(d, f))
			except ET.ParseError as e: bad += 1; print("XML", os.path.join(d, f), e)
print("XML files parsed: %d, errors: %d" % (n, bad))
EOF
tail -1 $OUT/4_xml.txt
# 5. screen contracts (skinName + self[...] widgets) of 57b7a5127d vs the skin, golden and candidate
python3 mi/tools/mla/contracts.py extract e2_57b/lib/python $OUT/contracts_57b.json > /dev/null
for t in build94 build_s8cand; do
	python3 mi/tools/mla/contracts.py check $OUT/contracts_57b.json $(find $t/usr/share/enigma2/CineView_FHD_MLA -name '*.xml' | grep -v '/generations/\|/active/' | sort) > $OUT/5_contracts_$t.txt 2>&1
	echo "$t: $(tail -1 $OUT/5_contracts_$t.txt)"
done
diff <(sed 's#build94/##' $OUT/5_contracts_build94.txt) <(sed 's#build_s8cand/##' $OUT/5_contracts_build_s8cand.txt) > $OUT/5_contracts_diff.txt && echo "contracts: candidate findings identical to golden" || echo "contracts: candidate differs from golden (see 5_contracts_diff.txt)"
echo S8STATIC_DONE
