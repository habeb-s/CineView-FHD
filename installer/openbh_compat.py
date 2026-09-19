# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import os
import re
import sys

SCREEN_RE = r'\n?[ \t]*<screen\b(?=[^>]*\bname=["\']%s["\'])[^>]*>.*?</screen>[ \t]*\n?'

# OpenBH quick-plugin icons are always scaled to their slot.
# Current OpenBH 6.0 classes intentionally fall back to these legacy skin names.
# Do NOT create the modern aliases below: if present they take precedence and can
# bypass the proven OpenBH layouts.
REMOVE_ALIASES = (
    "SingleEPG", "InfobarSingleEPG", "MultiEPG",
    "GridEPG", "GridEPGPIG", "InfoBarGridEPG",
    "ExtensionsList", "EPGExtensionsList",
)

def _read(path):
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _write(path, data):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(data)

def _remove_screen(data, name):
    return re.sub(SCREEN_RE % re.escape(name), "\n", data, flags=re.S)

def _normalise_math(data):
    pat = re.compile(r'((?:size|position)=["\'][^"\']*?)(\d+)\*(\d+)([^"\']*["\'])')
    while True:
        data2, n = pat.subn(lambda m: m.group(1) + str(int(m.group(2)) * int(m.group(3))) + m.group(4), data)
        data = data2
        if not n:
            return data


def _stretch_second_infobar(data, name):
    """Preserve OpenBH's native SecondInfoBar widgets, but make the panel edge-to-edge."""
    pat = re.compile(SCREEN_RE % re.escape(name), re.S)
    m = pat.search(data)
    if not m:
        return data

    block = m.group(0)
    head = re.search(r'<screen\b[^>]*>', block)
    if not head:
        return data
    headtxt = head.group(0)

    sm = re.search(r'\bsize=["\'](\d+),(\d+)["\']', headtxt)
    if sm:
        old_w, old_h = int(sm.group(1)), int(sm.group(2))
    else:
        old_w, old_h = 1920, 520

    newhead = headtxt
    if sm:
        newhead = re.sub(r'\bsize=["\'][^"\']+["\']', 'size="1920,%d"' % old_h, newhead, count=1)
    else:
        newhead = newhead[:-1] + ' size="1920,%d">' % old_h

    pm = re.search(r'\bposition=["\']([^"\']+)["\']', newhead)
    if pm:
        pos = pm.group(1)
        if re.match(r'^\d+,\d+$', pos):
            y = pos.split(',', 1)[1]
            newhead = re.sub(r'\bposition=["\'][^"\']+["\']', 'position="0,%s"' % y, newhead, count=1)
        elif pos == "center,center":
            y = max(0, (1080 - old_h) // 2)
            newhead = re.sub(r'\bposition=["\'][^"\']+["\']', 'position="0,%d"' % y, newhead, count=1)
    else:
        y = max(0, (1080 - old_h) // 2)
        newhead = newhead[:-1] + ' position="0,%d">' % y

    block = block[:head.start()] + newhead + block[head.end():]
    delta = 1920 - old_w

    def stretch_tag(mt):
        tag = mt.group(0)
        pm2 = re.search(r'position=["\'](\d+),(\d+)["\']', tag)
        sm2 = re.search(r'size=["\'](\d+),(\d+)["\']', tag)
        if not pm2 or not sm2:
            return tag
        x, y = int(pm2.group(1)), int(pm2.group(2))
        w, h = int(sm2.group(1)), int(sm2.group(2))
        nx, nw = x, w

        if x <= 55 and w >= old_w - 110:
            nx, nw = 0, 1920
        elif delta:
            if x >= int(old_w * 0.68) and w < int(old_w * 0.45):
                nx = x + delta
            elif x < int(old_w * 0.68) and (x + w) >= old_w - 30:
                nw = w + delta

        tag = re.sub(r'position=["\']\d+,\d+["\']', 'position="%d,%d"' % (nx, y), tag, count=1)
        tag = re.sub(r'size=["\']\d+,\d+["\']', 'size="%d,%d"' % (nw, h), tag, count=1)
        return tag

    block = re.sub(r'<(?:eLabel|widget)\b[^>]*>', stretch_tag, block)

    bgm = re.search(r'backgroundColor=["\']([^"\']+)["\']', block)
    bg = bgm.group(1) if bgm else "steThemePrimary"
    full_bg = '<eLabel position="0,0" size="1920,%d" backgroundColor="%s" zPosition="0"/>' % (old_h, bg)
    first_close = block.find('>')
    if first_close >= 0 and full_bg not in block:
        block = block[:first_close + 1] + "\n\t\t" + full_bg + block[first_close + 1:]

    return data[:m.start()] + block + data[m.end():]



def _extend_infobar_edges(data, name, second=False):
    """Keep CineView InfoBars slightly inset from the physical screen edges."""
    pat = re.compile(SCREEN_RE % re.escape(name), re.S)
    m = pat.search(data)
    if not m:
        return data
    block = m.group(0)

    # Bottom technical bar: restore the approved small side/bottom margin.
    block = block.replace('position="0,842" size="1920,238"', 'position="24,842" size="1872,236"')
    block = block.replace('position="0,842" size="1920,2"', 'position="24,842" size="1872,2"')
    block = block.replace('position="0,1078" size="1920,2"', 'position="24,1076" size="1872,2"')
    block = block.replace('position="0,842" size="2,238"', 'position="24,842" size="2,236"')
    block = block.replace('position="1918,842" size="2,238"', 'position="1894,842" size="2,236"')

    if second:
        # Keep the approved Now/Next composition and only pull it slightly
        # away from the outer edges, preserving the centre gap and content.
        block = block.replace('position="0,145" size="860,440"', 'position="35,145" size="825,440"')
        block = block.replace('position="925,145" size="995,440"', 'position="925,145" size="960,440"')

    return data[:m.start()] + block + data[m.end():]

def _screen(name, body, position="center,center", size="1820,880", title=""):
    t = (' title="%s"' % title) if title else ""
    bg = ' backgroundColor="transparent"' if name in ("SecondInfoBar", "SecondInfoBarECM") else ""
    return '\n\t<screen name="%s" position="%s" size="%s" flags="wfNoBorder"%s%s>\n%s\n\t</screen>\n' % (
        name, position, size, t, bg, body)

CHOICEBOX = """\t\t<eLabel position="0,0" size="1100,800" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="text" position="25,20" size="1050,150" font="Regular;30" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="2"/>
\t\t<widget name="list" position="25,185" size="1050,520" font="Regular;30" itemHeight="52" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="3"/>
\t\t<widget name="description" position="25,720" size="1050,55" font="Regular;23" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="2"/>"""

PLUGIN_BROWSER = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="list" position="55,55" size="1710,690" itemHeight="72" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="5"/>
\t\t<eLabel position="45,770" size="1730,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="key_red" position="70,795" size="410,48" font="Regular;29" halign="center" valign="center" transparent="1" foregroundColor="foreground" zPosition="6"/>
\t\t<widget name="key_green" position="500,795" size="410,48" font="Regular;29" halign="center" valign="center" transparent="1" foregroundColor="foreground" zPosition="6"/>
\t\t<widget name="key_yellow" position="930,795" size="410,48" font="Regular;29" halign="center" valign="center" transparent="1" foregroundColor="foreground" zPosition="6"/>
\t\t<widget name="key_0" position="1360,795" size="80,48" font="Regular;26" halign="center" valign="center" transparent="1" foregroundColor="grey" zPosition="6"/>
\t\t<widget name="key_previous" position="1450,795" size="140,48" font="Regular;22" halign="center" valign="center" transparent="1" foregroundColor="grey" zPosition="6"/>
\t\t<widget name="key_next" position="1600,795" size="140,48" font="Regular;22" halign="center" valign="center" transparent="1" foregroundColor="grey" zPosition="6"/>"""

SINGLE_EPG = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel position="1195,0" size="2,785" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="lab1" position="35,35" size="1120,720" font="Regular;28" halign="center" valign="center" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="20"/>
\t\t<widget name="list" position="35,35" size="1120,720" itemHeight="50" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="10"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1510,35" size="260,390" zPosition="18"/>
\t\t<widget source="Event" render="Label" position="1230,35" size="250,120" font="Regular;30" foregroundColor="foreground" transparent="1" zPosition="12"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1230,170" size="250,45" font="Regular;24" foregroundColor="secondFG" transparent="1" zPosition="12"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Default</convert></widget>
\t\t<widget source="Event" render="Label" position="1230,230" size="540,500" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top" zPosition="12"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="35,780" size="1735,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="key_red" position="55,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_green" position="490,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_yellow" position="925,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_blue" position="1360,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>"""

MULTI_EPG = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel position="1195,0" size="2,785" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="date" position="1280,35" size="420,42" font="Regular;30" halign="center" foregroundColor="foreground" transparent="1" zPosition="10"/>
\t\t<widget name="now_button" position="35,35" size="370,50" transparent="1" zPosition="2"/>
\t\t<widget name="now_button_sel" pixmap="border/epg_now_on.png" position="35,35" size="370,50" alphatest="blend" zPosition="3"/>
\t\t<widget name="now_text" position="35,35" size="370,50" text="NOW" font="Regular;28" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="next_button" position="410,35" size="370,50" transparent="1" zPosition="2"/>
\t\t<widget name="next_button_sel" pixmap="border/epg_next_on.png" position="410,35" size="370,50" alphatest="blend" zPosition="3"/>
\t\t<widget name="next_text" position="410,35" size="370,50" text="NEXT" font="Regular;28" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="more_button" position="785,35" size="370,50" transparent="1" zPosition="2"/>
\t\t<widget name="more_button_sel" pixmap="border/epg_next_on.png" position="785,35" size="370,50" alphatest="blend" zPosition="3"/>
\t\t<widget name="more_text" position="785,35" size="370,50" text="MORE" font="Regular;28" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="lab1" position="35,105" size="1120,650" font="Regular;28" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="20"/>
\t\t<widget name="list" position="35,105" size="1120,650" itemHeight="45" setEventItemFont="Regular;28" setEventTimeFont="Regular;24" setColWidths="365,170" setColGap="20" setTimeWidth="135" setIconDistance="10" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="10"/>
\t\t<widget name="bouquetlist" position="35,105" size="1120,650" itemHeight="45" font="Regular;28" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="0" zPosition="30"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1510,100" size="260,390" zPosition="18"/>
\t\t<widget source="Event" render="Label" position="1230,100" size="250,100" font="Regular;30" foregroundColor="foreground" transparent="1" zPosition="12"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1230,220" size="540,500" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top" zPosition="12"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="35,780" size="1735,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="key_red" position="55,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_green" position="490,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_yellow" position="925,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_blue" position="1360,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>"""

SECOND_INFO_OPENBH = """\n<!-- Enlarged event panels: raised to keep clear of the lower controls. -->
    <eLabel position="0,145" size="860,440" backgroundColor="steSecondInfoBG" zPosition="2"/>
    <eLabel position="925,145" size="995,440" backgroundColor="steSecondInfoBG" zPosition="2"/>
    <widget source="session.Event_Now" render="RunningText" position="95,165" size="480,42" transparent="1" zPosition="12" foregroundColor="secondFG" font="Regular;31" noWrap="1" options="movetype=running,direction=left,step=2,steptime=50,startdelay=1600,pause=900,repeat=0,always=0"><convert type="EventName">Name</convert></widget>
    <widget source="session.Event_Now" render="RunningText" position="95,220" size="480,295" transparent="1" zPosition="12" foregroundColor="foreground" font="Regular;25" halign="block" options="movetype=running,direction=top,step=2,steptime=65,startdelay=2200,pause=1700,repeat=0,always=0,wrap=1"><convert type="EventName">FullDescription</convert></widget>
    <widget source="session.Event_Now" render="CineViewPosterX" position="612,180" size="205,308" zPosition="18" nexts="0"/>
    <widget source="session.Event_Now" render="Label" position="95,535" size="160,30" transparent="1" zPosition="12" font="Regular;22" foregroundColor="grey"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <widget source="session.Event_Now" render="Label" position="415,535" size="160,30" transparent="1" zPosition="12" font="Regular;22" foregroundColor="grey" halign="right"><convert type="EventTime">EndTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>

    <widget source="session.Event_Next" render="RunningText" position="950,165" size="580,42" transparent="1" zPosition="12" foregroundColor="secondFG" font="Regular;31" noWrap="1" options="movetype=running,direction=left,step=2,steptime=50,startdelay=1600,pause=900,repeat=0,always=0"><convert type="EventName">Name</convert></widget>
    <widget source="session.Event_Next" render="RunningText" position="950,220" size="580,295" transparent="1" zPosition="12" foregroundColor="foreground" font="Regular;25" halign="block" options="movetype=running,direction=top,step=2,steptime=65,startdelay=2200,pause=1700,repeat=0,always=0,wrap=1"><convert type="EventName">FullDescription</convert></widget>
    <widget source="session.Event_Now" render="CineViewPosterX" position="1575,180" size="205,308" zPosition="18" nexts="1"/>
    <widget source="session.Event_Next" render="Label" position="950,535" size="160,30" transparent="1" zPosition="12" font="Regular;22" foregroundColor="grey"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <widget source="session.Event_Next" render="Label" position="1370,535" size="160,30" transparent="1" zPosition="12" font="Regular;22" foregroundColor="grey" halign="right"><convert type="EventTime">EndTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>

    <!-- Same technical bar as primary InfoBar, aligned to bottom edge. No ButtonTemplate here. -->
    <eLabel position="0,842" size="1920,238" backgroundColor="steSecondInfoBG" zPosition="5"/>
    <eLabel position="0,842" size="1920,2" backgroundColor="#007c7c7c" zPosition="6"/>
    <eLabel position="0,1078" size="1920,2" backgroundColor="#007c7c7c" zPosition="6"/>
    <eLabel position="0,842" size="2,238" backgroundColor="#007c7c7c" zPosition="6"/>
    <eLabel position="1918,842" size="2,238" backgroundColor="#007c7c7c" zPosition="6"/>
    <widget source="session.Event_Now" render="CineViewPosterX" position="40,850" size="105,158" zPosition="20"/>
    <eLabel position="156,852" size="2,154" backgroundColor="#00444444" zPosition="8"/>
    <widget source="session.CurrentService" render="Picon" mode="infobar" scale="aspect" position="200,852" size="200,110" alphatest="blend" transparent="1" zPosition="20"><convert type="ServiceName">Reference</convert></widget>
    <widget source="session.CurrentService" render="RunningText" position="170,966" size="260,28" transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;21" noWrap="1" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1600,pause=1000,repeat=0,always=0"><convert type="ServiceName">NameOnly</convert></widget>
    <widget source="session.CurrentService" render="ChannelNumber" position="170,994" size="50,20" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;16"/>
    <widget source="session.CurrentService" render="RunningText" position="225,994" size="205,20" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;16" noWrap="1" options="movetype=running,direction=left,step=2,steptime=60,startdelay=1500,pause=1000,repeat=0,always=0"><convert type="ServiceName">Provider</convert></widget>

    <eLabel position="446,852" size="2,154" backgroundColor="#00444444" zPosition="8"/>
    <widget source="session.CurrentService" render="Label" position="464,850" size="340,72" transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;18" valign="center"><convert type="CineViewTransponderInfo">TransponderInfo</convert></widget>
    <widget source="session.CurrentService" render="Label" position="464,928" size="98,30" transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;18"><convert type="ServiceOrbitalPosition"/></widget>
    <widget source="session.CurrentService" render="Label" position="566,928" size="238,30" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;18" noWrap="1"><convert type="ServiceName">Provider</convert></widget>
    <eLabel position="812,852" size="2,154" backgroundColor="#00444444" zPosition="8"/>
    <widget source="session.CurrentService" render="RunningText" position="830,858" size="225,140" transparent="1" zPosition="20" foregroundColor="#0044dd44" font="Regular;17" valign="top" options="movetype=swimming,direction=top,step=1,steptime=70,startdelay=2200,pause=1400,repeat=0,always=0"><convert type="CineViewCamInfo">Info</convert></widget>

    <eLabel position="1072,852" size="2,154" backgroundColor="#00444444" zPosition="8"/>
    <widget source="session.Event_Now" render="RunningText" position="1090,854" size="520,38" transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;27" noWrap="1" options="movetype=running,direction=left,step=2,steptime=50,startdelay=1500,pause=1000,repeat=0,always=0"><convert type="EventName">Name</convert></widget>
    <widget source="session.Event_Now" render="Label" position="1620,856" size="110,28" transparent="1" zPosition="20" font="Regular;19" halign="right"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <widget source="session.Event_Now" render="Label" position="1740,856" size="125,28" transparent="1" zPosition="20" font="Regular;19" halign="right"><convert type="EventTime">EndTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <widget source="session.Event_Now" render="Progress" position="1090,900" size="775,7" pixmap="infobar/pbar.png" backgroundColor="un33333a" zPosition="20"><convert type="EventTime">Progress</convert></widget>
    <widget source="session.Event_Next" render="RunningText" position="1090,924" size="520,34" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;23" noWrap="1" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1700,pause=1000,repeat=0,always=0"><convert type="EventName">Name</convert></widget>
    <widget source="session.Event_Next" render="Label" position="1620,926" size="110,27" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;18" halign="right"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <widget source="session.Event_Next" render="Label" position="1740,926" size="125,27" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;18" halign="right"><convert type="EventTime">EndTime</convert><convert type="ClockToText">Format:%H:%M</convert></widget>
    <ePixmap pixmap="infobar/imdb_badge.png" position="1600,968" size="76,28" zPosition="21" alphatest="blend"/>
    <widget source="session.Event_Now" render="Label" position="1684,969" size="82,27" transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;18"><convert type="CineViewIMDb">Plain</convert></widget>
    <widget source="session.Event_Now" render="Label" position="1768,969" size="100,27" transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;17"><convert type="CineViewIMDb">Stars</convert></widget>

    <eLabel position="36,1016" size="1848,2" backgroundColor="#00444444" zPosition="8"/>
    <eLabel text="SNR:" position="40,1030" size="55,28" transparent="1" zPosition="20" font="Regular;19"/>
    <widget source="session.FrontendStatus" render="Label" position="94,1030" size="70,28" transparent="1" zPosition="20" font="Regular;19"><convert type="FrontendInfo">SNR</convert></widget>
    <widget source="session.FrontendStatus" render="Progress" position="165,1038" size="160,10" pixmap="window/progress.png" backgroundColor="un33333a" zPosition="20"><convert type="FrontendInfo">SNR</convert></widget>
    <eLabel text="dB:" position="338,1030" size="37,28" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;19"/>
    <widget source="session.FrontendStatus" render="Label" position="377,1030" size="105,28" transparent="1" zPosition="20" foregroundColor="secondFG" font="Regular;19"><convert type="FrontendInfo">SNRdB</convert></widget>
    <eLabel text="AGC" position="487,1030" size="42,28" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;18"/>
    <widget source="session.FrontendStatus" render="Label" position="531,1030" size="75,28" transparent="1" zPosition="20" font="Regular;18"><convert type="FrontendInfo">AGC</convert></widget>
    <eLabel text="BER" position="612,1030" size="42,28" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;18"/>
    <widget source="session.FrontendStatus" render="Label" position="657,1030" size="70,28" transparent="1" zPosition="20" font="Regular;18"><convert type="FrontendInfo">BER</convert></widget>
    <widget source="session.CurrentService" render="Label" position="735,1030" size="108,28" transparent="1" zPosition="20" font="Regular;18"><convert type="ServiceOrbitalPosition"/></widget>
    <widget render="VideoSize" source="session.CurrentService" position="848,1030" size="155,28" font="Regular;18" transparent="1" zPosition="20"/>
    <widget source="session.CurrentService" render="Pixmap" pixmap="infobar/ico_format_hd.png" position="1008,1027" size="60,32" zPosition="22" alphatest="on"><convert type="ServiceInfo">IsHD</convert><convert type="ConditionalShowHide"/></widget>
    <widget source="session.CurrentService" render="Pixmap" pixmap="infobar/ico_format_4k.png" position="1008,1027" size="60,32" zPosition="23" alphatest="on"><convert type="ServiceInfo">Is4K</convert><convert type="ConditionalShowHide"/></widget>
    <widget source="session.CurrentService" render="Label" position="1077,1030" size="132,28" transparent="1" zPosition="24" foregroundColor="secondFG" font="Regular;18"><convert type="CineViewCPUTemp">Short</convert></widget>
    <widget source="session.CurrentService" render="Pixmap" pixmap="infobar/ico_format_16_9.png" position="1216,1027" size="60,32" zPosition="22" alphatest="on"><convert type="ServiceInfo">IsWidescreen</convert><convert type="ConditionalShowHide"/></widget>
    <widget source="session.CurrentService" render="Pixmap" pixmap="infobar/ico_dolby_on.png" position="1280,1027" size="50,32" zPosition="22" alphatest="on"><convert type="ServiceInfo">IsMultichannel</convert><convert type="ConditionalShowHide"/></widget>
    <widget source="session.CurrentService" render="Pixmap" pixmap="infobar/ico_hbbtv_on.png" position="1336,1027" size="70,32" zPosition="22" alphatest="on"><convert type="ServiceInfo">HasHBBTV</convert><convert type="ConditionalShowHide"/></widget>
    <widget source="session.CurrentService" render="Pixmap" pixmap="infobar/ico_txt_on.png" position="1410,1027" size="44,32" zPosition="22" alphatest="on"><convert type="ServiceInfo">HasTelext</convert><convert type="ConditionalShowHide"/></widget>
    <eLabel text="Bitrate:" position="1464,1030" size="72,28" transparent="1" zPosition="20" foregroundColor="grey" font="Regular;18"/>
    <widget source="session.CurrentService" render="Label" position="1538,1030" size="120,28" transparent="1" zPosition="20" foregroundColor="foreground" font="Regular;18"><convert type="CineViewBitrate">Mbps</convert></widget>
    <widget source="session.OAWeather" render="OAWeatherPixmap" position="1668,1025" size="34,34" transparent="1" zPosition="24" alphatest="blend"><convert type="OAWeather">weathericon,current</convert></widget>
    <widget source="session.OAWeather" render="RunningText" position="1708,1030" size="105,28" transparent="1" zPosition="24" foregroundColor="foreground" font="Regular;18" noWrap="1" options="movetype=running,direction=left,step=2,steptime=65,startdelay=1800,pause=1200,repeat=0,always=0"><convert type="OAWeather">city</convert></widget>
    <widget source="session.OAWeather" render="Label" position="1815,1030" size="66,28" transparent="1" zPosition="24" foregroundColor="secondFG" font="Regular;18" halign="right"><convert type="OAWeather">temperature_current</convert></widget>
"""

GRID_EPG = """\t\t<eLabel position="0,0" size="1880,1000" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel position="25,20" size="1830,300" backgroundColor="steThemeOverlay" zPosition="1"/>
\t\t<widget source="Event" render="CineViewPosterX" position="45,35" size="185,278" zPosition="18"/>
\t\t<widget source="Event" render="RunningText" position="260,38" size="1570,48" font="Regular;32" foregroundColor="secondFG" backgroundColor="steThemeOverlay" transparent="1" noWrap="1" zPosition="12" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1200,pause=900,repeat=0,always=0"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="260,98" size="420,38" font="Regular;25" foregroundColor="grey" backgroundColor="steThemeOverlay" transparent="1" zPosition="12"><convert type="EventTime">StartTime</convert><convert type="ClockToText">Default</convert></widget>
\t\t<widget source="Event" render="Label" position="690,98" size="420,38" font="Regular;25" foregroundColor="grey" backgroundColor="steThemeOverlay" transparent="1" zPosition="12"><convert type="EventTime">EndTime</convert><convert type="ClockToText">Format:- %H:%M</convert></widget>
\t\t<widget source="Event" render="RunningText" position="260,148" size="1570,145" font="Regular;24" foregroundColor="foreground" backgroundColor="steThemeOverlay" transparent="1" zPosition="12" options="movetype=running,direction=top,step=1,steptime=70,startdelay=2000,pause=1400,repeat=0,always=0"><convert type="EventName">ExtendedDescription</convert></widget>
\t\t<widget name="timeline_text" position="45,340" size="1790,42" itemHeight="42" font="Regular;26" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="10"/>
\t\t<widget name="timeline0" position="45,340" size="2,42" zPosition="11"/>
\t\t<widget name="timeline1" position="45,340" size="2,42" zPosition="11"/>
\t\t<widget name="timeline2" position="45,340" size="2,42" zPosition="11"/>
\t\t<widget name="timeline3" position="45,340" size="2,42" zPosition="11"/>
\t\t<widget name="timeline4" position="45,340" size="2,42" zPosition="11"/>
\t\t<widget name="timeline5" position="45,340" size="2,42" zPosition="11"/>
\t\t<widget name="lab1" position="45,392" size="1790,475" font="Regular;28" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="20"/>
\t\t<widget name="list" position="45,392" size="1790,475" itemHeight="59" Wrap="1" EntryFontWrap="no" ServiceFont="Regular;27" foregroundColor="foreground" backgroundColor="steThemePrimary" ServiceForegroundColorNow="secondFG" ServiceBackgroundColor="steThemePrimary" ServiceBackgroundColorNow="steThemeOverlay" ServiceBackgroundColorSelected="selectedBG" EntryBackgroundColorNow="steThemeOverlay" EntryForegroundColorNowSelected="selectedFG" EntryBackgroundColorNowSelected="selectedBG" EntryBackgroundColor="steThemePrimary" EntryForegroundColorSelected="selectedFG" EntryBackgroundColorSelected="selectedBG" transparent="1" scrollbarMode="showNever" EventNamePadding="6" ServiceNamePadding="6" ServiceBorderVerWidth="2" EventBorderVerWidth="2" zPosition="10"/>
\t\t<widget name="timeline_now" position="45,392" size="3,475" zPosition="21"/>
\t\t<widget name="bouquetlist" position="45,392" size="1790,475" itemHeight="59" font="Regular;28" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="0" zPosition="30"/>
\t\t<eLabel position="35,892" size="1810,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="key_red" position="55,918" size="400,48" font="Regular;28" halign="center" valign="center" transparent="1"/>
\t\t<widget name="key_green" position="490,918" size="400,48" font="Regular;28" halign="center" valign="center" transparent="1"/>
\t\t<widget name="key_yellow" position="925,918" size="400,48" font="Regular;28" halign="center" valign="center" transparent="1"/>
\t\t<widget name="key_blue" position="1360,918" size="400,48" font="Regular;28" halign="center" valign="center" transparent="1"/>"""

GRID_COMMON = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel position="1195,0" size="2,785" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="timeline_text" position="35,35" size="1120,42" itemHeight="42" font="Regular;26" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="10"/>
\t\t<widget name="timeline0" position="35,35" size="2,42" zPosition="11"/>
\t\t<widget name="timeline1" position="35,35" size="2,42" zPosition="11"/>
\t\t<widget name="timeline2" position="35,35" size="2,42" zPosition="11"/>
\t\t<widget name="timeline3" position="35,35" size="2,42" zPosition="11"/>
\t\t<widget name="timeline4" position="35,35" size="2,42" zPosition="11"/>
\t\t<widget name="timeline5" position="35,35" size="2,42" zPosition="11"/>
\t\t<widget name="lab1" position="35,90" size="1120,665" font="Regular;28" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="20"/>
\t\t<widget name="list" position="35,90" size="1120,665" itemHeight="70" Wrap="1" EntryFontWrap="no" ServiceFont="Regular;27" foregroundColor="foreground" backgroundColor="steThemePrimary" ServiceForegroundColorNow="secondFG" ServiceBackgroundColor="steThemePrimary" ServiceBackgroundColorNow="steThemeOverlay" ServiceBackgroundColorSelected="selectedBG" EntryBackgroundColorNow="steThemeOverlay" EntryForegroundColorNowSelected="selectedFG" EntryBackgroundColorNowSelected="selectedBG" EntryBackgroundColor="steThemePrimary" EntryForegroundColorSelected="selectedFG" EntryBackgroundColorSelected="selectedBG" transparent="1" scrollbarMode="showNever" EventNamePadding="6" ServiceNamePadding="6" ServiceBorderVerWidth="2" EventBorderVerWidth="2" zPosition="10"/>
\t\t<widget name="timeline_now" position="35,90" size="3,665" zPosition="21"/>
\t\t<widget name="bouquetlist" position="35,90" size="1120,665" itemHeight="45" font="Regular;28" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="0" zPosition="30"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1510,35" size="260,390" zPosition="18"/>
\t\t<widget source="Event" render="Label" position="1230,35" size="250,105" font="Regular;30" foregroundColor="foreground" transparent="1" zPosition="12"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1230,165" size="540,565" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top" zPosition="12"><convert type="EventName">ExtendedDescription</convert></widget>
\t\t<eLabel position="35,780" size="1735,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="key_red" position="55,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_green" position="490,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_yellow" position="925,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>
\t\t<widget name="key_blue" position="1360,805" size="400,45" font="Regular;28" halign="center" transparent="1"/>"""

GRID_PIG = """\t\t<eLabel position="1205,20" size="565,320" backgroundColor="black" zPosition="13"/>
\t\t<widget source="session.VideoPicture" render="Pig" position="1220,35" size="535,290" backgroundColor="black" zPosition="14"/>\n""" + GRID_COMMON

QUICK_EPG = """\t\t<eLabel position="0,0" size="1920,420" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="lab1" position="55,70" size="800,230" font="Regular;28" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="20"/>
\t\t<widget name="list" position="55,70" size="800,230" itemHeight="50" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="1" zPosition="10"/>
\t\t<widget name="bouquetlist" position="55,70" size="800,230" itemHeight="50" font="Regular;27" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="0" zPosition="30"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1580,25" size="190,285" zPosition="18"/>
\t\t<widget source="Event" render="Label" position="900,55" size="640,60" font="Regular;30" foregroundColor="foreground" transparent="1" zPosition="12"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="900,125" size="640,175" font="Regular;24" foregroundColor="foreground" transparent="1" valign="top" zPosition="12"><convert type="EventName">FullDescription</convert></widget>
\t\t<eLabel position="45,320" size="1810,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="key_red" position="55,340" size="400,45" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget name="key_green" position="490,340" size="400,45" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget name="key_yellow" position="925,340" size="400,45" font="Regular;27" halign="center" transparent="1"/>
\t\t<widget name="key_blue" position="1360,340" size="400,45" font="Regular;27" halign="center" transparent="1"/>"""

INFOBAR_GRID = """\t\t<eLabel position="0,0" size="1920,325" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="timeline_text" position="55,35" size="1810,38" itemHeight="38" font="Regular;25" foregroundColor="foreground" transparent="1" zPosition="10"/>
\t\t<widget name="timeline0" position="55,35" size="2,38" zPosition="11"/>
\t\t<widget name="timeline1" position="55,35" size="2,38" zPosition="11"/>
\t\t<widget name="timeline2" position="55,35" size="2,38" zPosition="11"/>
\t\t<widget name="timeline3" position="55,35" size="2,38" zPosition="11"/>
\t\t<widget name="timeline4" position="55,35" size="2,38" zPosition="11"/>
\t\t<widget name="timeline5" position="55,35" size="2,38" zPosition="11"/>
\t\t<widget name="lab1" position="55,82" size="1810,115" font="Regular;27" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="20"/>
\t\t<widget name="list" position="55,82" size="1810,115" itemHeight="55" Wrap="1" EntryFontWrap="no" ServiceFont="Regular;25" foregroundColor="foreground" backgroundColor="steThemePrimary" ServiceForegroundColorNow="secondFG" ServiceBackgroundColor="steThemePrimary" ServiceBackgroundColorNow="steThemeOverlay" ServiceBackgroundColorSelected="selectedBG" EntryBackgroundColorNow="steThemeOverlay" EntryForegroundColorNowSelected="selectedFG" EntryBackgroundColorNowSelected="selectedBG" EntryBackgroundColor="steThemePrimary" EntryForegroundColorSelected="selectedFG" EntryBackgroundColorSelected="selectedBG" transparent="1" scrollbarMode="showNever" zPosition="10"/>
\t\t<widget name="timeline_now" position="55,82" size="3,115" zPosition="21"/>
\t\t<widget name="bouquetlist" position="55,82" size="1810,115" itemHeight="40" font="Regular;25" enableWrapAround="1" scrollbarMode="showNever" foregroundColor="foreground" backgroundColor="steThemePrimary" foregroundColorSelected="selectedFG" backgroundColorSelected="selectedBG" transparent="0" zPosition="30"/>
\t\t<eLabel position="45,220" size="1810,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="key_red" position="55,240" size="400,42" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget name="key_green" position="490,240" size="400,42" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget name="key_yellow" position="925,240" size="400,42" font="Regular;26" halign="center" transparent="1"/>
\t\t<widget name="key_blue" position="1360,240" size="400,42" font="Regular;26" halign="center" transparent="1"/>"""


EVENT_VIEW = """\t\t<eLabel position="0,0" size="1820,880" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="channel" position="45,30" size="1120,45" font="Regular;32" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="5"/>
\t\t<widget name="epg_eventname" position="45,88" size="1120,70" font="Regular;38" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="5"/>
\t\t<widget name="datetime" position="45,175" size="680,38" font="Regular;27" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="5"/>
\t\t<widget name="duration" position="750,175" size="415,38" font="Regular;27" halign="right" foregroundColor="grey" backgroundColor="steThemePrimary" transparent="1" zPosition="5"/>
\t\t<eLabel position="45,225" size="1120,2" backgroundColor="steThemePanelAlt" zPosition="3"/>
\t\t<widget name="FullDescription" position="45,250" size="1120,505" font="Regular;29" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="5"/>
\t\t<eLabel position="1200,25" size="575,730" backgroundColor="steThemeOverlay" zPosition="2"/>
\t\t<widget source="Event" render="CineViewPosterX" position="1310,65" size="355,532" zPosition="8"/>
\t\t<widget source="Event" render="Label" position="1230,620" size="515,80" font="Regular;27" halign="center" valign="center" foregroundColor="foreground" backgroundColor="steThemeOverlay" transparent="1" zPosition="8"><convert type="EventName">Name</convert></widget>
\t\t<eLabel position="35,780" size="1750,2" backgroundColor="steThemePanelAlt" zPosition="3"/>
\t\t<widget name="red" position="50,800" size="390,50" transparent="1" zPosition="4"/>
\t\t<widget name="green" position="485,800" size="390,50" transparent="1" zPosition="4"/>
\t\t<widget name="yellow" position="920,800" size="390,50" transparent="1" zPosition="4"/>
\t\t<widget name="blue" position="1355,800" size="390,50" transparent="1" zPosition="4"/>
\t\t<eLabel position="50,800" size="390,50" backgroundColor="#00a00000" zPosition="3"/>
\t\t<eLabel position="485,800" size="390,50" backgroundColor="#00008000" zPosition="3"/>
\t\t<eLabel position="920,800" size="390,50" backgroundColor="#00a08000" zPosition="3"/>
\t\t<eLabel position="1355,800" size="390,50" backgroundColor="#000040a0" zPosition="3"/>
\t\t<widget name="key_red" position="60,803" size="370,44" font="Regular;27" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="6"/>
\t\t<widget name="key_green" position="495,803" size="370,44" font="Regular;27" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="6"/>
\t\t<widget name="key_yellow" position="930,803" size="370,44" font="Regular;27" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="6"/>
\t\t<widget name="key_blue" position="1365,803" size="370,44" font="Regular;27" halign="center" valign="center" foregroundColor="foreground" transparent="1" zPosition="6"/>"""

GREEN_PANEL = """\t\t<eLabel position="0,0" size="1500,850" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel text="OpenBH Green Panel" position="45,25" size="1410,55" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<eLabel position="35,92" size="1430,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="list" render="Listbox" position="45,115" size="1410,595" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="5">
\t\t\t<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryText(pos = (130, 5), size = (1180, 38), font=0, text = 0),
MultiContentEntryText(pos = (130, 43), size = (1180, 30), font=1, text = 1),
MultiContentEntryPixmapAlphaTest(pos = (10, 20), size = (100, 40), png = 2, flags = BT_SCALE)
],
"fonts": [gFont("Regular", 31), gFont("Regular", 23)],
"itemHeight": 80
}
\t\t\t</convert>
\t\t</widget>
\t\t<eLabel position="35,735" size="1430,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<eLabel position="50,760" size="330,55" backgroundColor="#00a00000" zPosition="2"/>
\t\t<eLabel position="405,760" size="330,55" backgroundColor="#00008000" zPosition="2"/>
\t\t<eLabel position="760,760" size="330,55" backgroundColor="#00a08000" zPosition="2"/>
\t\t<eLabel position="1115,760" size="330,55" backgroundColor="#000040a0" zPosition="2"/>
\t\t<widget name="key_red" position="60,765" size="310,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="key_green" position="415,765" size="310,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="key_yellow" position="770,765" size="310,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="key_blue" position="1125,765" size="310,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>"""

BLUE_PANEL = """\t\t<eLabel position="0,0" size="1500,850" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel text="OpenBH Blue Panel" position="45,25" size="1410,55" font="Regular;38" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<eLabel position="35,92" size="1430,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="lab1" position="45,112" size="360,38" font="Regular;27" foregroundColor="foreground" transparent="1" zPosition="4"/>
\t\t<widget name="list" position="420,108" size="610,48" font="Regular;29" itemHeight="48" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemeOverlay" transparent="1" zPosition="4"/>
\t\t<widget name="lab2" position="1050,112" size="380,38" font="Regular;26" halign="center" foregroundColor="grey" transparent="1" zPosition="4"/>
\t\t<eLabel position="35,175" size="1430,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="lab3" position="45,195" size="200,38" font="Regular;27" foregroundColor="grey" transparent="1" zPosition="4"/>
\t\t<widget name="activecam" position="245,195" size="500,38" font="Regular;29" foregroundColor="secondFG" transparent="1" zPosition="4"/>
\t\t<widget name="Ilab1" position="45,255" size="680,38" font="Regular;26" foregroundColor="foreground" transparent="1" zPosition="4"/>
\t\t<widget name="Ilab2" position="45,300" size="680,38" font="Regular;26" foregroundColor="foreground" transparent="1" zPosition="4"/>
\t\t<widget name="Ilab3" position="45,345" size="680,38" font="Regular;26" foregroundColor="foreground" transparent="1" zPosition="4"/>
\t\t<widget name="Ilab4" position="45,390" size="680,38" font="Regular;26" foregroundColor="foreground" transparent="1" zPosition="4"/>
\t\t<eLabel position="760,195" size="2,500" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget name="Ecmtext" position="790,195" size="640,500" font="Regular;24" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="4"/>
\t\t<eLabel position="35,735" size="1430,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<eLabel position="50,760" size="330,55" backgroundColor="#00a00000" zPosition="2"/>
\t\t<eLabel position="405,760" size="330,55" backgroundColor="#00008000" zPosition="2"/>
\t\t<eLabel position="760,760" size="330,55" backgroundColor="#00a08000" zPosition="2"/>
\t\t<eLabel position="1115,760" size="330,55" backgroundColor="#000040a0" zPosition="2"/>
\t\t<widget name="key_red" position="60,765" size="310,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="key_green" position="415,765" size="310,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="key_yellow" position="770,765" size="310,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="key_blue" position="1125,765" size="310,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>"""


FAST_PLUGIN_SETUP = """\t\t<eLabel position="0,0" size="1300,800" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<eLabel text="OpenBH Fast Plugin Setup" position="40,25" size="1220,50" font="Regular;36" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1" zPosition="3"/>
\t\t<eLabel position="30,88" size="1240,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<widget source="list" render="Listbox" position="40,110" size="1220,565" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="4">
\t\t\t<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryText(pos = (120, 5), size = (1060, 36), font=0, text = 0),
MultiContentEntryText(pos = (120, 41), size = (1060, 28), font=1, text = 1),
MultiContentEntryPixmapAlphaTest(pos = (10, 15), size = (90, 50), png = 2, flags = BT_SCALE)
],
"fonts": [gFont("Regular", 30), gFont("Regular", 22)],
"itemHeight": 80
}
\t\t\t</convert>
\t\t</widget>
\t\t<eLabel position="30,700" size="1240,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
\t\t<eLabel position="455,720" size="390,55" backgroundColor="#00a00000" zPosition="2"/>
\t\t<widget name="key_red" position="465,725" size="370,45" font="Regular;27" halign="center" valign="center" transparent="1" zPosition="4"/>"""

GREEN_PANEL_SETUP = """\t\t<eLabel position="0,0" size="1200,560" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget source="list" render="Listbox" position="35,35" size="1130,490" enableWrapAround="1" scrollbarMode="showOnDemand" foregroundColor="foreground" backgroundColor="steThemePrimary" transparent="1" zPosition="4">
\t\t\t<convert type="TemplatedMultiContent">
{"template": [
MultiContentEntryText(pos = (95, 8), size = (990, 48), font=0, text = 0),
MultiContentEntryPixmapAlphaTest(pos = (12, 10), size = (64, 48), png = 1, flags = BT_SCALE)
],
"fonts": [gFont("Regular", 29)],
"itemHeight": 68
}
\t\t\t</convert>
\t\t</widget>"""

SECOND_INFOBAR = """\t\t<eLabel position="0,0" size="1920,520" backgroundColor="steSecondInfoBG" zPosition="0"/>
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

SCREENS = (
    ("ChoiceBox", CHOICEBOX, "center,center", "1100,800", "Select"),
    ("PluginBrowser", PLUGIN_BROWSER, "center,center", "1820,880", "Plugin Browser"),
    ("EventView", EVENT_VIEW, "center,center", "1820,880", "Event View"),
    ("DeliteGreenPanel", GREEN_PANEL, "center,center", "1500,850", "OpenBH Green Panel"),
    ("DeliteBluePanel", BLUE_PANEL, "center,center", "1500,850", "OpenBH Blue Panel"),
    ("DeliteSetupFp", FAST_PLUGIN_SETUP, "center,center", "1300,800", "OpenBH Fast Plugin Setup"),
    ("BhSetupGreen", GREEN_PANEL_SETUP, "center,center", "1200,560", "OpenBH Green Panel Setup"),
    ("EPGSelection", SINGLE_EPG, "center,center", "1820,880", "EPG Selection"),
    ("EPGSelectionMulti", MULTI_EPG, "center,center", "1820,880", "Multi EPG"),
    ("QuickEPG", QUICK_EPG, "0,660", "1920,420", "Quick EPG"),
    ("GraphicalEPG", GRID_EPG, "center,center", "1880,1000", "Graphical EPG"),
    ("GraphicalEPGPIG", GRID_PIG, "center,center", "1820,880", "Graphical EPG"),
    ("GraphicalInfoBarEPG", INFOBAR_GRID, "0,745", "1920,325", "InfoBar EPG"),
)

def patch_file(path):
    data = _normalise_math(_read(path))

    # OpenBH 6.0 uses the legacy names above as official fallbacks.
    for name in REMOVE_ALIASES:
        data = _remove_screen(data, name)

    # Replace only the proven OpenBH fallback screens.
    for name, body, pos, size, title in SCREENS:
        data = _remove_screen(data, name)

    # CineView owns its poster renderer on OpenBH; never depend on image PosterX.
    data = data.replace('render="PosterX"', 'render="CineViewPosterX"')
    data = data.replace("render='PosterX'", "render='CineViewPosterX'")

    # Keep both InfoBars slightly inset from the physical screen edges.
    data = _extend_infobar_edges(data, "InfoBar")
    data = _extend_infobar_edges(data, "SecondInfoBar", True)
    data = _extend_infobar_edges(data, "SecondInfoBarECM", True)

    idx = data.rfind("</skin>")
    if idx < 0:
        return False
    blocks = "".join(_screen(name, body, pos, size, title) for name, body, pos, size, title in SCREENS)
    data = data[:idx] + blocks + data[idx:]
    _write(path, data)
    return True

def main(root):
    changed = 0
    if os.path.isfile(root):
        changed = 1 if patch_file(root) else 0
    else:
        for name in os.listdir(root):
            if name.startswith("skin") and name.endswith(".xml"):
                if patch_file(os.path.join(root, name)):
                    changed += 1
    print(changed)
    return 0 if changed else 3

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
