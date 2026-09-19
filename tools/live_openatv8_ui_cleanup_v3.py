#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 3:
    raise SystemExit("usage: ui_cleanup.py LIVE_SKIN PREVIOUS_SKIN")

live_path = Path(sys.argv[1])
prev_path = Path(sys.argv[2])
skin = live_path.read_text(errors="ignore")
previous = prev_path.read_text(errors="ignore")


def find_screen(text, name):
    m = re.search(r'(?s)<screen(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>', text)
    if not m:
        raise SystemExit("MISSING_SCREEN:" + name)
    return m.group(0)


def replace_screen(text, name, block):
    pat = re.compile(r'(?s)<screen(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>')
    out, count = pat.subn(block, text, count=1)
    if count != 1:
        raise SystemExit("REPLACE_FAIL:" + name)
    return out


def upsert_after(text, anchor_name, name, block):
    pat = re.compile(r'(?s)<screen(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>')
    if pat.search(text):
        return pat.sub(block, text, count=1)
    anchor = find_screen(text, anchor_name)
    return text.replace(anchor, anchor + "\n\n" + block, 1)


info_before = find_screen(skin, "InfoBar")
epg_before = {n: find_screen(skin, n) for n in (
    "EPGSelection", "EPGSelectionMulti", "QuickEPG",
    "GraphicalEPG", "GraphicalEPGPIG", "GraphicalInfoBarEPG"
)}

# Restore Signal Finder exactly to the pre-redesign version.
skin = replace_screen(skin, "Satfinder", find_screen(previous, "Satfinder"))

# Choice lists: retain existing full-screen layout, only fix clipped text.
choice = find_screen(skin, "ChoiceBox")
choice = re.sub(r'itemHeight="50"', 'itemHeight="64"', choice)
choice = re.sub(r'font="Regular;33"', 'font="Regular;30"', choice)
skin = replace_screen(skin, "ChoiceBox", choice)

# GUI skin selector: keep full-screen, give each name enough vertical room.
selector = find_screen(skin, "SkinSelector")
selector = selector.replace('size = (675,50)', 'size = (675,64)')
selector = selector.replace('size = (400,50)', 'size = (400,64)')
selector = selector.replace('gFont("Regular",33)', 'gFont("Regular",30)')
selector = selector.replace('"itemHeight":50', '"itemHeight":64')
skin = replace_screen(skin, "SkinSelector", selector)

# Full-screen OpenATV Setup, including the Skin Settings page.
setup_template = """<screen name="{name}" title="Setup" position="fill" flags="wfNoBorder">
    <eLabel position="0,0" size="1920,1080" backgroundColor="steThemePrimary" zPosition="0"/>
    <widget source="Title" render="Label" position="35,24" size="1850,54" font="Regular;38" foregroundColor="foreground" transparent="1" zPosition="2"/>
    <eLabel position="30,92" size="1860,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
    <widget name="config" position="45,125" size="1120,780" itemHeight="60" font="Regular;30" transparent="1" enableWrapAround="1" scrollbarMode="showOnDemand" zPosition="3"/>
    <eLabel position="1200,125" size="2,780" backgroundColor="steThemePanelAlt" zPosition="2"/>
    <widget name="description" position="1240,150" size="610,470" font="Regular;26" foregroundColor="foreground" transparent="1" valign="top" zPosition="3"/>
    <widget name="footnote" position="1240,650" size="610,180" font="Regular;23" foregroundColor="secondFG" transparent="1" valign="top" zPosition="3"/>
    <eLabel position="30,935" size="1860,2" backgroundColor="steThemePanelAlt" zPosition="2"/>
    <widget source="key_red" render="Label" position="80,960" size="500,58" font="Regular;28" foregroundColor="foreground" transparent="1" valign="center" zPosition="3"/>
    <widget source="key_green" render="Label" position="650,960" size="500,58" font="Regular;28" foregroundColor="foreground" transparent="1" valign="center" zPosition="3"/>
    <widget name="HelpWindow" position="0,0" size="0,0" alphatest="blend" transparent="1" zPosition="1"/>
</screen>"""
skin = replace_screen(skin, "Setup", setup_template.format(name="Setup"))
skin = upsert_after(skin, "Setup", "SetupSkin", setup_template.format(name="SetupSkin"))
skin = upsert_after(skin, "SetupSkin", "setup_Skin", setup_template.format(name="setup_Skin"))

# Fix only displayed units in the InfoBar family; layout remains unchanged.
skin = skin.replace(
    '<convert type="PliExtraInfo">TransponderInfo</convert>',
    '<convert type="CineViewTransponderInfo">TransponderInfo</convert>'
)

ET.fromstring(skin)

# EPG is intentionally untouched in this pass.
for name, old in epg_before.items():
    if find_screen(skin, name) != old:
        raise SystemExit("EPG_CHANGED:" + name)

# Primary InfoBar may differ only by converter name.
info_after = find_screen(skin, "InfoBar")
normalized = info_after.replace("CineViewTransponderInfo", "PliExtraInfo")
if normalized != info_before:
    raise SystemExit("INFOBAR_LAYOUT_CHANGED")

sat_after = find_screen(skin, "Satfinder")
if sat_after != find_screen(previous, "Satfinder"):
    raise SystemExit("SATFINDER_NOT_RESTORED")

choice_after = find_screen(skin, "ChoiceBox")
if 'itemHeight="64"' not in choice_after or 'font="Regular;30"' not in choice_after:
    raise SystemExit("CHOICEBOX_NOT_FIXED")

selector_after = find_screen(skin, "SkinSelector")
if '"itemHeight":64' not in selector_after or 'gFont("Regular",30)' not in selector_after:
    raise SystemExit("SKINSELECTOR_NOT_FIXED")

live_path.write_text(skin)
print("SATFINDER_RESTORED")
print("CHOICEBOX_TEXT_HEIGHT_FIXED")
print("SKIN_SELECTOR_TEXT_HEIGHT_FIXED")
print("SETUP_FULLSCREEN_ADDED")
print("INFOBAR_LAYOUT_UNCHANGED_FORMATTER_FIXED")
print("EPG_UNCHANGED")
