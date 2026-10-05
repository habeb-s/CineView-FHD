#!/bin/bash
# Columns EPG pack (build51) on the native vertical EPG: open, move the active column (RIGHT) and the event (DOWN),
# the event card must follow the selection; posters ON / OFF (card reflow); navy + burgundy; INFO -> EventViewSimple
# (plugin rule) and back; skin errors / tracebacks after each step.  Restore: Classic EPG, navy, posters ON.
exec 9>~/cineview-mla/t58.lock; flock -n 9 || { echo "t58 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build51}
S=~/cineview-mla/shots/t58; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HBO="1:0:19:784:C6D4:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error" $f | grep -v "progressPercentWidth\|piconMargin\|Summary" | tail -6 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 8; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
cols() {  # $1 tag
  zap $HBO; X; op vertical 9; ga col_$1_open; $RC 106; sleep 3; ga col_$1_right1; $RC 106; sleep 3; $RC 108; sleep 3; ga col_$1_right2_down1
  $RC 108; sleep 3; $RC 108; sleep 3; ga col_$1_down3; $RC 358; sleep 5; ga col_$1_info; X; sleep 2; ga col_$1_back; X; sleep 2; X; sleep 2
}
~/cineview-mla/deploy_b.sh $NEW
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
for t in navy burgundy; do
  $R "$E apply --theme $t --set epg=columns 2>&1 | tail -1"; restart ""; errs
  echo "== $t posters ON"; cols ${t}_on; errs
done
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=False;"; errs
echo "== burgundy posters OFF"; cols burgundy_off; errs
restart "python3 /tmp/cvmla/setcfg.py config.plugins.cineviewmla.poster_epg=True;"
$R "$E apply --theme navy --set epg=classic 2>&1 | tail -1"; $R "rm -rf $P"; restart ""; st; errs
echo T58_DONE
