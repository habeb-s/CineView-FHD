#!/bin/bash
# t106l - OpenViX (Slot 4): Arabic UI run.  config.osd.language -> ar_AE with the GUI stopped, t106 main sections,
# then the previous language is restored (GUI stopped again).  No other setting is touched.  HDD never used.
R=~/cineview-mla/r4.sh
restart_gui() { local o=$($R pidof enigma2); $R "init 4; for i in \$(seq 1 30); do pidof enigma2 >/dev/null || break; sleep 1; done; $1 init 3"
	for i in $(seq 1 90); do p=$($R 'pidof enigma2' 2>/dev/null); [ -n "$p" ] && [ "$p" != "$o" ] && break; sleep 2; done
	for i in $(seq 1 60); do curl -s -m 3 -o /dev/null -w "%{http_code}" http://192.168.1.250/api/statusinfo 2>/dev/null | grep -q 200 && break; sleep 3; done; sleep 30; }
LANG0=$($R 'sed -n "s/^config.osd.language=//p" /etc/enigma2/settings'); echo "language before: '${LANG0:-(default)}'"
restart_gui "sed -i '/^config.osd.language=/d' /etc/enigma2/settings; echo config.osd.language=ar_AE >> /etc/enigma2/settings;"
echo "language now: $($R 'sed -n "s/^config.osd.language=//p" /etc/enigma2/settings')"
ZAP=${ZAP:-1:0:1:290E:1EDC:71:822FFC:0:0:0:} DEVTOOL=1 bash ~/cineview-mla/t106v.sh arabic ${*:-infobar sib chansel grid single multi eventview pvr plugins designs setup_ui msg_yesno msg_long}
restart_gui "sed -i '/^config.osd.language=/d' /etc/enigma2/settings; [ -n '$LANG0' ] && echo 'config.osd.language=$LANG0' >> /etc/enigma2/settings;"
echo "language restored: $($R 'sed -n "s/^config.osd.language=//p" /etc/enigma2/settings')"
echo T106L_DONE
