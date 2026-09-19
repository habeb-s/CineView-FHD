#!/usr/bin/env python3
from __future__ import print_function

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def apply_adapter(adapter, skin_dir):
    subprocess.check_call([sys.executable, adapter, skin_dir])


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
        })
    return out


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

    report = {"files": {}, "summary": {"geometry_mismatches": 0, "duplicates": 0}}
    geometry_mismatches = []

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

        if f["mismatches"] or f["duplicates"]:
            report["files"][name] = f

    print("CineView OpenATV/OpenBH geometry parity audit")
    print("skin files:", len(files))
    print("geometry mismatches:", report["summary"]["geometry_mismatches"])
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

    if args.report:
        with open(args.report, "w") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)

    shutil.rmtree(tmp, ignore_errors=True)
    if args.strict and (report["summary"]["geometry_mismatches"] or report["summary"]["duplicates"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
