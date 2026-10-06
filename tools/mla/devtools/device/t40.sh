#!/bin/bash
# build36 check (Slot 8): Graphical Plus without the 'date' SkinError (posters ON/OFF, cursor moves, the OFF screen
# chosen by the plugin), reliable IMDb ratings (InfoBar / SIB / EventView / Graphical Plus on several channels) with the
# identity meta and the IMDb value of that exact id fetched from ai-agent for comparison.  Ends with Classic,
# classic-lines, navy, posters on; dev trigger plugin removed.
exec 9>~/cineview-mla/t40.lock; flock -n 9 || { echo "t40 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build36}
S=~/cineview-mla/shots/t40; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"; HBO2="1:0:19:785:C6D4:16E:A00000:0:0:0:"; CINEMAX="1:0:19:786:C6D4:16E:A00000:0:0:0:"; HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 @$($R 'date +%T') $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|Processing screen .GraphicalEPG" $f | grep -v "progressPercentWidth\|piconMargin" | tail -4'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "mkdir -p /tmp/cvmla; echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
apply() { $R "$E apply $* 2>&1 | tail -1"; }
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
apply --theme navy --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=graphicalplus --set eventview=classic-lines --set pvr=classic
restart ""; errs
echo "== Graphical Plus ON"
zap $HBO; X; op graph 9; ga gp_on; $RC 106; sleep 3; ga gp_on_right; $RC 108; sleep 3; ga gp_on_down; X; errs
echo "== Graphical Plus OFF"
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=False;"; errs
zap $HBO; X; op graph 9; ga gp_off; $RC 106; sleep 3; ga gp_off_right; $RC 108; sleep 3; ga gp_off_down; X; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=True;"; errs
echo "== IMDb ratings (reliable identities only)"
for ch in "$HBO|hbo" "$HBO2|hbo2" "$CINEMAX|cinemax" "$HRT1|hrt1"; do
  zap ${ch%%|*}; X; sleep 6; $RC 352; sleep 2; ga imdb_${ch##*|}_infobar; X; $RC 358; sleep 5; ga imdb_${ch##*|}_eventview; X
  t=$(curl -s -m 8 "http://192.168.1.250/api/epgservicenow?sRef=${ch%%|*}" | python3 -c "import json,sys; e=(json.load(sys.stdin).get('events') or [{}])[0]; print(e.get('title',''))")
  echo "   ${ch##*|}: now='$t'"
  # clean video-only frame + its EPG/service data (Modern/Minimal mockups use a matching frame and data)
  [ "${ch##*|}" = hrt1 ] && { curl -s -m 60 -o $S/video_hrt1.png "http://192.168.1.250/grab?format=png&mode=video&r=1920"; curl -s -m 8 -o $S/hrt1_now.json "http://192.168.1.250/api/epgservicenow?sRef=${ch%%|*}"; curl -s -m 8 -o $S/hrt1_next.json "http://192.168.1.250/api/epgservicenext?sRef=${ch%%|*}"; echo "   hrt1 video frame $(ok $S/video_hrt1.png && echo png-ok || echo PNG-BAD)"; }
done
$R 'python3 - <<EOF
import json, glob, os
p = json.load(open("/etc/enigma2/cineview_mla/runtime.json")).get("poster_cache", "/media/usb/cineview-mla/dev-cache/mla/poster") + "/id"
for f in sorted(glob.glob(p + "/*.json"), key=os.path.getmtime, reverse=True)[:40]:
    print(open(f).read().strip())
EOF' > $S/identity_meta.jsonl
$R 'tail -60 /tmp/CINEVIEW-MLA/poster.log' > $S/poster_log.txt
errs
$R "rm -rf $P"
apply --set epg=classic
restart ""; st; errs
$R "grep -E 'show_second_infobar|cineviewmla.poster' /etc/enigma2/settings"
echo T40_DONE
