#!/bin/bash
# mkpyc.sh <build dir> <out dir>: compile the package's importable modules (Components/CineViewMLA*, the CineView
# Designs plugin) with the RECEIVER's own Python (OpenATV 8.0.1: Python 3.14), for package_ipk.py --pyc <out dir>.
# On the receiver only /tmp/cvmla/pyc is used (removed afterwards); nothing installed is touched.
# The .pyc files are sourceless-loadable (legacy location <module>.pyc next to where the .py would be), with an
# unchecked hash (no source to compare with) and the final install path as their file name (tracebacks stay readable).
set -e
. ~/cineview-mla/p6lib.sh
B=${1:?build}; O=${2:?out}
rm -rf "$O"; mkdir -p "$O"
LIST=$(cd "$B" && find usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA -name '*.py'; cd "$B" && find usr/lib/enigma2/python/Components -name 'CineViewMLA*.py')
( cd "$B" && tar -czf - $LIST ) | $R 'rm -rf /tmp/cvmla/pyc && mkdir -p /tmp/cvmla/pyc && tar -C /tmp/cvmla/pyc -xzf -'
$R 'cd /tmp/cvmla/pyc && python3 - <<EOF
import os, sys, py_compile
n = 0
for root, d, files in os.walk("usr"):
    for f in files:
        if f.endswith(".py"):
            src = os.path.join(root, f)
            py_compile.compile(src, cfile=src + "c", dfile="/" + src, doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
            os.remove(src)
            n += 1
open("PYVER", "w").write("%d.%d" % sys.version_info[:2])
print("compiled", n, "modules with Python", sys.version.split()[0], file=sys.stderr)  # stdout carries the tar
EOF
tar -czf - .' | tar -C "$O" -xzf -
$R 'rm -rf /tmp/cvmla/pyc'
echo "PYVER $(cat $O/PYVER); $(find $O -name '*.pyc' | wc -l) pyc files in $O"
