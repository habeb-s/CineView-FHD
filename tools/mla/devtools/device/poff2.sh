#!/bin/bash
# Phase B retake (SecondInfoBar was caught during its fade-in), then restore the rc4 package files and the
# selection with the EventView line-jump test pack (posters ON).
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/poff
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ga() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1 @$($R 'date +%T')"; }
restart() { o=$(pid); $R 'init 4; for i in $(seq 1 25); do pidof enigma2 >/dev/null || break; sleep 1; done; '"$1"' init 3'; newe2 $o; sleep 28; }
errs() { $R 'f=/home/root/logs/$(ls -t /home/root/logs | grep debug | head -1); echo "   tracebacks=$(grep -a -c Traceback $f) skin_errors_new=$(grep -a "Skin\] Error" $f | grep -v -c "progressPercentWidth\|piconMargin") e2pid=$(pidof enigma2)"'; }
ALL="poster_infobar poster_secondinfobar poster_channelselection poster_epg poster_eventview"
cfg() { for k in $ALL; do printf 'config.plugins.cineviewmla.%s=%s ' $k $1; done; }
sib() { curl -s -m 8 -o /dev/null "http://192.168.1.250/api/zap?sRef=1:0:19:784:C6D4:16E:A00000:0:0:0:"; sleep 8; X; $RC 352; sleep 1; $RC 352; sleep 8; ga $1_secondinfobar; X; }
sib on
restart "python3 /tmp/cvmla/setcfg.py $(cfg False);"; errs
sib off
echo "== restore rc4 package files + selection (line-jump test pack), posters ON"
restart "python3 /tmp/cvmla/setcfg.py $(cfg True); opkg install --force-reinstall /tmp/cvmla/up.ipk 2>&1 | tail -2; opkg status enigma2-plugin-skins-cineview-fhd-mla | grep Version; $E apply --set eventview=classic-lines 2>&1 | tail -1;"
st; errs
$R "grep -c 'CineViewMLAShowIf\">config.plugins.cineviewmla.poster_infobar,True,Invert' /usr/share/enigma2/CineView_FHD_MLA/active/infobar.xml; grep -c 'step=29,steptime=1740' /usr/share/enigma2/CineView_FHD_MLA/active/eventview.xml"
echo POFF2_DONE
