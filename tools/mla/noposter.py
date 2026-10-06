#!/usr/bin/env python3
"""No Poster layout instead of a placeholder (user decision 2026-10-05 22:03: "no placeholder when an event has
no poster; use the real No Poster layout").

A screen is DYNAMIC when its text widgets already have posters-ON / posters-OFF variants
(CineViewMLAShowIf "<poster key>,True[,Invert]") for the toggle key of a poster widget in the same screen.  In such
a screen the variants can follow the poster of the event that is on screen, not only the user's switch:
* every "<key>,True..." argument gets ",poster0" (or ",poster1" for the NEXT card when the screen has a NEXT poster
  widget, nexts="1"); CineViewMLAShowIf then shows the ON variant only while that poster widget shows a REAL poster
  (Components/CineViewMLAPosterState.py, published by the poster renderer);
* the default placeholder (tile, icon slices, inner frame line; or the old per-size default bitmap) is removed;
* poster decorations gated by the switch (frame strips / frame bitmaps: ConfigEntryTest <key>,False,Invert +
  ConditionalShowHide) follow the poster instead (CineViewMLAShowIf <key>,True,posterN);
* the poster widget gets underlay="1" (no default picture decoded; nothing drawn when there is no poster).
Screens without variants (separate *_CVPosterOff screens chosen when the screen opens, list screens without
variants) cannot switch per event and are reported, unchanged.
usage: run(skin) -> (dynamic [(file, screen, variants)], static [(file, screen)])"""
import os
import re

PLACEHOLDER = re.compile(r'\t*<widget\b[^>]*pixmap="mla_assets/(?:poster_tile\.png|poster_icon_[^"]+|px_3f4e65\.png|poster_default_\d+x\d+\.png)"[^>]*?(?:/>|>.*?</widget>)\n?', re.S)
WIDGET = re.compile(r'<widget\b[^>]*?(?:/>|>.*?</widget>)', re.S)


def _rect(tag):
	p = re.search(r'position="(\d+),(\d+)"', tag)
	s = re.search(r'size="(\d+),(\d+)"', tag)
	if not (p and s):
		return None
	x, y, w, h = int(p.group(1)), int(p.group(2)), int(s.group(1)), int(s.group(2))
	return x, y, x + w, y + h


def _inside(r, outer, pad=8):
	return r and outer and r[0] >= outer[0] - pad and r[1] >= outer[1] - pad and r[2] <= outer[2] + pad and r[3] <= outer[3] + pad


# Named EventView screens whose ON / OFF version the CineView MLA plugin picks when the screen OPENS (cached poster ->
# ON, none -> '<name>_CVPosterOff').  They have no per-event variants, but the ON version must not show a placeholder
# either if its poster then cannot be shown: placeholder removed, poster underlay="1", frames follow the poster.
# (static audit 2026-10-06, tools/mla/audit_np.py: 11 such screens kept the placeholder)
PLUGIN_SWITCHED = ("EventView", "EventViewSimple", "InfoBarEventView")


def screen_body(body, force=False):
	posters = []
	for m in WIDGET.finditer(body):
		w = m.group(0)
		if 'render="CineViewMLAPosterX"' in w:
			k = re.search(r'toggle="([^"]+)"', w)
			n = re.search(r'nexts="(\d+)"', w)
			if k:
				posters.append((k.group(1), int(n.group(1)) if n else 0, _rect(w)))
	keys = set(k for k, _, _ in posters)
	if not keys:
		return body, 0, False
	variants = sum(len(re.findall(r'CineViewMLAShowIf">%s,True' % re.escape(k), body)) for k in keys)
	if not variants and not force:
		return body, 0, False
	has_next = set(k for k, n, _ in posters if n == 1)

	def fix_widget(m):
		w = m.group(0)
		if 'render="CineViewMLAPosterX"' in w:
			return w if 'underlay="1"' in w else w.replace('render="CineViewMLAPosterX"', 'render="CineViewMLAPosterX" underlay="1"', 1)
		for k in keys:
			# decorations gated by the switch -> follow the poster
			gate = re.search(r'<convert type="ConfigEntryTest">%s,False,Invert</convert>\s*<convert type="ConditionalShowHide"\s*/>' % re.escape(k), w)
			if gate and 'pixmap=' in w:
				r = _rect(w)
				n = 0
				for pk, pn, pr in posters:
					if pk == k and _inside(r, pr):
						n = pn
				w = w.replace(gate.group(0), '<convert type="CineViewMLAShowIf">%s,True,poster%d</convert>' % (k, n))
			if 'CineViewMLAShowIf">%s,True' % k in w:
				nxt = k in has_next and ("Event_Next" in w or re.search(r'<convert type="[^"]+">Next', w) is not None)
				w = re.sub(r'(CineViewMLAShowIf">%s,True[^<]*)</convert>' % re.escape(k),
					lambda mm: mm.group(1) + ("" if ",poster" in mm.group(1) else ",poster%d" % (1 if nxt else 0)) + "</convert>", w)
		return w

	body = PLACEHOLDER.sub("", body)
	body = WIDGET.sub(fix_widget, body)
	return body, variants, True


def gate(lines, key, with_poster, n=0):
	"""Generator helper for list screens whose layout is fixed when they open (EPG / PVR cards): returns the same
	elements shown only while the card's poster widget (toggle key, nexts n) shows a real poster (with_poster=True)
	or only while it does not (False).  eLabels become Label widgets with an empty text (ShowIf 'text='); widgets get
	a CineViewMLAShowIf at the end of their converter chain; named widgets (Python-owned) are returned unchanged."""
	arg = "%s,True%s,poster%d" % (key, "" if with_poster else ",Invert", n)
	out = []
	for l in lines:
		if not l:
			continue
		s = l.strip()
		ind = l[:len(l) - len(l.lstrip())]
		if s.startswith("<eLabel"):
			attrs = s[len("<eLabel"):].rstrip("/>").rstrip()
			out.append('%s<widget source="session.CurrentService" render="Label"%s>\n%s\t<convert type="CineViewMLAShowIf">%s,text=</convert>\n%s</widget>' % (ind, attrs, ind, arg, ind))
		elif s.startswith("<widget") and 'name="' in s.split(">", 1)[0] and 'source="' not in s.split(">", 1)[0]:
			out.append(l)
		elif s.startswith("<widget") and s.endswith("/>") and "</widget>" not in s:
			out.append('%s>\n%s\t<convert type="CineViewMLAShowIf">%s</convert>\n%s</widget>' % (l.rstrip()[:-2].rstrip(), ind, arg, ind))
		elif s.startswith("<widget") and s.endswith("</widget>"):
			k = l.rfind("</widget>")
			out.append(l[:k].rstrip() + '\n%s\t<convert type="CineViewMLAShowIf">%s</convert>\n%s</widget>' % (ind, arg, ind) + l[k + len("</widget>"):])
		else:
			out.append(l)
	return out


POSTERX = re.compile(r'\t*<widget\b[^>]*render="CineViewMLAPosterX"[^>]*?(?:/>|>.*?</widget>)\n?', re.S)


def no_default(name, body):
	"""No poster widget may draw the default image (static audit 2026-10-06):
	* '<name>_CVPosterOff' screens are No Poster screens: the plugin now also opens them with the switch ON for an event
	  without a cached poster, where the renderer would draw the default image (and a poster downloaded later would
	  cover the posters-off text) -> the poster widget is removed;
	* any other poster widget gets underlay="1" (nothing drawn without a real poster)."""
	if name.endswith("_CVPosterOff"):
		return POSTERX.sub("", body)
	return POSTERX.sub(lambda m: m.group(0) if 'underlay="1"' in m.group(0) else m.group(0).replace('render="CineViewMLAPosterX"', 'render="CineViewMLAPosterX" underlay="1"', 1), body)


def run(skin):
	dynamic, static = [], []
	base = os.path.join(skin, "layouts")
	for sec in sorted(os.listdir(base)):
		for pack in sorted(os.listdir(os.path.join(base, sec))):
			p = os.path.join(base, sec, pack, "screens.openatv.xml")
			if not os.path.isfile(p):
				continue
			src = open(p, encoding="utf-8").read()
			out = []
			last = 0
			for m in re.finditer(r'(<screen name="([^"]+)"[^>]*>)(.*?)(</screen>)', src, re.S):
				body, nvar, dyn = screen_body(m.group(3), force=(sec == "eventview" and m.group(2) in PLUGIN_SWITCHED))
				body = no_default(m.group(2), body)
				rel = os.path.relpath(p, skin)
				if 'render="CineViewMLAPosterX"' in m.group(3):
					(dynamic if dyn else static).append((rel, m.group(2), nvar) if dyn else (rel, m.group(2)))
				out.append(src[last:m.start(3)] + body)
				last = m.end(3)
			out.append(src[last:])
			new = "".join(out)
			if new != src:
				import xml.etree.ElementTree as ET
				ET.fromstring(new.split("?>", 1)[1] if new.startswith("<?xml") else new)
				open(p, "w", encoding="utf-8").write(new)
	return dynamic, static
