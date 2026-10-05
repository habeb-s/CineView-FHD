#!/bin/bash
# t83: the same attribution run as t81 (fixed zap order, gAccel debug, 8 rounds) on build75: the widget-size poster
# PNG is made with PIL from the original (no gPixmap; ePicLoad.getData() allocates accelAuto, picload.cpp:1348).
# The derived widget-size folder sz/ (USB dev cache) is moved aside for the run, so EVERY poster takes the first-decode
# path; afterwards the ePicLoad-made folder is put back and the PIL-made one is kept as sz.t83pil for the A/B
# comparison of identical posters.  Originals are only read.  Nothing on the HDD.
exec 9>~/cineview-mla/t83.lock; flock -n 9 || { echo "t83 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build75}
C=/media/usb/cineview-mla/dev-cache/reference/poster
$R "cd $C && [ -d sz ] && [ ! -e sz.t83bak ] && mv sz sz.t83bak; rm -rf sz.t83pil; echo sz aside: \$(ls sz.t83bak | wc -l) files"
$R ': > /tmp/CINEVIEW-MLA/poster.log 2>/dev/null; true'
cd ~/cineview-mla && ./t81.sh $NEW deploy c
echo "== t83: widget-size PNGs made with PIL during the run: $($R 'grep -a -c "sized make" /tmp/CINEVIEW-MLA/poster.log')"
$R 'grep -a "sized make\|sized save\|sized load\|picload fallback" /tmp/CINEVIEW-MLA/poster.log | cut -c1-150 | tail -8'
$R "cd $C && mv sz sz.t83pil && mv sz.t83bak sz && echo restored: sz \$(ls sz | wc -l) files, sz.t83pil \$(ls sz.t83pil | wc -l) files"
# A/B of identical posters: ePicLoad-made (sz) vs PIL-made during this run (sz.t83pil)
S=~/cineview-mla/shots/t83; rm -rf $S; mkdir -p $S
$R "cd $C && python3 - <<'PYEOF'
import os, math
from PIL import Image, ImageChops, ImageStat
a, b = 'sz', 'sz.t83pil'
both = sorted(set(os.listdir(a)) & set(os.listdir(b)))
res = []
for n in both:
    x = Image.open(os.path.join(a, n)).convert('RGB'); y = Image.open(os.path.join(b, n)).convert('RGB')
    if x.size != y.size:
        print('SIZE MISMATCH', n, x.size, y.size); continue
    d = ImageChops.difference(x, y); ms = sum(v * v for v in ImageStat.Stat(d).rms) / 3
    res.append((99.0 if ms == 0 else 10 * math.log10(255 * 255 / ms), n, x, y))
res.sort(key=lambda r: r[0])
if res:
    v = [r[0] for r in res]
    print('AB pairs=%d psnr min/median/max %.1f/%.1f/%.1f' % (len(v), v[0], v[len(v) // 2], v[-1]))
for i, (p, n, x, y) in enumerate(res[:2] + res[len(res) // 2:len(res) // 2 + 1]):
    w, h = x.size; s = max(1, 300 // w + (1 if w < 300 else 0))
    c = Image.new('RGB', (2 * w * s + 30, h * s + 20), (40, 40, 40))
    c.paste(x.resize((w * s, h * s), Image.NEAREST), (10, 10)); c.paste(y.resize((w * s, h * s), Image.NEAREST), (w * s + 20, 10))
    c.save('/tmp/t83ab_%d.png' % i); print('ab', i, n, '%.1f dB' % p)
PYEOF"
for i in 0 1 2; do $R "[ -f /tmp/t83ab_$i.png ] && cat /tmp/t83ab_$i.png" > $S/AB_$i.png; [ -s $S/AB_$i.png ] || rm -f $S/AB_$i.png; done
$R 'rm -f /tmp/t83ab_*.png'
echo T83_DONE
