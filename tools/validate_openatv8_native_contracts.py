#!/usr/bin/env python3
"""Strict OpenATV 8 CineView contract + geometry validator."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PROTECTED = {
    "InfoBar",
    "SecondInfoBar",
    "SecondInfoBarECM",
    "PluginBrowser",
    "PluginBrowserList",
    "PluginBrowserGrid",
    "QuickMenu",
    "Setup",
    "SkinSelection",
    "ChannelSelection",
    "SimpleChannelSelection",
    "GraphicalEPG",
    "GraphicalEPGPIG",
    "GraphicalInfoBarEPG",
    "EPGSelection",
    "EPGSelectionMulti",
    "EPGvertical",
    "EPGverticalPIG",
    "EventViewSimple",
    "InfoBarEventView",
    "Satfinder",
    "ScanSetup",
    "ScanSimple",
    "NimSelection",
    "NimSetup",
    "MovieSelection",
}

GEOMETRY_EXCEPTIONS = {
    # Dynamic/intentional OpenATV/CineView overlays.
    "MessageBoxSimple",
    "Standby",
}


def direct_screens(path: Path):
    root = ET.parse(path).getroot()
    out = {}
    duplicates = []
    for s in root.findall("screen"):
        name = s.get("name")
        if not name:
            continue
        if name in out:
            duplicates.append(name)
        out[name] = s
    if duplicates:
        raise AssertionError("duplicate authoritative screens: " + ", ".join(sorted(set(duplicates))))
    return out


def widget_tuples(screen):
    return [
        (e.tag, e.get("name"), e.get("source"), e.get("render"))
        for e in list(screen)
        if e.tag in {"widget", "panel"}
    ]


def has_source(screen, source: str) -> bool:
    return any(e.get("source") == source for e in list(screen) if e.tag == "widget")


def has_name(screen, name: str) -> bool:
    return any(e.get("name") == name for e in list(screen) if e.tag == "widget")


def canonical_hash(screen) -> str:
    return hashlib.sha256(ET.tostring(screen, encoding="utf-8")).hexdigest()


def require_screen(screens, name):
    if name not in screens:
        raise AssertionError(f"missing screen: {name}")
    return screens[name]


def assert_contracts(screens):
    # OpenATV 8 PluginBrowser is source/list based, not OpenViX widget name=list.
    pbl = require_screen(screens, "PluginBrowserList")
    pbg = require_screen(screens, "PluginBrowserGrid")
    if not has_source(pbl, "pluginList"):
        raise AssertionError("PluginBrowserList missing OpenATV source pluginList")
    if not has_source(pbg, "pluginGrid"):
        raise AssertionError("PluginBrowserGrid missing OpenATV source pluginGrid")

    qm = require_screen(screens, "QuickMenu")
    for src in ("mainlist", "sublist"):
        if not has_source(qm, src):
            raise AssertionError(f"QuickMenu missing OpenATV source {src}")

    sat = require_screen(screens, "Satfinder")
    if not has_source(sat, "Frontend") or not has_name(sat, "config"):
        raise AssertionError("Satfinder must keep OpenATV Frontend + config contract")

    # The shared EventView is also used by EventViewMovieEvent, which does NOT
    # expose Event / Service / FullDescription. Keep the common subset only.
    ev = require_screen(screens, "EventView")
    for name in ("channel", "datetime", "duration", "epg_description"):
        if not has_name(ev, name):
            raise AssertionError(f"EventView missing common component {name}")
    forbidden_names = {"FullDescription"}
    forbidden_sources = {
        "Event", "Service", "session.Event_Now", "session.Event_Next",
        "session.CurrentService", "session.FrontendStatus", "session.OAWeather",
    }
    for e in list(ev):
        if e.get("name") in forbidden_names:
            raise AssertionError(f"EventView unsafe component {e.get('name')}")
        if e.get("source") in forbidden_sources:
            raise AssertionError(f"EventView unsafe source {e.get('source')}")

    # Preserve the user's approved dual-event SecondInfoBar visual.
    sib = require_screen(screens, "SecondInfoBar")
    for src in ("session.Event_Now", "session.Event_Next"):
        if not has_source(sib, src):
            raise AssertionError(f"SecondInfoBar regression: missing {src}")

    # OpenATV EPG family.
    ge = require_screen(screens, "GraphicalEPG")
    for name in ("bouquetlist", "timeline_text", "timeline_now", "list"):
        if not has_name(ge, name):
            raise AssertionError(f"GraphicalEPG missing {name}")
    for epg_name in (
        "GraphicalEPGPIG", "GraphicalInfoBarEPG", "EPGSelection",
        "EPGSelectionMulti", "EPGvertical", "EPGverticalPIG",
    ):
        require_screen(screens, epg_name)


_num = re.compile(r"^-?\d+$")


def geometry_issues(screens):
    bad = []
    for name, s in screens.items():
        if name in GEOMETRY_EXCEPTIONS:
            continue
        size = s.get("size", "")
        if s.get("position") == "fill" or not size:
            sw, sh = 1920, 1080
        else:
            try:
                sw, sh = map(int, size.split(","))
            except Exception:
                continue
        for e in list(s):
            pos, esize = e.get("position", ""), e.get("size", "")
            if "," not in pos or "," not in esize:
                continue
            a, b = pos.split(","), esize.split(",")
            if len(a) != 2 or len(b) != 2:
                continue
            vals = [x.strip() for x in a + b]
            if not all(_num.match(x) for x in vals):
                continue
            x, y, w, h = map(int, vals)
            if x < 0 or y < 0 or x + w > sw or y + h > sh:
                bad.append((name, e.tag, e.get("name") or e.get("source") or "", pos, esize, sw, sh))
    return bad


def compare_protected(candidate, reference):
    changed = []
    for name in sorted(PROTECTED):
        if name in candidate and name in reference:
            if canonical_hash(candidate[name]) != canonical_hash(reference[name]):
                changed.append(name)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skin_dir", type=Path)
    ap.add_argument("--reference", type=Path)
    args = ap.parse_args()

    skin_xml = args.skin_dir / "skin.xml"
    screens = direct_screens(skin_xml)
    assert_contracts(screens)

    bad = geometry_issues(screens)
    if bad:
        for row in bad:
            print("OOB", "|".join(map(str, row)))
        raise SystemExit(f"geometry failures: {len(bad)}")

    if args.reference:
        ref = direct_screens(args.reference / "skin.xml")
        changed = compare_protected(screens, ref)
        if changed:
            raise SystemExit("protected OpenATV screens changed: " + ", ".join(changed))

    for path in sorted(args.skin_dir.rglob("*.xml")):
        ET.parse(path)

    print("OPENATV8_CONTRACTS_OK")
    print(f"authoritative_screens={len(screens)}")
    print(f"protected_screens={len(PROTECTED)}")
    print("geometry=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
