#!/bin/bash
# RTL one-line title experiment: 7 RunningText/Label configs fed the same long Arabic title (TextTest2 devtool).
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/rtltest; rm -rf $S; mkdir -p $S
cat ~/cineview-mla/rtltest.xml | $R 'cat > /tmp/cvmla/rtltest.xml'
python3 - > /tmp/rt.json <<'PY'
import json
n=json.load(open('/home/aiadmin/cineview-mla/arabic/narrow.json'))
print(json.dumps({"file":"/tmp/cvmla/rtltest.xml","screen":"RTLTest","seconds":40,"title_now":n["title_now"]},ensure_ascii=False))
PY
X; cat /tmp/rt.json | $R 'cat > /tmp/cvmla/texttest2.json.tmp && mv /tmp/cvmla/texttest2.json.tmp /tmp/cvmla/texttest2.json'
sleep 2.5; g0() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; echo "cap $1"; }
for k in 01 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18; do g0 t$k; sleep 0.6; done
X; echo RTL_DONE
