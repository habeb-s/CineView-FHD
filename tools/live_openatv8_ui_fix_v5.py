#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 3:
    raise SystemExit("usage: live_openatv8_ui_fix_v5.py SKIN_XML SKIN_TEMPLATES_XML")

skinp = Path(sys.argv[1])
tplp = Path(sys.argv[2])
s = skinp.read_text(errors="ignore")
t = tplp.read_text(errors="ignore")

def screen(text, name):
    m = re.search(r'(?s)<screen\b(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>', text)
    if not m:
        raise SystemExit("MISSING_SCREEN:" + name)
    return m.group(0)

def replace_screen(text, name, block):
    p = re.compile(r'(?s)<screen\b(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>')
    out, n = p.subn(block, text, count=1)
    if n != 1:
        raise SystemExit("REPLACE_FAIL:" + name)
    return out

def set_param(text, name, value):
    p = re.compile(r'<parameter name="' + re.escape(name) + r'"[^>]*/>')
    item = '<parameter name="%s" value="%s"/>' % (name, value)
    if p.search(text):
        return p.sub(item, text, count=1)
    if "<parameters>" not in text:
        raise SystemExit("PARAMETERS_MISSING")
    return text.replace("<parameters>", "<parameters>\n\t\t" + item, 1)

info_before = screen(s, "InfoBar")
sat_before = screen(s, "Satfinder")
second = screen(s, "SecondInfoBar")

# OpenATV may actually display SecondInfoBarSimple. Force it to the same
# OpenViX/CineView visual design as the intended SecondInfoBar.
second = second.replace('backgroundColor="steSecondInfoBG"', 'backgroundColor="steThemePanel"')
simple = re.sub(r'name="SecondInfoBar"', 'name="SecondInfoBarSimple"', second, count=1)
s = replace_screen(s, "SecondInfoBar", second)
s = replace_screen(s, "SecondInfoBarSimple", simple)

if re.search(r'<screen\b(?=[^>]*name="SecondInfoBarECM")', s):
    ecm = screen(s, "SecondInfoBarECM")
    ecm = ecm.replace('backgroundColor="steSecondInfoBG"', 'backgroundColor="steThemePanel"')
    s = replace_screen(s, "SecondInfoBarECM", ecm)

# Give OpenATV ChoiceList enough vertical space for LiberationSans descenders.
s = re.sub(r'<alias name="ChoiceList"[^>]*/>',
           '<alias name="ChoiceList" font="Regular" size="30" height="72"/>', s, count=1)
s = re.sub(r'<alias name="SelectionList"[^>]*/>',
           '<alias name="SelectionList" font="Regular" size="30" height="72"/>', s, count=1)
s = set_param(s, "ChoicelistVerticalAlignment", "*center")
s = set_param(s, "ChoicelistNameSingle", "18,0,1180,72")
s = set_param(s, "ChoicelistName", "82,0,1110,72")
s = set_param(s, "ChoicelistIcon", "12,10,52,42")

choice = screen(s, "ChoiceBox")
choice = re.sub(
    r'<widget name="list"[^>]*/>',
    '<widget name="list" position="620,82" size="1270,940" itemHeight="72" font="Regular;30" scrollbarMode="showOnDemand"/>',
    choice,
    count=1,
)
s = replace_screen(s, "ChoiceBox", choice)

selector = screen(s, "SkinSelector")
selector = re.sub(
    r'<widget name="preview"[^>]*/>',
    '<widget name="preview" position="55,155" size="555,416" alphatest="on"/>',
    selector,
    count=1,
)
selector = re.sub(
    r'<widget source="skins" render="Listbox"[^>]*>',
    '<widget source="skins" render="Listbox" position="620,70" size="1270,950" scrollbarMode="showOnDemand">',
    selector,
    count=1,
)
selector = re.sub(r'pos = \(20,0\), size = \([^)]*\)', 'pos = (20,0), size = (790,82)', selector)
selector = re.sub(r'pos = \((?:790|825),0\), size = \([^)]*\)', 'pos = (825,0), size = (410,82)', selector)
selector = re.sub(r'gFont\("Regular",\d+\)', 'gFont("Regular",38)', selector)
selector = re.sub(r'"itemHeight":\d+', '"itemHeight":82', selector)
s = replace_screen(s, "SkinSelector", selector)

# Setup / Skin Settings are built from ConfigTemplate, not directly from Setup.
cfg = screen(t, "ConfigTemplate")
cfg = re.sub(
    r'position="780,123" size="1110,855" itemHeight="45" font="Regular;33"',
    'position="700,105" size="1190,885" itemHeight="70" font="Regular;31"',
    cfg,
)
cfg = cfg.replace('position="780,985" size="1110,25"', 'position="700,998" size="1190,25"')
t = replace_screen(t, "ConfigTemplate", cfg)

desc = screen(t, "DescriptionTemplate")
desc = desc.replace(
    'position="30,570" size="720,300" font="Regular;32"',
    'position="35,570" size="620,300" font="Regular;28"',
)
t = replace_screen(t, "DescriptionTemplate", desc)

foot = screen(t, "FootnoteTemplate")
foot = foot.replace(
    'position="30,880" zPosition="1000" size="720,100" font="Regular;32"',
    'position="35,885" zPosition="1000" size="620,100" font="Regular;27"',
)
foot = foot.replace(
    'position="30,880" zPosition="1" size="720,100" font="Regular;32"',
    'position="35,885" zPosition="1" size="620,100" font="Regular;27"',
)
t = replace_screen(t, "FootnoteTemplate", foot)

ET.fromstring(s)
ET.fromstring(t)

if screen(s, "InfoBar") != info_before:
    raise SystemExit("INFOBAR_CHANGED")
if screen(s, "Satfinder") != sat_before:
    raise SystemExit("SATFINDER_CHANGED")
if 'position="70,145" size="790,440"' not in screen(s, "SecondInfoBarSimple"):
    raise SystemExit("SECONDINFO_SIMPLE_LAYOUT_MISSING")
if 'session.Event_Next' not in screen(s, "SecondInfoBarSimple"):
    raise SystemExit("SECONDINFO_SIMPLE_NEXT_MISSING")
if 'backgroundColor="steThemePanel"' not in screen(s, "SecondInfoBarSimple"):
    raise SystemExit("SECONDINFO_THEME_NOT_FIXED")
if 'itemHeight="70" font="Regular;31"' not in screen(t, "ConfigTemplate"):
    raise SystemExit("CONFIG_TEMPLATE_NOT_FIXED")
if 'gFont("Regular",38)' not in screen(s, "SkinSelector"):
    raise SystemExit("SKIN_SELECTOR_NOT_FIXED")

skinp.write_text(s)
tplp.write_text(t)

print("INFOBAR_UNTOUCHED")
print("SATFINDER_UNTOUCHED")
print("SECONDINFO_SIMPLE_OPENVIX_FIXED")
print("SECONDINFO_THEME_FIXED")
print("CHOICE_ROWS_FIXED")
print("CONFIG_TEMPLATE_FHD_FIXED")
print("SKIN_SELECTOR_LARGE_FIXED")
