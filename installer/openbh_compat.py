# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import os
import re
import sys

SCREEN_RE = r'\n?[ \t]*<screen\b(?=[^>]*\bname=["\']%s["\'])[^>]*>.*?</screen>[ \t]*\n?'

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

def _screen(name, body, position="center,center", size="1820,880", title=""):
    t = (' title="%s"' % title) if title else ""
    return '\n\t<screen name="%s" position="%s" size="%s" flags="wfNoBorder"%s>\n%s\n\t</screen>\n' % (
        name, position, size, t, body)

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

SCREENS = (
    ("ChoiceBox", CHOICEBOX, "center,center", "1100,800", "Select"),
    ("PluginBrowser", PLUGIN_BROWSER, "center,center", "1820,880", "Plugin Browser"),
    ("EPGSelection", SINGLE_EPG, "center,center", "1820,880", "EPG Selection"),
    ("EPGSelectionMulti", MULTI_EPG, "center,center", "1820,880", "Multi EPG"),
    ("QuickEPG", QUICK_EPG, "0,660", "1920,420", "Quick EPG"),
    ("GraphicalEPG", GRID_COMMON, "center,center", "1820,880", "Graphical EPG"),
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

    idx = data.rfind("</skin>")
    if idx < 0:
        return False
    blocks = "".join(_screen(name, body, pos, size, title) for name, body, pos, size, title in SCREENS)
    data = data[:idx] + blocks + data[idx:]
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
