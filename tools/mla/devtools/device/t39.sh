#!/bin/bash
# EventView motions, Arabic + English (Slot 8, build35), autonomous order 2026-10-04 22:06 §3d.
# The live EventView screen of the active pack is rendered by the dev tool CineViewMLATextTest2 with long Arabic and
# English texts (no EPG data touched).  Displayed-framebuffer recordings, 60 s, 5 fps, of the left description box:
#   classic-lines (line by line): every jump checked pixel-exactly (jumpcheck.py: doubled / stale lines)
#   classic (continuous swim):  fbana.py metrics (motion steps, frames with an empty top third = blank band)
# Two rounds per pack and language.  Restore: classic-lines active (as before), dev tool removed.
exec 9>~/cineview-mla/t39.lock; flock -n 9 || { echo "t39 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/t39; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
U=/media/usb/cineview-mla/tmp
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
cat ~/cineview-mla/fbrec2.py | $R 'cat > /tmp/cvmla/fbrec2.py'
tar -C ~/cineview-mla/repo/tools/mla/devtools -czf - CineViewMLATextTest2 | $R 'cat > /tmp/cvmla/tt2.tgz'
tt() {  # $1 lang
  python3 - "$1" <<'PYX' | $R 'cat > /tmp/cvmla/texttest2.json.tmp && mv /tmp/cvmla/texttest2.json.tmp /tmp/cvmla/texttest2.json'
import json,sys
n=json.load(open('/home/aiadmin/cineview-mla/arabic/long.json'))[sys.argv[1]]
d={"file":"eventview.xml","screen":"EventView","seconds":70,"title_now":n["title_now"],"desc_now":n["desc_now"],"short_now":n["desc_now"][:180],
   "title_next":n["title_next"],"desc_next":n["desc_next"],"short_next":n["desc_next"][:160]}
print(json.dumps(d,ensure_ascii=False))
PYX
}
rec() {  # $1 tag $2 mode(lines|swim)
  $R "python3 /tmp/cvmla/fbrec2.py 95 245 480 261 5 60 $U/rec.bin"
  $R "cat $U/rec.bin" > $S/$1.bin; $R "rm -f $U/rec.bin"
  if [ "$2" = lines ]; then
    python3 ~/cineview-mla/jumpcheck.py $S/$1.bin > $S/$1.jumps.txt
    echo "   $1: $(tail -1 $S/$1.jumps.txt)"
  else
    python3 ~/cineview-mla/fbana.py $S/$1.bin $S/$1.gif "$1" > $S/$1.ana.txt 2>&1
    echo "   $1: $(tail -2 $S/$1.ana.txt | tr '\n' ' ')"
  fi
}
round() { for lang in ar en; do X; tt $lang; sleep 4.2; rec ${1}_${lang} $2; X; sleep 2; done; errs; }
restart 'tar -C /usr/lib/enigma2/python/Plugins/Extensions -xzf /tmp/cvmla/tt2.tgz && echo devtool-installed;'
echo "== line by line (classic-lines)"
$R "$E apply --set eventview=classic-lines 2>&1 | tail -1"; restart ""; errs
round lines1 lines; round lines2 lines
echo "== continuous (classic)"
$R "$E apply --set eventview=classic 2>&1 | tail -1"; restart ""; errs
round swim1 swim; round swim2 swim
echo "== restore"
$R "$E apply --set eventview=classic-lines 2>&1 | tail -1"
restart 'rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLATextTest2 /tmp/cvmla/texttest2.json;'; st; errs
echo T39_DONE
