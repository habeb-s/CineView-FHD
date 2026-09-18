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
\t\t<eLabel text="Plugins" position="50,24" size="1740,58" font="Regular;44" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
\t\t<eLabel position="45,92" size="1750,3" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="pluginGrid" render="Listbox" position="50,112" size="1740,660" conditional="pluginGrid" listOrientation="grid" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="5">
\t\t\t<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryText(pos=(4, 4), size=(405, 196), font=0, backcolor=0x0016161a),
MultiContentEntryPixmapAlphaBlend(pos=(123, 18), size=(165, 82), png=3, flags=BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER),
MultiContentEntryText(pos=(12, 108), size=(385, 82), font=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER | RT_WRAP, text=1)
],
"fonts": [gFont("Regular", 30)],
"itemWidth": 415,
"itemHeight": 205
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

EVENT_VIEW = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="channel" position="50,28" size="1280,48" font="Regular;31" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget source="Title" render="Label" position="50,82" size="1280,62" font="Regular;40" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget name="datetime" position="50,152" size="500,40" font="Regular;25" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="duration" position="565,152" size="210,40" font="Regular;25" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="epg_description" position="50,210" size="1280,590" font="Regular;28" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1430,50" size="340,510" zPosition="8"/>
\t\t<widget source="Event" render="Label" position="1390,585" size="420,185" font="Regular;25" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" valign="top"><convert type="EventName">ShortDescription</convert></widget>
\t\t<eLabel position="45,835" size="1750,3" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="key_red" render="Label" position="65,855" size="300,48" font="Regular;26" transparent="1" valign="center"/>
\t\t<widget source="key_green" render="Label" position="405,855" size="300,48" font="Regular;26" transparent="1" valign="center"/>
\t\t<widget source="key_yellow" render="Label" position="745,855" size="300,48" font="Regular;26" transparent="1" valign="center"/>
\t\t<widget source="key_blue" render="Label" position="1085,855" size="300,48" font="Regular;26" transparent="1" valign="center"/>
\t\t<widget source="key_menu" render="Label" position="1430,855" size="160,48" font="Regular;24" foregroundColor="grey" transparent="1"/>
\t\t<widget source="key_info" render="Label" position="1610,855" size="160,48" font="Regular;24" foregroundColor="grey" transparent="1"/>"""

EVENT_SIMPLE = """\t\t<eLabel position="0,0" size="1840,830" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="channel" position="50,28" size="1280,48" font="Regular;31" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget source="Title" render="Label" position="50,82" size="1280,62" font="Regular;40" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="datetime" position="50,152" size="500,40" font="Regular;25" foregroundColor="grey" transparent="1"/>
\t\t<widget name="duration" position="565,152" size="210,40" font="Regular;25" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="epg_description" position="50,210" size="1280,540" font="Regular;28" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1430,50" size="340,510" zPosition="8"/>"""

INFOBAR_EVENT_VIEW = """\t\t<eLabel position="0,0" size="1920,360" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="45,28" size="1320,48" font="Regular;34" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="datetime" position="1380,30" size="320,36" font="Regular;23" foregroundColor="grey" transparent="1"/>
\t\t<widget name="duration" position="1710,30" size="165,36" font="Regular;23" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="FullDescription" position="45,95" size="1510,225" font="Regular;25" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1630,82" size="210,260" zPosition="8"/>"""

SECOND_INFO = """\t\t<eLabel position="0,0" size="1920,520" backgroundColor="steSecondInfoBG" zPosition="0"/>
\t\t<widget name="channel" position="50,24" size="1390,58" font="Regular;38" foregroundColor="secondFG" backgroundColor="steSecondInfoBG" transparent="1" zPosition="5"/>
\t\t<widget name="epg_description" position="50,95" size="1390,285" font="Regular;29" foregroundColor="foreground" backgroundColor="steSecondInfoBG" transparent="1" zPosition="5"/>
\t\t<widget source="session.Event_Now" render="CineViewPosterX" position="1540,28" size="300,390" zPosition="8"/>
\t\t<widget source="session.CurrentService" render="Label" position="50,388" size="900,34" font="Regular;24" foregroundColor="grey" backgroundColor="steSecondInfoBG" transparent="1" zPosition="5"><convert type="PliExtraInfo">TransponderInfo</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="970,388" size="390,34" font="Regular;24" foregroundColor="secondFG" backgroundColor="steSecondInfoBG" transparent="1" zPosition="5"><convert type="PliExtraInfo">CryptoNameCaid</convert></widget>
\t\t<eLabel position="40,432" size="1840,3" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="session.CurrentService" render="Picon" position="50,447" size="190,58" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="260,453" size="600,42" font="Regular;27" foregroundColor="foreground" transparent="1"><convert type="ServiceName">Name</convert></widget>
\t\t<widget source="key_red" render="Label" position="900,452" size="210,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="1130,452" size="210,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="1360,452" size="210,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1590,452" size="210,42" font="Regular;24" halign="center" transparent="1"/>"""

SINGLE_EPG = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Service" render="Picon" position="50,28" size="210,70" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="Title" render="Label" position="285,30" size="1040,58" font="Regular;39" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="number" position="50,120" size="1190,670" font="Regular;58" halign="center" valign="center" backgroundColor="steThemePrimary" transparent="1" zPosition="20"/>
\t\t<widget name="list" position="50,120" size="1190,670" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steThemePrimary" transparent="1" zPosition="10" EventFontSingle="Regular;30" MinimumItemHeight="62"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1480,110" size="285,430" zPosition="12"/>
\t\t<widget source="Event" render="Label" position="1280,110" size="180,125" font="Regular;30" foregroundColor="secondFG" transparent="1"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1280,565" size="485,225" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="45,835" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="60,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="500,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="940,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1380,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>"""

MULTI_EPG = """\t\t<eLabel position="0,0" size="1840,930" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="50,28" size="1190,58" font="Regular;39" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="now_button" position="50,98" size="380,48" transparent="1"/>
\t\t<widget name="now_button_sel" position="50,98" size="380,48" transparent="1"/>
\t\t<widget name="now_text" position="50,98" size="380,48" text="NOW" font="Regular;27" halign="center" valign="center" transparent="1"/>
\t\t<widget name="next_button" position="440,98" size="380,48" transparent="1"/>
\t\t<widget name="next_button_sel" position="440,98" size="380,48" transparent="1"/>
\t\t<widget name="next_text" position="440,98" size="380,48" text="NEXT" font="Regular;27" halign="center" valign="center" transparent="1"/>
\t\t<widget name="more_button" position="830,98" size="380,48" transparent="1"/>
\t\t<widget name="more_button_sel" position="830,98" size="380,48" transparent="1"/>
\t\t<widget name="more_text" position="830,98" size="380,48" text="MORE" font="Regular;27" halign="center" valign="center" transparent="1"/>
\t\t<widget name="date" position="1260,35" size="520,45" font="Regular;28" halign="right" transparent="1"/>
\t\t<widget name="bouquetlist" position="50,165" size="1190,625" scrollbarMode="showNever" backgroundColor="steThemePrimary" transparent="0" zPosition="20"/>
\t\t<widget name="list" position="50,165" size="1190,625" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steThemePrimary" transparent="1" zPosition="10" EventFontMulti="Regular;29" MinimumItemHeight="62"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1480,125" size="285,430" zPosition="12"/>
\t\t<widget source="Event" render="Label" position="1280,125" size="180,125" font="Regular;30" foregroundColor="secondFG" transparent="1"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1280,575" size="485,210" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="45,835" size="1750,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="60,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="500,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="940,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1380,855" size="400,48" font="Regular;27" halign="center" transparent="1"/>"""

QUICK_EPG = """\t\t<eLabel position="0,0" size="1920,460" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Service" render="Picon" position="45,35" size="210,75" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="Service" render="Label" position="280,40" size="620,52" font="Regular;36" foregroundColor="secondFG" transparent="1"><convert type="ServiceName">Name</convert></widget>
\t\t<widget name="list" position="45,130" size="930,250" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steThemePrimary" transparent="1" EventFontSingle="Regular;29" MinimumItemHeight="60"/>
\t\t<widget source="Event" render="Label" position="1010,45" size="540,335" font="Regular;25" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<widget source="Event" render="CineViewPosterX" position="1610,25" size="235,350" zPosition="8"/>
\t\t<eLabel position="35,397" size="1850,3" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,410" size="400,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,410" size="400,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,410" size="400,42" font="Regular;24" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,410" size="400,42" font="Regular;24" halign="center" transparent="1"/>"""

GRID = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="45,24" size="1120,55" font="Regular;35" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="lab1" position="45,95" size="1120,650" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="20"/>
\t\t<widget name="timeline_text" position="45,95" size="1120,42" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget name="bouquetlist" position="45,140" size="1120,605" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
\t\t<widget name="list" position="45,140" size="1120,605" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10"/>
\t\t<widget name="timeline_now" position="45,140" size="4,605" zPosition="21"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1495,70" size="270,405" zPosition="12"/>
\t\t<widget source="Event" render="Label" position="1210,70" size="250,110" font="Regular;29" foregroundColor="foreground" transparent="1"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1210,205" size="555,520" font="Regular;23" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="35,775" size="1750,2" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>"""

GRID_PIG = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="45,24" size="1020,55" font="Regular;35" foregroundColor="secondFG" transparent="1"/>
\t\t<eLabel position="1240,40" size="525,295" backgroundColor="black" zPosition="4"/>
\t\t<widget source="session.VideoPicture" render="Pig" position="1255,55" size="495,265" backgroundColor="black" zPosition="5"/>
\t\t<widget source="Event" render="Label" position="45,92" size="1120,210" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<widget name="lab1" position="45,335" size="1720,410" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="20"/>
\t\t<widget name="timeline_text" position="45,335" size="1720,42" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="bouquetlist" position="45,380" size="1720,365" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
\t\t<widget name="list" position="45,380" size="1720,365" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10"/>
\t\t<widget name="timeline_now" position="45,380" size="4,365" zPosition="21"/>
\t\t<eLabel position="35,775" size="1750,2" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>"""

INFOBAR_GRID = """\t\t<eLabel position="0,0" size="1920,330" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="45,22" size="780,45" font="Regular;31" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="lab1" position="45,75" size="1830,180" font="Regular;25" halign="center" valign="center" transparent="1" zPosition="20"/>
\t\t<widget name="timeline_text" position="45,75" size="1830,36" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="bouquetlist" position="45,112" size="1830,143" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
\t\t<widget name="list" position="45,112" size="1830,143" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10"/>
\t\t<widget name="timeline_now" position="45,112" size="4,143" zPosition="21"/>
\t\t<widget source="key_red" render="Label" position="55,278" size="400,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,278" size="400,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,278" size="400,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,278" size="400,40" font="Regular;23" halign="center" transparent="1"/>"""

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

VERTICAL_EPG = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="45,25" size="1730,52" font="Regular;35" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="bouquetlist" position="45,90" size="1730,700" backgroundColor="steThemePrimary" scrollbarMode="showNever" zPosition="20"/>
\t\t<widget name="list" position="45,90" size="1730,700" backgroundColor="steThemePrimary" scrollbarMode="showNever" zPosition="19"/>
\t\t<widget name="currCh1" position="45,95" size="330,42" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="currCh2" position="385,95" size="330,42" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="currCh3" position="725,95" size="330,42" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="currCh4" position="1065,95" size="330,42" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="currCh5" position="1405,95" size="330,42" font="Regular;27" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="list1" position="45,145" size="330,590" backgroundColor="steThemePrimary" scrollbarMode="showNever"/>
\t\t<widget name="list2" position="385,145" size="330,590" backgroundColor="steThemePrimary" scrollbarMode="showNever"/>
\t\t<widget name="list3" position="725,145" size="330,590" backgroundColor="steThemePrimary" scrollbarMode="showNever"/>
\t\t<widget name="list4" position="1065,145" size="330,590" backgroundColor="steThemePrimary" scrollbarMode="showNever"/>
\t\t<widget name="list5" position="1405,145" size="330,590" backgroundColor="steThemePrimary" scrollbarMode="showNever"/>
\t\t<eLabel position="35,775" size="1750,2" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>"""

INFOBAR_FHD = """\t\t<eLabel position="0,0" size="1920,320" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="session.CurrentService" render="Picon" position="40,34" size="220,120" transparent="1" alphatest="blend" zPosition="5"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="290,30" size="640,48" font="Regular;36" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="5"><convert type="ServiceName">Name</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="290,80" size="640,34" font="Regular;24" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="5"><convert type="ExtendedServiceInfo">Provider</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="945,34" size="160,44" font="Regular;30" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" halign="center" zPosition="5"><convert type="ExtendedServiceInfo">ServiceNumber</convert></widget>
\t\t<widget source="session.CurrentService" render="FixedLabel" text="HD" position="1120,34" size="92,44" font="Regular;28" foregroundColor="secondFG" backgroundColor="steThemePanelAlt" halign="center" valign="center" zPosition="6"><convert type="ServiceInfo">IsHD</convert><convert type="ConditionalShowHide"/></widget>
\t\t<widget source="session.CurrentService" render="Label" position="1230,34" size="260,44" font="Regular;27" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" halign="center" zPosition="5"><convert type="PliExtraInfo">ResolutionString</convert></widget>
\t\t<widget source="global.CurrentTime" render="Label" position="1580,26" size="280,54" font="Regular;39" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" halign="right"><convert type="ClockToText">Default</convert></widget>
\t\t<widget source="session.Event_Now" render="Label" position="290,125" size="90,42" font="Regular;28" foregroundColor="grey" transparent="1"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Default</convert></widget>
\t\t<widget source="session.Event_Now" render="Label" position="390,125" size="1040,42" font="Regular;31" foregroundColor="foreground" transparent="1"><convert type="EventName">Name</convert></widget>
\t\t<widget source="session.Event_Now" render="Label" position="1450,125" size="210,42" font="Regular;27" foregroundColor="secondFG" transparent="1" halign="right"><convert type="EventTime">Remaining</convert><convert type="RemainingToText"/></widget>
\t\t<widget source="session.Event_Next" render="Label" position="290,172" size="90,40" font="Regular;26" foregroundColor="grey" transparent="1"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Default</convert></widget>
\t\t<widget source="session.Event_Next" render="Label" position="390,172" size="1040,40" font="Regular;28" foregroundColor="grey" transparent="1"><convert type="EventName">Name</convert></widget>
\t\t<widget source="session.Event_Now" render="Progress" position="290,215" size="1370,10" backgroundColor="steThemePanelAlt" zPosition="5"><convert type="EventTime">Progress</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="290,238" size="900,35" font="Regular;25" foregroundColor="foreground" transparent="1" noWrap="1"><convert type="PliExtraInfo">TransponderInfo</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="1210,238" size="410,35" font="Regular;25" foregroundColor="secondFG" transparent="1" halign="center"><convert type="PliExtraInfo">CryptoNameCaid</convert></widget>
\t\t<widget source="session.FrontendStatus" render="Label" position="40,190" size="210,38" font="Regular;27" foregroundColor="foreground" transparent="1"><convert type="FrontendInfo">SNRdB</convert></widget>
\t\t<widget source="session.FrontendStatus" render="Progress" position="40,235" size="210,14" backgroundColor="steThemePanelAlt"><convert type="FrontendInfo">SNR</convert></widget>
\t\t<widget source="session.FrontendStatus" render="Label" position="40,258" size="210,32" font="Regular;23" foregroundColor="grey" transparent="1"><convert type="FrontendInfo">SNR</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="1640,238" size="230,35" font="Regular;24" foregroundColor="grey" transparent="1" halign="right"><convert type="ExtendedServiceInfo">SatName</convert></widget>
\t\t<eLabel position="30,298" size="1860,3" backgroundColor="steThemePanelAlt" zPosition="2"/>"""


SCREENS = (
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
    ("GraphicalEPG", GRID, "center,center", "1820,880", "Graphical EPG"),
    ("GraphicalEPGPIG", GRID_PIG, "center,center", "1820,880", "Graphical EPG"),
    ("GraphicalInfoBarEPG", INFOBAR_GRID, "0,750", "1920,330", "InfoBar EPG"),
    ("EPGvertical", VERTICAL_EPG, "center,center", "1820,880", "Vertical EPG"),
    ("EPGverticalPIG", VERTICAL_EPG, "center,center", "1820,880", "Vertical EPG"),
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
