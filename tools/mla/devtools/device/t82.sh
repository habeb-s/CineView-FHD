#!/bin/bash
# No Poster layout instead of a placeholder (build73): every model, navy, posters ON.  The same screens on a channel
# whose current event HAS a poster (HBO HD / HBO 2 / HBO 3: whichever) and on HRT1 (news: generic, no poster):
# InfoBar, SecondInfoBar, channel list card, EventView (live) and EventView from the EPG (EventViewSimple).
# Expected: with a poster -> the posters-ON arrangement with the poster; without -> the posters-OFF arrangement, no
# placeholder.  USB only; nothing played / deleted; HDD not opened.  Restore: Classic navy, posters ON.
exec 9>~/cineview-mla/t82.lock; flock -n 9 || { echo "t82 already running"; exit 1; }
. ~/cineview-mla/p6lib.sh
NEW=${1:-build73}
S=~/cineview-mla/shots/t82; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
HRT1="1:0:19:D49:C738:16E:A00000:0:0:0:"
P=/usr/lib/enigma2/python/Plugins/Extensions/CineViewMLAScreenOpen
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; echo "cap $1 $(ok $S/$1.png && echo png-ok || echo PNG-BAD)"; }
op() { $R "echo $1 > /tmp/cvmla/open.txt"; sleep ${2:-5}; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") accel=$(grep -a -c "accelAlloc failed" $f) e2pid=$(pidof enigma2) crashlogs=$(ls /home/root/logs | grep -c crash)"; grep -a "Traceback\|Skin\] Error\|PosterState\|poster state\|ShowIf\]" $f | grep -v "progressPercentWidth\|piconMargin" | tail -4 | cut -c1-170'; }
zap() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=$1"; sleep 10; }
ap() { local out; out=$($R "$E apply $* 2>&1 | tail -4"); echo "$out" | grep -q "failed\|not defined\|Error\|rror:" && echo "   APPLY FAILED: $*"; }
model() {
  case $1 in
    classic) echo "--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic-lines";;
    details) echo "--set infobar=details --set secondinfobar=details --set channelselection=posterlist --set epg=graphicalplus --set pvr=cover --set eventview=detailscard";;
    cinema)  echo "--set infobar=cinema --set secondinfobar=cinema --set channelselection=videofirst --set epg=graphicalplus --set pvr=cinema --set eventview=feature";;
    modern)  echo "--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern";;
    minimal) echo "--set infobar=minimal --set secondinfobar=minimal --set channelselection=minimal --set epg=minimal --set pvr=minimal --set eventview=minimal";;
  esac
}
four() {  # $1 tag
  X; $RC 352; sleep 5; ga ${1}_ib; X; sleep 2
  $RC 352; sleep 1.5; $RC 352; sleep 5; ga ${1}_sib; X; sleep 2
  $RC 358; sleep 6; ga ${1}_ev; X; sleep 2
  $RC 108; sleep 6; ga ${1}_cs; X; sleep 2
}
~/cineview-mla/deploy_b.sh $NEW >/dev/null 2>&1
cat ~/cineview-mla/devtools/CineViewMLAScreenOpen/plugin.py | $R "mkdir -p $P && cat > $P/plugin.py && touch $P/__init__.py"
for m in modern classic details cinema minimal; do
  echo "== $m"; ap --theme navy $(model $m); restart ""; errs
  zap "1:0:19:784:C6D4:16E:A00000:0:0:0:"; four ${m}_hbo
  zap "1:0:19:786:C6D4:16E:A00000:0:0:0:"; four ${m}_hbo3
  zap $HRT1; four ${m}_hrt1
  errs
done
ap --theme navy $(model classic)
$R "rm -rf $P"; restart ""; st; errs
echo T82_DONE
