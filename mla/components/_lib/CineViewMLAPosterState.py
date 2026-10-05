# -*- coding: utf-8 -*-
"""CineView MLA — which poster widgets currently SHOW a real poster (shared by the poster renderer and the
CineViewMLAShowIf converter).

Used for the "No Poster" layout (user decision 2026-10-05 22:03): when an event has no poster, a screen that has a
posters-OFF arrangement uses it for that event instead of showing a placeholder.  The poster renderer
(CineViewMLAPosterX) publishes its decision per (toggle key, nexts); converters created with the flag
",poster0" / ",poster1" follow it.
State is per process and in memory only; nothing is stored."""
import weakref

_STATE = {}       # (toggle key, nexts) -> True (a real poster is shown) / False (none, or not yet)
_LISTENERS = []   # weak references to converters


def get(key, nexts):
	return _STATE.get((key, nexts), False)


def listen(obj):
	try:
		_LISTENERS.append(weakref.ref(obj))
	except TypeError:
		pass


def publish(key, nexts, available):
	if not key:
		return
	k = (key, int(nexts or 0))
	available = bool(available)
	if _STATE.get(k) is available:
		return
	_STATE[k] = available
	alive = []
	for ref in _LISTENERS:
		obj = ref()
		if obj is None:
			continue
		alive.append(ref)
		try:
			obj.poster_state_changed(k[0], k[1])
		except Exception as err:
			print("[CineViewMLAPosterState] listener error: %s" % err)
	_LISTENERS[:] = alive
