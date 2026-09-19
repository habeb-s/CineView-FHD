# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import re
import sys
import xml.etree.ElementTree as ET

SCREEN_RE = r'\n?[ \t]*<screen\\b(?=[^>]*\\bname=["\\\']%s["\\\'])[^>]*>.*?</screen>[ \t]*\n?'

SETUP = r"""<screen name="Setup" title="Setup" position="fill" flags="wfNoBorder">
    <panel name="PigTemplate"/>
    <widget name="config" position="780,105" size="1110,885" itemHeight="70" font="Regular;31" scrollbarMode="showOnDemand"/>
    <widget name="description" objectTypes="description,Button,Label" position="35,570" size="620,300" font="Regular;28" valign="top" halign="block"/>
    <widget source="description" render="Label" objectTypes="description,StaticText" position="35,570" size="620,300" font="Regular;28" valign="top" halign="block"/>
    <widget name="footnote" objectTypes="footnote,Button,Label" position="35,885" zPosition="1000" size="620,100" font="Regular;27" valign="top" halign="block"/>
    <widget source="footnote" render="Label" objectTypes="footnote,StaticText" position="35,885" zPosition="1" size="620,100" font="Regular;27" valign="top" halign="block"/>
    <widget name="HelpWindow" conditional="HelpWindow" pixmap="icons/vkey_icon.png" position="3,310" zPosition="1" size="1,1" transparent="1" alphatest="on"/>
    <widget name="introduction" conditional="introduction" position="0,0" size="0,0"/>
</screen>"""

GRAPHICAL = r"""<screen name="GraphicalEPG" position="center,center" size="1820,880" flags="wfNoBorder" title="Graphical EPG">
    <eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
    <widget source="Title" render="Label" position="45,20" size="900,52" font="Regular;35" foregroundColor="secondFG" transparent="1" zPosition="12"/>
    <widget source="global.CurrentTime" render="Label" position="1240,24" size="245,42" font="Regular;28" foregroundColor="foreground" transparent="1" halign="right" zPosition="12"><convert type="ClockToText">Default</convert></widget>
    <widget source="global.CurrentTime" render="Label" position="1500,24" size="275,42" font="Regular;24" foregroundColor="grey" transparent="1" halign="right" zPosition="12"><convert type="ClockToText">Format:%d.%m.%Y</convert></widget>

    <widget name="timeline_text" position="45,88" size="1280,42" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="12"/>
    <widget name="lab1" position="45,132" size="1280,610" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="20"/>
    <widget name="bouquetlist" position="45,132" size="1280,610" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
    <widget name="list" position="45,132" size="1280,610" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="1" zPosition="10"/>
    <widget name="timeline_now" position="45,132" size="4,610" zPosition="21"/>

    <eLabel position="1360,88" size="415,654" backgroundColor="steThemePanel" zPosition="2"/>
    <widget source="Event" render="CineViewPosterX" position="1462,108" size="210,315" zPosition="18"/>
    <widget source="Event" render="Label" position="1390,445" size="355,50" font="Regular;30" foregroundColor="secondFG" transparent="1" noWrap="1" zPosition="18"><convert type="EventName">Name</convert></widget>
    <widget source="Event" render="Label" position="1390,500" size="130,34" font="Regular;22" foregroundColor="grey" transparent="1" zPosition="18"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <widget source="Event" render="Label" position="1530,500" size="150,34" font="Regular;22" foregroundColor="grey" transparent="1" zPosition="18"><convert type="EventTime">EndTime</convert><convert type="ClockToText">Format:- %H:%M</convert></widget>
    <widget source="Event" render="Label" position="1390,545" size="355,175" font="Regular;22" foregroundColor="foreground" transparent="1" valign="top" zPosition="18"><convert type="EventName">ExtendedDescription</convert></widget>

    <eLabel position="35,775" size="1750,2" backgroundColor="steThemePanelAlt" zPosition="3"/>
    <widget source="key_red" render="Label" position="55,800" size="400,45" font="Regular;26" halign="center" transparent="1" zPosition="12"/>
    <widget source="key_green" render="Label" position="490,800" size="400,45" font="Regular;26" halign="center" transparent="1" zPosition="12"/>
    <widget source="key_yellow" render="Label" position="925,800" size="400,45" font="Regular;26" halign="center" transparent="1" zPosition="12"/>
    <widget source="key_blue" render="Label" position="1360,800" size="400,45" font="Regular;26" halign="center" transparent="1" zPosition="12"/>
</screen>"""


def _read(path):
    with io.open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def _write(path, data):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(data)


def _remove_screen(data, name):
    return re.sub(SCREEN_RE % re.escape(name), "\n", data, flags=re.S)


def _add_before_skin_end(data, block):
    index = data.rfind("</skin>")
    if index < 0:
        raise RuntimeError("missing </skin>")
    return data[:index] + "\n" + block.strip() + "\n" + data[index:]


def _set_parameter(data, name, value):
    pattern = re.compile(r'<parameter\\b[^>]*\\bname=["\\\']' + re.escape(name) + r'["\\\'][^>]*/>')
    tag = '<parameter name="%s" value="%s"/>' % (name, value)
    if pattern.search(data):
        return pattern.sub(tag, data, count=1)
    end = data.find("</parameters>")
    if end < 0:
        raise RuntimeError("missing </parameters>")
    return data[:end] + "\t\t" + tag + "\n" + data[end:]


def patch(path):
    data = _read(path)

    # Keep Setup content fully to the right of the 720px PIG.
    data = _remove_screen(data, "Setup")
    data = _add_before_skin_end(data, SETUP)

    # OpenATV ChoiceList.py defaults text boxes to only 25px high.
    # CineView uses a 33px font, so unselected rows were visibly clipped.
    data = re.sub(
        r'<alias name="ChoiceList"[^>]*/>',
        '<alias name="ChoiceList" font="Regular" size="33" height="52"/>',
        data,
        count=1,
    )
    data = re.sub(
        r'<alias name="SelectionList"[^>]*/>',
        '<alias name="SelectionList" font="Regular" size="33" height="52"/>',
        data,
        count=1,
    )
    data = _set_parameter(data, "ChoicelistVerticalAlignment", "center")
    data = _set_parameter(data, "ChoicelistNameSingle", "8,0,1070,52")
    data = _set_parameter(data, "ChoicelistName", "72,0,1006,52")
    data = _set_parameter(data, "ChoicelistIcon", "10,7,48,38")
    data = _set_parameter(data, "ChoicelistDash", "8,0,1070,52")

    # Native OpenATV GraphicalEPG Event source with explicit z-order.
    data = _remove_screen(data, "GraphicalEPG")
    data = _add_before_skin_end(data, GRAPHICAL)

    ET.fromstring(data)
    _write(path, data)


if __name__ == "__main__":
    patch(sys.argv[1])
    print("CINEVIEW_OPENATV_V6_OK")
