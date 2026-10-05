#!/usr/bin/env python3
"""Dry run of the poster-cache policy on the receiver (no file or directory is created): extracts
_cineview_mounts / _cineview_is_multiboot_mount / _mla_cache_plan from the installed CineViewMLAPosterX.py and prints
the choice (1) with the development runtime.json and (2) as a release install would see it (runtime.json hidden)."""
import ast
import builtins
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "/usr/lib/enigma2/python/Components/Renderer/CineViewMLAPosterX.py"
tree = ast.parse(open(SRC).read())
want = {"_cineview_mounts", "_cineview_is_multiboot_mount", "_mla_cache_plan"}
code = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in want]
missing = want - {n.name for n in code}
ns = {"os": os, "re": __import__("re")}
exec(compile(ast.Module(body=code, type_ignores=[]), SRC, "exec"), ns)
print("functions:", sorted(n.name for n in code), "missing:", sorted(missing))
print("1. development  :", ns["_mla_cache_plan"]())
real_open = builtins.open


def fake_open(path, *a, **k):
	if str(path).endswith("cineview_mla/runtime.json"):
		raise FileNotFoundError(path)
	return real_open(path, *a, **k)


builtins.open = fake_open
try:
	print("2. release view :", ns["_mla_cache_plan"]())
finally:
	builtins.open = real_open
for mp in ("/media/hdd", "/media/usb"):
	try:
		print("   %-10s ismount=%s dev=%s root_dev=%s" % (mp, os.path.ismount(mp), os.stat(mp).st_dev, os.stat("/").st_dev))
	except OSError as e:
		print("  ", mp, e)
print("   /media/hdd/poster exists:", os.path.isdir("/media/hdd/poster"), "(read only check)")
