# -*- coding: utf-8 -*-
# OpenATV 8 live contract audited on Vu+ Duo 4K SE, build 20260917.
from __future__ import print_function

import io
import os
import re
import sys
import xml.etree.ElementTree as ET

SCREEN_RE = r'\n?[ \t]*<screen\b(?=[^>]*\bname=["\']%s["\'])[^>]*>.*?</screen>[ \t]*\n?'


def _read(path):
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _write(path, data):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(data)


def _remove_screen(data, name):
    return re.sub(SCREEN_RE % re.escape(name), "\n", data, flags=re.S)


def _screen(name, body, position="center,center", size="1820,880", title=""):
    t = (' title="%s"' % title) if title else ""
    return '\n\t<screen name="%s" position="%s" size="%s" flags="wfNoBorder"%s>\n%s\n\t</screen>\n' % (
        name, position, size, t, body)


PLUGIN_LIST = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel text="Plugins" position="50,24" size="1740,58" font="Regular;44" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
\t\t<eLabel position="45,92" size="1750,3" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="pluginList" render="Listbox" position="50,112" size="1740,660" conditional="pluginList" listOrientation="vertical" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="5">
\t\t\t<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryPixmapAlphaBlend(pos=(12, 12), size=(150, 72), png=3, flags=BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER),
MultiContentEntryText(pos=(185, 4), size=(1460, 47), font=0, text=1),
MultiContentEntryText(pos=(185, 51), size=(1460, 34), font=1, text=2)
],
"fonts": [gFont("Regular", 37), gFont("Regular", 25)],
"itemHeight": 96
}
\t\t\t</convert>
\t\t</widget>
\t\t<widget name="quickselect" position="50,112" size="1740,660" font="Regular;150" foregroundColor="secondFG" halign="center" valign="center" transparent="1" zPosition="8"/>
\t\t<widget name="description" position="60,785" size="1720,55" font="Regular;27" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<eLabel position="45,855" size="1750,3" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="key_red" render="Label" position="60,872" size="310,46" font="Regular;26" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="390,872" size="310,46" font="Regular;26" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="720,872" size="310,46" font="Regular;26" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1050,872" size="310,46" font="Regular;26" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_menu" render="Label" position="1395,872" size="170,46" font="Regular;24" halign="center" valign="center" foregroundColor="grey" transparent="1"/>
\t\t<widget source="key_help" render="Label" position="1585,872" size="170,46" font="Regular;24" halign="center" valign="center" foregroundColor="grey" transparent="1"/>"""

PLUGIN_GRID = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="50,22" size="1335,58" font="Regular;39" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="lab1" position="50,92" size="1335,655" font="Regular;29" halign="center" valign="center" transparent="1" zPosition="20"/>
\t\t<widget name="timeline_text" position="50,92" size="1335,46" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget name="bouquetlist" position="50,140" size="1335,607" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
\t\t<widget name="list" position="50,140" size="1335,607" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10" ServiceFontGraphical="Regular;29" EntryFontGraphical="Regular;27" NumberOfRows="8" MinimumItemHeight="70" EntryFontWrap="no"/>
\t\t<widget name="timeline_now" position="50,140" size="5,607" zPosition="21"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1460,70" size="300,450" zPosition="12"/>
\t\t<widget source="Event" render="Label" position="1415,545" size="390,76" font="Regular;29" foregroundColor="secondFG" transparent="1" halign="center"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1415,630" size="390,120" font="Regular;23" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">ShortDescription</convert></widget>
\t\t<eLabel position="45,835" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="60,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="500,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="940,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1380,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>"""

GRID_PIG = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="50,22" size="1060,58" font="Regular;39" foregroundColor="secondFG" transparent="1"/>
\t\t<widget source="Event" render="Label" position="50,92" size="1040,210" font="Regular;25" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="1240,35" size="540,304" backgroundColor="black" zPosition="4"/>
\t\t<widget source="session.VideoPicture" render="Pig" position="1255,50" size="510,287" backgroundColor="black" zPosition="5"/>
\t\t<widget name="lab1" position="50,350" size="1730,400" font="Regular;29" halign="center" valign="center" transparent="1" zPosition="20"/>
\t\t<widget name="timeline_text" position="50,350" size="1730,46" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="bouquetlist" position="50,398" size="1730,352" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
\t\t<widget name="list" position="50,398" size="1730,352" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10" ServiceFontGraphical="Regular;28" EntryFontGraphical="Regular;26" NumberOfRows="5" MinimumItemHeight="66" EntryFontWrap="no"/>
\t\t<widget name="timeline_now" position="50,398" size="5,352" zPosition="21"/>
\t\t<eLabel position="45,835" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="60,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="500,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="940,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1380,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>"""

INFOBAR_GRID = """\t\t<eLabel position="0,0" size="1920,420" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="45,20" size="900,48" font="Regular;34" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="lab1" position="45,82" size="1830,245" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="20"/>
\t\t<widget name="timeline_text" position="45,82" size="1830,42" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="bouquetlist" position="45,126" size="1830,201" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
\t\t<widget name="list" position="45,126" size="1830,201" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10" ServiceFontInfobar="Regular;27" EventFontInfobar="Regular;25" NumberOfRows="3" MinimumItemHeight="62" EntryFontWrap="no"/>
\t\t<widget name="timeline_now" position="45,126" size="5,201" zPosition="21"/>
\t\t<eLabel position="35,350" size="1850,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,365" size="400,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,365" size="400,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,365" size="400,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,365" size="400,42" font="Regular;24" halign="center" transparent="1"/>"""

QUICK_MENU = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel text="Quick Menu" position="50,24" size="1740,58" font="Regular;44" foregroundColor="secondFG" transparent="1"/>
\t\t<widget source="mainlist" render="Listbox" position="50,105" size="625,680" backgroundColor="steThemePrimary" transparent="1" itemHeight="92" zPosition="5">
\t\t\t<templates><template name="Default" fonts="Regular;31,Regular;22" itemWidth="625" itemHeight="92"><mode name="default">
\t\t\t\t<pixmap index="2" position="10,10" size="70,70" alpha="blend" scale="centerScaled"/>
\t\t\t\t<text index="0" position="95,3" size="515,46" font="0" verticalAlignment="center"/>
\t\t\t\t<text index="1" position="110,49" size="500,34" font="1" verticalAlignment="center"/>
\t\t\t</mode></template></templates>
\t\t</widget>
\t\t<eLabel position="695,103" size="3,682" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="sublist" render="Listbox" position="725,105" size="625,680" backgroundColor="steThemePrimary" transparent="1" itemHeight="92" zPosition="5">
\t\t\t<templates><template name="Default" fonts="Regular;31,Regular;22" itemWidth="625" itemHeight="92"><mode name="default">
\t\t\t\t<text index="0" position="10,3" size="600,46" font="0" verticalAlignment="center"/>
\t\t\t\t<text index="1" position="25,49" size="585,34" font="1" verticalAlignment="center"/>
\t\t\t</mode></template></templates>
\t\t</widget>
\t\t<eLabel position="1390,110" size="390,220" backgroundColor="black" zPosition="3"/>
\t\t<widget source="session.VideoPicture" render="Pig" position="1390,110" size="390,220" backgroundColor="black" zPosition="4"/>
\t\t<widget name="description" position="1380,360" size="410,425" backgroundColor="steThemePrimary" transparent="1" font="Regular;26" foregroundColor="foreground" halign="center" valign="center" zPosition="4"/>
\t\t<eLabel position="45,835" size="1750,3" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="key_red" render="Label" position="60,855" size="360,48" backgroundColor="key_red" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_green" render="Label" position="440,855" size="360,48" backgroundColor="key_green" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_yellow" render="Label" position="820,855" size="360,48" backgroundColor="key_yellow" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_help" render="Label" position="1500,855" size="280,48" backgroundColor="key_back" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>"""

MESSAGE_BOX = """\t\t<eLabel position="0,0" size="960,520" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="icon" pixmaps="icons/input_question.png,icons/input_info.png,icons/input_warning.png,icons/input_error.png,icons/input_message.png" position="35,35" size="64,64" alphatest="blend" conditional="icon" scale="1" transparent="1" zPosition="4"/>
\t\t<widget name="text" position="125,35" size="790,300" font="Regular;28" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget name="list" position="35,355" size="890,125" conditional="list" enableWrapAround="1" font="Regular;28" itemHeight="50" scrollbarMode="showOnDemand" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>"""

VERTICAL_EPG = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="50,24" size="1740,54" font="Regular;38" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="bouquetlist" position="50,92" size="1740,690" backgroundColor="steThemePrimary" scrollbarMode="showNever" zPosition="20"/>
\t\t<widget name="list" position="50,92" size="1740,690" backgroundColor="steThemePrimary" scrollbarMode="showNever" zPosition="19"/>
\t\t<widget source="piconCh1" render="Picon" position="60,98" size="105,55" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="piconCh2" render="Picon" position="410,98" size="105,55" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="piconCh3" render="Picon" position="760,98" size="105,55" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="piconCh4" render="Picon" position="1110,98" size="105,55" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="piconCh5" render="Picon" position="1460,98" size="105,55" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget name="currCh1" position="170,102" size="220,45" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="currCh2" position="520,102" size="220,45" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="currCh3" position="870,102" size="220,45" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="currCh4" position="1220,102" size="220,45" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="currCh5" position="1570,102" size="220,45" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="list1" position="50,165" size="330,610" backgroundColor="steThemePrimary" scrollbarMode="showNever" EventFontVertical="Regular;25" TimeFontVertical="Regular;23"/>
\t\t<widget name="list2" position="400,165" size="330,610" backgroundColor="steThemePrimary" scrollbarMode="showNever" EventFontVertical="Regular;25" TimeFontVertical="Regular;23"/>
\t\t<widget name="list3" position="750,165" size="330,610" backgroundColor="steThemePrimary" scrollbarMode="showNever" EventFontVertical="Regular;25" TimeFontVertical="Regular;23"/>
\t\t<widget name="list4" position="1100,165" size="330,610" backgroundColor="steThemePrimary" scrollbarMode="showNever" EventFontVertical="Regular;25" TimeFontVertical="Regular;23"/>
\t\t<widget name="list5" position="1450,165" size="330,610" backgroundColor="steThemePrimary" scrollbarMode="showNever" EventFontVertical="Regular;25" TimeFontVertical="Regular;23"/>
\t\t<eLabel position="45,835" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="60,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="500,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="940,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1380,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>"""


SATFINDER_FHD = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="introduction" position="0,0" size="1,1" font="Regular;1"/>
\t\t<eLabel text="SIGNAL FINDER" position="50,28" size="700,58" font="Regular;42" foregroundColor="secondFG" transparent="1"/>
\t\t<widget source="Frontend" render="Label" position="1350,35" size="420,45" font="Regular;29" foregroundColor="grey" halign="right" transparent="1"><convert type="FrontendInfo">TYPE</convert></widget>
\t\t<eLabel text="SNR" position="50,120" size="150,45" font="Regular;31" foregroundColor="foreground" transparent="1"/>
\t\t<widget source="Frontend" render="Progress" position="210,122" size="960,34" backgroundColor="steThemePanelAlt" borderWidth="2"><convert type="FrontendInfo">SNR</convert></widget>
\t\t<widget source="Frontend" render="Label" position="1190,110" size="190,55" font="Regular;38" foregroundColor="secondFG" halign="right"><convert type="FrontendInfo">SNR</convert></widget>
\t\t<widget source="Frontend" render="Label" position="1410,110" size="330,55" font="Regular;38" foregroundColor="foreground" halign="right"><convert type="FrontendInfo">SNRdB</convert></widget>
\t\t<eLabel text="AGC" position="50,190" size="150,45" font="Regular;31" foregroundColor="foreground" transparent="1"/>
\t\t<widget source="Frontend" render="Progress" position="210,192" size="960,34" backgroundColor="steThemePanelAlt" borderWidth="2"><convert type="FrontendInfo">AGC</convert></widget>
\t\t<widget source="Frontend" render="Label" position="1190,180" size="190,55" font="Regular;38" foregroundColor="secondFG" halign="right"><convert type="FrontendInfo">AGC</convert></widget>
\t\t<eLabel text="BER" position="50,260" size="150,45" font="Regular;31" foregroundColor="foreground" transparent="1"/>
\t\t<widget source="Frontend" render="Label" position="210,250" size="280,55" font="Regular;38" foregroundColor="foreground"><convert type="FrontendInfo">BER</convert></widget>
\t\t<widget source="Frontend" render="FixedLabel" text="LOCK" position="520,250" size="220,55" font="Regular;34" foregroundColor="secondFG" backgroundColor="steThemePanelAlt" halign="center" valign="center"><convert type="FrontendInfo">LOCK</convert><convert type="ConditionalShowHide"/></widget>
\t\t<eLabel position="45,325" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget name="config" position="50,350" size="1740,455" font="Regular;31" itemHeight="58" scrollbarMode="showOnDemand"/>
\t\t<eLabel position="45,835" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="70,855" size="360,48" backgroundColor="key_red" foregroundColor="key_text" font="Regular;27" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_green" render="Label" position="460,855" size="360,48" backgroundColor="key_green" foregroundColor="key_text" font="Regular;27" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_yellow" render="Label" position="850,855" size="360,48" backgroundColor="key_yellow" foregroundColor="key_text" font="Regular;27" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_blue" render="Label" position="1240,855" size="360,48" backgroundColor="key_blue" foregroundColor="key_text" font="Regular;27" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>"""

CHOICEBOX_FHD = """\t\t<eLabel position="0,0" size="1760,900" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="text" position="50,35" size="1660,90" font="Regular;33" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<eLabel position="45,135" size="1670,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget name="list" position="50,155" size="1660,690" font="Regular;32" itemHeight="58" scrollbarMode="showOnDemand" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<eLabel position="45,860" size="1670,3" backgroundColor="steThemePanelAlt"/>"""

INFORMATION_SERVICE_FHD = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="information" position="55,45" size="1730,760" font="Regular;29" splitPosition="760" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<eLabel position="45,825" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,850" size="290,52" backgroundColor="key_red" conditional="key_red" font="Regular;26" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_green" render="Label" position="365,850" size="290,52" backgroundColor="key_green" conditional="key_green" font="Regular;26" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_yellow" render="Label" position="675,850" size="290,52" backgroundColor="key_yellow" conditional="key_yellow" font="Regular;26" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_blue" render="Label" position="985,850" size="290,52" backgroundColor="key_blue" conditional="key_blue" font="Regular;26" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_menu" render="Label" position="1470,850" size="140,52" backgroundColor="key_back" conditional="key_menu" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="key_help" render="Label" position="1630,850" size="140,52" backgroundColor="key_back" conditional="key_help" font="Regular;25" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>"""

CHANNEL_SELECTION_FHD = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="list" position="50,75" size="1210,710" scrollbarMode="showOnDemand" serviceItemHeight="62" serviceNumberFont="Regular;29" serviceNameFont="Regular;31" serviceInfoFont="Regular;25" transparent="1"/>
\t\t<widget source="ServiceEvent" render="CineViewPosterX" position="1470,85" size="285,430" zPosition="8"/>
\t\t<widget source="ServiceEvent" render="Label" position="1300,545" size="490,62" font="Regular;31" foregroundColor="secondFG" transparent="1"><convert type="EventName">Name</convert></widget>
\t\t<widget source="ServiceEvent" render="Label" position="1300,620" size="490,165" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">ExtendedDescription</convert></widget>
\t\t<eLabel position="45,825" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,850" size="400,52" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,850" size="400,52" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,850" size="400,52" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,850" size="400,52" font="Regular;27" halign="center" transparent="1"/>"""


SCREENS = (
    ("Satfinder", SATFINDER_FHD, "center,center", "1840,930", "Signal Finder"),
    ("ChoiceBox", CHOICEBOX_FHD, "center,center", "1760,900", "Choice Box"),
    ("InformationService", INFORMATION_SERVICE_FHD, "center,center", "1840,930", "Service Information"),
    ("ServiceInformation", INFORMATION_SERVICE_FHD, "center,center", "1840,930", "Service Information"),
    ("ChannelSelection", CHANNEL_SELECTION_FHD, "center,center", "1840,930", "Channel Selection"),
    ("InfoBar", INFOBAR_FHD, "0,760", "1920,320", ""),
    ("InfoBarLite", INFOBAR_FHD, "0,760", "1920,320", ""),
    ("PluginBrowserList", PLUGIN_LIST, "center,center", "1840,930", "Plugin Browser"),
    ("PluginBrowserGrid", PLUGIN_GRID, "center,center", "1840,930", "Plugin Browser"),
    ("PluginBrowser", PLUGIN_LIST, "center,center", "1840,930", "Plugin Browser"),
    ("MessageBox", MESSAGE_BOX, "center,center", "960,520", "Message"),
    ("MessageBoxModal", MESSAGE_BOX, "center,center", "960,520", "Message"),
    ("QuickMenu", QUICK_MENU, "center,center", "1840,930", "Quick Launch Menu"),
    ("EventView", EVENT_VIEW, "center,center", "1820,880", "Event View"),
    ("EventViewSimple", EVENT_SIMPLE, "center,center", "1820,760", "Event View"),
    ("InfoBarEventView", INFOBAR_EVENT_VIEW, "0,0", "1920,360", "Event View"),
    ("SecondInfoBar", SECOND_INFO, "0,560", "1920,520", "Second InfoBar"),
    ("SecondInfoBarECM", SECOND_INFO, "0,560", "1920,520", "Second InfoBar"),
    ("EPGSelection", SINGLE_EPG, "center,center", "1840,930", "EPG Selection"),
    ("EPGSelectionMulti", MULTI_EPG, "center,center", "1840,930", "Multi EPG"),
    ("QuickEPG", QUICK_EPG, "0,620", "1920,460", "Quick EPG"),
    ("GraphicalEPG", GRID, "center,center", "1840,930", "Graphical EPG"),
    ("GraphicalEPGPIG", GRID_PIG, "center,center", "1840,930", "Graphical EPG"),
    ("GraphicalInfoBarEPG", INFOBAR_GRID, "0,660", "1920,420", "InfoBar EPG"),
    ("EPGvertical", VERTICAL_EPG, "center,center", "1840,930", "Vertical EPG"),
    ("EPGverticalPIG", VERTICAL_EPG, "center,center", "1840,930", "Vertical EPG"),
)


def patch_file(path):
    data = _read(path)
    for name, body, pos, size, title in SCREENS:
        data = _remove_screen(data, name)

    data = data.replace('render="PosterX"', 'render="CineViewPosterX"')
    data = data.replace("render='PosterX'", "render='CineViewPosterX'")
    # OpenATV 8 removed several legacy ServiceInfo arguments. Leaving them in a
    # widget raises during skin processing because ServiceInfo cannot resolve them.
    unsupported_serviceinfo = (
        "IsSDAndNotWidescreen",
        "IsSDAndWidescreen",
        "IsVideoAVC",
        "IsVideoHEVC",
        "IsVideoMPEG2",
        "Provider",
        "Reference",
        "VideoSize",
    )
    for arg in unsupported_serviceinfo:
        pat = re.compile(
            r'<widget\\b(?:(?!</widget>).)*?<convert\\s+type=["\\\']ServiceInfo["\\\']>\\s*'
            + re.escape(arg)
            + r'\\s*</convert>(?:(?!</widget>).)*?</widget>',
            re.S,
        )
        data = pat.sub("", data)

    # OpenATV 8 MessageBox has no timerRunning attribute. MessageBox and
    # MessageBoxModal are replaced below with the native OpenATV-style fixed
    # widget contract, so no legacy CineView sizing applet is executed.
    data = data.replace("if self.timerRunning:", "if getattr(self, \"timerRunning\", False):")

    idx = data.rfind("</skin>")
    if idx < 0:
        return False
    blocks = "".join(_screen(name, body, pos, size, title) for name, body, pos, size, title in SCREENS)
    data = data[:idx] + blocks + data[idx:]
    try:
        ET.fromstring(data)
    except Exception:
        return False
    _write(path, data)
    return True


def main(root):
    changed = 0
    for name in os.listdir(root):
        if name.startswith("skin") and name.endswith(".xml"):
            if patch_file(os.path.join(root, name)):
                changed += 1
    print(changed)
    return 0 if changed else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
