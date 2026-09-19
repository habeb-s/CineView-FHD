#!/usr/bin/env python3
from __future__ import print_function

import argparse
import json
from collections import Counter
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def apply_adapter(adapter, skin_dir):
    subprocess.check_call([sys.executable, adapter, skin_dir])


def visual_slots(node):
    slots = []
    for child in list(node):
        if child.tag not in ("widget", "eLabel", "ePixmap", "panel"):
            continue
        pos = child.get("position")
        size = child.get("size")
        if not pos and not size:
            continue
        slots.append((
            child.tag,
            pos,
            size,
            child.get("font"),
        ))
    return slots


def screen_map(path):
    root = ET.parse(path).getroot()
    out = {}
    for node in root.iter("screen"):
        name = node.get("name")
        if not name:
            continue
        out.setdefault(name, []).append({
            "position": node.get("position"),
            "size": node.get("size"),
            "title": node.get("title"),
            "visual_slots": visual_slots(node),
        })
    return out


def allowed_openbh_missing_slots(screen, slots):
    """Platform-contract exceptions, not visual regressions.

    OpenBH PluginBrowser has no quickselect/description components. Keep the
    approved OpenATV coordinates for every supported widget and ignore only
    those two unsupported visual slots.
    """
    if screen not in ("PluginBrowser", "PluginBrowserList", "PluginBrowserGrid"):
        return slots
    allowed = {
        ("widget", "45,110", "1830,800", "Regular;120"),
        ("widget", "45,110", "1830,820", "Regular;120"),
        ("widget", "55,925", "1810,55", "Regular;24"),
    }
    return [slot for slot in slots if tuple(slot) not in allowed]


OPENBH_ONLY_EXPECTATIONS = {
    "DeliteGreenPanel": {
        "screen": ("center,center", "1820,880"),
        "slots": [
            ("eLabel", "0,0", "1820,880", None),
            ("widget", "45,115", "1730,625", None),
        ],
    },
    "DeliteBluePanel": {
        "screen": ("center,center", "1820,880"),
        "slots": [
            ("eLabel", "0,0", "1820,880", None),
            ("widget", "895,195", "835,545", "Regular;24"),
        ],
    },
    "DeliteSetupFp": {
        "screen": ("center,center", "1820,880"),
        "slots": [
            ("eLabel", "0,0", "1820,880", None),
            ("widget", "45,115", "1730,625", None),
        ],
    },
    "BhSetupGreen": {
        "screen": ("center,center", "1820,880"),
        "slots": [
            ("eLabel", "0,0", "1820,880", None),
            ("widget", "45,115", "1730,690", None),
        ],
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin-dir", required=True)
    ap.add_argument("--openatv-adapter", required=True)
    ap.add_argument("--openbh-adapter", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="cineview-parity-")
    atv = os.path.join(tmp, "atv")
    bh = os.path.join(tmp, "bh")
    shutil.copytree(args.skin_dir, atv)
    shutil.copytree(args.skin_dir, bh)

    apply_adapter(args.openatv_adapter, atv)
    apply_adapter(args.openbh_adapter, bh)

    files = sorted(set(
        x for x in os.listdir(atv)
        if x.startswith("skin") and x.endswith(".xml")
    ) & set(
        x for x in os.listdir(bh)
        if x.startswith("skin") and x.endswith(".xml")
    ))

    report = {"files": {}, "summary": {"geometry_mismatches": 0, "child_geometry_mismatches": 0, "openbh_only_failures": 0, "duplicates": 0}}
    geometry_mismatches = []
    child_mismatches = []

    for name in files:
        apath = os.path.join(atv, name)
        bpath = os.path.join(bh, name)
        amap = screen_map(apath)
        bmap = screen_map(bpath)
        common = sorted(set(amap) & set(bmap))
        f = {"mismatches": [], "duplicates": []}

        for screen in common:
            if len(amap[screen]) != 1 or len(bmap[screen]) != 1:
                item = {
                    "screen": screen,
                    "openatv_count": len(amap[screen]),
                    "openbh_count": len(bmap[screen]),
                }
                f["duplicates"].append(item)
                report["summary"]["duplicates"] += 1
                continue
            ag = (amap[screen][0].get("position"), amap[screen][0].get("size"))
            bg = (bmap[screen][0].get("position"), bmap[screen][0].get("size"))
            if ag != bg:
                item = {
                    "screen": screen,
                    "openatv": {"position": ag[0], "size": ag[1]},
                    "openbh": {"position": bg[0], "size": bg[1]},
                }
                f["mismatches"].append(item)
                geometry_mismatches.append((name, item))
                report["summary"]["geometry_mismatches"] += 1

            ac = Counter(tuple(x) for x in amap[screen][0]["visual_slots"])
            bc = Counter(tuple(x) for x in bmap[screen][0]["visual_slots"])
            if ac != bc:
                missing = allowed_openbh_missing_slots(screen, list((ac - bc).elements()))
                extra = list((bc - ac).elements())
                if missing or extra:
                    item = {
                        "screen": screen,
                        "missing_openatv_slots": [list(x) for x in missing[:30]],
                        "extra_openbh_slots": [list(x) for x in extra[:30]],
                        "missing_count": len(missing),
                        "extra_count": len(extra),
                    }
                    f.setdefault("child_mismatches", []).append(item)
                    child_mismatches.append((name, item))
                    report["summary"]["child_geometry_mismatches"] += 1

        # OpenBH-only screens have no OpenATV peer. Enforce full CineView
        # geometry explicitly so they cannot regress to small native dialogs.
        for screen, expected in OPENBH_ONLY_EXPECTATIONS.items():
            nodes = bmap.get(screen, [])
            if len(nodes) != 1:
                continue
            node = nodes[0]
            failed = []
            if (node.get("position"), node.get("size")) != expected["screen"]:
                failed.append("screen")
            slots = set(tuple(x) for x in node.get("visual_slots", []))
            for slot in expected["slots"]:
                if slot not in slots:
                    failed.append("slot:%s/%s" % (slot[1], slot[2]))
            if failed:
                f.setdefault("openbh_only_failures", []).append({
                    "screen": screen,
                    "failed": failed,
                })
                report["summary"]["openbh_only_failures"] += 1

        if f["mismatches"] or f["duplicates"] or f.get("child_mismatches") or f.get("openbh_only_failures"):
            report["files"][name] = f

    print("CineView OpenATV/OpenBH geometry parity audit")
    print("skin files:", len(files))
    print("geometry mismatches:", report["summary"]["geometry_mismatches"])
    print("child geometry mismatches:", report["summary"]["child_geometry_mismatches"])
    print("OpenBH-only coverage failures:", report["summary"]["openbh_only_failures"])
    print("duplicate screen mismatches:", report["summary"]["duplicates"])
    for filename, item in geometry_mismatches:
        print("MISMATCH %s :: %s :: ATV %s %s :: BH %s %s" % (
            filename,
            item["screen"],
            item["openatv"]["position"],
            item["openatv"]["size"],
            item["openbh"]["position"],
            item["openbh"]["size"],
        ))
    for filename, item in child_mismatches:
        print("CHILD_MISMATCH %s :: %s :: missing_atv=%d extra_bh=%d" % (
            filename,
            item["screen"],
            item["missing_count"],
            item["extra_count"],
        ))

    if args.report:
        with open(args.report, "w") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)

    shutil.rmtree(tmp, ignore_errors=True)
    if args.strict and (
        report["summary"]["geometry_mismatches"]
        or report["summary"]["child_geometry_mismatches"]
        or report["summary"]["openbh_only_failures"]
        or report["summary"]["duplicates"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
