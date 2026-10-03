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


RENDERER_PATCHES = [
	# Next-event posters (nexts>0) are chained from the END of the event the source currently holds.
	# The original takes row[nexts] of lookupEvent(now-list); at an event boundary that list can still
	# start with the event that just ended, so the "next" widget showed the NEW current event's poster
	# until the next refresh (device-observed on HRT1 18:10, Brigitte Bardot shown as next).
	("""        return _lookup_event(_source_ref(self.source), self.nexts)""", """        if ev is not None and self.nexts > 0:
            try:
                ref = _source_ref(self.source)
                t = ev.getBeginTime() + ev.getDuration()
                nxt = None
                for _ in range(self.nexts):
                    nxt = _epg.lookupEventTime(ref, t) if ref is not None else None
                    if nxt is None:
                        break
                    t = nxt.getBeginTime() + nxt.getDuration()
                if nxt is not None and nxt.getEventName():
                    return nxt.getEventName()
            except Exception:
                pass
        return _lookup_event(_source_ref(self.source), self.nexts)"""),
	# (old, new) — exact, each must occur once in the golden CineViewPosterX.py
	('''            if key == "nexts":''', '''            if key == "toggle":
                self.toggle = value
            elif key == "nexts":'''),
	('''        self.nexts = 0
        self._title = ""''', '''        self.nexts = 0
        self.toggle = None
        self._title = ""'''),
	('''        title = _clean_title(self._resolve_title())''', '''        if not self._enabled():
            self.instance.hide()
            self._timer.stop()
            return
        title = _clean_title(self._resolve_title())'''),
	('''    def _show(self, path):
        try:''', '''    def _enabled(self):
        # CineView MLA live switch (config.plugins.cineviewmla.poster_<section>); unknown => shown.
        if not self.toggle:
            return True
        try:
            from Components.config import configfile
            return configfile.getResolvedKey(self.toggle, silent=True) != "False"
        except Exception:
            return True

    def _show(self, path):
        if not self._enabled():
            self.instance.hide()
            return
        try:'''),
]


BITRATE_PATCHES = [
	# T6 (device-proven): a `bitrate` reader started while the service is still starting can stay at
	# video=0 for the whole service (display "0.13 Mbps" = audio only) while a fresh reader on the same
	# PIDs reads 4-6 Mbps.  The original engine never restarts a reader for the same service, and on a
	# service change starts the new reader in the same tick it kills the old one.
	("import NavigationInstance\n", """import NavigationInstance
import os
import signal
import time


def _kill_orphan_readers():
    # A `bitrate` reader whose parent is not this enigma2 is left over from a previous enigma2
    # session (eConsoleAppContainer children survive init 4/3).  The demux hands the video PES of a
    # service to one reader only, so such an orphan makes every new reader report video=0 (T6).
    me = os.getpid()
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            stat = open("/proc/%s/stat" % pid).read()
            comm = stat[stat.index("(") + 1:stat.rindex(")")]
            ppid = int(stat[stat.rindex(")") + 2:].split()[1])
            if comm == "bitrate" and ppid != me:
                os.kill(int(pid), signal.SIGKILL)
        except Exception:
            pass
"""),
	("""        self.vmin = self.vmax = self.vavg = self.vcur = 0
        self.amin = self.amax = self.aavg = self.acur = 0

    def _clear_values(self):""", """        self.vmin = self.vmax = self.vavg = self.vcur = 0
        self.amin = self.amax = self.aavg = self.acur = 0
        self.has_video = False
        self.zero_video = 0
        self.started_at = 0.0
        self.last_restart = 0.0
        self.not_before = 0.0

    def _clear_values(self):"""),
	("""        self.remaining = ""
        self.lines = []
        self._clear_values()

    def _closed(self, retval):""", """        self.remaining = ""
        self.lines = []
        self._clear_values()
        self.zero_video = 0
        self.not_before = time.time() + 1.0  # let the killed reader release its demux filters

    def _closed(self, retval):"""),
	("""                    self.amin, self.amax, self.aavg, self.acur = [int(float(x)) for x in a[:4]]""", """                    self.amin, self.amax, self.aavg, self.acur = [int(float(x)) for x in a[:4]]
                    self.zero_video = self.zero_video + 1 if (self.has_video and not self.vcur) else 0"""),
	("""            key = ref.toString()
            if self.running and key == self.service_key:
                return""", """            key = ref.toString()
            now = time.time()
            if self.running and key == self.service_key:
                # watchdog: video PID present but the reader keeps delivering 0 kbit/s video
                if self.zero_video >= 5 and now - self.started_at > 5 and now - self.last_restart > 10:
                    self.last_restart = now
                    self.stop()
                return
            if now < self.not_before:
                return"""),
	("""            self.remaining = ""
            self.lines = []
            self._clear_values()
            self.running = True
            rc = self.container.execute(cmd)""", """            self.remaining = ""
            self.lines = []
            self._clear_values()
            self.has_video = bool(vpid)
            self.zero_video = 0
            self.started_at = now
            self.running = True
            _kill_orphan_readers()
            rc = self.container.execute(cmd)"""),
	("""            if key != self.service_key:
                self.stop()
            self.service_key = key""", """            if key != self.service_key:
                was_running = self.running
                self.stop()
                self.service_key = key
                if was_running:
                    return  # start the new reader on the next poll, after the old one released the demux
            self.service_key = key"""),
]


SIB_TEXTFIT = {
	# (source, position) of the approved RunningText widgets -> narrow (posters on) / wide (posters off)
	# geometry.  Panels: left 55..860 (poster frame from x=609), right 925..1865 (frame from x=1572).
	("session.Event_Now", "95,165"): ("title", (95, 165, 480, 64), (95, 165, 725, 64)),
	("session.Event_Now", "95,220"): ("desc", (95, 245, 480, 261), (95, 245, 725, 261)),
	("session.Event_Next", "950,165"): ("title", (950, 165, 580, 64), (950, 165, 890, 64)),
	("session.Event_Next", "950,220"): ("desc", (950, 245, 580, 261), (950, 245, 890, 261)),
}
SIB_OPTS = {
	# title: two wrapped lines, scrolls vertically only when a title needs more than two lines
	"title": ('font="Regular;27"', "movetype=swimming,direction=top,step=1,steptime=70,startdelay=3000,pause=3000,repeat=0,always=0,wrap=1"),
	# description: unchanged font; box = 9 whole lines (line height 29 px for Regular;25, measured on device); 'swimming' (native RunningText) starts with the
	# first lines visible and moves up to the last line and back, never outside the box
	"desc": ('font="Regular;25"', "movetype=swimming,direction=top,step=1,steptime=60,startdelay=4000,pause=3000,repeat=0,always=0,wrap=1"),
}


def apply_sib_textfit(skin):
	"""SecondInfoBar fix (approved by the user for Slot 8 / MLA classic): full event title and
	description inside their panels; when posters are off the texts use the poster area instead of
	leaving it empty.  Uses CineViewMLAShowIf (text pass-through + native-style visibility)."""
	changes = []
	for section, names in SIB_TEXTFIT_SCREENS:
		_textfit_section(skin, section, names, changes)
	return changes


# EventView added on the user's approval (2026-10-03 18:19): same four widgets/positions/sources.
SIB_TEXTFIT_SCREENS = (("secondinfobar", ("SecondInfoBar", "SecondInfoBarSimple")), ("eventview", ("EventView",)))


def _textfit_section(skin, section, screen_names, changes):
	path = os.path.join(skin, "layouts", section, "classic", "screens.openatv.xml")
	src = open(path, encoding="utf-8").read()
	key = POSTER_TOGGLE % section

	def screen_fix(m):
		body = m.group(0)
		name = _attrs(body[:body.index(">")]).get("name", "?")
		if name not in screen_names:
			return body

		def widget_fix(wm):
			tag, conv = wm.group(1), wm.group(2)
			a = _attrs(tag)
			spec = SIB_TEXTFIT.get((a.get("source"), a.get("position")))
			if not spec:
				return wm.group(0)
			kind, narrow, wide = spec
			font, opts = SIB_OPTS[kind]
			out = []
			for geo, value, inv in ((narrow, "True", ""), (wide, "True", ",Invert")):
				t = re.sub(r'position="[^"]*"', 'position="%d,%d"' % geo[:2], tag)
				t = re.sub(r'size="[^"]*"', 'size="%d,%d"' % geo[2:], t)
				t = re.sub(r'font="[^"]*"', font, t)
				t = re.sub(r'options="[^"]*"', 'options="%s"' % opts, t)
				t = re.sub(r'\s*noWrap="1"', "", t)
				out.append('%s\n\t\t\t%s\n\t\t\t<convert type="CineViewMLAShowIf">%s,%s%s</convert>\n\t\t</widget>' % (t, conv, key, value, inv))
			changes.append((name, a.get("source"), kind))
			return "\n\t\t".join(out)

		return re.sub(r'(<widget\b[^>]*render="RunningText"[^>]*>)\s*(<convert type="EventName">(?:Name|FullDescription)</convert>)\s*</widget>', widget_fix, body)

	new = re.sub(r"<screen\b.*?</screen>", screen_fix, src, flags=re.S)
	open(path, "w", encoding="utf-8").write(new)


def run(*a):
	subprocess.check_call(list(a))


POSTER_TOGGLE = "config.plugins.cineviewmla.poster_%s"
FRAME_DIR = "mla_assets"


def _attrs(tag):
	return dict(re.findall(r'(\w+)="([^"]*)"', tag))


def apply_poster_toggles(skin):
	"""M5 — live poster switches per section, without changing the enabled-state pixels.

	* every CineViewMLAPosterX widget gets toggle="config.plugins.cineviewmla.poster_<section>"
	  (the renderer hides itself when that setting is False);
	* every static frame eLabel around a poster (no text, 1..6 px larger on each side) becomes a
	  Pixmap widget of the same rectangle/z-order, filled with the same colour, shown through the
	  native ConfigEntryTest(<key>,False,Invert) + ConditionalShowHide chain (OpenATV 57b7a51:
	  a missing key resolves to None, so the frame stays visible unless the switch is False).
	Returns a list of (section, screen, what) changes for the build log."""
	from PIL import Image
	changes = []
	for sec in sorted(os.listdir(os.path.join(skin, "layouts"))):
		path = os.path.join(skin, "layouts", sec, "classic", "screens.openatv.xml")
		if not os.path.isfile(path):
			continue
		key = POSTER_TOGGLE % sec
		src = open(path, encoding="utf-8").read()

		def screen_fix(m):
			body = m.group(0)
			name = _attrs(body[:body.index(">")]).get("name", "?")
			posters = []

			def tag_poster(pm):
				tag = pm.group(0)
				a = _attrs(tag)
				posters.append(tuple(map(int, a["position"].split(","))) + tuple(map(int, a["size"].split(","))))
				changes.append((sec, name, "poster toggle"))
				return tag[:-2].rstrip() + ' toggle="%s" />' % key

			body = re.sub(r'<widget\b[^>]*render="CineViewMLAPosterX"[^>]*/>', tag_poster, body)

			def frame_fix(lm):
				tag = lm.group(0)
				a = _attrs(tag)
				if "text" in a or "position" not in a or "size" not in a or not re.fullmatch(r"#[0-9A-Fa-f]{8}", a.get("backgroundColor", "")):
					return tag
				x, y = map(int, a["position"].split(","))
				w, h = map(int, a["size"].split(","))
				for px, py, pw, ph in posters:
					if 0 < px - x <= 6 and 0 < py - y <= 6 and 0 < x + w - px - pw <= 6 and 0 < y + h - py - ph <= 6:
						col = a["backgroundColor"]
						if col[1:3].lower() != "00":
							return tag  # translucent frame: not reproducible as an opaque pixmap — leave as is
						fname = "frame_%s_%dx%d.png" % (col[3:].lower(), w, h)
						fpath = os.path.join(skin, FRAME_DIR, fname)
						if not os.path.isfile(fpath):
							os.makedirs(os.path.dirname(fpath), exist_ok=True)
							Image.new("RGB", (w, h), tuple(int(col[i:i + 2], 16) for i in (3, 5, 7))).save(fpath)
						changes.append((sec, name, "frame %dx%d" % (w, h)))
						return ('<widget source="session.CurrentService" render="Pixmap" pixmap="%s/%s" position="%d,%d" size="%d,%d" zPosition="%s">'
							'<convert type="ConfigEntryTest">%s,False,Invert</convert><convert type="ConditionalShowHide" /></widget>'
							% (FRAME_DIR, fname, x, y, w, h, a.get("zPosition", "0"), key))
				return tag

			return re.sub(r"<eLabel\b[^>]*/>", frame_fix, body)

		new = re.sub(r"<screen\b.*?</screen>", screen_fix, src, flags=re.S)
		if new != src:
			open(path, "w", encoding="utf-8").write(new)
	return changes


def load_theme_module(control_dir):
	spec = importlib.util.spec_from_file_location("cv_theme", os.path.join(control_dir, "theme.py"))
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	return m


def main(golden, comps, control, out):
	sys.dont_write_bytecode = True  # the engine is imported from the output tree below
	skin = os.path.join(out, SKIN)
	if os.path.exists(out):
		shutil.rmtree(out)
	run(sys.executable, os.path.join(HERE, "migrate_classic.py"), golden, os.path.join(REPO, "mla", "sections.json"), skin)
	for sec, scr, what in apply_poster_toggles(skin):
		print("M5 %-16s %-22s %s" % (sec, scr, what))
	for scr, source, kind in apply_sib_textfit(skin):
		print("SIB-TEXTFIT %-20s %-18s %s (narrow+wide)" % (scr, source, kind))

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
	shutil.copytree(os.path.join(REPO, "mla", "engine"), os.path.join(skin, "mla", "engine"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
	shutil.copy2(os.path.join(REPO, "mla", "sections.json"), os.path.join(skin, "mla", "sections.json"))
	shutil.copytree(os.path.join(REPO, "mla", "guardian"), os.path.join(skin, "mla", "guardian"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

	# MLA control screens (new, uniquely named) — included after core/common.
	shutil.copy2(os.path.join(REPO, "mla", "ui", "mla_ui.openatv.xml"), os.path.join(skin, "core", "mla_ui.openatv.xml"))
	sk = open(os.path.join(skin, "skin.xml"), encoding="utf-8").read()
	anchor = '<include filename="core/common.openatv.xml" />'
	assert sk.count(anchor) == 1, "include anchor missing"
	sk = sk.replace(anchor, anchor + '\n\t<include filename="core/mla_ui.openatv.xml" />')
	open(os.path.join(skin, "skin.xml"), "w", encoding="utf-8").write(sk)

	# Preview images.  Layout previews come from REAL device screenshots (env MLA_PREVIEWS:
	# dir with <section>.png); theme previews are color swatches of the palette.
	try:
		from PIL import Image, ImageDraw
		prev = os.environ.get("MLA_PREVIEWS")
		if prev:
			for sec in json.load(open(os.path.join(REPO, "mla", "sections.json")))["sections"]:
				src = os.path.join(prev, sec + ".png")
				if os.path.isfile(src):
					Image.open(src).convert("RGB").resize((720, 405)).save(os.path.join(skin, "layouts", sec, "classic", "preview.png"))
		for key in theme.THEMES:
			pal = theme.palette(key)
			rgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (3, 5, 7))
			im = Image.new("RGB", (720, 405), rgb(pal["steThemePrimary"]))
			d = ImageDraw.Draw(im)
			d.rectangle([0, 0, 720, 70], fill=rgb(pal["steThemeTop"]))
			d.rectangle([30, 100, 340, 375], fill=rgb(pal["steThemePanel"]))
			d.rectangle([370, 100, 690, 375], fill=rgb(pal["steThemePanelAlt"]))
			d.rectangle([370, 160, 690, 210], fill=rgb(pal["steThemeSelected"]))
			d.rectangle([30, 20, 260, 50], fill=rgb(pal["steThemeAccent"]))
			d.text((390, 175), theme.THEMES[key][0], fill=rgb(pal["steThemeText"]))
			im.save(os.path.join(skin, "themes", key, "preview.png"))
	except ImportError:
		print("PIL not available: previews skipped")

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
			if base == "CineViewBitrate":
				for old, new in BITRATE_PATCHES:
					assert src.count(old) == 1, "bitrate patch anchor not unique: %r" % old[:50]
					src = src.replace(old, new)
			if base == "CineViewPosterX":
				assert src.count(POSTER_PATCH_OLD) == 1
				for old, new in RENDERER_PATCHES:
					assert src.count(old) == 1, "renderer patch anchor not unique: %r" % old[:40]
					src = src.replace(old, new)
				src = src.replace(POSTER_PATCH_OLD, POSTER_PATCH_NEW).replace('"/tmp/CINEVIEW"', '"/tmp/CINEVIEW-MLA"').replace("/tmp/CINEVIEW/poster.log", "/tmp/CINEVIEW-MLA/poster.log")
			open(os.path.join(out, PY, kind, COMPONENT_RENAMES[base] + ".py"), "w", encoding="utf-8").write(src)

	# MLA's own components (not derived from the golden set).
	own = os.path.join(REPO, "mla", "components")
	for kind in sorted(os.listdir(own)) if os.path.isdir(own) else []:
		for f in sorted(os.listdir(os.path.join(own, kind))):
			if f.endswith(".py"):
				shutil.copy2(os.path.join(own, kind, f), os.path.join(out, PY, kind, f))

	# Runtime plugin + native pre-start hook (installed by the deploy step, not by the build).
	shutil.copytree(os.path.join(REPO, "mla", "plugin", "CineViewMLA"), os.path.join(out, "usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA"), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
	open(os.path.join(out, "usr/lib/enigma2/python/Plugins/Extensions/CineViewMLA", "__init__.py"), "w").close()

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
