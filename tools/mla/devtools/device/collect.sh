#!/bin/bash
# Copy selected device screenshots (PNG 1920x1080) as JPG (1280x720, q82) into the repo evidence folder,
# plus device scripts, then commit + push on dev/mla-openatv.   usage: collect.sh <dest subdir> <src dir> [glob...]
set -e
DEST=$1; SRC=$(readlink -f $2); shift 2
cd ~/cineview-mla/repo && git pull -q --rebase
D=docs/mla/evidence/$DEST; mkdir -p $D
for pat in "$@"; do
  for f in $SRC/$pat; do
    [ -f "$f" ] || continue
    rel=${f#$SRC/}; out=$D/$(echo ${rel%.png} | tr '/' '_').jpg
    convert "$f" -resize 1280x720 -quality 82 "$out"
  done
done
mkdir -p tools/mla/devtools/device
cp ~/cineview-mla/{p7family.sh,evtear.sh,evtear.py,evband.py,themecheck.py,rtltest.sh,rtltest.xml,p8ui.sh,p8pkg.sh,p5test.sh,p5restore.sh,deploy_b.sh,collect.sh} tools/mla/devtools/device/ 2>/dev/null || true
git add -A docs/mla/evidence tools/mla/devtools/device
git commit -qm "evidence: $DEST device screenshots + device test scripts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_012fViUcPdZFjrUqLnH6WNgX" || true
git push -q origin dev/mla-openatv && git log --oneline -1
