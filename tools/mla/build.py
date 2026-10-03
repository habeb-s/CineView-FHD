#!/usr/bin/env python3
"""Build the installable CineView MLA tree (OpenATV) from the approved golden live set.

usage: build.py <golden CineView_FHD dir> <golden python Components dir> <golden CineViewControl dir> <out root>

Output layout (relative to <out root>, mirrors the receiver's filesystem):
  usr/share/enigma2/CineView_FHD_MLA/            skin (thin skin.xml, core/, layouts/, themes/, assets, generations/g000000, active -> g000000)
  usr/share/enigma2/CineView_FHD_MLA/mla/        sections.json + engine/
  usr/lib/enigma2/python/Components/{Renderer,Converter}/CineViewMLA*.py
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SKIN = "usr/share/enigma2/CineView_FHD_MLA"
PY = "usr/lib/enigma2/python/Components"
DEFAULT_THEME = "navy"
POSTER_PATCH_OLD = "CACHE_ROOT = _cineview_poster_cache_root()\n"
POSTER_PATCH_NEW = '''def _mla_cache_root():
    # CineView MLA: explicit, isolated cache.  Never the HDD block device (checked by st_dev,
    # not by path name).  Configured in /etc/enigma2/cineview_mla/runtime.json ("poster_cache").
    default = "/media/usb/cineview-mla/dev-cache/mla/poster"
    path = default
    try:
        import json as _json
        path = _json.load(open("/etc/enigma2/cineview_mla/runtime.json")).get("poster_cache", default)
    except Exception:
        pass
    deny = set()
    for src, mp, fstype, opts in _cineview_mounts():
        if mp in ("/media/hdd", "/hdd") or src.startswith("UUID=ea5ccf03"):
            try:
                deny.add(os.stat(mp).st_dev)
            except OSError:
                pass
    try:
        if not os.path.isdir(path):
            os.makedirs(path)
        if os.stat(path).st_dev not in deny and os.access(path, os.W_OK):
            return path
    except Exception:
        pass
    fallback = "/tmp/CINEVIEW-MLA/poster"
    try:
        if not os.path.isdir(fallback):
            os.makedirs(fallback)
    except Exception:
        pass
    return fallback

CACHE_ROOT = _mla_cache_root()
'''


def run(*a):
	subprocess.check_call(list(a))


def load_theme_module(control_dir):
	spec = importlib.util.spec_from_file_location("cv_theme", os.path.join(control_dir, "theme.py"))
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	return m


def main(golden, comps, control, out):
	skin = os.path.join(out, SKIN)
	if os.path.exists(out):
		shutil.rmtree(out)
	run(sys.executable, os.path.join(HERE, "migrate_classic.py"), golden, os.path.join(REPO, "mla", "sections.json"), skin)

	# Themes: the original CineView palette() applied to the golden <colors>; navy == golden (verified).
	theme = load_theme_module(control)
	tpl = open(os.path.join(skin, "themes", "golden", "theme.xml"), encoding="utf-8").read()
	for key in theme.THEMES:
		data = tpl
		for name, val in theme.palette(key).items():
			pat = r'(<color\s+name="' + re.escape(name) + r'"\s+value=")#[0-9A-Fa-f]{8}(")'
			data, n = re.subn(pat, lambda m: m.group(1) + val + m.group(2), data, count=1)
			assert n == 1, f"theme color {name} missing"
		os.makedirs(os.path.join(skin, "themes", key), exist_ok=True)
		open(os.path.join(skin, "themes", key, "theme.xml"), "w", encoding="utf-8").write(data)
		json.dump({"id": key, "label": theme.THEMES[key][0], "base": theme.THEMES[key][1]}, open(os.path.join(skin, "themes", key, "theme.json"), "w"))
	assert open(os.path.join(skin, "themes", "navy", "theme.xml")).read() == tpl, "navy must equal golden colors"
	shutil.rmtree(os.path.join(skin, "themes", "golden"))
	# Per-theme bitmap assets of the original theme engine (if shipped).
	src_theme_assets = os.path.join(golden, "themes")
	if os.path.isdir(src_theme_assets):
		for key in os.listdir(src_theme_assets):
			shutil.copytree(os.path.join(src_theme_assets, key), os.path.join(skin, "themes", key, "assets"), dirs_exist_ok=True)

	# Engine + section definitions.
	shutil.copytree(os.path.join(REPO, "mla", "engine"), os.path.join(skin, "mla", "engine"))
	shutil.copy2(os.path.join(REPO, "mla", "sections.json"), os.path.join(skin, "mla", "sections.json"))

	# Python components: renamed copies, isolated config + isolated poster cache.
	sys.path.insert(0, HERE)
	from migrate_classic import COMPONENT_RENAMES
	for kind in ("Renderer", "Converter"):
		os.makedirs(os.path.join(out, PY, kind), exist_ok=True)
		for f in sorted(os.listdir(os.path.join(comps, kind))):
			base = f[:-3]
			if not f.endswith(".py") or base not in COMPONENT_RENAMES:
				continue
			src = open(os.path.join(comps, kind, f), encoding="utf-8").read()
			for old, new in sorted(COMPONENT_RENAMES.items(), key=lambda kv: -len(kv[0])):
				src = re.sub(r"\b" + old + r"\b", new, src)
			src = src.replace("config.plugins.cineview.", "config.plugins.cineviewmla.").replace('hasattr(config.plugins, "cineview")', 'hasattr(config.plugins, "cineviewmla")').replace("config.plugins.cineview =", "config.plugins.cineviewmla =").replace('hasattr(config.plugins.cineview,', 'hasattr(config.plugins.cineviewmla,')
			if base == "CineViewPosterX":
				assert src.count(POSTER_PATCH_OLD) == 1
				src = src.replace(POSTER_PATCH_OLD, POSTER_PATCH_NEW).replace('"/tmp/CINEVIEW"', '"/tmp/CINEVIEW-MLA"').replace("/tmp/CINEVIEW/poster.log", "/tmp/CINEVIEW-MLA/poster.log")
			open(os.path.join(out, PY, kind, COMPONENT_RENAMES[base] + ".py"), "w", encoding="utf-8").write(src)

	# Factory generation g000000 (= classic everywhere, navy) built by the real engine.
	os.makedirs(os.path.join(skin, "generations"), exist_ok=True)
	env = dict(os.environ, MLA_SKIN_DIR=skin, MLA_STATE_DIR=os.path.join(out, "_buildstate"))
	spec = importlib.util.spec_from_file_location("mla_composer", os.path.join(skin, "mla", "engine", "composer.py"))
	os.environ.update({"MLA_SKIN_DIR": skin, "MLA_STATE_DIR": env["MLA_STATE_DIR"]})
	comp = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(comp)
	sel = {"theme": DEFAULT_THEME, "layouts": {s: "classic" for s in comp.sections()}}
	problems = comp.validate(sel)
	if problems:
		print("VALIDATION (build, no device components):")
		print("\n".join("  " + p for p in problems))
	os.makedirs(os.path.join(skin, "generations", comp.FACTORY))
	os.rmdir(os.path.join(skin, "generations", comp.FACTORY))
	comp.build_generation(sel, comp.FACTORY)
	assert comp.verify_generation(comp.FACTORY)
	os.symlink(os.path.join("generations", comp.FACTORY), os.path.join(skin, "active"))
	shutil.rmtree(env["MLA_STATE_DIR"], ignore_errors=True)
	files = sum(len(f) for _, _, f in os.walk(out))
	print(f"BUILD OK: {files} files -> {out}")


if __name__ == "__main__":
	if len(sys.argv) != 5:
		print(__doc__)
		sys.exit(2)
	main(*sys.argv[1:])
