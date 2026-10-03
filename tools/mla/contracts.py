#!/usr/bin/env python3
"""Extract Enigma2 Screen contracts (skinName + self[...] widgets/sources) from an
OpenATV enigma2 source tree, and check skin XML screens against them.

usage:
  contracts.py extract <enigma2/lib/python> <out.json>
  contracts.py check   <contracts.json> <skin.xml> [<skin2.xml> ...] [--screens A,B,...]

Static analysis only: a missing match is a finding to verify on the device,
not proof of a runtime failure (screens can be fed by plugins or dynamic names).
"""
import ast
import json
import os
import sys
import xml.etree.ElementTree as ET

GLOBAL_SOURCES = ("session.", "global.", "Title", "ServiceEvent", "Event", "CurrentService")


def _str_values(node):
	"""String literals found in a skinName assignment value."""
	out = []
	for n in ast.walk(node):
		if isinstance(n, ast.Constant) and isinstance(n.value, str):
			out.append(n.value)
	return out


def extract(root):
	classes = {}
	for dirpath, _, files in os.walk(root):
		for f in files:
			if not f.endswith(".py"):
				continue
			path = os.path.join(dirpath, f)
			rel = os.path.relpath(path, root)
			try:
				tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
			except SyntaxError:
				continue
			for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
				info = classes.setdefault(cls.name, {"file": rel, "bases": [], "keys": {}, "skinNames": []})
				info["bases"] = [b.id if isinstance(b, ast.Name) else getattr(b, "attr", "?") for b in cls.bases]
				for n in ast.walk(cls):
					if isinstance(n, ast.Assign):
						for t in n.targets:
							if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == "self"
									and isinstance(t.slice, ast.Constant) and isinstance(t.slice.value, str)):
								kind = "?"
								if isinstance(n.value, ast.Call):
									fn = n.value.func
									kind = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "?")
								info["keys"].setdefault(t.slice.value, kind)
							if (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self"
									and t.attr == "skinName"):
								for s in _str_values(n.value):
									if s not in info["skinNames"]:
										info["skinNames"].append(s)
	return classes


def resolved_keys(classes, name, seen=None):
	seen = seen or set()
	if name in seen or name not in classes:
		return {}
	seen.add(name)
	keys = {}
	for b in classes[name]["bases"]:
		keys.update(resolved_keys(classes, b, seen))
	keys.update(classes[name]["keys"])
	return keys


def check(contracts, skin_files, only=None):
	classes = contracts
	by_screen = {}
	for cname, info in classes.items():
		for s in [cname] + info["skinNames"]:
			by_screen.setdefault(s, set()).add(cname)
	screens = {}
	for f in skin_files:
		for s in ET.parse(f).getroot().iter("screen"):
			if s.get("name"):
				screens[s.get("name")] = s  # last loaded file wins only within this list order
	report = {}
	for name, el in sorted(screens.items()):
		if only and name not in only:
			continue
		owners = sorted(by_screen.get(name, []))
		keys = {}
		for o in owners:
			keys.update(resolved_keys(classes, o))
		missing = []
		for w in el.iter("widget"):
			ref = w.get("name") or w.get("source")
			if not ref or ref.startswith(GLOBAL_SOURCES):
				continue
			base = ref.split(".")[0]
			if base not in keys:
				missing.append(ref)
		report[name] = {"owners": owners, "missing": sorted(set(missing)), "known_keys": len(keys)}
	return report


def main():
	if len(sys.argv) >= 4 and sys.argv[1] == "extract":
		data = extract(sys.argv[2])
		json.dump(data, open(sys.argv[3], "w"), indent=1, sort_keys=True)
		print("classes:", len(data))
	elif len(sys.argv) >= 4 and sys.argv[1] == "check":
		only = None
		args = sys.argv[3:]
		if "--screens" in args:
			i = args.index("--screens")
			only = set(args[i + 1].split(","))
			args = args[:i] + args[i + 2:]
		rep = check(json.load(open(sys.argv[2])), args, only)
		for k, v in rep.items():
			flag = "OK " if v["owners"] and not v["missing"] else ("NO-OWNER" if not v["owners"] else "MISSING")
			print(f"{flag:8} {k:28} owners={','.join(v['owners'])[:60]} missing={v['missing']}")
	else:
		print(__doc__)
		sys.exit(2)


if __name__ == "__main__":
	main()
