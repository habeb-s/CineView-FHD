# -*- coding: utf-8 -*-
"""Shared definitions for tools/build_release.py and tools/verify_release.py."""
import json, os, re

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CFG = json.load(open(os.path.join(ROOT, "packaging", "release.json"), encoding="utf-8"))
CTRL = "usr/lib/enigma2/python/Plugins/Extensions/CineViewControl"


def new_version():
	s = open(os.path.join(ROOT, "updater", "CineViewUpdater", "plugin.py"), encoding="utf-8").read()
	return re.search(r'^PLUGIN_VERSION = "([0-9.]+)"$', s, re.M).group(1)


def vtuple(v):
	return tuple(int(x) for x in v.split("."))


def ipk_name(img, version):
	return "enigma2-plugin-skins-cineview-%s_%s_all.ipk" % (img, version)


def managed(img):
	"""{package path: repository path} of the files copied verbatim into the package of <img>."""
	out = {}
	for group in ("all", img):
		for src, dst in CFG["files"].get(group, {}).items():
			out[dst] = src
	return out


def postinst(version):
	return open(os.path.join(ROOT, "packaging", "postinst.in"), encoding="utf-8").read().replace("@VERSION@", version)


def plugin_edits(base, new):
	"""CineViewControl plugin.py version strings: (old, new, occurrences in the base package)."""
	return [("VERSION='%s'" % base, "VERSION='%s'" % new, 1), ("Official %s" % base, "Official %s" % new, 1)]
