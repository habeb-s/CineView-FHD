#!/usr/bin/env python3
"""Migrate the approved CineView FHD (OpenATV) live skin into the MLA structure as the
"classic" layout of every section.

Faithfulness rules (OpenATV 8.0.1 / enigma2 57b7a51, verified in skin.py):
  * load order of the golden set: skin.xml includes skin_templates.xml, skin_plugins.xml,
    openatv_skin.xml (in that order), and screens of the including file win
    (domScreens[name] is overwritten by each later loadSkin call; the parent's own
    screens are registered after its includes).  -> effective screen = last writer.
  * non-screen data (fonts/parameters/...) of includes is applied before the parent's.
  * "~/x" in attribute values resolves against the directory of the defining file
    (the golden skin root).  The generated files live in sub-folders, so every "~/x"
    is rewritten to the absolute golden-equivalent path in the MLA skin dir.
  * CineView Python components are renamed (CineViewX -> CineViewMLAX) so the MLA skin
    never shares code with an installed stable CineView.

usage: migrate_classic.py <golden CineView_FHD dir> <sections.json> <out dir>
"""
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

SKIN_NAME = "CineView_FHD_MLA"
SKIN_ROOT = "/usr/share/enigma2/" + SKIN_NAME
LOAD_ORDER = ["skin_templates.xml", "skin_plugins.xml", "openatv_skin.xml", "skin.xml"]
COMPONENT_RENAMES = {
	"CineViewPosterX": "CineViewMLAPosterX",
	"CineViewBitrate": "CineViewMLABitrate",
	"CineViewCPUTemp": "CineViewMLACPUTemp",
	"CineViewCamInfo": "CineViewMLACamInfo",
	"CineViewIMDb": "CineViewMLAIMDb",
	"CineViewTransponderInfo": "CineViewMLATransponderInfo",
	"CineViewTransponder": "CineViewMLATransponder",
}
ASSET_DIRS_SKIP = {"allScreens", "mySkin_off"}  # not referenced by the live set (checked by validator)


def tilde_fix(value):
	parts = value.split(",")
	return ",".join((SKIN_ROOT + "/" + p.strip()[2:]) if p.strip().startswith("~/") else p for p in parts)


def rewrite(el):
	for node in el.iter():
		for k, v in list(node.attrib.items()):
			if "~/" in v:
				node.set(k, tilde_fix(v))
			if k == "render" and v in COMPONENT_RENAMES:
				node.set(k, COMPONENT_RENAMES[v])
		if node.tag == "convert" and node.get("type") in COMPONENT_RENAMES:
			node.set("type", COMPONENT_RENAMES[node.get("type")])
	return el


def write_xml(path, root):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	ET.indent(root, space="\t")
	data = ET.tostring(root, encoding="unicode")
	with open(path, "w", encoding="utf-8") as f:
		f.write('<?xml version="1.0" encoding="utf-8"?>\n' + data + "\n")


def main(golden, sections_file, out):
	sections = json.load(open(sections_file))["sections"]
	effective, origin, nonscreen = {}, {}, []
	for fn in LOAD_ORDER:
		root = ET.parse(os.path.join(golden, fn)).getroot()
		for child in root:
			if child.tag == "screen" and child.get("name"):
				effective[child.get("name")] = child
				origin[child.get("name")] = fn
			elif child.tag not in ("include", "screen"):
				nonscreen.append((fn, child))
	report = {"effective_screens": len(effective), "by_origin": {}, "sections": {}, "nonscreen": []}
	for n, fn in origin.items():
		report["by_origin"][fn] = report["by_origin"].get(fn, 0) + 1

	# Theme (colors) — only in skin.xml in the golden set.
	colors = [c for fn, c in nonscreen if c.tag == "colors"]
	assert len(colors) == 1, "expected exactly one <colors> block"
	write_xml(os.path.join(out, "themes", "golden", "theme.xml"), _wrap([copy.deepcopy(colors[0])]))

	# Core base data: includes' non-screen data first (in load order), then parent's.
	base = [copy.deepcopy(c) for fn, c in nonscreen if c.tag not in ("colors", "output")]
	for fn, c in nonscreen:
		report["nonscreen"].append(f"{fn}:{c.tag}")
	write_xml(os.path.join(out, "core", "base.openatv.xml"), _wrap([rewrite(b) for b in base]))
	output = [c for fn, c in nonscreen if c.tag == "output"]

	# Section packs.
	assigned = set()
	for sec, spec in sections.items():
		names = [n for n in spec["required"] + spec.get("optional", []) if n in effective]
		missing = [n for n in spec["required"] if n not in effective]
		assert not missing, f"golden lacks required screens for {sec}: {missing}"
		pack = os.path.join(out, "layouts", sec, "classic")
		write_xml(os.path.join(pack, "screens.openatv.xml"), _wrap([rewrite(copy.deepcopy(effective[n])) for n in names]))
		manifest = {
			"schema": 1, "id": "classic", "section": sec, "name": "CineView Classic",
			"version": "1.0.0", "author": "habeb-s", "license": "CineView-Proprietary",
			"origin": "migrated:approved-live (golden openatv-final-20260926 == slot3 live, sha256 73d7cd9f9425)",
			"targets": {"openatv": {"file": "screens.openatv.xml", "min_version": "8.0.1"}},
			"provides_screens": names, "options": [], "preview": "preview.png",
		}
		json.dump(manifest, open(os.path.join(pack, "manifest.json"), "w"), indent=1)
		assigned.update(names)
		report["sections"][sec] = names

	# Everything else is core/common.
	common = [rewrite(copy.deepcopy(effective[n])) for n in effective if n not in assigned]
	write_xml(os.path.join(out, "core", "common.openatv.xml"), _wrap(common))
	report["core_common_screens"] = len(common)

	# Thin skin.xml: output + ordered includes (theme first: windowstyle needs the colors).
	skin = ET.Element("skin")
	for o in output:
		skin.append(copy.deepcopy(o))
	for inc in ["active/theme.xml", "core/base.openatv.xml", "core/common.openatv.xml"] + [f"active/{s}.xml" for s in sections]:
		ET.SubElement(skin, "include", {"filename": inc})
	write_xml(os.path.join(out, "skin.xml"), skin)

	# Assets: copy every non-XML file/dir of the golden root.
	for entry in sorted(os.listdir(golden)):
		src = os.path.join(golden, entry)
		if entry in ASSET_DIRS_SKIP or entry.endswith(".xml") or ".xml." in entry:
			continue
		dst = os.path.join(out, entry)
		if os.path.isdir(src):
			shutil.copytree(src, dst, dirs_exist_ok=True)
		else:
			shutil.copy2(src, dst)
	json.dump(report, open(os.path.join(out, "MIGRATION_REPORT.json"), "w"), indent=1)
	print(json.dumps({k: v for k, v in report.items() if k != "sections"}, indent=1))
	for s, n in report["sections"].items():
		print(f"  {s}: {n}")


def _wrap(children):
	root = ET.Element("skin")
	for c in children:
		root.append(c)
	return root


if __name__ == "__main__":
	if len(sys.argv) != 4:
		print(__doc__)
		sys.exit(2)
	main(*sys.argv[1:])
