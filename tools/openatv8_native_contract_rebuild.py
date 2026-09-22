#!/usr/bin/env python3
"""Rebuild only the OpenATV-8-native CineView contracts that were proven wrong.

Target baseline:
- OpenATV 8.0.0-beta build 20260922
- Enigma2 commit 45414bc8f2529cd99d9e921de0a50fbede13514f

This tool deliberately does NOT copy OpenViX screen bindings into OpenATV.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


EVENT_VIEW = r'''
	<screen name="EventView" position="fill" flags="wfNoBorder">
		<panel name="PigLessTemplate"/>
		<widget name="channel" position="70,125" size="1780,48" font="Regular;36" valign="center" halign="left"/>
		<widget name="datetime" position="70,190" size="500,42" font="Regular;30" valign="center" halign="left"/>
		<widget name="duration" position="590,190" size="300,42" font="Regular;30" valign="center" halign="left"/>
		<widget name="epg_description" position="70,255" size="1780,710" font="Regular;30"/>
	</screen>
'''.strip()


def screen_pattern(name: str) -> re.Pattern[str]:
    return re.compile(
        r'(?ms)^[ \t]*<screen\b(?=[^>]*\bname="' + re.escape(name) +
        r'")[^>]*>.*?</screen>[ \t]*(?:\n|$)'
    )


def get_screen(data: str, name: str) -> str:
    matches = list(screen_pattern(name).finditer(data))
    if len(matches) != 1:
        raise RuntimeError(f"{name}: expected exactly one authoritative screen, found {len(matches)}")
    return matches[0].group(0)


def replace_screen(data: str, name: str, replacement: str) -> str:
    pattern = screen_pattern(name)
    matches = list(pattern.finditer(data))
    if len(matches) != 1:
        raise RuntimeError(f"{name}: expected exactly one authoritative screen, found {len(matches)}")
    return data[:matches[0].start()] + replacement + "\n" + data[matches[0].end():]


def edit_screen(data: str, name: str, replacements: list[tuple[str, str]]) -> str:
    old_block = get_screen(data, name)
    block = old_block
    for old, new in replacements:
        count = block.count(old)
        if count != 1:
            raise RuntimeError(f"{name}: expected one occurrence of {old!r}, found {count}")
        block = block.replace(old, new, 1)
    return data.replace(old_block, block, 1)


def validate_xml_tree(root: Path) -> int:
    checked = 0
    for path in sorted(root.rglob("*.xml")):
        try:
            ET.parse(path)
        except Exception as exc:
            raise RuntimeError(f"XML invalid: {path}: {exc}") from exc
        checked += 1
    return checked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skin_dir", type=Path)
    ap.add_argument("--backup", action="store_true")
    args = ap.parse_args()

    skin_dir = args.skin_dir.resolve()
    skin_xml = skin_dir / "skin.xml"
    if not skin_xml.is_file():
        raise SystemExit(f"missing {skin_xml}")

    if args.backup:
        backup = skin_xml.with_suffix(".xml.before-openatv8-native")
        shutil.copy2(skin_xml, backup)
        print(f"backup={backup}")

    data = skin_xml.read_text(encoding="utf-8")

    # EventView must be safe for BOTH EventViewEPGSelect and EventViewMovieEvent.
    # The movie variant has no Event / Service / FullDescription source, so the
    # common EventView intentionally uses only the common named components.
    data = replace_screen(data, "EventView", EVENT_VIEW)

    # Keep OpenATV JobView contract, fix only the blue footer geometry.
    data = edit_screen(data, "JobView", [
        ('position="1500,1032" size="34,34"', 'position="1320,1032" size="34,34"'),
        ('position="1550,1030" size="540,38"', 'position="1370,1030" size="510,38"'),
    ])

    # Keep OpenATV AdapterSetup contract, move DNS fields fully inside 1920px.
    data = edit_screen(data, "AdapterSetup", [
        ('source="DNS1text" render="Label" position="1400,675" size="225,37"',
         'source="DNS1text" render="Label" position="1340,675" size="250,37"'),
        ('source="DNS2text" render="Label" position="1400,720" size="225,37"',
         'source="DNS2text" render="Label" position="1340,720" size="250,37"'),
        ('source="DNS1" render="Label" position="1640,675" size="300,37"',
         'source="DNS1" render="Label" position="1600,675" size="280,37"'),
        ('source="DNS2" render="Label" position="1640,720" size="300,37"',
         'source="DNS2" render="Label" position="1600,720" size="280,37"'),
    ])

    # The long-key help label was 316px beyond the right edge.
    data = edit_screen(data, "HelpMenu", [
        ('name="long_key" conditional="long_key" position="1636,922" size="600,30"',
         'name="long_key" conditional="long_key" position="1225,922" size="600,30"'),
    ])

    skin_xml.write_text(data, encoding="utf-8")
    checked = validate_xml_tree(skin_dir)
    print("patched=EventView,JobView,AdapterSetup,HelpMenu")
    print(f"xml_validated={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
