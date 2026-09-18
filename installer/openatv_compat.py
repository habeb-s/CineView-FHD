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


PLUGIN_LIST = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel text="Plugins" position="45,24" size="1730,52" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
\t\t<eLabel position="35,88" size="1750,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="pluginList" render="Listbox" position="45,110" size="1730,590" conditional="pluginList" listOrientation="vertical" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="5">
\t\t\t<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryPixmapAlphaBlend(pos=(12, 12), size=(120, 52), png=3, flags=BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER),
MultiContentEntryText(pos=(155, 5), size=(1515, 38), font=0, text=1),
MultiContentEntryText(pos=(155, 43), size=(1515, 29), font=1, text=2)
],
"fonts": [gFont("Regular", 31), gFont("Regular", 22)],
"itemHeight": 80
}
\t\t\t</convert>
\t\t</widget>
\t\t<widget name="quickselect" position="45,110" size="1730,590" font="Regular;120" foregroundColor="secondFG" halign="center" valign="center" transparent="1" zPosition="8"/>
\t\t<widget name="description" position="55,715" size="1710,55" font="Regular;24" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<eLabel position="35,785" size="1750,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="key_red" render="Label" position="55,805" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="385,805" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="715,805" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1045,805" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_menu" render="Label" position="1390,805" size="170,45" font="Regular;23" halign="center" valign="center" foregroundColor="grey" transparent="1"/>
\t\t<widget source="key_help" render="Label" position="1580,805" size="170,45" font="Regular;23" halign="center" valign="center" foregroundColor="grey" transparent="1"/>"""

PLUGIN_GRID = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel text="Plugins" position="45,24" size="1730,52" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
\t\t<eLabel position="35,88" size="1750,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="pluginGrid" render="Listbox" position="45,110" size="1730,590" conditional="pluginGrid" listOrientation="grid" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="5">
\t\t\t<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryText(pos=(4, 4), size=(326, 156), font=0, backcolor=0x0016161a),
MultiContentEntryPixmapAlphaBlend(pos=(105, 18), size=(120, 52), png=3, flags=BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER),
MultiContentEntryText(pos=(12, 82), size=(306, 68), font=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER | RT_WRAP, text=1)
],
"fonts": [gFont("Regular", 25)],
"itemWidth": 334,
"itemHeight": 164
}
\t\t\t</convert>
\t\t</widget>
\t\t<widget name="quickselect" position="45,110" size="1730,590" font="Regular;120" foregroundColor="secondFG" halign="center" valign="center" transparent="1" zPosition="8"/>
\t\t<widget name="description" position="55,715" size="1710,55" font="Regular;24" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<eLabel position="35,785" size="1750,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="key_red" render="Label" position="55,805" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="385,805" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="715,805" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1045,805" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget source="key_menu" render="Label" position="1390,805" size="170,45" font="Regular;23" halign="center" valign="center" foregroundColor="grey" transparent="1"/>
\t\t<widget source="key_help" render="Label" position="1580,805" size="170,45" font="Regular;23" halign="center" valign="center" foregroundColor="grey" transparent="1"/>"""

EVENT_VIEW = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="channel" position="45,28" size="1180,45" font="Regular;30" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget source="Title" render="Label" position="45,82" size="1180,60" font="Regular;38" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget name="datetime" position="45,150" size="420,38" font="Regular;24" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="duration" position="480,150" size="180,38" font="Regular;24" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="FullDescription" position="45,205" size="1190,530" font="Regular;26" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1385,55" size="340,510" zPosition="8"/>
\t\t<widget source="Event" render="Label" position="1280,590" size="445,145" font="Regular;23" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" valign="top"><convert type="EventName">ShortDescription</convert></widget>
\t\t<eLabel position="35,770" size="1750,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="red" pixmap="buttons/red.png" position="75,802" size="34,34" alphatest="blend"/>
\t\t<widget source="key_red" render="Label" position="120,797" size="300,44" font="Regular;25" transparent="1" valign="center"/>
\t\t<widget name="green" pixmap="buttons/green.png" position="490,802" size="34,34" alphatest="blend"/>
\t\t<widget source="key_green" render="Label" position="535,797" size="300,44" font="Regular;25" transparent="1" valign="center"/>
\t\t<widget name="yellow" pixmap="buttons/yellow.png" position="905,802" size="34,34" alphatest="blend"/>
\t\t<widget source="key_yellow" render="Label" position="950,797" size="300,44" font="Regular;25" transparent="1" valign="center"/>
\t\t<widget name="blue" pixmap="buttons/blue.png" position="1320,802" size="34,34" alphatest="blend"/>
\t\t<widget source="key_blue" render="Label" position="1365,797" size="300,44" font="Regular;25" transparent="1" valign="center"/>"""

EVENT_SIMPLE = """\t\t<eLabel position="0,0" size="1820,760" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="channel" position="45,28" size="1180,45" font="Regular;30" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget source="Title" render="Label" position="45,82" size="1180,60" font="Regular;38" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="datetime" position="45,150" size="420,38" font="Regular;24" foregroundColor="grey" transparent="1"/>
\t\t<widget name="duration" position="480,150" size="180,38" font="Regular;24" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="FullDescription" position="45,205" size="1190,500" font="Regular;26" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1385,55" size="340,510" zPosition="8"/>"""

INFOBAR_EVENT_VIEW = """\t\t<eLabel position="0,0" size="1920,360" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="45,28" size="1320,48" font="Regular;34" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget name="datetime" position="1380,30" size="320,36" font="Regular;23" foregroundColor="grey" transparent="1"/>
\t\t<widget name="duration" position="1710,30" size="165,36" font="Regular;23" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="FullDescription" position="45,95" size="1510,225" font="Regular;25" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1630,82" size="210,260" zPosition="8"/>"""

SECOND_INFO = """\t\t<eLabel position="0,0" size="1920,520" backgroundColor="steSecondInfoBG" zPosition="0"/>
\t\t<widget name="channel" position="45,25" size="1370,55" font="Regular;34" foregroundColor="secondFG" backgroundColor="steSecondInfoBG" transparent="1" zPosition="4"/>
\t\t<widget name="FullDescription" position="45,95" size="1370,300" font="Regular;25" foregroundColor="foreground" backgroundColor="steSecondInfoBG" transparent="1" zPosition="4"/>
\t\t<widget source="session.Event_Now" render="CineViewPosterX" position="1535,28" size="300,390" zPosition="8"/>
\t\t<eLabel position="35,430" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="session.CurrentService" render="Picon" position="45,447" size="180,55" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="245,455" size="650,38" font="Regular;24" foregroundColor="grey" transparent="1"><convert type="ServiceName">Name</convert></widget>
\t\t<widget source="key_red" render="Label" position="920,452" size="210,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="1140,452" size="210,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="1360,452" size="210,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1580,452" size="210,40" font="Regular;23" halign="center" transparent="1"/>"""

SINGLE_EPG = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Service" render="Picon" position="45,28" size="180,60" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="Title" render="Label" position="245,30" size="930,55" font="Regular;36" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="number" position="45,110" size="1120,630" font="Regular;50" halign="center" valign="center" backgroundColor="steThemePrimary" transparent="1" zPosition="20"/>
\t\t<widget name="list" position="45,110" size="1120,630" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steThemePrimary" transparent="1" zPosition="10"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1495,105" size="270,405" zPosition="12"/>
\t\t<widget source="Event" render="Label" position="1220,105" size="245,120" font="Regular;29" foregroundColor="foreground" transparent="1"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1220,245" size="545,475" font="Regular;23" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="35,775" size="1750,2" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>"""

MULTI_EPG = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Title" render="Label" position="45,28" size="1120,55" font="Regular;36" foregroundColor="secondFG" transparent="1"/>
\t\t<widget name="now_button" position="45,95" size="350,45" transparent="1"/>
\t\t<widget name="now_button_sel" position="45,95" size="350,45" transparent="1"/>
\t\t<widget name="now_text" position="45,95" size="350,45" text="NOW" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget name="next_button" position="405,95" size="350,45" transparent="1"/>
\t\t<widget name="next_button_sel" position="405,95" size="350,45" transparent="1"/>
\t\t<widget name="next_text" position="405,95" size="350,45" text="NEXT" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget name="more_button" position="765,95" size="350,45" transparent="1"/>
\t\t<widget name="more_button_sel" position="765,95" size="350,45" transparent="1"/>
\t\t<widget name="more_text" position="765,95" size="350,45" text="MORE" font="Regular;25" halign="center" valign="center" transparent="1"/>
\t\t<widget name="date" position="1210,35" size="550,45" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget name="bouquetlist" position="45,155" size="1120,585" scrollbarMode="showNever" backgroundColor="steThemePrimary" transparent="0" zPosition="20"/>
\t\t<widget name="list" position="45,155" size="1120,585" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steThemePrimary" transparent="1" zPosition="10"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1495,120" size="270,405" zPosition="12"/>
\t\t<widget source="Event" render="Label" position="1210,120" size="250,120" font="Regular;29" foregroundColor="foreground" transparent="1"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1210,260" size="555,455" font="Regular;23" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="35,775" size="1750,2" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>"""

QUICK_EPG = """\t\t<eLabel position="0,0" size="1920,420" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="Service" render="Picon" position="45,35" size="190,60" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="Service" render="Label" position="250,38" size="560,50" font="Regular;32" foregroundColor="secondFG" transparent="1"><convert type="ServiceName">Name</convert></widget>
\t\t<widget name="list" position="45,115" size="830,230" scrollbarMode="showOnDemand" enableWrapAround="1" backgroundColor="steThemePrimary" transparent="1"/>
\t\t<widget source="Event" render="Label" position="920,45" size="600,300" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
\t\t<widget source="Event" render="CineViewPosterX" position="1580,25" size="215,320" zPosition="8"/>
\t\t<eLabel position="35,365" size="1850,2" backgroundColor="steThemePanelAlt"/>
\t\t<widget source="key_red" render="Label" position="55,375" size="400,38" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="490,375" size="400,38" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="925,375" size="400,38" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1360,375" size="400,38" font="Regular;23" halign="center" transparent="1"/>"""

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

SCREENS = (
    ("PluginBrowserList", PLUGIN_LIST, "center,center", "1820,880", "Plugin Browser"),
    ("PluginBrowserGrid", PLUGIN_GRID, "center,center", "1820,880", "Plugin Browser"),
    ("PluginBrowser", PLUGIN_LIST, "center,center", "1820,880", "Plugin Browser"),
    ("EventView", EVENT_VIEW, "center,center", "1820,880", "Event View"),
    ("EventViewSimple", EVENT_SIMPLE, "center,center", "1820,760", "Event View"),
    ("InfoBarEventView", INFOBAR_EVENT_VIEW, "0,0", "1920,360", "Event View"),
    ("SecondInfoBar", SECOND_INFO, "0,560", "1920,520", "Second InfoBar"),
    ("SecondInfoBarECM", SECOND_INFO, "0,560", "1920,520", "Second InfoBar"),
    ("EPGSelection", SINGLE_EPG, "center,center", "1820,880", "EPG Selection"),
    ("EPGSelectionMulti", MULTI_EPG, "center,center", "1820,880", "Multi EPG"),
    ("QuickEPG", QUICK_EPG, "0,660", "1920,420", "Quick EPG"),
    ("GraphicalEPG", GRID, "center,center", "1820,880", "Graphical EPG"),
    ("GraphicalEPGPIG", GRID_PIG, "center,center", "1820,880", "Graphical EPG"),
    ("GraphicalInfoBarEPG", INFOBAR_GRID, "0,750", "1920,330", "InfoBar EPG"),
)


def patch_file(path):
    data = _read(path)
    for name, body, pos, size, title in SCREENS:
        data = _remove_screen(data, name)

    data = data.replace('render="PosterX"', 'render="CineViewPosterX"')
    data = data.replace("render='PosterX'", "render='CineViewPosterX'")

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
