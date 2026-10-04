#!/usr/bin/env python3
"""Build the installable CineView MLA tree (OpenATV) from the approved golden live set.

usage: build.py <golden CineView_FHD dir> <golden python Components dir> <golden CineViewControl dir> <out root>

Output layout (relative to <out root>, mirrors the receiver's filesystem):
  usr/share/enigma2/CineView_FHD_MLA/            skin (thin skin.xml, core/, layouts/, themes/, assets, generations/g000000, active -> g000000)
  usr/share/enigma2/CineView_FHD_MLA/mla/        sections.json + engine/
  usr/lib/enigma2/python/Components/{Renderer,Converter}/CineViewMLA*.py
"""
import glob
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


IMDB_PATCHES = [
	("        self.mode = (type or 'plain').lower()\n",
	 "        args = [a.strip() for a in (type or 'plain').lower().split(',')]\n        self.mode = args[0] or 'plain'\n        self.empty = '' if 'hide' in args[1:] else '--'\n"),
	("        if not title:\n            return '--'\n", "        if not title:\n            return self.empty\n        if self.empty == '' and not _cv_rateable(title, self.source):\n            return ''  # only films/series identified from the EPG text get a rating (title searches mis-match)\n"),
	("        if rating is None:\n            return '--'\n", "        if rating is None:\n            return self.empty\n"),
]
IMDB_GENERIC_HELPER = """

def _cv_bool(self):
    # ',hide' badge switch (Pixmap + ConditionalShowHide): True only while a rating is shown.
    return self.getText() not in ('', '--')


CineViewMLAIMDb.boolean = property(_cv_bool)

def _cv_rateable(title, source):
    # P7 device tests: 'Dnevnik 3' (news) got IMDb 8.5/10, 'Skener 7' (sports magazine) 7.9/10 - a bare title
    # search returns some other work.  With ',hide' a rating is shown only when the event is identified as a
    # film or a series from its own EPG text (same rules as the poster identity engine) and is not generic.
    try:
        from Components.CineViewMLAPosterMatch import identify
        ev = getattr(source, 'event', None)
        short = (ev.getShortDescription() if ev else '') or ''
        ext = (ev.getExtendedDescription() if ev else '') or ''
        i = identify(title, short, ext)
        return i.get('generic') is None and i.get('kind') in ('movie', 'series')
    except Exception:
        return False
"""
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
				for direction in ("ltr", "rtl"):
					t = re.sub(r'position="[^"]*"', 'position="%d,%d"' % geo[:2], tag)
					t = re.sub(r'size="[^"]*"', 'size="%d,%d"' % geo[2:], t)
					t = re.sub(r'font="[^"]*"', font, t)
					t = re.sub(r'options="[^"]*"', 'options="%s"' % opts, t)
					t = re.sub(r'\s*noWrap="1"', "", t)
					if direction == "rtl":  # right-to-left text: right aligned (see CineViewMLAShowIf)
						t = re.sub(r'\s*halign="[^"]*"', "", t)
						t = t[:-1].rstrip() + ' halign="right">'
					out.append('%s\n\t\t\t%s\n\t\t\t<convert type="CineViewMLAShowIf">%s,%s%s,dir=%s</convert>\n\t\t</widget>' % (t, conv, key, value, inv, direction))
			changes.append((name, a.get("source"), kind))
			return "\n\t\t".join(out)

		return re.sub(r'(<widget\b[^>]*render="RunningText"[^>]*>)\s*(<convert type="EventName">(?:Name|FullDescription)</convert>)\s*</widget>', widget_fix, body)

	new = re.sub(r"<screen\b.*?</screen>", screen_fix, src, flags=re.S)
	open(path, "w", encoding="utf-8").write(new)


def make_default_poster(path):
	"""Neutral, language-free CineView placeholder (2:3, JPEG for loadJPG): dark panel + film-frame glyph."""
	from PIL import Image, ImageDraw
	W, H = 600, 900
	im = Image.new("RGB", (W, H))
	d = ImageDraw.Draw(im)
	for y in range(H):  # vertical gradient in the Classic panel tones
		t = y / (H - 1)
		d.line([(0, y), (W, y)], fill=(int(14 + 10 * t), int(24 + 14 * t), int(42 + 20 * t)))
	d.rectangle([18, 18, W - 19, H - 19], outline=(60, 78, 104), width=3)
	cx, cy, fw, fh = W // 2, H // 2 - 20, 260, 190  # film frame with sprocket holes
	d.rounded_rectangle([cx - fw // 2, cy - fh // 2, cx + fw // 2, cy + fh // 2], radius=14, outline=(120, 140, 168), width=8)
	for i in range(6):
		x = cx - fw // 2 + 22 + i * ((fw - 44) // 5) - 9
		for yy in (cy - fh // 2 + 16, cy + fh // 2 - 34):
			d.rounded_rectangle([x, yy, x + 18, yy + 18], radius=4, fill=(120, 140, 168))
	d.polygon([(cx - 28, cy - 34), (cx - 28, cy + 34), (cx + 36, cy)], fill=(232, 176, 48))
	os.makedirs(os.path.dirname(path), exist_ok=True)
	im.save(path, "JPEG", quality=90)


def recolor_rgb(rgb, base_hex, black=False):
	"""Same re-tint rule as recolor_png() for one colour -> 'RRGGBB'."""
	import colorsys
	nh, nl, ns = colorsys.rgb_to_hls(0x0A / 255.0, 0x1D / 255.0, 0x35 / 255.0)
	th, tl, ts = colorsys.rgb_to_hls(*(int(base_hex[i:i + 2], 16) / 255.0 for i in (1, 3, 5)))
	h, l, s = colorsys.rgb_to_hls(*(c / 255.0 for c in rgb))
	if base_hex.upper() == "#0A1D35":
		return "%02X%02X%02X" % rgb
	if black:
		h2, s2, l2 = h, s * 0.06, l * 0.9
	else:
		h2, s2, l2 = th, min(1.0, s * ts / ns), min(1.0, l * (0.5 + 0.5 * tl / nl))
	return "%02X%02X%02X" % tuple(int(c * 255 + 0.5) for c in colorsys.hls_to_rgb(h2, l2, s2))


def recolor_png(src, dst, base_hex, black=False):
	"""Re-tint a navy-tinted Classic bitmap for another theme: pixels in the navy hue band take the theme's
	hue/saturation (lightness kept, scaled toward the theme base); alpha and neutral pixels are untouched."""
	import colorsys
	from PIL import Image
	NAVY = (0x0A, 0x1D, 0x35)
	nh, nl, ns = colorsys.rgb_to_hls(*[c / 255.0 for c in NAVY])
	tr, tg, tb = (int(base_hex[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
	th, tl, ts = colorsys.rgb_to_hls(tr, tg, tb)
	im = Image.open(src).convert("RGBA")
	px = im.load()
	for y in range(im.height):
		for x in range(im.width):
			r, g, b, a = px[x, y]
			h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
			if a == 0 or s < 0.12 or not (195 / 360.0 <= h <= 240 / 360.0):
				continue
			if black:
				h2, s2, l2 = h, s * 0.06, l * 0.9
			else:
				h2, s2 = th, min(1.0, s * ts / ns)
				l2 = min(1.0, l * (0.5 + 0.5 * tl / nl))
			r2, g2, b2 = colorsys.hls_to_rgb(h2, l2, s2)
			px[x, y] = (int(r2 * 255 + 0.5), int(g2 * 255 + 0.5), int(b2 * 255 + 0.5), a)
	os.makedirs(os.path.dirname(dst), exist_ok=True)
	im.save(dst, "PNG")


def make_preview_none(path):
	"""Designs UI placeholder when an item has no preview (replaces the empty grey frame).  Neutral charcoal
	that sits well on every colour theme, a language-free 'picture' glyph and the constant accent yellow."""
	from PIL import Image, ImageDraw
	W, H = 720, 405
	im = Image.new("RGB", (W, H))
	d = ImageDraw.Draw(im)
	for y in range(H):
		t = y / (H - 1)
		v = int(22 + 10 * t)
		d.line([(0, y), (W, y)], fill=(v, v + 2, v + 6))
	cx, cy, w, h = W // 2, H // 2, 210, 150
	d.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], radius=16, outline=(110, 116, 128), width=7)
	d.polygon([(cx - 80, cy + 50), (cx - 25, cy - 10), (cx + 10, cy + 25), (cx + 35, cy + 2), (cx + 80, cy + 50)], fill=(110, 116, 128))
	d.ellipse([cx + 34, cy - 50, cx + 66, cy - 18], fill=(249, 199, 49))
	d.line([(cx - w // 2 - 14, cy + h // 2 + 14), (cx + w // 2 + 14, cy - h // 2 - 14)], fill=(160, 166, 176), width=8)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	im.save(path, "PNG")


def _p7_preview(pack_dir, skin):
	"""Selector preview of a P7 pack: the spec mockup (posters on), real font, 720x405."""
	import tempfile
	from PIL import Image
	sec = os.path.basename(os.path.dirname(pack_dir))
	with tempfile.TemporaryDirectory() as t:
		subprocess.check_call([sys.executable, os.path.join(HERE, "p7", "render_p7.py"), os.path.join(skin, "fonts"), t], stdout=subprocess.DEVNULL)
		fam = os.path.basename(pack_dir)
		Image.open(os.path.join(t, "%s_%s_posters_on.png" % (fam, sec))).convert("RGB").resize((720, 405)).save(os.path.join(pack_dir, "preview.png"))


def run(*a):
	subprocess.check_call(list(a))


POSTER_TOGGLE = "config.plugins.cineviewmla.poster_%s"
FRAME_DIR = "mla_assets"


def _attrs(tag):
	return dict(re.findall(r'(\w+)="([^"]*)"', tag))


IMDB_BADGE = '<ePixmap pixmap="infobar/imdb_badge.png" position="1600,968" size="76,28" zPosition="21" alphatest="blend" />'
IMDB_BADGE_NEW = ('<widget source="session.Event_Now" render="Pixmap" pixmap="infobar/imdb_badge.png" position="1600,968" size="76,28" zPosition="21" alphatest="blend">'
	'<convert type="CineViewMLAIMDb">Shown,hide</convert><convert type="ConditionalShowHide" /></widget>')


def _pitch(size):
	"""Device-measured LiberationSans line pitch (same formula as tools/mla/p7/spec_p7.line_height)."""
	import math
	return int(round(size * 1854 / 2048.0)) + int(math.ceil(size * 434 / 2048.0))


CLASSIC_RTL_SCREENS = {"infobar": ("InfoBar",), "secondinfobar": ("SecondInfoBar", "SecondInfoBarSimple"), "eventview": ("EventView",)}


def apply_classic_rtl_titles(skin):
	"""User approval 2026-10-04 11:58 (C-1): in Classic the event titles of the Main InfoBar strip ran horizontally,
	and 57b7a51 RunningText mis-measures right-to-left text in horizontal modes, so an Arabic title started at its
	END.  Fix = the method proven in Details/Cinema: the original widget stays exactly as it is for left-to-right
	text (ShowIf dir=ltr) and a right-to-left twin at the same position pages vertically by exactly one line pitch
	(first line first, whole lines only).  The twin's box is clipped to whole lines (same top, same width) so no part
	of the next line shows.  The strip is the same in InfoBar, SecondInfoBar(Simple) and EventView."""
	out = []
	for sec, screens in CLASSIC_RTL_SCREENS.items():
		f = os.path.join(skin, "layouts", sec, "classic", "screens.openatv.xml")
		x = open(f, encoding="utf-8").read()
		n = 0
		for scr in screens:
			m = re.search(r'<screen name="%s".*?</screen>' % scr, x, re.S)
			body = m.group(0)
			new = body
			for w in re.findall(r'[ \t]*<widget source="session\.Event_(?:Now|Next)" render="RunningText"[^>]*options="movetype=running,direction=left[^"]*"[^>]*>\s*<convert type="EventName">Name</convert>\s*</widget>', body):
				ind = re.match(r'[ \t]*', w).group(0)
				size = int(re.search(r'font="Regular;(\d+)"', w).group(1))
				pw, ph = (int(v) for v in re.search(r'size="(\d+),(\d+)"', w).group(1, 2))
				pt = _pitch(size)
				ltr = w.replace('</widget>', '\t<convert type="CineViewMLAShowIf">always,True,dir=ltr</convert>\n%s</widget>' % ind)
				rtl = re.sub(r'options="[^"]*"', 'options="movetype=swimming,direction=top,step=1,steptime=25,startdelay=3000,pagelength=%d,pagedelay=2500,pause=3000,repeat=0,always=0,wrap=1" halign="right"' % pt, w)
				rtl = rtl.replace(' noWrap="1"', '').replace('size="%d,%d"' % (pw, ph), 'size="%d,%d"' % (pw, max(pt, (ph // pt) * pt)))
				rtl = rtl.replace('</widget>', '\t<convert type="CineViewMLAShowIf">always,True,dir=rtl</convert>\n%s</widget>' % ind)
				new = new.replace(w, ltr + "\n" + rtl, 1)
				n += 1
			x = x.replace(body, new, 1)
		open(f, "w", encoding="utf-8").write(x)
		out.append((sec, n))
	return out


def apply_classic_chlist_description(skin):
	"""User approval 2026-10-04 11:58 (C-2): the channel-list event description used movetype=running (the text
	enters from BELOW the box, so the box looks empty for seconds).  Swimming starts with the first line at the
	top; every other option (step, speed, delays) and the box stay as they were."""
	f = os.path.join(skin, "layouts", "channelselection", "classic", "screens.openatv.xml")
	x = open(f, encoding="utf-8").read()
	m = re.search(r'<screen name="ChannelSelection".*?</screen>', x, re.S)
	body = m.group(0)
	ws = re.findall(r'<widget source="ServiceEvent" render="RunningText"[^>]*options="movetype=running,direction=top[^"]*"[^>]*>\s*<convert type="EventName">FullDescription</convert>', body)
	assert len(ws) == 1, "channel-list description widget not found exactly once (%d)" % len(ws)
	new = body.replace(ws[0], ws[0].replace('movetype=running,direction=top', 'movetype=swimming,direction=top'), 1)
	open(f, "w", encoding="utf-8").write(x.replace(body, new, 1))
	return 1


def apply_classic_imdb_rule(skin):
	"""User decision 2026-10-04: Classic follows the rating rule of the new families - a rating (and its badge)
	only for an event identified as a film or series from its EPG text; never '--'.  Same positions/sizes:
	the static badge becomes a Pixmap widget that is hidden while no rating is shown."""
	out = []
	for sec in sorted(os.listdir(os.path.join(skin, "layouts"))):
		f = os.path.join(skin, "layouts", sec, "classic", "screens.openatv.xml")
		if not os.path.isfile(f):
			continue
		x = open(f, encoding="utf-8").read()
		n = x.count('<convert type="CineViewMLAIMDb">Plain</convert>') + x.count('<convert type="CineViewMLAIMDb">Stars</convert>')
		if not n:
			continue
		b = x.count(IMDB_BADGE)
		x = x.replace('<convert type="CineViewMLAIMDb">Plain</convert>', '<convert type="CineViewMLAIMDb">Plain,hide</convert>')
		x = x.replace('<convert type="CineViewMLAIMDb">Stars</convert>', '<convert type="CineViewMLAIMDb">Stars,hide</convert>')
		x = x.replace(IMDB_BADGE, IMDB_BADGE_NEW)
		open(f, "w", encoding="utf-8").write(x)
		out.append((sec, n, b))
	return out


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


# ---------------------------------------------------------------------------------------------------------
# Phase B (user approval 2026-10-04 16:04, EXPERIMENTAL until visually approved): Classic posters OFF.
# Posters ON keeps every Classic element exactly as it is (same position, size, colour, z-order); each element
# that has to move when the section's poster switch is OFF gets an "ON" copy (shown unless the switch is False)
# and an "OFF" copy at its new place (shown only when the switch is False).  Elements that only make sense next
# to the poster (the separator right of it, a divider above the poster row) get the ON copy only.
# Mechanics (all OpenATV-native or our own tested converter):
#   widgets      : CineViewMLAShowIf <key>,True[,Invert][,dir=..] appended (an existing "always,True,dir=x"
#                  direction switch becomes "<key>,True[,Invert],dir=x");
#   static boxes : eLabel -> Label widget on session.CurrentService with the same backgroundColor (theme
#                  colour names keep working) and CineViewMLAShowIf <key>,True[,Invert],text=  (empty caption);
#   untouched    : widgets driven by ConditionalShowHide (IMDb badge) and every element that does not move.
POFF_STRIP = {"hide_x": 156, "shift_from": 156, "shift_to": 1072, "shift": -130, "event_x": 1090, "ymin": 842, "ymax": 1015}
POFF_RULES = {
	# section: {screen: [(match(tag, x, y, w, h) -> bool, action)]}; action = "hide" | (dx, dy, dw, dh)
	"channelselection": {"ChannelSelection": [
		(lambda t, x, y, w, h: t == "widget" and (x, y, w, h) == (1205, 305, 340, 383), (0, 0, 295, 233)),  # description: full width, 22 lines
		(lambda t, x, y, w, h: t == "eLabel" and (x, y, w, h) == (1205, 716, 635, 2), "hide"),             # divider above the poster row
	]},
	"epg": {
		"EPGSelection": [(lambda t, x, y, w, h: t == "widget" and (x, y, w, h) == (1205, 246, 340, 360), (0, 0, 265, 0))],
		"EPGSelectionMulti": [(lambda t, x, y, w, h: t == "widget" and (x, y, w, h) == (1210, 120, 250, 120), (0, 0, 305, 0))],
		"QuickEPG": [(lambda t, x, y, w, h: t == "widget" and (x, y, w, h) == (920, 45, 600, 300), (0, 0, 275, 0))],
		"GraphicalEPG": [
			(lambda t, x, y, w, h: t == "widget" and (x, y, w, h) in ((230, 72, 1625, 48), (230, 168, 1625, 138)), (-185, 0, 185, 0)),
			(lambda t, x, y, w, h: t == "widget" and (x, y) in ((230, 126), (350, 126)), (-185, 0, 0, 0)),
		],
		"GraphMultiEPG": [
			(lambda t, x, y, w, h: t == "widget" and (x, y, w, h) in ((70, 90, 1490, 46), (70, 188, 1490, 135), (202, 157, 1180, 8)), (0, 0, 285, 0)),
			(lambda t, x, y, w, h: t == "widget" and (x, y) == (1394, 145), (285, 0, 0, 0)),
		],
	},
}


def _poff_strip_rule(t, x, y, w, h):
	"""The InfoBar strip shared by InfoBar, SecondInfoBar* and EventView: the poster block (16..156) is
	removed, every column right of it moves 130 px left, the event column keeps its right edge and grows."""
	s = POFF_STRIP
	if not (s["ymin"] <= y <= s["ymax"]):
		return None
	if x == s["hide_x"] and w == 2:
		return "hide"
	if s["shift_from"] < x <= s["shift_to"]:
		return (s["shift"], 0, 0, 0)
	if x == s["event_x"]:
		return (s["shift"], 0, -s["shift"], 0)
	return None


def _poff_variant(el, key, off, pos=None, size=None):
	tag = el.lstrip()[1:].split(None, 1)[0]
	ind = re.match(r"[ \t]*", el).group(0)
	a = _attrs(el[:el.index(">") + 1])
	if pos:
		el = re.sub(r'position="[^"]*"', 'position="%d,%d"' % pos, el, count=1)
	if size:
		el = re.sub(r'size="[^"]*"', 'size="%d,%d"' % size, el, count=1)
	inv = ",Invert" if off else ""
	if tag == "eLabel":
		keep = " ".join('%s="%s"' % (k, v) for k, v in a.items() if k not in ("position", "size", "text"))
		p = pos or tuple(map(int, a["position"].split(",")))
		s = size or tuple(map(int, a["size"].split(",")))
		return ('%s<widget source="session.CurrentService" render="Label" position="%d,%d" size="%d,%d" %s>'
			'<convert type="CineViewMLAShowIf">%s,True%s,text=</convert></widget>' % (ind, p[0], p[1], s[0], s[1], keep, key, inv))
	m = re.search(r'<convert type="CineViewMLAShowIf">always,True(,dir=(?:ltr|rtl))</convert>', el)
	if m:
		return el.replace(m.group(0), '<convert type="CineViewMLAShowIf">%s,True%s%s</convert>' % (key, inv, m.group(1)), 1)
	conv = '<convert type="CineViewMLAShowIf">%s,True%s</convert>' % (key, inv)
	if el.rstrip().endswith("/>"):
		return el.rstrip()[:-2].rstrip() + ">" + conv + "</widget>"
	i = el.rindex("</widget>")
	return el[:i].rstrip() + "\n" + ind + "\t" + conv + "\n" + ind + el[i:]


def apply_classic_posters_off(skin):
	"""Returns [(section, screen, moved, hidden)].  Only screens that contain a CineViewMLAPosterX are touched."""
	out = []
	elre = re.compile(r'[ \t]*<(?:eLabel|widget|ePixmap)\b[^>]*?(?:/>|>.*?</widget>)', re.S)
	for sec in ("infobar", "secondinfobar", "eventview", "channelselection", "epg"):
		path = os.path.join(skin, "layouts", sec, "classic", "screens.openatv.xml")
		src = open(path, encoding="utf-8").read()
		key = POSTER_TOGGLE % sec

		def screen_fix(m):
			body = m.group(0)
			name = _attrs(body[:body.index(">")]).get("name", "?")
			if 'render="CineViewMLAPosterX"' not in body:
				return body
			rules = POFF_RULES.get(sec, {}).get(name, [])
			strip = sec in ("infobar", "secondinfobar", "eventview") and any(
				_attrs(p).get("position") == "40,850" and _attrs(p).get("size") == "105,158"
				for p in re.findall(r'<widget\b[^>]*render="CineViewMLAPosterX"[^>]*>', body))
			moved = hidden = 0

			def el_fix(em):
				nonlocal moved, hidden
				el = em.group(0)
				head = el[:el.index(">") + 1]
				if "ConditionalShowHide" in el or 'render="CineViewMLAPosterX"' in head:
					return el
				a = _attrs(head)
				if "position" not in a or "size" not in a:
					return el
				t = el.lstrip()[1:].split(None, 1)[0]
				try:
					x, y = map(int, a["position"].split(","))
					w, h = map(int, a["size"].split(","))
				except ValueError:
					return el
				act = None
				for match, action in rules:
					if match(t, x, y, w, h):
						act = action
						break
				if act is None and strip:
					act = _poff_strip_rule(t, x, y, w, h)
				if act is None:
					return el
				on = _poff_variant(el, key, False)
				if act == "hide":
					hidden += 1
					return on
				dx, dy, dw, dh = act
				moved += 1
				return on + "\n" + _poff_variant(el, key, True, (x + dx, y + dy), (w + dw, h + dh))

			body = elre.sub(el_fix, body)
			out.append((sec, name, moved, hidden))
			return body

		new = re.sub(r"<screen\b.*?</screen>", screen_fix, src, flags=re.S)
		open(path, "w", encoding="utf-8").write(new)
	return out


# Screens whose texts are Python-owned named widgets (self["FullDescription"], self["epg_description"], ...):
# a skin cannot make a conditional copy of them.  For posters OFF the skin ships a second screen
# "<name>_CVPosterOff" with the wider geometry, and the CineView MLA plugin (sessionstart, MLA skin active,
# switch False) puts that name in front of the screen's skinName list before the skin is applied — the native
# skinName fallback picks it; with the switch ON (or the plugin absent) nothing changes.  No enigma2 file is
# modified.  (user request 2026-10-04 17:01: "safe runtime solution")
POFF_NAMED = {
	("secondinfobar", "SecondInfoBarECM"): {"channel": 1790, "epg_description": 1790, "#PliExtraInfo": 1790},
	("eventview", "EventViewSimple"): {"channel": 1730, "Title": 1730, "FullDescription": 1730},
	("eventview", "InfoBarEventView"): {"FullDescription": 1795},
}


def apply_classic_posters_off_named(skin):
	out = []
	for (sec, scr), widths in POFF_NAMED.items():
		path = os.path.join(skin, "layouts", sec, "classic", "screens.openatv.xml")
		src = open(path, encoding="utf-8").read()
		m = re.search(r'([ \t]*)<screen name="%s"(.*?)</screen>' % re.escape(scr), src, re.S)
		assert m, scr
		body = m.group(0)
		new = body.replace('<screen name="%s"' % scr, '<screen name="%s_CVPosterOff"' % scr, 1)
		n = 0
		for key, w in widths.items():
			if key.startswith("#"):  # a source widget identified by its converter text
				pat = r'(<widget\b[^>]*size=")(\d+),(\d+)("[^>]*>\s*<convert type="%s")' % re.escape(key[1:])
			elif key == "Title":
				pat = r'(<widget source="Title"[^>]*size=")(\d+),(\d+)(")'
			else:
				pat = r'(<widget name="%s"[^>]*size=")(\d+),(\d+)(")' % re.escape(key)
			new, k = re.subn(pat, lambda mm: "%s%d,%s%s" % (mm.group(1), w, mm.group(3), mm.group(4)), new, count=1)
			assert k == 1, (scr, key)
			n += k
		open(path, "w", encoding="utf-8").write(src.replace(body, body + "\n" + new, 1))
		out.append((sec, scr, n))
	return out


def make_classic_lines_pack(skin):
	"""EventView 'Classic — line by line' (user approval in principle 2026-10-04 17:01; Classic with continuous
	scrolling stays the factory choice).  Same pack as Classic EventView, only the 8 EventView description widgets:
	* one whole line (29 px = pitch of size 25) every 1740 ms instead of 1 px every 60 ms (same reading speed);
	* transparent="0" backgroundColor="steSecondInfoBG": the label paints the panel colour it sits on (the same ARGB
	  value), so every repaint overwrites its whole box — a stale line can no longer stay behind (device 17:0x:
	  one doubled Arabic line for 1.7 s in a transparent label)."""
	src = os.path.join(skin, "layouts", "eventview", "classic")
	dst = os.path.join(skin, "layouts", "eventview", "classic-lines")
	if os.path.exists(dst):
		shutil.rmtree(dst)
	shutil.copytree(src, dst)
	p = os.path.join(dst, "screens.openatv.xml")
	x = open(p, encoding="utf-8").read()
	m = re.search(r'<screen name="EventView".*?</screen>', x, re.S)
	body = m.group(0)
	n = 0

	def fix(wm):
		nonlocal n
		t = wm.group(0)
		if 'EventName">FullDescription' in t and "step=1,steptime=60,startdelay=4000" in t:
			n += 1
			t = t.replace("step=1,steptime=60,startdelay=4000", "step=%d,steptime=1740,startdelay=4000" % _pitch(25))
			t = t.replace('transparent="1"', 'transparent="0" backgroundColor="steSecondInfoBG"', 1)
		return t

	body2 = re.sub(r'<widget\b[^>]*render="RunningText".*?</widget>', fix, body, flags=re.S)
	assert n == 8, "EventView description widgets: %d" % n
	open(p, "w", encoding="utf-8").write(x.replace(body, body2, 1))
	mf = os.path.join(dst, "manifest.json")
	d = json.load(open(mf))
	d.update({"id": "classic-lines", "name": "CineView Classic (line by line)"})
	json.dump(d, open(mf, "w"), indent=1)
	return n


def apply_zorder_backgrounds(skin):
	"""Z-order fix (device 2026-10-04 18:0x, t30): in 57b7a51 Screen.createGUIScreen() creates the plain skin
	<eLabel> elements AFTER all widgets, and eWidget::insertIntoParent() puts a child after every sibling with
	z <= its own z.  An opaque background <eLabel ... zPosition="0"> therefore covers every widget with
	zPosition 0 (inherited from the golden CineView FHD: QuickEPG, Multi EPG header/description, InfoBarEventView,
	EventViewSimple, SecondInfoBarECM bottom row, vertical / PiG EPGs were blank on the TV).
	Fix = the native pattern of enigma2's own skin_default.xml: the background eLabel goes to zPosition="-1".
	Only layout packs; only opaque eLabels that cover a widget.  Geometry and colours are unchanged."""
	sys.path.insert(0, HERE)
	import zorder_check
	out = []
	for p in sorted(glob.glob(os.path.join(skin, "layouts", "*", "*", "screens*.xml"))):
		covered = zorder_check.check(p)
		if not covered:
			continue
		bad = {(c[0], c[2], c[3]) for c in covered if c[1] == "eLabel"}
		assert len(bad) == len({(c[0], c[2], c[3]) for c in covered}), "covering element is not an eLabel: %s" % p
		x = open(p, encoding="utf-8").read()

		def fix_screen(sm):
			body = sm.group(0)
			name = re.match(r'<screen name="([^"]+)"', body).group(1)
			for scr, pos, size in bad:
				if scr != name:
					continue
				pat = r'<eLabel position="%s" size="%s"([^>]*?)zPosition="0"' % (re.escape(pos), re.escape(size))
				body, k = re.subn(pat, lambda m: '<eLabel position="%s" size="%s"%szPosition="-1"' % (pos, size, m.group(1)), body)
				assert k == 1, "eLabel %s %s in %s: %d matches" % (pos, size, name, k)
				out.append((os.path.relpath(p, skin), name, pos, size))
			return body
		x = re.sub(r'<screen name="[^"]+".*?</screen>', fix_screen, x, flags=re.S)
		open(p, "w", encoding="utf-8").write(x)
		assert not zorder_check.check(p), "z-order still covered after fix: %s" % p
	return out


def load_theme_module(control_dir):
	spec = importlib.util.spec_from_file_location("cv_theme", os.path.join(control_dir, "theme.py"))
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	return m


def main(golden, comps, control, out):
	sys.dont_write_bytecode = True  # the engine is imported from the output tree below
	skin = os.path.join(out, SKIN)
	# Static guard (found on device 18:41): never ship code that binds "_" and calls gettext _().
	run(sys.executable, os.path.join(HERE, "check_gettext_shadow.py"), os.path.join(REPO, "mla"), os.path.join(HERE, "devtools"))
	if os.path.exists(out):
		shutil.rmtree(out)
	run(sys.executable, os.path.join(HERE, "migrate_classic.py"), golden, os.path.join(REPO, "mla", "sections.json"), skin)
	for sec, n in apply_classic_rtl_titles(skin):
		print("RTL titles (Classic) %-14s %d event-title widgets got a right-to-left twin" % (sec, n))
	print("Channel-list description (Classic): swimming from the top (%d widget)" % apply_classic_chlist_description(skin))
	for sec, n, b in apply_classic_imdb_rule(skin):
		print("IMDb rule (Classic) %-14s %d rating widgets, %d badges" % (sec, n, b))
	for sec, scr, what in apply_poster_toggles(skin):
		print("M5 %-16s %-22s %s" % (sec, scr, what))
	for scr, source, kind in apply_sib_textfit(skin):
		print("SIB-TEXTFIT %-20s %-18s %s (narrow+wide)" % (scr, source, kind))
	if os.environ.get("MLA_CLASSIC_POFF", "1") == "1":  # Phase B, user-approved 2026-10-04 17:01 (MLA_CLASSIC_POFF=0 = rc4 layout)
		for sec, scr, mv, hd in apply_classic_posters_off(skin):
			print("POSTERS-OFF (Classic) %-16s %-22s %d moved, %d hidden" % (sec, scr, mv, hd))
		for sec, scr, n in apply_classic_posters_off_named(skin):
			print("POSTERS-OFF (Classic, named widgets) %-16s %s_CVPosterOff: %d widgets widened" % (sec, scr, n))
	print("EventView pack classic-lines: %d description widgets (line by line, opaque label)" % make_classic_lines_pack(skin))
	# P7: Details family (user-approved direction 2026-10-03; Classic packs untouched).
	make_default_poster(os.path.join(skin, "mla_assets", "poster_default.jpg"))  # the P7 poster slots embed it
	sys.path.insert(0, os.path.join(HERE, "p7"))
	import gen_details
	import gen_cinema
	for d in gen_details.generate(skin) + gen_cinema.generate(skin):
		print("P7 pack:", os.path.relpath(d, skin))
		_p7_preview(d, skin)
	# D1 (user-approved 2026-10-04 17:01): Channel Selection families Poster List / Video First (+ list on the right).
	sys.path.insert(0, os.path.join(HERE, "p8cs"))
	import gen_channels
	mocks = os.environ.get("MLA_CS_MOCKS", "")
	for d in gen_channels.generate(skin):
		print("D1 pack:", os.path.relpath(d, skin))
		pid = os.path.basename(d)
		src = os.path.join(mocks, {"posterlist": "posterlist_on.png", "videofirst": "videofirst_on.png", "videofirst-right": "videofirst_on_right.png"}[pid])
		if mocks and os.path.isfile(src):
			from PIL import Image
			Image.open(src).convert("RGB").resize((720, 405)).save(os.path.join(d, "preview.png"))
		else:
			make_preview_none(os.path.join(d, "preview.png"))

	for f, scr, pos, size in apply_zorder_backgrounds(skin):
		print("Z-ORDER %-45s %-28s background eLabel %s %s -> zPosition -1" % (f, scr, pos, size))

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
	# G-1 (EPG): the GraphicalEPG cells use enigma2's NATIVE default 0x2D455E (EpgList.backColor), a slate
	# blue that stayed in every theme (theme sweep: ~25 % navy residue on the EPG only).  A theme role
	# steEpgCell takes over: navy = exactly 0x2D455E (Classic unchanged), other themes = the same cell
	# re-tinted to the theme hue (black: neutral).
	for key in theme.THEMES:
		cell = "#00%s" % recolor_rgb((0x2D, 0x45, 0x5E), theme.THEMES[key][1], key == "black")
		tx = os.path.join(skin, "themes", key, "theme.xml")
		x = open(tx, encoding="utf-8").read()
		anchor = "</colors>"
		assert x.count(anchor) == 1
		x = x.replace(anchor, '\t<color name="steEpgCell" value="%s" />\n\t%s' % (cell, anchor))
		open(tx, "w", encoding="utf-8").write(x)
	n_epg = 0
	ep = os.path.join(skin, "layouts", "epg", "classic", "screens.openatv.xml")
	x = open(ep, encoding="utf-8").read()
	for scr in ("GraphicalEPG", "GraphicalEPGPIG", "GraphicalInfoBarEPG", "GraphMultiEPG"):
		m = re.search(r'<screen name="%s"[^>]*>.*?</screen>' % scr, x, re.S)
		if not m:
			continue
		body = m.group(0)
		w = re.search(r'<widget name="list"[^>]*?/?>', body)
		if not w:
			continue
		tag = w.group(0)
		add = "".join(' %s="steEpgCell"' % a for a in ("EntryBackgroundColor", "EntryBackgroundColorPast", "ServiceBackgroundColor", "TimeBackgroundColor") if (a + "=") not in tag)
		if add:
			end = -2 if tag.endswith("/>") else -1
			body2 = body.replace(tag, tag[:end].rstrip() + add + tag[end:], 1)
			x = x.replace(body, body2, 1)
			n_epg += 1
	open(ep, "w", encoding="utf-8").write(x)
	print("G-1 EPG cell colour role on %d GraphicalEPG list widget(s)" % n_epg)
	shutil.rmtree(os.path.join(skin, "themes", "golden"))
	# Per-theme bitmap assets of the original theme engine (if shipped).
	src_theme_assets = os.path.join(golden, "themes")
	if os.path.isdir(src_theme_assets):
		for key in os.listdir(src_theme_assets):
			shutil.copytree(os.path.join(src_theme_assets, key), os.path.join(skin, "themes", key, "assets"), dirs_exist_ok=True)

	# G-1: per-theme bitmaps.  The original engine swapped 3 hand-made bitmaps per theme; the scan of the skin
	# for navy-tinted bitmaps in use found 4 more (event progress bar infobar/pbar.png [P7 purple test], progress bar, PVR position pointer, and the GraphicalEPG
	# "now" cell, which 57b7a51 loads natively by fixed path).  Every theme bitmap lives in the generation
	# (active/assets/<rel>) and the skin path is a symlink to it, so the XML is untouched (Classic parity) and
	# bitmaps switch atomically with the colours.  navy = the original files.
	theme_assets = ("infobar/hd.png", "infobar/bl80.png", "extensions/transblack.png", "infobar/pbar.png",
		"window/progress.png", "dvr/position_pointer1.png", "epg/CurrentEvent.png")
	for rel in theme_assets:
		orig = os.path.join(skin, rel)
		navy = os.path.join(skin, "themes", "navy", "assets", rel)
		os.makedirs(os.path.dirname(navy), exist_ok=True)
		if not os.path.isfile(navy):
			shutil.copy2(orig, navy)
		assert open(navy, "rb").read() == open(orig, "rb").read(), "navy asset must equal the Classic bitmap: " + rel
		for key in theme.THEMES:
			dst = os.path.join(skin, "themes", key, "assets", rel)
			if not os.path.isfile(dst):
				recolor_png(orig, dst, theme.THEMES[key][1], key == "black")
		os.remove(orig)
		os.symlink(os.path.join("..", "active", "assets", rel), orig)
	print("G-1 theme assets (symlinked to active/assets):", len(theme_assets))

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
			if base == "CineViewIMDb":
				# P7: ",hide" argument (new families only): no rating -> empty text instead of the "--" placeholder
				# (rule: never show unavailable information). Classic keeps its approved behaviour (no ",hide").
				for old, new in IMDB_PATCHES:
					assert src.count(old) == 1, "imdb patch anchor not unique: %r" % old[:50]
					src = src.replace(old, new)
				src += IMDB_GENERIC_HELPER
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
		dest = os.path.join(out, PY) if kind == "_lib" else os.path.join(out, PY, kind)  # _lib = plain modules
		for f in sorted(os.listdir(os.path.join(own, kind))):
			if f.endswith(".py"):
				shutil.copy2(os.path.join(own, kind, f), os.path.join(dest, f))

	# P5: unified poster identity (one engine and one cache key for every screen) + neutral default poster.
	posterx = os.path.join(out, PY, "Renderer", "CineViewMLAPosterX.py")
	with open(posterx, "a", encoding="utf-8") as f:
		f.write(open(os.path.join(HERE, "patches", "posterx_identity.py"), encoding="utf-8").read())
	make_default_poster(os.path.join(skin, "mla_assets", "poster_default.jpg"))
	make_preview_none(os.path.join(skin, "mla_assets", "preview_none.png"))

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
