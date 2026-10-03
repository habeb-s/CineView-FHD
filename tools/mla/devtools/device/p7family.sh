#!/bin/bash
# P7 Details — device test on Slot 8 (build17).  Ends on Classic navy (factory), posters on.
. ~/cineview-mla/p6lib.sh
FAM=${FAM:-details}; S=~/cineview-mla/shots/$FAM; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ga() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; curl -s -m 20 -o $S/$1_osd.png "http://192.168.1.250/grab?format=png&mode=osd&r=1920"; echo "cap $1 @$($R 'date +%T')"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 30; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "tracebacks=$(grep -a -c Traceback $f)"; grep -a "Skin\] Error\|ShowIf\] invalid" $f | grep -v "progressPercentWidth\|piconMargin" | head -8'; }
arab() {  # $1 file $2 screen $3 tag
  python3 - "$1" "$2" > /tmp/tt2.json <<'PY'
import json,sys
n=json.load(open('/home/aiadmin/cineview-mla/arabic/narrow.json'))
d={"file":sys.argv[1],"screen":sys.argv[2],"seconds":24,"title_now":n["title_now"],"desc_now":n["desc_now"],"short_now":n["desc_now"][:180],
   "title_next":n.get("title_next",n["title_now"]),"desc_next":n.get("desc_next",n["desc_now"]),"short_next":n.get("desc_next",n["desc_now"])[:160]}
print(json.dumps(d,ensure_ascii=False))
PY
  X; cat /tmp/tt2.json | $R 'cat > /tmp/cvmla/texttest2.json.tmp && mv /tmp/cvmla/texttest2.json.tmp /tmp/cvmla/texttest2.json'; sleep 4; ga ${3}_t2; sleep 11; ga ${3}_t13; X
}
sib() { X; $RC 352; sleep 1; $RC 352; sleep 3; }
CH="1:0:19:784:C6D4:16E:A00000:0:0:0:|HBO 1:0:19:D49:C738:16E:A00000:0:0:0:|HRT1 1:0:16:123:3:40:A00000:0:0:0:|RTL 1:0:1:6E8:C544:16E:A00000:0:0:0:|N1 1:0:19:786:C6D4:16E:A00000:0:0:0:|Cinemax"
tour() { # $1 tag
  for c in $CH; do ref=${c%%|*}; n=${c##*|}
    curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$ref"; sleep 10
    X; $RC 352; sleep 2; ga ${1}_${n}_ib
    curl -s -m 5 "http://192.168.1.250/api/signal" | python3 -c "import json,sys; d=json.load(sys.stdin); print('   webif signal', '$n', d.get('snr'), d.get('snr_db'), d.get('agc'), d.get('ber'))" 2>/dev/null
    sib; ga ${1}_${n}_sib_t3; sleep 12; ga ${1}_${n}_sib_t15; X
  done
}
# 0. deploy build17 (+ generic text-test devtool), backup first
[ -n "$DEPLOY" ] && ./deploy_b.sh ${BLD:-build18} | grep -v "Skin\] Error\|InputDevice"
tar -C ~/cineview-mla/repo/tools/mla/devtools -czf - CineViewMLATextTest2 | $R 'tar -C /usr/lib/enigma2/python/Plugins/Extensions -xzf - && echo devtool-installed; grep -q CineViewMLATextTest2 /media/usb/cineview-mla/state/aux-installed 2>/dev/null || echo "/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLATextTest2 (devtool, Slot 8)" >> /media/usb/cineview-mla/state/aux-installed'
# 1. Details on both sections (independent selections), posters on
$R "$E validate --set infobar=$FAM --set secondinfobar=$FAM 2>&1 | tail -2; $E apply --set infobar=$FAM --set secondinfobar=$FAM 2>&1 | tail -1"
restart ""; st; errs
tour on
arab secondinfobar.xml SecondInfoBar ar_sib_on
arab infobar.xml InfoBar ar_ib_on
# 2. posters off (both sections)
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_infobar=False config.plugins.cineviewmla.poster_secondinfobar=False;"
errs
curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=1:0:19:784:C6D4:16E:A00000:0:0:0:"; sleep 10
X; $RC 352; sleep 2; ga off_HBO_ib; sib; ga off_HBO_sib_t3; sleep 12; ga off_HBO_sib_t15; X
arab secondinfobar.xml SecondInfoBar ar_sib_off
arab infobar.xml InfoBar ar_ib_off
# 3. independence: Classic InfoBar + Details SecondInfoBar
$R "$E apply --set infobar=classic --set secondinfobar=$FAM 2>&1 | tail -1"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_infobar=True config.plugins.cineviewmla.poster_secondinfobar=True;"
X; $RC 352; sleep 2; ga mix_ib_classic; sib; ga mix_sib_$FAM; X
# 4. the six themes on the family (IB + SIB, OSD layer; themecheck afterwards)
for t in ${THEMES:-navy black graphite burgundy green purple}; do
  $R "$E apply --theme $t --set infobar=$FAM --set secondinfobar=$FAM 2>&1 | tail -1"
  restart ""; errs
  mkdir -p $S/themes/$t
  X; $RC 352; sleep 2; ga themes/$t/ib; sib; ga themes/$t/sib; X
done
# 5. back to Classic navy (factory), posters on
$R "$E rollback --to factory 2>&1 | tail -1"; restart ""; st; errs
X; $RC 352; sleep 2; ga final_classic_ib; X
echo DETAILS_DONE
