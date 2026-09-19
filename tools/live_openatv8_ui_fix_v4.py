#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 3:
    raise SystemExit("usage: live_openatv8_ui_fix_v4.py LIVE_SKIN OLD_VIX_SKIN")

live_path = Path(sys.argv[1])
old_path = Path(sys.argv[2])
skin = live_path.read_text(errors="ignore")
old = old_path.read_text(errors="ignore")


def one(text, name):
    m = re.search(r'(?s)<screen(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>', text)
    if not m:
        raise SystemExit("MISSING_SCREEN:" + name)
    return m.group(0)


def replace(text, name, block):
    pat = re.compile(r'(?s)<screen(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>')
    out, count = pat.subn(block, text, count=1)
    if count != 1:
        raise SystemExit("REPLACE_FAIL:" + name)
    return out


def inner(block):
    return block[block.find(">") + 1:block.rfind("</screen>")]


info_before = one(skin, "InfoBar")
sat_before = one(skin, "Satfinder")

# 1) Exact first OpenViX event-panel design + current OpenATV primary InfoBar below it.
vix_second = one(old, "SecondInfoBar")
marker = "<!-- Same technical bar as primary InfoBar"
cut = vix_second.find(marker)
if cut < 0:
    raise SystemExit("OLD_SECONDINFO_MARKER_MISSING")
vix_top = vix_second[:cut]
vix_top = vix_top.replace('render="PosterX"', 'render="CineViewPosterX"')
second = vix_top + inner(info_before) + "\n</screen>"
second = second.replace('name="SecondInfoBar"', 'name="SecondInfoBar"', 1)
second_ecm = second.replace('name="SecondInfoBar"', 'name="SecondInfoBarECM"', 1)
skin = replace(skin, "SecondInfoBar", second)
skin = replace(skin, "SecondInfoBarECM", second_ecm)

# 2) Fix all OpenATV ChoiceList rows at the source of the clipping problem.
skin = re.sub(
    r'<alias name="ChoiceList"[^>]*/>',
    '<alias name="ChoiceList" font="Regular" size="31" height="64"/>',
    skin,
    count=1
)
skin = re.sub(
    r'<alias name="SelectionList"[^>]*/>',
    '<alias name="SelectionList" font="Regular" size="30" height="62"/>',
    skin,
    count=1
)

def set_param(text, name, value):
    pat = re.compile(r'<parameter name="' + re.escape(name) + r'"[^>]*/>')
    item = '<parameter name="%s" value="%s"/>' % (name, value)
    if pat.search(text):
        return pat.sub(item, text, count=1)
    anchor = '<parameters>'
    if anchor not in text:
        raise SystemExit("PARAMETERS_BLOCK_MISSING")
    return text.replace(anchor, anchor + "\n\t\t" + item, 1)

skin = set_param(skin, "ChoicelistVerticalAlignment", "*center")
skin = set_param(skin, "ChoicelistNameSingle", "18,0,1180,64")
skin = set_param(skin, "ChoicelistName", "82,0,1110,64")
skin = set_param(skin, "ChoicelistIcon", "12,12,52,40")

# ConfigList fonts were missing from CineView's window style. Add them globally.
if '<configList ' not in skin:
    pat = re.compile(r'(<windowstyle id="0" type="skinned">\s*<title[^>]*/>)')
    skin, count = pat.subn(
        r'\1\n\t\t<configList entryLeftOffset="18" headerLeftOffset="8" headerFont="Regular;28" entryFont="Regular;28" valueFont="Regular;27"/>',
        skin,
        count=1
    )
    if count != 1:
        raise SystemExit("WINDOWSTYLE_CONFIGLIST_INSERT_FAIL")
else:
    skin = re.sub(
        r'<configList[^>]*/>',
        '<configList entryLeftOffset="18" headerLeftOffset="8" headerFont="Regular;28" entryFont="Regular;28" valueFont="Regular;27"/>',
        skin,
        count=1
    )

# 3) ChoiceBox remains full-screen, but with a larger readable list area.
choice = one(skin, "ChoiceBox")
choice = re.sub(
    r'<widget name="list"[^>]*/>',
    '<widget name="list" position="650,90" size="1240,930" itemHeight="64" font="Regular;31" scrollbarMode="showOnDemand"/>',
    choice,
    count=1
)
skin = replace(skin, "ChoiceBox", choice)

# 4) GUI Skin list: still full-screen, now substantially larger/readable.
selector = one(skin, "SkinSelector")
selector = re.sub(
    r'<widget name="preview"[^>]*/>',
    '<widget name="preview" position="70,170" size="535,401" alphatest="on"/>',
    selector,
    count=1
)
selector = re.sub(
    r'<widget source="skins" render="Listbox"[^>]*>',
    '<widget source="skins" render="Listbox" position="650,85" size="1240,930" scrollbarMode="showOnDemand">',
    selector,
    count=1
)
selector = selector.replace('pos = (20,0), size = (675,64)', 'pos = (20,0), size = (760,72)')
selector = selector.replace('pos = (700,0), size = (400,64)', 'pos = (790,0), size = (420,72)')
selector = selector.replace('pos = (20,0), size = (675,50)', 'pos = (20,0), size = (760,72)')
selector = selector.replace('pos = (700,0), size = (400,50)', 'pos = (790,0), size = (420,72)')
selector = selector.replace('gFont("Regular",30)', 'gFont("Regular",34)')
selector = selector.replace('gFont("Regular",33)', 'gFont("Regular",34)')
selector = selector.replace('"itemHeight":64', '"itemHeight":72')
selector = selector.replace('"itemHeight":50', '"itemHeight":72')
skin = replace(skin, "SkinSelector", selector)

# 5) Full-screen Skin Settings / Setup with enough vertical room per row.
for setup_name in ("Setup", "SetupSkin", "setup_Skin"):
    block = one(skin, setup_name)
    block = re.sub(
        r'<widget name="config"[^>]*/>',
        '<widget name="config" position="45,120" size="1180,800" itemHeight="70" font="Regular;29" transparent="1" enableWrapAround="1" scrollbarMode="showOnDemand" zPosition="3"/>',
        block,
        count=1
    )
    block = re.sub(
        r'<widget name="description"[^>]*/>',
        '<widget name="description" position="1270,145" size="570,500" font="Regular;26" foregroundColor="foreground" transparent="1" valign="top" zPosition="3"/>',
        block,
        count=1
    )
    block = re.sub(
        r'<widget name="footnote"[^>]*/>',
        '<widget name="footnote" position="1270,675" size="570,190" font="Regular;23" foregroundColor="secondFG" transparent="1" valign="top" zPosition="3"/>',
        block,
        count=1
    )
    skin = replace(skin, setup_name, block)

# 6) Rebuild the graphical EPG to use the FHD canvas instead of a small grid.
graph = r'''<screen name="GraphicalEPG" position="center,center" size="1820,930" flags="wfNoBorder" title="Graphical EPG">
    <eLabel position="0,0" size="1820,930" backgroundColor="steThemePrimary" zPosition="0"/>
    <widget source="Title" render="Label" position="45,24" size="1200,50" font="Regular;36" foregroundColor="secondFG" transparent="1"/>
    <widget source="global.CurrentTime" render="Label" position="1450,24" size="320,46" font="Regular;27" foregroundColor="grey" halign="right" transparent="1"><convert type="ClockToText">Format:%d.%m.%Y %H:%M</convert></widget>
    <widget name="timeline_text" position="45,92" size="1180,44" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
    <widget name="lab1" position="45,138" size="1180,625" font="Regular;28" halign="center" valign="center" backgroundColor="steThemePrimary" transparent="0" zPosition="2"/>
    <widget name="bouquetlist" position="45,138" size="1180,625" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
    <widget name="list" position="45,138" size="1180,625" scrollbarMode="showNever" transparent="1" zPosition="10" ServiceFontGraphical="Regular;28" EntryFontGraphical="Regular;26" NumberOfRows="9" MinimumItemHeight="66" EntryFontWrap="no"/>
    <widget name="timeline_now" position="45,138" zPosition="21" size="5,625"/>

    <eLabel position="1260,82" size="520,682" backgroundColor="steThemePanel" zPosition="1"/>
    <widget source="Event" render="CineViewPosterX" position="1380,105" size="280,420" zPosition="12"/>
    <widget source="Event" render="RunningText" position="1290,545" size="460,48" font="Regular;30" foregroundColor="secondFG" transparent="1" halign="center" noWrap="1" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1400,pause=900,repeat=0,always=0"><convert type="EventName">Name</convert></widget>
    <widget source="Event" render="Label" position="1290,605" size="460,135" font="Regular;23" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">ExtendedDescription</convert></widget>

    <eLabel position="35,805" size="1750,2" backgroundColor="steThemePanelAlt"/>
    <widget source="key_red" render="Label" position="55,830" size="400,52" font="Regular;26" halign="center" transparent="1"/>
    <widget source="key_green" render="Label" position="490,830" size="400,52" font="Regular;26" halign="center" transparent="1"/>
    <widget source="key_yellow" render="Label" position="925,830" size="400,52" font="Regular;26" halign="center" transparent="1"/>
    <widget source="key_blue" render="Label" position="1360,830" size="400,52" font="Regular;26" halign="center" transparent="1"/>
</screen>'''

graph_pig = r'''<screen name="GraphicalEPGPIG" position="center,center" size="1820,930" flags="wfNoBorder" title="Graphical EPG">
    <eLabel position="0,0" size="1820,930" backgroundColor="steThemePrimary" zPosition="0"/>
    <widget source="Title" render="Label" position="45,24" size="1200,50" font="Regular;36" foregroundColor="secondFG" transparent="1"/>
    <widget source="global.CurrentTime" render="Label" position="1450,24" size="320,46" font="Regular;27" foregroundColor="grey" halign="right" transparent="1"><convert type="ClockToText">Format:%d.%m.%Y %H:%M</convert></widget>
    <widget name="timeline_text" position="45,92" size="1180,44" foregroundColor="secondFG" backgroundColor="steThemePrimary" transparent="1"/>
    <widget name="lab1" position="45,138" size="1180,625" font="Regular;28" halign="center" valign="center" backgroundColor="steThemePrimary" transparent="0" zPosition="2"/>
    <widget name="bouquetlist" position="45,138" size="1180,625" backgroundColor="steThemePrimary" scrollbarMode="showNever" transparent="0" zPosition="15"/>
    <widget name="list" position="45,138" size="1180,625" scrollbarMode="showNever" transparent="1" zPosition="10" ServiceFontGraphical="Regular;28" EntryFontGraphical="Regular;26" NumberOfRows="9" MinimumItemHeight="66" EntryFontWrap="no"/>
    <widget name="timeline_now" position="45,138" zPosition="21" size="5,625"/>

    <eLabel position="1260,82" size="520,682" backgroundColor="steThemePanel" zPosition="1"/>
    <eLabel position="1280,105" size="480,270" backgroundColor="black" zPosition="3"/>
    <widget source="session.VideoPicture" render="Pig" position="1290,115" size="460,259" backgroundColor="black" zPosition="4"/>
    <widget source="Event" render="RunningText" position="1290,405" size="460,48" font="Regular;30" foregroundColor="secondFG" transparent="1" halign="center" noWrap="1" options="movetype=running,direction=left,step=2,steptime=55,startdelay=1400,pause=900,repeat=0,always=0"><convert type="EventName">Name</convert></widget>
    <widget source="Event" render="Label" position="1290,470" size="460,260" font="Regular;23" foregroundColor="foreground" transparent="1" valign="top"><convert type="EventName">ExtendedDescription</convert></widget>

    <eLabel position="35,805" size="1750,2" backgroundColor="steThemePanelAlt"/>
    <widget source="key_red" render="Label" position="55,830" size="400,52" font="Regular;26" halign="center" transparent="1"/>
    <widget source="key_green" render="Label" position="490,830" size="400,52" font="Regular;26" halign="center" transparent="1"/>
    <widget source="key_yellow" render="Label" position="925,830" size="400,52" font="Regular;26" halign="center" transparent="1"/>
    <widget source="key_blue" render="Label" position="1360,830" size="400,52" font="Regular;26" halign="center" transparent="1"/>
</screen>'''

skin = replace(skin, "GraphicalEPG", graph)
skin = replace(skin, "GraphicalEPGPIG", graph_pig)

ET.fromstring(skin)

# Hard safety invariants.
if one(skin, "InfoBar") != info_before:
    raise SystemExit("PRIMARY_INFOBAR_CHANGED")
if one(skin, "Satfinder") != sat_before:
    raise SystemExit("SATFINDER_CHANGED")
if 'position="70,145" size="790,440"' not in one(skin, "SecondInfoBar"):
    raise SystemExit("OPENVIX_SECONDINFO_NOT_APPLIED")
if 'session.Event_Next' not in one(skin, "SecondInfoBar"):
    raise SystemExit("SECONDINFO_NEXT_MISSING")
if 'render="CineViewPosterX"' not in one(skin, "SecondInfoBar"):
    raise SystemExit("SECONDINFO_POSTER_RENDERER_MISSING")
if 'NumberOfRows="9"' not in one(skin, "GraphicalEPG"):
    raise SystemExit("GRAPH_EPG_NOT_REBUILT")
if 'gFont("Regular",34)' not in one(skin, "SkinSelector"):
    raise SystemExit("SKIN_SELECTOR_NOT_ENLARGED")
if 'name="ChoiceList" font="Regular" size="31" height="64"' not in skin:
    raise SystemExit("CHOICELIST_ALIAS_NOT_FIXED")
if '<configList entryLeftOffset="18"' not in skin:
    raise SystemExit("CONFIGLIST_STYLE_NOT_FIXED")

live_path.write_text(skin)
print("PRIMARY_INFOBAR_UNTOUCHED")
print("SATFINDER_UNTOUCHED")
print("OPENVIX_FIRST_SECONDINFO_APPLIED")
print("CHOICELIST_GLOBAL_CLIPPING_FIXED")
print("CONFIGLIST_GLOBAL_CLIPPING_FIXED")
print("GUI_SKIN_LIST_ENLARGED")
print("SKIN_SETTINGS_FULLSCREEN_ROWS_FIXED")
print("GRAPHICAL_EPG_FHD_REBUILT")
