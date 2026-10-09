#!/usr/bin/env python3
"""CineView MLA composition engine (pure Python, no enigma2 imports).

Builds an immutable "generation" (theme + one layout pack per section), seals it with a
SHA-256 manifest written last, and switches the skin's `active` symlink atomically.
A transaction journal makes every step recoverable after a crash or power loss.

CLI (on the receiver):
  composer.py status
  composer.py validate  [--theme T] [--set section=layout ...]
  composer.py apply     [--theme T] [--set section=layout ...] [--trial]
  composer.py commit                         # mark current generation as last-known-good
  composer.py rollback  [--to lkg|factory]
  composer.py recover                        # used at boot / after interruption (includes ensure)
  composer.py ensure                         # rebuild active for the installed optional plugins (weather)
Environment overrides (tests): MLA_SKIN_DIR, MLA_STATE_DIR, MLA_FAULT=<step>, MLA_COMPONENTS_ROOT
"""
import hashlib
import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET

SKIN_DIR = os.environ.get("MLA_SKIN_DIR", "/usr/share/enigma2/CineView_FHD_MLA")
STATE_DIR = os.environ.get("MLA_STATE_DIR", "/etc/enigma2/cineview_mla")
FACTORY = "g000000"
ENIGMA_INFO = "/usr/lib/enigma.info"
DEFAULT_IMAGE = "openatv"  # the image every layout pack provides a screen file for (targets.openatv)
# Bitmaps that differ per colour theme (the original CineView theme engine swapped exactly these).
THEME_ASSETS = ("infobar/hd.png", "infobar/bl80.png", "extensions/transblack.png", "infobar/pbar.png",
	"window/progress.png", "dvr/position_pointer1.png", "epg/CurrentEvent.png")  # skin paths are symlinks to active/assets
KEEP = 3
# Optional features: widgets that need components of a PLUGIN the image may not have installed.  When any of a
# feature's components is missing on the receiver, exactly these widgets are left out of the generation (the rest
# of the design is unchanged) and validation checks that pruned generation - the one Enigma2 really loads.  Every
# other missing renderer/converter still blocks.  OAWeather (oe-alliance plugin) provides session.OAWeather, the
# OAWeather converter and the OAWeatherPixmap renderer; it is not part of every OpenATV/OpenViX/OpenBH install.
OPTIONAL_FEATURES = {
	"weather": {"source": "session.OAWeather", "Renderer": {"OAWeatherPixmap"}, "Converter": {"OAWeather"}, "Sources": {"OAWeather"}},
}
FEATURES_FILE = "features.json"  # inside a generation: features left out when it was built
BUILTIN_COLORS = {"key_back", "key_blue", "key_green", "key_red", "key_text", "key_yellow", "transparent", "black", "white",
	"red", "green", "blue", "yellow", "grey", "gray", "orange", "foreground", "background", "darkgrey", "lightgrey", "cyan", "magenta"}


class MLAError(Exception):
	pass


def image():
	"""Target image of the screen files: MLA_IMAGE (package build) or the receiver's /usr/lib/enigma.info distro;
	openatv when neither is available.  Never derived from a receiver model."""
	img = os.environ.get("MLA_IMAGE")
	if not img:
		try:
			for line in open(ENIGMA_INFO):
				if line.startswith("distro="):
					img = line.split("=", 1)[1].strip().strip("'\"").lower()
					break
		except OSError:
			pass
	return img or DEFAULT_IMAGE


def target_file(layout):
	"""The layout pack's screen file for this image: its own override when the native contract differs
	(targets.<image>), otherwise the shared file (targets.openatv)."""
	t = layout["targets"]
	return (t.get(image()) or t[DEFAULT_IMAGE])["file"]


def core_files():
	"""Core screen files in load order; an image override (core/common.<image>.xml, shipped only in that image's
	package) follows the shared files - the last definition of a screen wins in the skin loader."""
	files = [_p("core", "base.openatv.xml"), _p("core", "common.openatv.xml")]
	extra = _p("core", "common.%s.xml" % image())
	if image() != DEFAULT_IMAGE and os.path.isfile(extra):
		files.append(extra)
	return files


def _p(*a):
	return os.path.join(SKIN_DIR, *a)


def _s(*a):
	return os.path.join(STATE_DIR, *a)


def _fault(step):
	if os.environ.get("MLA_FAULT") == step:
		raise MLAError("injected fault at " + step)


def _fsync_file(path):
	fd = os.open(path, os.O_RDONLY)
	try:
		os.fsync(fd)
	finally:
		os.close(fd)


def _fsync_dir(path):
	fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
	try:
		os.fsync(fd)
	finally:
		os.close(fd)


def _atomic_write(path, data):
	tmp = path + ".tmp"
	with open(tmp, "w", encoding="utf-8") as f:
		f.write(data)
		f.flush()
		os.fsync(f.fileno())
	os.replace(tmp, path)
	_fsync_dir(os.path.dirname(path))


def _log(msg):
	os.makedirs(STATE_DIR, exist_ok=True)
	line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n"
	path = _s("history.log")
	try:
		if os.path.exists(path) and os.path.getsize(path) > 65536:
			os.replace(path, path + ".1")
		with open(path, "a", encoding="utf-8") as f:
			f.write(line)
	except OSError:
		pass
	sys.stderr.write(line)


def _sha(path):
	h = hashlib.sha256()
	with open(path, "rb") as f:
		for b in iter(lambda: f.read(1 << 16), b""):
			h.update(b)
	return h.hexdigest()


# ---------------------------------------------------------------- registry
def sections():
	"""Section definitions; an image package may ship mla/sections.<image>.json with per-section replacements of
	"required"/"optional" (screens that image's native contract has / lacks)."""
	secs = json.load(open(_p("mla", "sections.json")))["sections"]
	extra = _p("mla", "sections.%s.json" % image())
	if image() != DEFAULT_IMAGE and os.path.isfile(extra):
		for sec, over in json.load(open(extra)).get("sections", {}).items():
			if sec in secs:
				secs[sec].update({k: v for k, v in over.items() if k in ("required", "optional")})
	return secs


def layouts():
	out = {}
	base = _p("layouts")
	for sec in sorted(os.listdir(base)):
		for lid in sorted(os.listdir(os.path.join(base, sec))):
			mf = os.path.join(base, sec, lid, "manifest.json")
			if os.path.isfile(mf):
				try:
					out.setdefault(sec, {})[lid] = json.load(open(mf))
				except ValueError as e:
					_log(f"registry: broken manifest {mf}: {e}")
	return out


def themes():
	base = _p("themes")
	return sorted(t for t in os.listdir(base) if os.path.isfile(os.path.join(base, t, "theme.xml")))


def current_selection():
	try:
		return json.load(open(_s("selection.json")))
	except (OSError, ValueError):
		return {"theme": "navy", "layouts": {s: "classic" for s in sections()}}


# ---------------------------------------------------------------- optional features
def unavailable_features(components):
	"""Optional features whose components are not all installed.  components=None (not on a receiver): none."""
	if components is None:
		return []
	out = []
	for feat, spec in sorted(OPTIONAL_FEATURES.items()):
		for kind in ("Renderer", "Converter", "Sources"):
			if kind in components and not spec[kind] <= components[kind]:
				out.append(feat)
				break
	return out


def _is_feature_widget(node, feats):
	if node.tag != "widget":
		return False
	for f in feats:
		spec = OPTIONAL_FEATURES[f]
		if node.get("source") == spec["source"] or node.get("render") in spec["Renderer"]:
			return True
		if any(c.tag == "convert" and c.get("type") in spec["Converter"] for c in node.iter()):
			return True
	return False


def _prune(root, feats):
	"""Remove the widgets of the given (unavailable) features; returns how many were removed."""
	if not feats:
		return 0
	n = 0
	for parent in list(root.iter()):
		for child in list(parent):
			if _is_feature_widget(child, feats):
				parent.remove(child)
				n += 1
	return n


def _parse(path):
	return ET.parse(path, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))


def generation_omitted(gid):
	try:
		return sorted(json.load(open(os.path.join(_gen_dir(gid), FEATURES_FILE))).get("omitted", []))
	except (OSError, ValueError, AttributeError):
		return []  # generations built before 1.0.4: nothing was left out


# ---------------------------------------------------------------- validation
def _screens(path, feats=()):
	root = _parse(path).getroot()
	_prune(root, feats)
	return {s.get("name"): s for s in root.iter("screen") if s.get("name")}


def validate(selection, components=None, warnings=None):
	"""Static checks of a selection. Returns blocking problems (empty = OK).
	Problems found in core/common screens (often plugin screens whose components ship with
	the plugin) are appended to `warnings` instead of blocking."""
	problems = []
	section_files = set()
	feats = unavailable_features(components)  # their widgets are not part of the generation that will be built
	secs, lays = sections(), layouts()
	if selection["theme"] not in themes():
		problems.append(f"unknown theme {selection['theme']}")
	files = core_files()
	for sec, spec in secs.items():
		lid = selection["layouts"].get(sec)
		if lid not in lays.get(sec, {}):
			problems.append(f"{sec}: unknown layout {lid}")
			continue
		f = _p("layouts", sec, lid, target_file(lays[sec][lid]))
		names = set(_screens(f))
		for req in spec["required"]:
			if req not in names:
				problems.append(f"{sec}/{lid}: missing required screen {req}")
		files.append(f)
		section_files.add(f)
	seen, colors = {}, set(BUILTIN_COLORS)
	theme_file = _p("themes", selection["theme"], "theme.xml")
	if os.path.isfile(theme_file):
		colors |= {c.get("name") for c in ET.parse(theme_file).getroot().iter("color")}
	all_screens = {}
	for f in files:
		try:
			scr = _screens(f, feats)
		except ET.ParseError as e:
			problems.append(f"XML error {f}: {e}")
			continue
		override = os.path.basename(f) == "common.%s.xml" % image() and image() != DEFAULT_IMAGE
		for n in scr:
			if n in seen and override and os.path.basename(seen[n]) in ("base.openatv.xml", "common.openatv.xml"):
				pass  # intended: the image's core override replaces the shared screen (last definition wins)
			elif n in seen:
				problems.append(f"duplicate screen {n} in {os.path.basename(f)} and {os.path.basename(seen[n])}")
			seen[n] = f
		all_screens.update(scr)
	for n, el in all_screens.items():
		sink = problems if seen.get(n) in section_files else (warnings if warnings is not None else [])
		for node in el.iter():
			if node.tag == "panel" and node.get("name") and node.get("name") not in all_screens:
				sink.append(f"{n}: panel '{node.get('name')}' not defined")
			for k, v in node.attrib.items():
				# numeric values are flags, not colours (EMC MovieCenter: CoolDateColor="1", CoolTitleColor="1")
				if k.lower().endswith("color") and v and not v.startswith("#") and v not in colors and "," not in v and not v.isdigit():
					sink.append(f"{n}: color '{v}' not defined")
			if components is not None:
				r = node.get("render")
				if r and r not in components["Renderer"]:
					sink.append(f"{n}: renderer {r} not installed")
				if node.tag == "convert" and node.get("type") not in components["Converter"]:
					sink.append(f"{n}: converter {node.get('type')} not installed")
	return sorted(set(problems))


def installed_components(root=None):
	root = root or os.environ.get("MLA_COMPONENTS_ROOT", "/usr/lib/enigma2/python/Components")
	if not os.path.isdir(root):
		return None  # not on a receiver: skip component checks
	out = {"Renderer": {"Label", "Pixmap", "Listbox", "FixedLabel", "Progress", "Canvas", "Pig"}, "Converter": set(), "Sources": set()}
	for kind in ("Renderer", "Converter", "Sources"):
		d = os.path.join(root, kind)
		if os.path.isdir(d):
			out[kind] |= {f.split(".")[0] for f in os.listdir(d) if f.endswith((".py", ".pyc"))}
	return out


# ---------------------------------------------------------------- generations
def _gen_dir(gid):
	return _p("generations", gid)


def _active_target():
	try:
		return os.path.basename(os.readlink(_p("active")))
	except OSError:
		return None


def verify_generation(gid):
	d = _gen_dir(gid)
	mf = os.path.join(d, "MANIFEST.sha256")
	if not os.path.isfile(mf):
		return False
	try:
		for line in open(mf, encoding="utf-8"):
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			digest, name = line.split("  ", 1)
			if _sha(os.path.join(d, name)) != digest:
				return False
	except (OSError, ValueError):
		return False
	# A generation made before G-1 has no theme bitmaps; the skin now needs them -> not usable.
	return all(os.path.isfile(os.path.join(d, "assets", rel)) for rel in THEME_ASSETS)


def _next_gid():
	ids = [int(g[1:]) for g in os.listdir(_p("generations")) if g.startswith("g") and g[1:].isdigit()]
	return "g%06d" % (max(ids) + 1 if ids else 1)


def _journal(state, **kw):
	data = {"state": state, "time": int(time.time())}
	data.update(kw)
	os.makedirs(STATE_DIR, exist_ok=True)
	_atomic_write(_s("txn.json"), json.dumps(data))


def _read_journal():
	try:
		return json.load(open(_s("txn.json")))
	except (OSError, ValueError):
		return None


def _lkg():
	try:
		g = open(_s("lkg")).read().strip()
		return g if g else FACTORY
	except OSError:
		return FACTORY


def build_generation(selection, gid, components=None):
	d = _gen_dir(gid)
	feats = unavailable_features(components)
	lays = layouts()
	os.makedirs(d)
	files = {"theme.xml": _p("themes", selection["theme"], "theme.xml")}
	for sec in sections():
		lid = selection["layouts"][sec]
		files[f"{sec}.xml"] = _p("layouts", sec, lid, target_file(lays[sec][lid]))
	# Theme bitmaps travel WITH the generation (G-1): the skin paths are symlinks to active/assets/<rel>,
	# so colours and bitmaps switch together, atomically, and are covered by the manifest.
	for rel in THEME_ASSETS:
		src = _p("themes", selection["theme"], "assets", rel)
		files["assets/" + rel] = src if os.path.isfile(src) else _p("themes", "navy", "assets", rel)  # fallback: Classic bitmap
	lines = []
	for name, src in files.items():
		dst = os.path.join(d, name)
		os.makedirs(os.path.dirname(dst), exist_ok=True)
		tree = _parse(src) if feats and name.endswith(".xml") and name != "theme.xml" else None
		if tree is not None and _prune(tree.getroot(), feats):
			tree.write(dst, encoding="utf-8", xml_declaration=True)  # same screens, minus the optional widgets
		else:
			shutil.copyfile(src, dst)
		_fsync_file(dst)
		lines.append(f"{_sha(dst)}  {name}")
		_fault("stage")
	sel = json.dumps(selection, sort_keys=True)
	with open(os.path.join(d, "selection.json"), "w") as f:
		f.write(sel)
	_fsync_file(os.path.join(d, "selection.json"))
	lines.append(f"{_sha(os.path.join(d, 'selection.json'))}  selection.json")
	with open(os.path.join(d, FEATURES_FILE), "w") as f:
		f.write(json.dumps({"omitted": feats}))
	_fsync_file(os.path.join(d, FEATURES_FILE))
	lines.append(f"{_sha(os.path.join(d, FEATURES_FILE))}  {FEATURES_FILE}")
	_fault("seal")
	_atomic_write(os.path.join(d, "MANIFEST.sha256"), "# CineView MLA generation " + gid + "\n" + "\n".join(lines) + "\n")
	_fsync_dir(_p("generations"))


def switch_to(gid):
	if not verify_generation(gid):
		raise MLAError(f"refusing to switch to unverified generation {gid}")
	tmp = _p("active.tmp")
	if os.path.lexists(tmp):
		os.remove(tmp)
	os.symlink(os.path.join("generations", gid), tmp)
	_fault("switch")
	os.replace(tmp, _p("active"))
	_fsync_dir(SKIN_DIR)


def apply(selection, trial=False, components=None):
	problems = validate(selection, components)
	if problems:
		raise MLAError("validation failed:\n  " + "\n  ".join(problems))
	prev = _active_target()
	gid = _next_gid()
	_journal("PREPARING", gid=gid, prev=prev)
	try:
		build_generation(selection, gid, components)
	except Exception:
		shutil.rmtree(_gen_dir(gid), ignore_errors=True)
		_journal("ABORTED", gid=gid, prev=prev)
		raise
	_journal("STAGED", gid=gid, prev=prev)
	if not verify_generation(gid):
		shutil.rmtree(_gen_dir(gid), ignore_errors=True)
		_journal("ABORTED", gid=gid, prev=prev)
		raise MLAError("sealed generation failed verification")
	switch_to(gid)
	_atomic_write(_s("selection.json"), json.dumps(selection, sort_keys=True))
	_journal("TRIAL" if trial else "SWITCHED", gid=gid, prev=prev)
	_log(f"apply: {prev} -> {gid} trial={trial} omitted={unavailable_features(components)} selection={json.dumps(selection, sort_keys=True)}")
	if not trial:
		commit()
	return gid


def commit():
	gid = _active_target()
	if gid and verify_generation(gid):
		_atomic_write(_s("lkg"), gid)
		_journal("COMMITTED", gid=gid)
		_reset_boot_count()
		_cleanup(keep={gid, FACTORY})
		_log(f"commit: lkg={gid}")
		return gid
	raise MLAError("nothing valid to commit")


def _reset_boot_count():
	_atomic_write(_s("boot.count"), "0")


def _cleanup(keep):
	gens = sorted(g for g in os.listdir(_p("generations")) if g.startswith("g"))
	sealed = [g for g in gens if g not in keep]
	for g in sealed[:-KEEP] if len(sealed) > KEEP else []:
		shutil.rmtree(_gen_dir(g), ignore_errors=True)


def rollback(to="lkg"):
	target = FACTORY if to == "factory" else _lkg()
	if not verify_generation(target):
		target = FACTORY
	switch_to(target)
	try:
		sel = json.load(open(os.path.join(_gen_dir(target), "selection.json")))
		_atomic_write(_s("selection.json"), json.dumps(sel, sort_keys=True))
	except (OSError, ValueError):
		pass
	if target == FACTORY:
		# Factory is chosen explicitly (user "Factory design", guardian level 2) or forced (lkg invalid):
		# it becomes the last-known-good, so a later crash-loop rollback can never bring back a design
		# the user has left.
		_atomic_write(_s("lkg"), FACTORY)
	_journal("ROLLED_BACK", gid=target)
	_cleanup(keep={target, FACTORY, _lkg()})  # reverted trials must not accumulate (device: 6 generations after P6)
	_log(f"rollback: active -> {target}")
	return _ensure_safe() or target


def mark_trial_running():
	"""Called by the runtime plugin when a GUI session starts on a TRIAL generation.  From now on the trial
	must be confirmed in THIS session: any later start that still finds TRIAL_RUNNING (crash, manual
	restart, power loss, prompt never answered) is reverted to last-known-good by recover()."""
	j = _read_journal()
	if j and j.get("state") == "TRIAL" and j.get("gid") == _active_target():
		_journal("TRIAL_RUNNING", gid=j.get("gid"), prev=j.get("prev"), since=int(time.time()))
		_log(f"trial: session started on {j.get('gid')}, awaiting confirmation")
		return True
	return bool(j and j.get("state") == "TRIAL_RUNNING")


def ensure_components(components=None):
	"""Keep the active generation loadable with the components installed NOW: rebuild it (same selection) when
	it holds widgets of an optional feature whose plugin is missing - e.g. the factory generation on an image
	without OAWeather - or when it was built without a feature whose plugin has since been installed.
	Returns the new generation id, or None when nothing had to change."""
	if components is None:
		components = installed_components()
	if components is None:
		return None
	cur = _active_target()
	if not cur or not verify_generation(cur):
		return None
	want = unavailable_features(components)
	if want == generation_omitted(cur):
		return None
	try:
		sel = json.load(open(os.path.join(_gen_dir(cur), "selection.json")))
	except (OSError, ValueError):
		sel = current_selection()
	problems = validate(sel, components)
	if problems:
		_log("ensure: cannot rebuild %s: %s" % (cur, "; ".join(problems)))
		return None
	was_lkg = _lkg() == cur
	j = _read_journal()
	gid = _next_gid()
	try:
		build_generation(sel, gid, components)
	except Exception:
		shutil.rmtree(_gen_dir(gid), ignore_errors=True)
		raise
	if not verify_generation(gid):
		shutil.rmtree(_gen_dir(gid), ignore_errors=True)
		raise MLAError("rebuilt generation failed verification")
	switch_to(gid)
	if was_lkg:
		_atomic_write(_s("lkg"), gid)
	if j and j.get("gid") == cur:
		j["gid"] = gid
		_journal(j.pop("state"), **{k: v for k, v in j.items() if k != "time"})
	_cleanup(keep={gid, FACTORY, _lkg()})
	_log(f"ensure: {cur} -> {gid} omitted={want} (was {generation_omitted(cur)}) selection={json.dumps(sel, sort_keys=True)}")
	return gid


def _ensure_safe():
	try:
		return ensure_components()
	except Exception as e:  # never break the boot path: the previous generation stays active
		_log(f"ensure: ERROR {e}")
		return None


def recover():
	"""Repair any interrupted transaction; always leaves `active` on a sealed, verified generation."""
	actions = []
	j0 = _read_journal()
	if j0 and j0.get("state") == "TRIAL_RUNNING":
		target = rollback("lkg")
		actions.append(f"unconfirmed trial {j0.get('gid')} from the previous session -> {target}")
	if os.path.lexists(_p("active.tmp")):
		os.remove(_p("active.tmp"))
		actions.append("removed stale active.tmp")
	j = _read_journal()
	if j and j.get("state") in ("PREPARING", "STAGED", "ABORTED"):
		gid = j.get("gid")
		if gid and gid != _active_target() and os.path.isdir(_gen_dir(gid)):
			shutil.rmtree(_gen_dir(gid), ignore_errors=True)
			actions.append(f"discarded unfinished generation {gid} ({j['state']})")
		_journal("RECOVERED", gid=_active_target())
	for g in os.listdir(_p("generations")):
		if g != _active_target() and not os.path.isfile(os.path.join(_gen_dir(g), "MANIFEST.sha256")):
			shutil.rmtree(_gen_dir(g), ignore_errors=True)
			actions.append(f"removed unsealed generation {g}")
	cur = _active_target()
	if not cur or not verify_generation(cur):
		target = rollback("lkg")
		actions.append(f"active {cur} invalid -> {target}")
	g = _ensure_safe()
	if g:
		actions.append(f"active rebuilt for the installed components -> {g}")
	if actions:
		_log("recover: " + "; ".join(actions))
	return actions


def status():
	return {"active": _active_target(), "active_valid": bool(_active_target()) and verify_generation(_active_target()),
		"lkg": _lkg(), "journal": _read_journal(), "selection": current_selection(),
		"generations": sorted(os.listdir(_p("generations"))), "themes": themes(),
		"layouts": {s: sorted(v) for s, v in layouts().items()}}


def _parse_args(argv):
	sel = current_selection()
	sel = {"theme": sel.get("theme", "navy"), "layouts": dict(sel.get("layouts", {}))}
	trial, to = False, "lkg"
	i = 0
	while i < len(argv):
		a = argv[i]
		if a == "--theme":
			sel["theme"] = argv[i + 1]; i += 1
		elif a == "--set":
			s, l = argv[i + 1].split("=", 1); sel["layouts"][s] = l; i += 1
		elif a == "--trial":
			trial = True
		elif a == "--to":
			to = argv[i + 1]; i += 1
		i += 1
	for s in sections():
		sel["layouts"].setdefault(s, "classic")
	return sel, trial, to


def main(argv):
	if not argv:
		print(__doc__)
		return 2
	cmd, rest = argv[0], argv[1:]
	sel, trial, to = _parse_args(rest)
	try:
		if cmd == "status":
			print(json.dumps(status(), indent=1))
		elif cmd == "validate":
			w = []
			p = validate(sel, installed_components(), w)
			print("\n".join(p) if p else "VALID")
			print(f"warnings (core/plugin screens, non-blocking): {len(sorted(set(w)))}")
			if "-v" in rest:
				print("\n".join("  W " + x for x in sorted(set(w))))
			return 1 if p else 0
		elif cmd == "apply":
			print(apply(sel, trial=trial, components=installed_components()))
		elif cmd == "ensure":
			print(ensure_components() or "nothing to do")
		elif cmd == "commit":
			print(commit())
		elif cmd == "rollback":
			print(rollback(to))
		elif cmd == "recover":
			print("\n".join(recover()) or "nothing to recover")
		else:
			print(__doc__)
			return 2
	except MLAError as e:
		_log(f"{cmd}: ERROR {e}")
		print("ERROR:", e)
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
