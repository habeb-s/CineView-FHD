#!/bin/bash
# Modern InfoBar on the receiver (build38, Slot 8; look NOT approved, real-device review only):
#  A posters ON: HRT1 (FTA, clean video), HBO 2 (reliable poster + IMDb), Cinemax; OpenWebif signal saved per grab
#  B posters OFF: HRT1, HBO 2
#  C six themes, posters ON, HRT1
#  D long Arabic / English titles (CineViewMLATextTest2 on the live InfoBar screen)
#  restore: infobar=classic, navy, posters on, dev tools removed.
exec 9>~/cineview-mla/t43.lock; flock -n 9 || { echo "t43 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build38}
S=~/cineview-mla/shots/t43; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"; HBO2="1:0:19:785:C6D4:16E:A00000:0:0:0:"; CINEMAX="1:0:19:786:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; curl -s -m 8 -o $S/$1.signal.json "http://192.168.1.250/api/signal"; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD) signal=$(python3 -c "import json; d=json.load(open('$S/$1.signal.json')); print(d.get('snr'), d.get('db'), d.get('agc'))" 2>/dev/null)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|CVModernBold\|LiberationSans-Bold" $f | grep -v "progressPercentWidth\|piconMargin" | tail -5'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 9; }
ib() { zap $1; X; sleep 2; $RC 352; sleep 2.5; ga $2; X; }
~/cineview-mla/deploy_b.sh $NEW
$R "$E apply --theme navy --set infobar=modern 2>&1 | tail -1"
restart ""; errs
echo "== A posters ON"
ib $HRT1 a_on_hrt1; ib $HBO2 a_on_hbo2; ib $CINEMAX a_on_cinemax
echo "== B posters OFF"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_infobar=False;"; errs
ib $HRT1 b_off_hrt1; ib $HBO2 b_off_hbo2
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_infobar=True;"; errs
echo "== C themes"
for t in black burgundy graphite green purple navy; do
  $R "$E apply --theme $t --set infobar=modern 2>&1 | tail -1"; restart ""
  ib $HRT1 c_theme_$t
done
errs
echo "== D long texts AR / EN"
tar -C ~/cineview-mla/repo/tools/mla/devtools -czf - CineViewMLATextTest2 | $R 'cat > /tmp/cvmla/tt2.tgz'
restart 'tar -C /usr/lib/enigma2/python/Plugins/Extensions -xzf /tmp/cvmla/tt2.tgz && echo devtool-installed;'
zap $HRT1; X
for lang in ar en; do
  python3 - "$lang" <<'PYX' | $R 'cat > /tmp/cvmla/texttest2.json.tmp && mv /tmp/cvmla/texttest2.json.tmp /tmp/cvmla/texttest2.json'
import json,sys
n=json.load(open('/home/aiadmin/cineview-mla/arabic/long.json'))[sys.argv[1]]
print(json.dumps({"file":"infobar.xml","screen":"InfoBar","seconds":30,"title_now":n["title_now"],"desc_now":n["desc_now"],"short_now":n["desc_now"][:180],
  "title_next":n["title_next"],"desc_next":n["desc_next"],"short_next":n["desc_next"][:160]},ensure_ascii=False))
PYX
  sleep 4; ga d_long_${lang}_t0; sleep 6; ga d_long_${lang}_t6; X; sleep 3
done
errs
echo "== restore"
$R "$E apply --theme navy --set infobar=classic 2>&1 | tail -1"
restart 'rm -rf /usr/lib/enigma2/python/Plugins/Extensions/CineViewMLATextTest2 /tmp/cvmla/texttest2.json;'; st; errs
$R "grep -E 'cineviewmla.poster' /etc/enigma2/settings"
echo T43_DONE
