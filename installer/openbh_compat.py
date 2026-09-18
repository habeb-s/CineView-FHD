# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import os
import re
import sys

SCREEN_RE = r'\n?[ \t]*<screen\b(?=[^>]*\bname=["\']%s["\'])[^>]*>.*?</screen>[ \t]*\n?'

def _read(path):
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _write(path, data):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(data)

def _remove_screen(data, name):
    return re.sub(SCREEN_RE % re.escape(name), "\n", data, flags=re.S)

def _normalise_math(data):
    # Enigma2 XML dimensions must be numeric; turn values such as 17*45 into 765.
    pat = re.compile(r'((?:size|position)=["\'][^"\']*?)(\d+)\*(\d+)([^"\']*["\'])')
    while True:
        data2, n = pat.subn(lambda m: m.group(1) + str(int(m.group(2)) * int(m.group(3))) + m.group(4), data)
        data = data2
        if not n:
            return data

def _screen(name, body, title=""):
    title_attr = (' title="%s"' % title) if title else ""
    return '\n\t<screen name="%s" position="fill" flags="wfNoBorder"%s>\n%s\n\t</screen>\n' % (name, title_attr, body)

PLUGIN_BROWSER = """\t\t<eLabel position="35,35" size="1850,955" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="list" position="85,105" size="1750,805" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="5"/>
\t\t<widget name="key_red" position="100,940" size="430,42" font="Regular;28" halign="center" transparent="1" zPosition="6"/>
\t\t<widget name="key_green" position="535,940" size="430,42" font="Regular;28" halign="center" transparent="1" zPosition="6"/>"""

EXTENSIONS = """\t\t<eLabel position="170,90" size="1580,900" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="list" position="230,155" size="1460,755" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="5"/>"""

SINGLE_OLD = """\t\t<eLabel position="40,35" size="1840,950" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="lab1" position="70,115" size="1080,790" font="Regular;30" halign="center" valign="center" zPosition="20"/>
\t\t<widget name="list" position="70,115" size="1080,790" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="10"/>
\t\t<widget source="Event" render="Label" position="1210,120" size="600,55" font="Regular;34" transparent="1" zPosition="10"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="1210,200" size="600,650" font="Regular;25" transparent="1" valign="top" zPosition="10"><convert type="EventName">FullDescription</convert></widget>"""

SINGLE_NEW = SINGLE_OLD + """
\t\t<widget name="bouquetlist" position="70,115" size="1080,790" font="Regular;30" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="30"/>"""

QUICK_OLD = """\t\t<eLabel position="60,560" size="1800,465" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="lab1" position="90,610" size="1740,330" font="Regular;30" halign="center" valign="center" zPosition="20"/>
\t\t<widget name="list" position="90,610" size="1740,330" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="10"/>"""

QUICK_NEW = QUICK_OLD + """
\t\t<widget name="bouquetlist" position="90,610" size="1740,330" font="Regular;30" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="30"/>"""

MULTI = """\t\t<eLabel position="35,35" size="1850,950" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="date" position="70,70" size="1780,45" font="Regular;30" halign="center" transparent="1" zPosition="10"/>
\t\t<widget name="now_button" pixmap="border/epg_off.png" position="260,125" size="225,50" alphatest="blend" zPosition="2"/>
\t\t<widget name="now_button_sel" pixmap="border/epg_now_on.png" position="260,125" size="225,50" alphatest="blend" zPosition="3"/>
\t\t<widget name="now_text" position="260,125" size="225,50" text="NOW" font="Regular;26" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="next_button" pixmap="border/epg_off.png" position="850,125" size="225,50" alphatest="blend" zPosition="2"/>
\t\t<widget name="next_button_sel" pixmap="border/epg_next_on.png" position="850,125" size="225,50" alphatest="blend" zPosition="3"/>
\t\t<widget name="next_text" position="850,125" size="225,50" text="NEXT" font="Regular;26" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="more_button" pixmap="border/epg_off.png" position="1435,125" size="225,50" alphatest="blend" zPosition="2"/>
\t\t<widget name="more_button_sel" pixmap="border/epg_next_on.png" position="1435,125" size="225,50" alphatest="blend" zPosition="3"/>
\t\t<widget name="more_text" position="1435,125" size="225,50" text="MORE" font="Regular;26" halign="center" valign="center" transparent="1" zPosition="4"/>
\t\t<widget name="lab1" position="70,195" size="1780,710" font="Regular;30" halign="center" valign="center" zPosition="20"/>
\t\t<widget name="list" position="70,195" size="1780,710" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="10"/>
\t\t<widget name="bouquetlist" position="70,195" size="1780,710" font="Regular;30" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="30"/>"""

GRID = """\t\t<eLabel position="35,35" size="1850,950" backgroundColor="steThemePrimary" zPosition="0"/>
\t\t<widget name="timeline_text" position="70,95" size="1780,55" font="Regular;25" transparent="1" zPosition="10"/>
\t\t<widget name="lab1" position="70,150" size="1780,650" font="Regular;30" halign="center" valign="center" zPosition="20"/>
\t\t<widget name="list" position="70,150" size="1780,650" scrollbarMode="showNever" transparent="1" zPosition="10"/>
\t\t<widget name="bouquetlist" position="70,150" size="1780,650" font="Regular;30" scrollbarMode="showOnDemand" enableWrapAround="1" zPosition="30"/>
\t\t<widget name="timeline_now" pixmap="border/vline.png" position="70,150" size="3,650" alphatest="blend" zPosition="22"/>
\t\t<widget name="timeline0" pixmap="border/vline.png" position="70,150" size="2,650" alphatest="blend" zPosition="21"/>
\t\t<widget name="timeline1" pixmap="border/vline.png" position="70,150" size="2,650" alphatest="blend" zPosition="21"/>
\t\t<widget name="timeline2" pixmap="border/vline.png" position="70,150" size="2,650" alphatest="blend" zPosition="21"/>
\t\t<widget name="timeline3" pixmap="border/vline.png" position="70,150" size="2,650" alphatest="blend" zPosition="21"/>
\t\t<widget name="timeline4" pixmap="border/vline.png" position="70,150" size="2,650" alphatest="blend" zPosition="21"/>
\t\t<widget name="timeline5" pixmap="border/vline.png" position="70,150" size="2,650" alphatest="blend" zPosition="21"/>
\t\t<widget source="Event" render="Label" position="80,825" size="1760,45" font="Regular;31" transparent="1" zPosition="10"><convert type="EventName">Name</convert></widget>
\t\t<widget source="Event" render="Label" position="80,875" size="1760,95" font="Regular;23" transparent="1" valign="top" zPosition="10"><convert type="EventName">ExtendedDescription</convert></widget>"""

SCREENS = [
    ("PluginBrowser", PLUGIN_BROWSER, "Plugin Browser"),
    ("ExtensionsList", EXTENSIONS, "Extensions"),
    ("EPGExtensionsList", EXTENSIONS, "EPG Extensions"),
    ("EPGSelection", SINGLE_OLD, "EPG Selection"),
    ("SingleEPG", SINGLE_NEW, "EPG Selection"),
    ("QuickEPG", QUICK_OLD, "Quick EPG"),
    ("InfobarSingleEPG", QUICK_NEW, "Quick EPG"),
    ("EPGSelectionMulti", MULTI, "Multi EPG"),
    ("MultiEPG", MULTI, "Multi EPG"),
    ("GraphicalEPG", GRID, "Graphical EPG"),
    ("GridEPG", GRID, "Graphical EPG"),
    ("GraphicalEPGPIG", GRID, "Graphical EPG"),
    ("GridEPGPIG", GRID, "Graphical EPG"),
    ("GraphicalInfoBarEPG", GRID, "InfoBar EPG"),
    ("InfoBarGridEPG", GRID, "InfoBar EPG"),
]

def patch_file(path):
    data = _normalise_math(_read(path))
    for name, body, title in SCREENS:
        data = _remove_screen(data, name)
    idx = data.rfind("</skin>")
    if idx < 0:
        return False
    blocks = "".join(_screen(name, body, title) for name, body, title in SCREENS)
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
