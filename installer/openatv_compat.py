# -*- coding: utf-8 -*-
# OpenATV 8 live contract audited on Vu+ Duo 4K SE, build 20260922 (compile 20260922140732, Python 3.14.7).
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


PLUGIN_LIST = """		<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="0"/>
		<eLabel text="Plugins" position="45,24" size="1830,52" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
		<eLabel position="35,88" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<widget source="pluginList" render="Listbox" position="45,110" size="1830,800" conditional="pluginList" listOrientation="vertical" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="5">
			<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryPixmapAlphaBlend(pos=(12, 4), size=(185, 80), png=3, flags=BT_SCALE),
MultiContentEntryText(pos=(220, 5), size=(1550, 38), font=0, text=1),
MultiContentEntryText(pos=(220, 43), size=(1550, 29), font=1, text=2)
],
"fonts": [gFont("Regular", 31), gFont("Regular", 22)],
"itemHeight": 88
}
			</convert>
		</widget>
		<widget name="quickselect" position="45,110" size="1830,800" font="Regular;120" foregroundColor="secondFG" halign="center" valign="center" transparent="1" zPosition="8"/>
		<widget name="description" position="55,925" size="1810,55" font="Regular;24" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
		<eLabel position="35,995" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<widget source="key_red" render="Label" position="55,1010" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
		<widget source="key_green" render="Label" position="385,1010" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
		<widget source="key_yellow" render="Label" position="715,1010" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
		<widget source="key_blue" render="Label" position="1045,1010" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
		<widget source="key_menu" render="Label" position="1390,1010" size="170,45" font="Regular;23" halign="center" valign="center" foregroundColor="grey" transparent="1"/>
		<widget source="key_help" render="Label" position="1580,1010" size="170,45" font="Regular;23" halign="center" valign="center" foregroundColor="grey" transparent="1"/>
	"""

PLUGIN_GRID = """		<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="0"/>
		<eLabel text="Plugins" position="45,24" size="1830,52" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
		<eLabel position="35,88" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<widget source="pluginGrid" render="Listbox" position="45,110" size="1830,820" conditional="pluginGrid" listOrientation="grid" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="5">
			<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryText(pos=(4, 4), size=(326, 156), font=0, backcolor=0x0016161a),
MultiContentEntryPixmapAlphaBlend(pos=(105, 18), size=(120, 52), png=3, flags=BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER),
MultiContentEntryText(pos=(12, 84), size=(306, 66), font=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER | RT_WRAP, text=1)
],
"fonts": [gFont("Regular", 25)],
"itemWidth": 334,
"itemHeight": 164
}
			</convert>
		</widget>
		<widget name="quickselect" position="45,110" size="1830,820" font="Regular;120" foregroundColor="secondFG" halign="center" valign="center" transparent="1" zPosition="8"/>
		<widget name="description" position="55,925" size="1810,55" font="Regular;24" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
		<eLabel position="35,995" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<widget source="key_red" render="Label" position="55,1010" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
		<widget source="key_green" render="Label" position="385,1010" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
		<widget source="key_yellow" render="Label" position="715,1010" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
		<widget source="key_blue" render="Label" position="1045,1010" size="310,45" font="Regular;25" halign="center" valign="center" transparent="1"/>
		<widget source="key_menu" render="Label" position="1390,1010" size="170,45" font="Regular;23" halign="center" valign="center" foregroundColor="grey" transparent="1"/>
		<widget source="key_help" render="Label" position="1580,1010" size="170,45" font="Regular;23" halign="center" valign="center" foregroundColor="grey" transparent="1"/>
	"""

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
\t\t<widget name="channel" position="45,25" size="1380,52" font="Regular;34" foregroundColor="secondFG" backgroundColor="steSecondInfoBG" transparent="1" zPosition="5"/>
\t\t<widget name="epg_description" position="45,88" size="1380,286" font="Regular;25" foregroundColor="foreground" backgroundColor="steSecondInfoBG" transparent="1" zPosition="5"/>
\t\t<widget source="session.Event_Now" render="CineViewPosterX" position="1535,28" size="300,390" zPosition="8"/>
\t\t<widget source="session.CurrentService" render="Label" position="45,382" size="1380,38" font="Regular;21" foregroundColor="grey" backgroundColor="steSecondInfoBG" transparent="1" zPosition="5"><convert type="PliExtraInfo">All</convert></widget>
\t\t<eLabel position="35,430" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="session.CurrentService" render="Picon" position="45,447" size="180,55" transparent="1" alphatest="blend"><convert type="ServiceName">Reference</convert></widget>
\t\t<widget source="session.CurrentService" render="Label" position="245,455" size="610,38" font="Regular;24" foregroundColor="grey" transparent="1"><convert type="ServiceName">Name</convert></widget>
\t\t<widget source="key_red" render="Label" position="885,452" size="220,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_green" render="Label" position="1115,452" size="220,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_yellow" render="Label" position="1345,452" size="220,40" font="Regular;23" halign="center" transparent="1"/>
\t\t<widget source="key_blue" render="Label" position="1575,452" size="220,40" font="Regular;23" halign="center" transparent="1"/>"""

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

QUICK_MENU = """		<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="0"/>
		<widget source="mainlist" render="Listbox" position="45,90" size="640,820" backgroundColor="steThemePrimary" transparent="1" itemHeight="86" zPosition="5">
			<templates>
				<template name="Default" fonts="Regular;29,Regular;20" itemWidth="640" itemHeight="86">
					<mode name="default">
						<pixmap index="2" position="10,11" size="64,64" alpha="blend" scale="centerScaled"/>
						<text index="0" position="90,4" size="530,43" font="0" verticalAlignment="center"/>
						<text index="1" position="105,47" size="515,30" font="1" verticalAlignment="center"/>
					</mode>
				</template>
			</templates>
		</widget>
		<eLabel position="710,88" size="2,825" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<widget source="sublist" render="Listbox" position="735,90" size="640,820" backgroundColor="steThemePrimary" transparent="1" itemHeight="86" zPosition="5">
			<templates>
				<template name="Default" fonts="Regular;29,Regular;20" itemWidth="640" itemHeight="86">
					<mode name="default">
						<text index="0" position="10,4" size="620,43" font="0" verticalAlignment="center"/>
						<text index="1" position="25,47" size="605,30" font="1" verticalAlignment="center"/>
					</mode>
				</template>
			</templates>
		</widget>
		<eLabel position="1420,92" size="455,256" backgroundColor="black" zPosition="3"/>
		<widget source="session.VideoPicture" render="Pig" position="1420,92" size="455,256" backgroundColor="black" zPosition="4"/>
		<widget name="description" position="1420,375" size="455,535" backgroundColor="steThemePrimary" transparent="1" font="Regular;24" foregroundColor="foreground" halign="center" valign="center" zPosition="4"/>
		<eLabel position="35,995" size="1850,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<widget source="key_red" render="Label" position="55,1010" size="360,45" backgroundColor="key_red" font="Regular;24" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
		<widget source="key_green" render="Label" position="435,1010" size="360,45" backgroundColor="key_green" font="Regular;24" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
		<widget source="key_yellow" render="Label" position="815,1010" size="360,45" backgroundColor="key_yellow" font="Regular;24" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
		<widget source="key_help" render="Label" position="1575,1010" size="300,45" backgroundColor="key_back" font="Regular;24" foregroundColor="key_text" halign="center" valign="center"><convert type="ConditionalShowHide"/></widget>
	"""


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


SKIN_SELECTION = """		<eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="0"/>
		<widget source="Title" render="Label" position="35,24" size="1850,54" font="Regular;38" foregroundColor="foreground" transparent="1" zPosition="2"/>
		<eLabel position="30,92" size="1860,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<widget name="preview" position="60,145" size="620,465" alphatest="on" zPosition="3"/>
		<eLabel position="735,120" size="2,800" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<widget name="config" position="780,120" size="1080,520" itemHeight="64" font="Regular;30" transparent="1" enableWrapAround="1" scrollbarMode="showOnDemand" zPosition="3"/>
		<widget name="description" position="780,660" size="1080,160" font="Regular;25" foregroundColor="foreground" transparent="1" valign="top" zPosition="3"/>
		<widget name="footnote" position="780,825" size="1080,90" font="Regular;22" foregroundColor="secondFG" transparent="1" valign="top" zPosition="3"/>
		<eLabel position="30,935" size="1860,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
		<panel name="ButtonTemplate"/>
		<widget name="HelpWindow" position="0,0" size="0,0" alphatest="blend" transparent="1" zPosition="1"/>"""

VERTICAL_EPG_PIG = """		<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
		<widget source="Title" render="Label" position="45,25" size="1080,52" font="Regular;35" foregroundColor="secondFG" transparent="1"/>
		<eLabel position="1190,45" size="585,330" backgroundColor="black" zPosition="3"/>
		<widget source="session.VideoPicture" render="Pig" position="1205,60" size="555,300" backgroundColor="black" zPosition="4"/>
		<widget source="Event" render="Label" position="45,95" size="1090,270" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">FullDescription</convert></widget>
		<widget name="bouquetlist" position="45,395" size="1730,350" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
		<widget name="list" position="45,395" size="1730,350" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10"/>
		<eLabel position="35,775" size="1750,2" backgroundColor="steThemePanelAlt"/>
		<widget source="key_red" render="Label" position="55,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
		<widget source="key_green" render="Label" position="490,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
		<widget source="key_yellow" render="Label" position="925,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>
		<widget source="key_blue" render="Label" position="1360,800" size="400,45" font="Regular;26" halign="center" transparent="1"/>"""

SCREENS = (
    ("PluginBrowserList", PLUGIN_LIST, "0,0", "1920,1080", "Plugin Browser"),
    ("PluginBrowserGrid", PLUGIN_GRID, "0,0", "1920,1080", "Plugin Browser"),
    ("PluginBrowser", PLUGIN_LIST, "0,0", "1920,1080", "Plugin Browser"),
    ("MessageBox", MESSAGE_BOX, "center,center", "960,520", "Message"),
    ("MessageBoxModal", MESSAGE_BOX, "center,center", "960,520", "Message"),
    ("SkinSelection", SKIN_SELECTION, "0,0", "1920,1080", "Skin Settings"),
    ("QuickMenu", QUICK_MENU, "0,0", "1920,1080", "Quick Launch Menu"),
    ("EventViewSimple", EVENT_SIMPLE, "center,center", "1820,760", "Event View"),
    ("InfoBarEventView", INFOBAR_EVENT_VIEW, "0,0", "1920,360", "Event View"),
    ("SecondInfoBarECM", SECOND_INFO, "0,560", "1920,520", "Second InfoBar"),
    ("QuickEPG", QUICK_EPG, "0,660", "1920,420", "Quick EPG"),
    ("GraphicalEPG", GRID, "center,center", "1820,880", "Graphical EPG"),
    ("GraphicalEPGPIG", GRID_PIG, "center,center", "1820,880", "Graphical EPG"),
    ("GraphicalInfoBarEPG", INFOBAR_GRID, "0,750", "1920,330", "InfoBar EPG"),
    ("EPGvertical", VERTICAL_EPG, "center,center", "1820,880", "Vertical EPG"),
    ("EPGverticalPIG", VERTICAL_EPG_PIG, "center,center", "1820,880", "Vertical EPG"),
)


def patch_file(path):
    data = _read(path)

    # Preserve the already-approved OpenATV primary InfoBar geometry.  The
    # latest CineView visual source is used everywhere else, but the primary
    # InfoBar is an explicit invariant on this receiver.
    info_pat = re.compile(SCREEN_RE % re.escape("InfoBar"), re.S)
    m = info_pat.search(data)
    if m:
        b = m.group(0)
        for old, new in (
            ('position="16,842" size="1888,236"', 'position="24,842" size="1872,236"'),
            ('position="16,842" size="1888,2"', 'position="24,842" size="1872,2"'),
            ('position="16,1076" size="1888,2"', 'position="24,1076" size="1872,2"'),
            ('position="16,842" size="2,236"', 'position="24,842" size="2,236"'),
            ('position="1902,842" size="2,236"', 'position="1894,842" size="2,236"'),
            ('position="170,858" size="260,70"', 'mode="infobar" scale="aspect" position="200,852" size="200,110"'),
            ('position="170,934" size="260,36"', 'position="170,966" size="260,28"'),
            ('font="Regular;23" noWrap="1" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1600,pause=1000,repeat=0,always=0"', 'font="Regular;21" noWrap="1" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1600,pause=1000,repeat=0,always=0"'),
            ('position="170,978" size="58,27"', 'position="170,994" size="50,20"'),
            ('foregroundColor="grey" font="Regular;20"', 'foregroundColor="grey" font="Regular;16"'),
            ('position="235,978" size="195,27"', 'position="225,994" size="205,20"'),
            ('foregroundColor="grey" font="Regular;18" noWrap="1" options="movetype=running,direction=left,step=2,steptime=60,startdelay=1500,pause=1000,repeat=0,always=0"', 'foregroundColor="grey" font="Regular;16" noWrap="1" options="movetype=running,direction=left,step=2,steptime=60,startdelay=1500,pause=1000,repeat=0,always=0"'),
            ('position="28,1016" size="1864,2"', 'position="36,1016" size="1848,2"'),
        ):
            b = b.replace(old, new)
        data = data[:m.start()] + b + data[m.end():]

    # Runtime-only OpenATV alternatives.  Clone CineView's own FHD layouts so
    # these modes never fall back to the small 1280x720 default skin.
    cloned = []
    for src_name, dst_name in (
        ("SimpleChannelSelection", "ChannelSelection_PIG"),
        ("SimpleChannelSelection", "SlimChannelSelection"),
        ("MovieSelection", "MovieSelectionSlim"),
    ):
        pat = re.compile(SCREEN_RE % re.escape(src_name), re.S)
        sm = pat.search(data)
        if sm:
            block = sm.group(0)
            block = re.sub(r'(<screen\\b[^>]*\\bname=["\\'])%s(["\\'])' % re.escape(src_name),
                           r'\\1%s\\2' % dst_name, block, count=1)
            data = _remove_screen(data, dst_name)
            cloned.append(block)

    for name, body, pos, size, title in SCREENS:
        data = _remove_screen(data, name)

    data = data.replace('render="PosterX"', 'render="CineViewPosterX"')
    data = data.replace("render='PosterX'", "render='CineViewPosterX'")
    data = data.replace('<convert type="PliExtraInfo">TransponderInfo</convert>',
                        '<convert type="CineViewTransponderInfo">TransponderInfo</convert>')
    # OpenATV 7.4-8.0 no longer exposes the old combined SD/aspect flags.
    # Preserve the visual intent using the supported aspect-ratio flags.
    data = re.sub(
        r'(<convert\s+type=["\']ServiceInfo["\']>\s*)IsSDAndWidescreen(\s*</convert>)',
        r'\1IsWidescreen\2',
        data,
    )
    data = re.sub(
        r'(<convert\s+type=["\']ServiceInfo["\']>\s*)IsSDAndNotWidescreen(\s*</convert>)',
        r'\1IsNotWidescreen\2',
        data,
    )

    # Other obsolete ServiceInfo arguments are removed with their containing
    # widget, because an unresolved converter can abort skin loading.
    unsupported_serviceinfo = (
        "IsVideoAVC",
        "IsVideoHEVC",
        "IsVideoMPEG2",
        "Provider",
        "Reference",
        "VideoSize",
    )
    for arg in unsupported_serviceinfo:
        pat = re.compile(
            r'<widget\b(?:(?!</widget>).)*?<convert\s+type=["\']ServiceInfo["\']>\s*'
            + re.escape(arg)
            + r'\s*</convert>(?:(?!</widget>).)*?</widget>',
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
    blocks += "\n".join(cloned)
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
