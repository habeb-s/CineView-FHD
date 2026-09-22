# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import re
import sys
import xml.etree.ElementTree as ET


def read(path):
    with io.open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return handle.read()


def write(path, data):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(data)


def screen_re(name):
    return re.compile(
        r'(<screen\b(?=[^>]*\bname=["\']' + re.escape(name) + r'["\'])[^>]*>)(.*?)(</screen>)',
        re.S,
    )


def add_timelines(data, name, y_pos, height):
    match = screen_re(name).search(data)
    if not match:
        return data
    body = match.group(2)
    if 'name="timeline0"' not in body:
        block = "\n".join(
            '        <widget name="timeline%d" pixmap="window/timeline.png" position="0,%d" size="1,%d" zPosition="22"/>'
            % (index, y_pos, height)
            for index in range(6)
        )
        marker = re.search(r'\s*<widget name="timeline_now"[^>]*/>', body)
        if marker:
            body = body[:marker.start()] + "\n" + block + "\n" + body[marker.start():]
    body = re.sub(
        r'<widget name="timeline_now"([^>]*?)position="[^"]+"([^>]*?)/>',
        lambda item: '<widget name="timeline_now"%sposition="6,%d"%s pixmap="window/timeline-now.png" alphatest="blend"/>'
        % (item.group(1), y_pos, item.group(2)),
        body,
        count=1,
    )
    return data[:match.start()] + match.group(1) + body + match.group(3) + data[match.end():]


def patch_vertical(data, name):
    match = screen_re(name).search(data)
    if not match:
        return data
    body = match.group(2)
    positions = [45, 385, 725, 1065, 1405]
    if 'source="piconCh1"' not in body:
        block = []
        for index, x_pos in enumerate(positions, 1):
            block.append(
                '        <widget name="Active%d" position="%d,95" size="330,42" backgroundColor="selectedBG" transparent="0" zPosition="2"/>'
                % (index, x_pos)
            )
            block.append(
                '        <widget source="piconCh%d" render="Picon" position="%d,95" size="70,42" zPosition="4" alphatest="blend" transparent="1"><convert type="ServiceName">Reference</convert></widget>'
                % (index, x_pos + 5)
            )
        marker = re.search(r'\s*<widget name="currCh1"', body)
        if marker:
            body = body[:marker.start()] + "\n" + "\n".join(block) + "\n" + body[marker.start():]
    for index, x_pos in enumerate(positions, 1):
        body = re.sub(
            r'<widget name="currCh%d"[^>]*/>' % index,
            '<widget name="currCh%d" position="%d,95" size="248,42" font="Regular;27" foregroundColor="secondFG" transparent="1" zPosition="5"/>'
            % (index, x_pos + 82),
            body,
            count=1,
        )
    return data[:match.start()] + match.group(1) + body + match.group(3) + data[match.end():]


TASK_VIEW = """<screen name="TaskView" title="Task View" position="fill" flags="wfNoBorder">
    <panel name="PigTemplate"/>
    <widget source="Title" render="Label" position="780,45" size="1110,48" font="Regular;34" foregroundColor="secondFG" transparent="1"/>
    <widget source="name" render="Label" position="780,120" size="1110,55" font="Regular;34" foregroundColor="foreground" transparent="1"/>
    <widget source="task" render="Label" position="780,185" size="1110,48" font="Regular;29" foregroundColor="grey" transparent="1"/>
    <widget source="progress" render="Progress" position="780,265" size="1110,48" borderWidth="2" backgroundColor="un33333a"/>
    <widget source="progress" render="Label" position="780,267" size="1110,44" font="Regular;31" foregroundColor="foreground" halign="center" valign="center" transparent="1" zPosition="2"><convert type="ProgressToText"/></widget>
    <widget source="status" render="Label" position="780,340" size="1110,48" font="Regular;29" transparent="1"/>
    <widget name="config" position="780,420" size="1110,150" itemHeight="52" font="Regular;29" scrollbarMode="showOnDemand"/>
    <panel name="ButtonTemplate"/>
</screen>"""


def patch_help(data):
    match = screen_re("HelpMenu").search(data)
    if not match:
        return data
    old = match.group(0)
    list_match = re.search(r'<widget source="list".*?</widget>', old, re.S)
    list_xml = (
        list_match.group(0)
        if list_match
        else '<widget source="list" render="Listbox" position="30,105" size="1100,850" scrollbarMode="showOnDemand"/>'
    )
    list_xml = re.sub(r'\sconditional="indicatorU0"', "", list_xml)
    list_xml = re.sub(r'position="[^"]+"', 'position="30,105"', list_xml, count=1)
    list_xml = re.sub(r'size="[^"]+"', 'size="1100,850"', list_xml, count=1)

    indicators = []
    for index in range(16):
        for side in ("U", "L"):
            indicators.append(
                '    <widget name="indicator%s%d" pixmap="yellow_circle23x23.png" position="1450,330" size="23,23" zPosition="20" alphatest="blend"/>'
                % (side, index)
            )

    help_screen = """<screen name="HelpMenu" title="Help" position="fill" flags="wfNoBorder">
    <panel name="PigLessTemplate"/>
    <widget source="Title" render="Label" position="30,25" size="1830,55" font="Regular;38" foregroundColor="secondFG" transparent="1"/>
    %s
    <widget name="description" position="1165,115" size="695,125" font="Regular;27" foregroundColor="foreground" transparent="1" valign="top"/>
    <widget name="buttonlist" position="1165,250" size="695,80" font="Regular;24" foregroundColor="yellow" transparent="1" valign="top"/>
    <widget name="rc" position="1450,330" size="154,500" zPosition="10" alphatest="blend" transparent="1"/>
    <widget name="label" position="1165,850" size="695,80" font="Regular;23" foregroundColor="secondFG" transparent="1" halign="center" valign="center"/>
%s
    <widget source="key_help" render="Label" position="1690,980" size="170,45" font="Regular;24" foregroundColor="secondFG" halign="center" valign="center" transparent="1"><convert type="ConditionalShowHide"/></widget>
</screen>""" % (list_xml, "\n".join(indicators))
    return data[:match.start()] + help_screen + data[match.end():]


def patch(path):
    data = read(path)

    data = data.replace(
        "MultiContentEntryPixmapAlphaBlend(pos=(12, 4), size=(185, 80), png=3, flags=BT_SCALE),",
        "MultiContentEntryPixmapAlphaBlend(pos=(12, 4), size=(185, 80), png=3, flags=BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER),",
    )

    data = add_timelines(data, "GraphicalEPG", 385, 545)
    data = add_timelines(data, "GraphicalEPGPIG", 380, 365)
    data = add_timelines(data, "GraphicalInfoBarEPG", 112, 143)
    data = patch_vertical(data, "EPGvertical")
    data = patch_vertical(data, "EPGverticalPIG")

    match = screen_re("SkinSelection").search(data)
    if match:
        body = match.group(2)
        body = re.sub(
            r'<widget name="config"[^>]*/>',
            '<widget name="config" position="780,120" size="1080,610" itemHeight="58" font="Regular;30" transparent="1" enableWrapAround="1" scrollbarMode="showOnDemand" zPosition="3"/>',
            body,
            count=1,
        )
        body = re.sub(
            r'<widget name="description"[^>]*/>',
            '<widget name="description" position="780,748" size="1080,110" font="Regular;25" foregroundColor="foreground" transparent="1" valign="top" zPosition="3"/>',
            body,
            count=1,
        )
        body = re.sub(
            r'<widget name="footnote"[^>]*/>',
            '<widget name="footnote" position="780,868" size="1080,55" font="Regular;22" foregroundColor="secondFG" transparent="1" valign="top" zPosition="3"/>',
            body,
            count=1,
        )
        data = data[:match.start()] + match.group(1) + body + match.group(3) + data[match.end():]

    if not screen_re("TaskView").search(data):
        match = screen_re("JobView").search(data)
        if match:
            data = data[:match.start()] + TASK_VIEW + "\n\n" + data[match.start():]

    data = patch_help(data)
    data = data.replace('position="1550,1030" size="540,38"', 'position="1550,1030" size="340,38"')
    data = data.replace(
        'source="DNS1" render="Label" position="1640,675" size="300,37"',
        'source="DNS1" render="Label" position="1640,675" size="250,37"',
    )
    data = data.replace(
        'source="DNS2" render="Label" position="1640,720" size="300,37"',
        'source="DNS2" render="Label" position="1640,720" size="250,37"',
    )
    data = data.replace(
        'source="session.CurrentService" render="Label" position="450,250" size="1620,800"',
        'source="session.CurrentService" render="Label" position="450,250" size="1420,800"',
    )
    data = data.replace('pixmap="icons/no_coverArt.png"', 'pixmap="dvr/no_coverArt.png"')
    data = data.replace(
        'pixmap="icons/icon_view.png"',
        'pixmap="/usr/share/enigma2/skin_default/icons/icon_view.png"',
    )

    ET.fromstring(data)
    write(path, data)
    return True


if __name__ == "__main__":
    patch(sys.argv[1])
    print("CINEVIEW_OPENATV_AUDITFIX_OK")
