#!/bin/bash
# t106x - OpenBH (Slot 5) matrix on top of t106.sh: design models, themes, posters on/off.
#   usage: t106x.sh models | themes | posters | epgpig
# (loop variables must not be named p: restart_gui uses $p for the enigma2 pid)
# Each case: selection applied by the engine (composer apply, the same path CineView Designs uses), GUI restart,
# then t106.sh opens the sections.  The selection before the run is restored at the end.  HDD never used.
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r5.sh
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
ZAP="1:0:19:786:C6D4:16E:A00000:0:0:0:"
restart_gui() { local o=$($R pidof enigma2); $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; $1 init 3"
	for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30; }
sel() { $R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\""; }
ORIG=$(sel); echo "selection before: $ORIG"
apply() { echo "== apply $*"; $R "$E apply $* 2>&1 | tail -1"; restart_gui; }
case ${1:?mode} in
models)
	declare -A M=(
		[classic]="--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic"
		[details]="--set infobar=details --set secondinfobar=details --set channelselection=posterlist --set epg=graphicalplus --set pvr=cover --set eventview=detailscard"
		[cinema]="--set infobar=cinema --set secondinfobar=cinema --set channelselection=videofirst --set epg=graphicalplus --set pvr=cinema --set eventview=feature"
		[modern]="--set infobar=modern --set secondinfobar=modern --set channelselection=modern --set epg=modern --set pvr=modern --set eventview=modern"
		[minimal]="--set infobar=minimal --set secondinfobar=minimal --set channelselection=minimal --set epg=minimal --set pvr=minimal --set eventview=minimal")
	for m in classic details cinema modern minimal; do
		apply --theme navy ${M[$m]}
		ZAP=$ZAP DEVTOOL=1 bash ~/cineview-mla/t106.sh model_$m infobar sib chansel grid single multi ibgrid evinfo eventview pvr
	done ;;
themes)
	for t in $($R 'ls /usr/share/enigma2/CineView_FHD_MLA/themes'); do
		apply --theme $t --set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic
		ZAP=$ZAP DEVTOOL=1 bash ~/cineview-mla/t106.sh theme_$t infobar chansel grid designs msg_yesno
	done ;;
posters)
	# all poster switches off (CineView Designs rows "Posters - <section>"), Classic and Details, then back on
	for m in classic details; do
		[ $m = classic ] && L="--set infobar=classic --set secondinfobar=classic --set channelselection=classic --set epg=classic --set pvr=classic --set eventview=classic"
		[ $m = details ] && L="--set infobar=details --set secondinfobar=details --set channelselection=posterlist --set epg=graphicalplus --set pvr=cover --set eventview=detailscard"
		$R "$E apply --theme navy $L 2>&1 | tail -1"
		restart_gui "sed -i '/^config.plugins.cineviewmla.poster_/d' /etc/enigma2/settings; for s in infobar secondinfobar channelselection epg pvr eventview; do echo config.plugins.cineviewmla.poster_\$s=false >> /etc/enigma2/settings; done;"
		ZAP=$ZAP DEVTOOL=1 bash ~/cineview-mla/t106.sh postersoff_$m infobar sib chansel grid evinfo
	done
	restart_gui "sed -i '/^config.plugins.cineviewmla.poster_/d' /etc/enigma2/settings;" ;;
epgpig)
	# OpenBH user setting config.epgselection.grid.pig (picture in graphics): off -> the pack's own GraphicalEPG
	# screen (GridEPG/GraphicalEPG) instead of its PiG variant.  The setting's previous value is restored.
	PIG=$($R 'sed -n "s/^config.epgselection.grid.pig=//p" /etc/enigma2/settings'); echo "grid.pig before: '${PIG:-(default)}'"
	for pk in classic graphicalplus modern minimal columns; do
		$R "$E apply --set epg=$pk 2>&1 | tail -1"
		restart_gui "sed -i '/^config.epgselection.grid.pig=/d' /etc/enigma2/settings; echo config.epgselection.grid.pig=False >> /etc/enigma2/settings;"
		ZAP=$ZAP DEVTOOL=1 bash ~/cineview-mla/t106.sh epgnopig_$pk grid ibgrid single multi
	done
	restart_gui "sed -i '/^config.epgselection.grid.pig=/d' /etc/enigma2/settings; [ -n '$PIG' ] && echo 'config.epgselection.grid.pig=$PIG' >> /etc/enigma2/settings;" ;;
esac
echo "== restore: $ORIG"; $R "$E apply $ORIG 2>&1 | tail -1"; restart_gui
echo T106X_DONE
