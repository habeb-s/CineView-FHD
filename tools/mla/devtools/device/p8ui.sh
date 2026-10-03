#!/bin/bash
# T3 + profiles through the real CineView Designs UI (Slot 8):
#  set theme Purple, InfoBar=Details, SecondInfoBar=Cinema -> MENU save profile -> RED (nothing applied)
#  -> reopen, MENU load profile -> GREEN trial -> restart -> YES keep -> committed; IB/SIB captured
#  -> MENU delete profile -> BLUE factory.  Ends on Classic navy (factory).
. ~/cineview-mla/p6lib.sh
S=~/cineview-mla/shots/p8ui; rm -rf $S; mkdir -p $S
P=/etc/enigma2/cineview_mla/profiles
ga() { curl -s -m 20 -o $S/$1.png "http://192.168.1.250/grab?format=png&mode=all&r=1920"; echo "cap $1 @$($R 'date +%T')"; }
st; $R "rm -f '$P/My CineView.json'; ls -la $P 2>/dev/null"
# 1. set values, save as profile
openui; g U01_open
$RC 106; sleep 1                    # theme navy -> purple
$RC 108; sleep 1; $RC 106; sleep 1  # InfoBar classic -> details
$RC 108; sleep 1; $RC 105; sleep 1  # SecondInfoBar classic -> cinema
g U02_values
$RC 139; sleep 2; g U03_menu        # profiles menu
$RC 352; sleep 3; g U04_keyboard    # "Save current settings as a profile" -> keyboard (default name)
$RC 399; sleep 3; g U05_saved_msg   # GREEN = accept the name
$R "ls -la $P; cat '$P/My CineView.json'"
sleep 3; $RC 398; sleep 3; g U06_after_red   # RED = cancel -> nothing applied
st
# 2. reopen, load the profile, apply as a trial, keep it
openui; g U07_reopen
$RC 139; sleep 2; $RC 108; sleep 1; g U08_menu_load; $RC 352; sleep 2; g U09_pick; $RC 352; sleep 2; g U10_loaded
sleep 5; o=$(pid); $RC 399; sleep 6; g U11_restart_q; $RC 352; newe2 $o; o2=$(pid); st
for k in $(seq 1 30); do sleep 4; $R 'grep -a "CineViewMLA\] session healthy" /home/root/logs/$(ls -t /home/root/logs | grep debug | head -1) >/dev/null' && break; done
sleep 2; g U12_keep_prompt; $RC 103; sleep 1; $RC 352; sleep 4; st; e2log 6
X; $RC 352; sleep 2; ga U13_ib_details; $RC 352; sleep 4; ga U14_sib_cinema; X
# 3. delete the profile, then factory
openui; $RC 139; sleep 2; $RC 108 108; sleep 1; g U15_menu_delete; $RC 352; sleep 2; $RC 352; sleep 2; g U16_confirm; $RC 103; sleep 1; $RC 352; sleep 3; g U16b_deleted
$R "ls -la $P"
$RC 174; sleep 2; openui; $RC 401; sleep 2; g U17_factory_q; $RC 103; sleep 1; o=$(pid); $RC 352; newe2 $o; sleep 20; st; e2log 8
X; $RC 352; sleep 2; ga U18_final_classic; X
echo P8UI_DONE
