#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 3:
    raise SystemExit("usage: restore_secondinfo_v6.py LIVE_SKIN REFERENCE_SKIN")

livep = Path(sys.argv[1])
refp = Path(sys.argv[2])
live = livep.read_text(errors="ignore")
ref = refp.read_text(errors="ignore")

def one(text, name):
    m = re.search(r'(?s)<screen\b(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>', text)
    if not m:
        return None
    return m.group(0)

def replace(text, name, block):
    p = re.compile(r'(?s)<screen\b(?=[^>]*name="' + re.escape(name) + r'")[^>]*>.*?</screen>')
    out, n = p.subn(block, text, count=1)
    if n != 1:
        raise SystemExit("REPLACE_FAIL:" + name)
    return out

info_before = one(live, "InfoBar")
sat_before = one(live, "Satfinder")
ref_second = one(ref, "SecondInfoBar")
if not ref_second:
    raise SystemExit("REFERENCE_SECONDINFO_MISSING")

# Restore the exact compact first design saved before the later SecondInfo/EPG redesign.
ref_second = ref_second.replace('render="PosterX"', 'render="CineViewPosterX"')
live = replace(live, "SecondInfoBar", ref_second)

ref_ecm = one(ref, "SecondInfoBarECM")
if ref_ecm and one(live, "SecondInfoBarECM"):
    ref_ecm = ref_ecm.replace('render="PosterX"', 'render="CineViewPosterX"')
    live = replace(live, "SecondInfoBarECM", ref_ecm)

ET.fromstring(live)

if one(live, "InfoBar") != info_before:
    raise SystemExit("PRIMARY_INFOBAR_CHANGED")
if one(live, "Satfinder") != sat_before:
    raise SystemExit("SATFINDER_CHANGED")
second = one(live, "SecondInfoBar")
if 'position="0,560" size="1920,520"' not in second:
    raise SystemExit("COMPACT_SECONDINFO_NOT_RESTORED")
if 'name="epg_description"' not in second or 'name="channel"' not in second:
    raise SystemExit("OPENATV_SECONDINFO_WIDGET_CONTRACT_MISSING")
if 'position="1545,30" size="285,380"' not in second:
    raise SystemExit("REFERENCE_POSTER_GEOMETRY_MISSING")

livep.write_text(live)
print("PRIMARY_INFOBAR_UNTOUCHED")
print("SATFINDER_UNTOUCHED")
print("FIRST_COMPACT_SECONDINFO_RESTORED")
