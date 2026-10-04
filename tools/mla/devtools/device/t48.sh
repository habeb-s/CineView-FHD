#!/bin/bash
# HD / 16:9 indicators after a restart on the SAME channel (t43: Modern chips missing in 2 of 6 theme runs, while
# the resolution showed 1920x1080).  Hypothesis: when enigma2 boots on the channel that is then "zapped" again,
# the InfoBar's ServiceInfo conditions miss the video-size event -> Enigma2 timing, not the skin.  Same sequence
# for Classic (native Pixmap + ConditionalShowHide icons) and Modern (Label chips + CineViewMLAShowIf bool):
# 4 x (restart while on HRT1, zap HRT1, OK, grab) + 2 x (zap HBO 2 -> zap HRT1, OK, grab).  Build41, Slot 8.
exec 9>~/cineview-mla/t48.lock; flock -n 9 || { echo "t48 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build41}
S=~/cineview-mla/shots/t48; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"; HBO2="1:0:19:785:C6D4:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 9; }
~/cineview-mla/deploy_b.sh $NEW
for ib in classic modern; do
  $R "$E apply --theme navy --set infobar=$ib 2>&1 | tail -1"
  zap $HRT1
  for i in 1 2 3 4; do restart ""; zap $HRT1; X; sleep 2; $RC 352; sleep 2.5; ga ${ib}_boot$i; X; done
  for i in 1 2; do zap $HBO2; zap $HRT1; X; sleep 2; $RC 352; sleep 2.5; ga ${ib}_zap$i; X; done
  errs
done
$R "$E apply --theme navy --set infobar=classic 2>&1 | tail -1"; restart ""; st; errs
echo T48_DONE
