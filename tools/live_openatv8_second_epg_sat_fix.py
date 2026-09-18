#!/usr/bin/env python3
# Targeted live fix for CineView FHD on OpenATV 8 build 20260917.
# Only SecondInfoBar/EPG/Satfinder are changed. Primary InfoBar is byte-preserved.

from pathlib import Path
import hashlib
import re
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("usage: live_openatv8_second_epg_sat_fix.py /path/to/skin.xml")

path = Path(sys.argv[1])
skin = path.read_text(errors="ignore")


def get_screen(text, name):
    m = re.search(r'(?s)<screen\\b(?=[^>]*\\bname=["\\']' + re.escape(name) + r'["\\'])[^>]*>.*?</screen>', text)
    if not m:
        raise SystemExit("MISSING_SCREEN:" + name)
    return m.group(0)


def replace_screen(text, name, new_block):
    pat = re.compile(r'(?s)<screen\\b(?=[^>]*\\bname=["\\']' + re.escape(name) + r'["\\'])[^>]*>.*?</screen>')
    out, count = pat.subn(new_block, text, count=1)
    if count != 1:
        raise SystemExit("REPLACE_FAIL:" + name)
    return out


def inner_screen(block):
    start = block.find(">")
    end = block.rfind("</screen>")
    if start < 0 or end < 0:
        raise SystemExit("BAD_SCREEN_BLOCK")
    return block[start + 1:end]


infobar_before = get_screen(skin, "InfoBar")
infobar_hash = hashlib.sha256(infobar_before.encode()).hexdigest()
infobar_inner = inner_screen(infobar_before)

second_panel = r'''
    <eLabel position="24,450" size="1872,392" backgroundColor="steSecondInfoBG" zPosition="40"/>
    <eLabel position="36,462" size="2,356" backgroundColor="steThemePanelAlt" zPosition="41"/>
    <eLabel position="1882,462" size="2,356" backgroundColor="steThemePanelAlt" zPosition="41"/>
    <eLabel position="36,818" size="1848,2" backgroundColor="steThemePanelAlt" zPosition="41"/>

    <eLabel text="NOW" position="54,468" size="105,34" font="Regular;22" foregroundColor="secondFG" backgroundColor="steSecondInfoBG" transparent="1" zPosition="45"/>
    <widget source="session.Event_Now" render="RunningText" position="170,464" size="575,42" font="Regular;30" foregroundColor="foreground" backgroundColor="steSecondInfoBG" transparent="1" noWrap="1" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1200,pause=900,repeat=0,always=0" zPosition="45"><convert type="EventName">Name</convert></widget>
    <widget source="session.Event_Now" render="Label" position="755,468" size="155,32" font="Regular;21" foregroundColor="grey" backgroundColor="steSecondInfoBG" transparent="1" halign="right" zPosition="45"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <widget source="session.Event_Now" render="Label" position="54,522" size="850,245" font="Regular;24" foregroundColor="foreground" backgroundColor="steSecondInfoBG" transparent="1" valign="top" zPosition="45"><convert type="EventName">FullDescription</convert></widget>
    <widget source="session.Event_Now" render="Progress" position="54,790" size="850,8" backgroundColor="steThemePanelAlt" zPosition="45"><convert type="EventTime">Progress</convert></widget>

    <eLabel position="948,466" size="2,336" backgroundColor="steThemePanelAlt" zPosition="44"/>

    <eLabel text="NEXT" position="982,468" size="105,34" font="Regular;22" foregroundColor="secondFG" backgroundColor="steSecondInfoBG" transparent="1" zPosition="45"/>
    <widget source="session.Event_Next" render="RunningText" position="1098,464" size="575,42" font="Regular;30" foregroundColor="foreground" backgroundColor="steSecondInfoBG" transparent="1" noWrap="1" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1200,pause=900,repeat=0,always=0" zPosition="45"><convert type="EventName">Name</convert></widget>
    <widget source="session.Event_Next" render="Label" position="1683,468" size="155,32" font="Regular;21" foregroundColor="grey" backgroundColor="steSecondInfoBG" transparent="1" halign="right" zPosition="45"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <widget source="session.Event_Next" render="Label" position="982,522" size="850,276" font="Regular;24" foregroundColor="foreground" backgroundColor="steSecondInfoBG" transparent="1" valign="top" zPosition="45"><convert type="EventName">FullDescription</convert></widget>
'''

SECOND = '<screen name="SecondInfoBar" position="fill" backgroundColor="transparent" flags="wfNoBorder" title="Second InfoBar">' + second_panel + infobar_inner + '\n</screen>'
SECOND_ECM = SECOND.replace('name="SecondInfoBar"', 'name="SecondInfoBarECM"', 1)

EPG_SINGLE = r'''<screen name="EPGSelection" position="center,center" size="1820,880" flags="wfNoBorder" title="EPG Selection">
    <eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
    <widget source="Title" render="Label" position="45,22" size="1730,52" font="Regular;36" foregroundColor="secondFG" transparent="1"/>
    <eLabel position="35,84" size="1750,2" backgroundColor="steThemePanelAlt"/>
    <widget name="number" position="45,102" size="1730,610" font="Regular;52" halign="center" valign="center" transparent="1" zPosition="20"/>
    <widget name="list" position="45,102" size="1730,610" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steThemePrimary" transparent="1" zPosition="10" EventFontSingle="Regular;29" MinimumItemHeight="58"/>
    <widget source="Event" render="Label" position="45,725" size="1730,42" font="Regular;28" foregroundColor="secondFG" transparent="1"><convert type="EventName">Name</convert></widget>
    <widget source="Event" render="Label" position="45,770" size="1730,34" font="Regular;21" foregroundColor="grey" transparent="1" noWrap="1"><convert type="EventName">ShortDescription</convert></widget>
    <eLabel position="35,812" size="1750,2" backgroundColor="steThemePanelAlt"/>
    <widget source="key_red" render="Label" position="55,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_green" render="Label" position="490,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_yellow" render="Label" position="925,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_blue" render="Label" position="1360,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
</screen>'''

EPG_MULTI = r'''<screen name="EPGSelectionMulti" position="center,center" size="1820,880" flags="wfNoBorder" title="Multi EPG">
    <eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
    <widget source="Title" render="Label" position="45,20" size="900,50" font="Regular;35" foregroundColor="secondFG" transparent="1"/>
    <widget name="date" position="1230,20" size="545,50" font="Regular;27" halign="right" transparent="1"/>
    <widget name="now_button" position="45,82" size="360,44" transparent="1"/>
    <widget name="now_button_sel" position="45,82" size="360,44" transparent="1"/>
    <widget name="now_text" position="45,82" size="360,44" text="NOW" font="Regular;25" halign="center" valign="center" transparent="1"/>
    <widget name="next_button" position="420,82" size="360,44" transparent="1"/>
    <widget name="next_button_sel" position="420,82" size="360,44" transparent="1"/>
    <widget name="next_text" position="420,82" size="360,44" text="NEXT" font="Regular;25" halign="center" valign="center" transparent="1"/>
    <widget name="more_button" position="795,82" size="360,44" transparent="1"/>
    <widget name="more_button_sel" position="795,82" size="360,44" transparent="1"/>
    <widget name="more_text" position="795,82" size="360,44" text="MORE" font="Regular;25" halign="center" valign="center" transparent="1"/>
    <eLabel position="35,136" size="1750,2" backgroundColor="steThemePanelAlt"/>
    <widget name="bouquetlist" position="45,150" size="1730,555" scrollbarMode="showNever" backgroundColor="steThemePrimary" transparent="0" zPosition="20"/>
    <widget name="list" position="45,150" size="1730,555" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steThemePrimary" transparent="1" zPosition="10" EventFontMulti="Regular;28" MinimumItemHeight="58"/>
    <widget source="Event" render="Label" position="45,718" size="1730,42" font="Regular;28" foregroundColor="secondFG" transparent="1"><convert type="EventName">Name</convert></widget>
    <widget source="Event" render="Label" position="45,763" size="1730,38" font="Regular;21" foregroundColor="grey" transparent="1" noWrap="1"><convert type="EventName">ShortDescription</convert></widget>
    <eLabel position="35,812" size="1750,2" backgroundColor="steThemePanelAlt"/>
    <widget source="key_red" render="Label" position="55,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_green" render="Label" position="490,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_yellow" render="Label" position="925,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_blue" render="Label" position="1360,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
</screen>'''

EPG_QUICK = r'''<screen name="QuickEPG" position="0,680" size="1920,400" flags="wfNoBorder" title="Quick EPG">
    <eLabel position="0,0" size="1920,400" backgroundColor="steSecondInfoBG" zPosition="0"/>
    <widget source="Service" render="Picon" position="45,28" size="190,62" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
    <widget source="Service" render="Label" position="255,30" size="620,54" font="Regular;34" foregroundColor="secondFG" transparent="1"><convert type="ServiceName">Name</convert></widget>
    <widget name="list" position="45,110" size="1040,220" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steSecondInfoBG" transparent="1" EventFontSingle="Regular;28" MinimumItemHeight="56"/>
    <widget source="Event" render="Label" position="1130,42" size="745,44" font="Regular;29" foregroundColor="secondFG" transparent="1"><convert type="EventName">Name</convert></widget>
    <widget source="Event" render="Label" position="1130,100" size="745,230" font="Regular;23" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
    <eLabel position="35,342" size="1850,2" backgroundColor="steThemePanelAlt"/>
    <widget source="key_red" render="Label" position="55,352" size="400,38" font="Regular;23" halign="center" transparent="1"/>
    <widget source="key_green" render="Label" position="490,352" size="400,38" font="Regular;23" halign="center" transparent="1"/>
    <widget source="key_yellow" render="Label" position="925,352" size="400,38" font="Regular;23" halign="center" transparent="1"/>
    <widget source="key_blue" render="Label" position="1360,352" size="400,38" font="Regular;23" halign="center" transparent="1"/>
</screen>'''

EPG_GRAPH = r'''<screen name="GraphicalEPG" position="center,center" size="1820,880" flags="wfNoBorder" title="Graphical EPG">
    <eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
    <widget source="global.CurrentTime" render="Label" position="45,20" size="160,48" font="Regular;30" foregroundColor="secondFG" transparent="1"><convert type="ClockToText">Default</convert></widget>
    <widget source="Title" render="Label" position="225,20" size="1160,48" font="Regular;34" foregroundColor="foreground" halign="center" transparent="1"/>
    <widget source="global.CurrentTime" render="Label" position="1410,20" size="365,48" font="Regular;27" foregroundColor="grey" halign="right" transparent="1"><convert type="ClockToText">Format:%d.%m.%Y</convert></widget>
    <widget name="timeline_text" position="45,84" size="1730,42" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
    <widget name="lab1" position="45,128" size="1730,500" font="Regular;28" halign="center" valign="center" backgroundColor="steThemePrimary" transparent="0" zPosition="2"/>
    <widget name="bouquetlist" position="45,128" size="1730,500" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
    <widget name="list" position="45,128" size="1730,500" scrollbarMode="showNever" transparent="1" zPosition="10" ServiceFontGraphical="Regular;27" EntryFontGraphical="Regular;25" NumberOfRows="8" MinimumItemHeight="60" EntryFontWrap="no"/>
    <widget name="timeline_now" position="45,128" zPosition="21" size="5,500"/>
    <widget source="Event" render="Label" position="45,645" size="170,38" font="Regular;25" foregroundColor="secondFG" transparent="1" halign="right"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Default</convert></widget>
    <widget source="Event" render="Label" position="220,645" size="150,38" font="Regular;25" foregroundColor="secondFG" transparent="1"><convert type="EventTime">EndTime</convert><convert type="ClockToText">Format:- %H:%M</convert></widget>
    <widget source="Event" render="Label" position="390,645" size="1385,38" font="Regular;28" foregroundColor="secondFG" transparent="1"><convert type="EventName">Name</convert></widget>
    <widget source="Event" render="Label" position="45,690" size="1730,105" font="Regular;22" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">ExtendedDescription</convert></widget>
    <eLabel position="35,812" size="1750,2" backgroundColor="steThemePanelAlt"/>
    <widget source="key_red" render="Label" position="55,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_green" render="Label" position="490,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_yellow" render="Label" position="925,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_blue" render="Label" position="1360,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
</screen>'''

EPG_GRAPH_PIG = r'''<screen name="GraphicalEPGPIG" position="center,center" size="1820,880" flags="wfNoBorder" title="Graphical EPG">
    <eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
    <widget source="Title" render="Label" position="45,20" size="1000,48" font="Regular;34" foregroundColor="secondFG" transparent="1"/>
    <widget source="Event" render="Label" position="45,80" size="1000,42" font="Regular;28" foregroundColor="foreground" transparent="1"><convert type="EventName">Name</convert></widget>
    <widget source="Event" render="Label" position="45,132" size="1000,150" font="Regular;22" foregroundColor="grey" transparent="1" valign="top"><convert type="EventName">ExtendedDescription</convert></widget>
    <eLabel position="1220,30" size="555,312" backgroundColor="black" zPosition="3"/>
    <widget source="session.VideoPicture" render="Pig" position="1230,40" size="535,301" backgroundColor="black" zPosition="4"/>
    <widget name="timeline_text" position="45,355" size="1730,42" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
    <widget name="lab1" position="45,399" size="1730,330" font="Regular;27" halign="center" valign="center" backgroundColor="steThemePrimary" transparent="0" zPosition="2"/>
    <widget name="bouquetlist" position="45,399" size="1730,330" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
    <widget name="list" position="45,399" size="1730,330" scrollbarMode="showNever" transparent="1" zPosition="10" ServiceFontGraphical="Regular;26" EntryFontGraphical="Regular;24" NumberOfRows="5" MinimumItemHeight="60" EntryFontWrap="no"/>
    <widget name="timeline_now" position="45,399" zPosition="21" size="5,330"/>
    <eLabel position="35,812" size="1750,2" backgroundColor="steThemePanelAlt"/>
    <widget source="key_red" render="Label" position="55,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_green" render="Label" position="490,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_yellow" render="Label" position="925,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
    <widget source="key_blue" render="Label" position="1360,825" size="400,42" font="Regular;25" halign="center" transparent="1"/>
</screen>'''

EPG_INFOGRAPH = r'''<screen name="GraphicalInfoBarEPG" position="0,650" size="1920,430" flags="wfNoBorder" title="InfoBar EPG">
    <eLabel position="0,0" size="1920,430" backgroundColor="steSecondInfoBG" zPosition="0"/>
    <widget source="Title" render="Label" position="45,18" size="1200,46" font="Regular;32" foregroundColor="secondFG" transparent="1"/>
    <widget source="global.CurrentTime" render="Label" position="1500,18" size="370,46" font="Regular;26" foregroundColor="grey" halign="right" transparent="1"><convert type="ClockToText">Format:%d.%m.%Y %H:%M</convert></widget>
    <widget name="timeline_text" position="45,76" size="1830,38" foregroundColor="secondFG" backgroundColor="steSecondInfoBG" transparent="1"/>
    <widget name="lab1" position="45,116" size="1830,205" font="Regular;26" halign="center" valign="center" backgroundColor="steSecondInfoBG" transparent="0" zPosition="2"/>
    <widget name="bouquetlist" position="45,116" size="1830,205" backgroundColor="steSecondInfoBG" scrollbarMode="showNever" transparent="0" zPosition="15"/>
    <widget name="list" position="45,116" size="1830,205" scrollbarMode="showNever" transparent="1" zPosition="10" ServiceFontInfobar="Regular;25" EventFontInfobar="Regular;23" NumberOfRows="3" MinimumItemHeight="58" EntryFontWrap="no"/>
    <widget name="timeline_now" position="45,116" zPosition="21" size="5,205"/>
    <eLabel position="35,342" size="1850,2" backgroundColor="steThemePanelAlt"/>
    <widget source="key_red" render="Label" position="55,355" size="400,42" font="Regular;23" halign="center" transparent="1"/>
    <widget source="key_green" render="Label" position="490,355" size="400,42" font="Regular;23" halign="center" transparent="1"/>
    <widget source="key_yellow" render="Label" position="925,355" size="400,42" font="Regular;23" halign="center" transparent="1"/>
    <widget source="key_blue" render="Label" position="1360,355" size="400,42" font="Regular;23" halign="center" transparent="1"/>
</screen>'''

SATFINDER = r'''<screen name="Satfinder" title="Signal Finder" position="fill" backgroundColor="steThemePrimary" flags="wfNoBorder">
    <eLabel text="SIGNAL FINDER" position="35,24" size="700,54" font="Regular;39" foregroundColor="secondFG" transparent="1"/>
    <eLabel position="30,92" size="1860,2" backgroundColor="steThemePanelAlt"/>

    <eLabel text="SNR" position="35,122" size="105,42" font="Regular;29" foregroundColor="foreground" transparent="1"/>
    <widget source="Frontend" render="Progress" position="150,128" size="1045,28" backgroundColor="steThemePanelAlt" borderWidth="1"><convert type="FrontendInfo">SNR</convert></widget>
    <widget source="Frontend" render="Label" position="1215,118" size="180,50" font="Regular;35" foregroundColor="secondFG" halign="right" transparent="1"><convert type="FrontendInfo">SNR</convert></widget>
    <widget source="Frontend" render="Label" position="1420,118" size="365,50" font="Regular;35" foregroundColor="foreground" halign="right" transparent="1"><convert type="FrontendInfo">SNRdB</convert></widget>

    <eLabel text="AGC" position="35,182" size="105,42" font="Regular;29" foregroundColor="foreground" transparent="1"/>
    <widget source="Frontend" render="Progress" position="150,188" size="1045,28" backgroundColor="steThemePanelAlt" borderWidth="1"><convert type="FrontendInfo">AGC</convert></widget>
    <widget source="Frontend" render="Label" position="1215,178" size="180,50" font="Regular;35" foregroundColor="secondFG" halign="right" transparent="1"><convert type="FrontendInfo">AGC</convert></widget>

    <eLabel text="BER" position="35,242" size="105,42" font="Regular;29" foregroundColor="foreground" transparent="1"/>
    <widget source="Frontend" render="Label" position="150,238" size="250,50" font="Regular;35" foregroundColor="foreground" transparent="1"><convert type="FrontendInfo">BER</convert></widget>
    <widget source="Frontend" render="FixedLabel" text="LOCK" position="430,238" size="210,50" font="Regular;30" foregroundColor="secondFG" backgroundColor="steThemePanelAlt" halign="center" valign="center"><convert type="FrontendInfo">LOCK</convert><convert type="ConditionalShowHide"/></widget>

    <eLabel position="30,310" size="1860,2" backgroundColor="steThemePanelAlt"/>
    <eLabel text="TUNER / SATELLITE / TRANSPONDER" position="40,328" size="1840,42" font="Regular;28" foregroundColor="secondFG" transparent="1"/>
    <widget name="config" position="40,378" size="1840,620" itemHeight="52" font="Regular;28" transparent="1" enableWrapAround="1" scrollbarMode="showOnDemand"/>
    <widget name="introduction" position="0,0" size="0,0" font="Regular;1"/>
</screen>'''

for name, block in (
    ("SecondInfoBar", SECOND),
    ("SecondInfoBarECM", SECOND_ECM),
    ("EPGSelection", EPG_SINGLE),
    ("EPGSelectionMulti", EPG_MULTI),
    ("QuickEPG", EPG_QUICK),
    ("GraphicalEPG", EPG_GRAPH),
    ("GraphicalEPGPIG", EPG_GRAPH_PIG),
    ("GraphicalInfoBarEPG", EPG_INFOGRAPH),
    ("Satfinder", SATFINDER),
):
    skin = replace_screen(skin, name, block)

ET.fromstring(skin)

if get_screen(skin, "InfoBar") != infobar_before:
    raise SystemExit("PRIMARY_INFOBAR_CHANGED")

sec = get_screen(skin, "SecondInfoBar")
if "session.Event_Now" not in sec or "session.Event_Next" not in sec:
    raise SystemExit("SECOND_EVENTS_MISSING")
if infobar_inner.strip() not in sec:
    raise SystemExit("PRIMARY_INFOBAR_COPY_MISSING_FROM_SECOND")

sat = get_screen(skin, "Satfinder")
if 'position="40,378" size="1840,620"' not in sat:
    raise SystemExit("SATFINDER_WIDE_CONFIG_MISSING")

path.write_text(skin)
print("PRIMARY_INFOBAR_UNCHANGED_SHA256=" + infobar_hash)
print("SECONDINFO_NOW_NEXT_AND_PRIMARY_COPY=OK")
print("EPG_NATIVE_FHD_LAYOUTS=OK")
print("SATFINDER_FULLWIDTH_CONFIG=OK")
