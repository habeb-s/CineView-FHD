#!/bin/bash
# t106n - OpenBH (Slot 5): shortened channel names are display-only.  Narrowest list design (videofirst), bar on the
# right and on the left: zap the long-named service FROM the channel list (OK on the row), then check that the
# playing service, the InfoBar, OpenWebif and the saved last service carry the full name; picon of the shortened
# row; the very large "All" list (timing in the debug log).  The bar setting and the design are restored.
. ~/cineview-mla/p6lib.sh
R=~/cineview-mla/r5.sh
S=~/cineview-mla/shots/t106n; rm -rf $S; mkdir -p $S
E='python3 /usr/share/enigma2/CineView_FHD_MLA/mla/engine/composer.py'
LONG="1:0:19:71B:C5A8:16E:A00000:0:0:0:"
ok() { python3 -c "from PIL import Image; Image.open('$1').load()" 2>/dev/null; }
ga() { for a in 1 2 3; do curl -s -m 60 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; ok $S/$1.png && break; done; }
restart_gui() { local o=$($R pidof enigma2); $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; $1 init 3"
	for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30; }
cur() { curl -s -m 10 http://192.168.1.250/api/getcurrent | python3 -c "import json,sys;d=json.load(sys.stdin)['info'];print('   playing: name=%r ref=%r' % (d.get('name'), d.get('ref')))"; }
log() { $R 'f=$(ls -t /home/root/logs/Enigma2_debug_*.log | head -1); grep -a "CineViewMLA\] channel names" $f | tail -'${1:-3}' | sed "s/^.*\[CineViewMLA\]/   [CineViewMLA]/"; echo "   tracebacks=$(grep -a Traceback $f | grep -a -v -c InputHotplug) skin_errors=$(grep -a -c "\[Skin\] Error\|SkinError" $f)"'; }
PB=$($R 'sed -n "s/^config.usage.show_event_progress_in_servicelist=//p" /etc/enigma2/settings')
ORIG=$($R "python3 -c \"import json;d=json.load(open('/etc/enigma2/cineview_mla/selection.json'));print('--theme', d['theme'], ' '.join('--set %s=%s'%kv for kv in sorted(d['layouts'].items())))\"")
$R "$E apply --set channelselection=videofirst 2>&1 | tail -1"
for bar in barright barleft; do
	restart_gui "sed -i '/^config.usage.show_event_progress_in_servicelist=/d' /etc/enigma2/settings; echo config.usage.show_event_progress_in_servicelist=$bar >> /etc/enigma2/settings;"
	echo "== $bar"
	curl -s -m 10 -o /dev/null "http://192.168.1.250/api/zap?sRef=$LONG"; sleep 6
	X; $RC 103; sleep 3; ga ${bar}_1_list; log 2
	$RC 108; sleep 1; $RC 352; sleep 6; cur          # zap the row below (from the list)
	X; $RC 103; sleep 3; $RC 103; sleep 1; ga ${bar}_2_back_on_long_row
	$RC 352; sleep 6; cur; ga ${bar}_3_zapped_from_list   # OK on the shortened row
	$RC 358; sleep 3; ga ${bar}_4_eventinfo; X
	X; $RC 103; sleep 3; $RC 398; sleep 12; ga ${bar}_5_all_services; log 2   # red = All
	X; X
done
restart_gui "sed -i '/^config.usage.show_event_progress_in_servicelist=/d' /etc/enigma2/settings; [ -n '$PB' ] && echo 'config.usage.show_event_progress_in_servicelist=$PB' >> /etc/enigma2/settings;"
echo "   saved last service: $($R 'sed -n "s/^config.tv.lastservice=//p" /etc/enigma2/settings')"
curl -s -m 10 -o /dev/null "http://192.168.1.250/api/zap?sRef=$LONG"; sleep 5
$R "$E apply $ORIG 2>&1 | tail -1"; restart_gui
echo "bar restored: '$($R 'sed -n "s/^config.usage.show_event_progress_in_servicelist=//p" /etc/enigma2/settings')'"
echo T106N_DONE
