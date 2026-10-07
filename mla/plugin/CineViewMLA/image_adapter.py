# -*- coding: utf-8 -*-
# CineView MLA - ImageAdapter: everything that differs between Enigma2 images lives here; the rest of the plugin
# (and the skin core) is shared.  The image is identified from Enigma2's own build information
# (/usr/lib/enigma.info "distro"), never from a receiver model list.
#
# Per image:
#   native_rows()   the image's own settings CineView Designs offers next to the CineView options.  Each row is shown
#                   only when the setting really exists in this image's config tree.
#   shutdown_hook   how the plugin learns that Enigma2 quits normally (guardian "clean exit" signal):
#                   "session"   - session.onShutdown (OpenATV 57b7a51)
#                   "autostart" - WHERE_AUTOSTART plugin called with reason=1 by PluginComponent.removePlugin from
#                                 plugins.shutdown() (OpenBH / OpenViX family: Session has no onShutdown)
#   choicebox_list  keyword of Screens.ChoiceBox for the item list:
#                   "choiceList" - OpenATV 57b7a51 ChoiceBox(session, text, choiceList, ...)
#                   "list"       - OpenBH 52dedddc314a / c06a87ef4c09 ChoiceBox(session, title, list, ...); any other
#                                  keyword is swallowed by its **kwargs, so choiceList= opens an EMPTY menu
#                                  (OpenBH t106f run: CineView profiles menu without entries)
# Adding an image = one entry in IMAGES (+ skin overrides only where its native screens differ).
import os

ENIGMA_INFO = "/usr/lib/enigma.info"
DEFAULT_IMAGE = "openatv"  # the image CineView MLA 1.0.0 was built and verified on

# OpenATV 8.0.1 (57b7a51) Components/UsageConfig: two separate native settings.
_OPENATV_ROWS = (
	("show_second_infobar", "Second InfoBar mode",
		"What the INFO key opens after the InfoBar (OpenATV setting).",
		"Second InfoBar, event information or nothing when INFO is pressed again."),
	("second_infobar_timeout", "Second InfoBar timeout",
		"How long the Second InfoBar stays on screen (OpenATV setting).",
		"After this time the Second InfoBar closes by itself."),
)
# OpenBH 5.6 / 6.0 (BlackHole/enigma2 52dedddc314a, c06a87ef4c09) Components/UsageConfig: ONE native setting -
# show_second_infobar = no / no timeout / 3..60 s / EPG / InfoBar EPG, opened by pressing OK twice (data/setup.xml).
_OPENBH_ROWS = (
	("show_second_infobar", "Second InfoBar",
		"Whether - and for how long - the Second InfoBar is shown when OK is pressed twice (OpenBH setting).",
		"No, no timeout, a time in seconds, or the EPG / InfoBar EPG instead, when OK is pressed twice."),
)

IMAGES = {
	"openatv": {"rows": _OPENATV_ROWS, "shutdown_hook": "session", "choicebox_list": "choiceList"},
	"openbh": {"rows": _OPENBH_ROWS, "shutdown_hook": "autostart", "choicebox_list": "list"},
}

_image = None


def image():
	"""'openatv', 'openbh', ... from /usr/lib/enigma.info (distro=...); DEFAULT_IMAGE when it cannot be read."""
	global _image
	if _image is None:
		_image = DEFAULT_IMAGE
		try:
			for line in open(ENIGMA_INFO):
				if line.startswith("distro="):
					_image = line.split("=", 1)[1].strip().strip("'\"").lower() or DEFAULT_IMAGE
					break
		except Exception as err:
			print("[CineViewMLA] image detection: %s - using %s" % (err, DEFAULT_IMAGE))
	return _image


def _spec():
	return IMAGES.get(image(), IMAGES[DEFAULT_IMAGE])


def native_rows(usage):
	"""[(key, config element, label, card text, description)] for this image; `usage` is config.usage.
	Rows whose setting does not exist in this image are left out (never an AttributeError)."""
	out = []
	for key, label, card, desc in _spec()["rows"]:
		cfg = getattr(usage, key, None)
		if cfg is not None:
			out.append((key, cfg, label, card, desc))
	return out


def shutdown_hook():
	return _spec()["shutdown_hook"]


def choice_list(items):
	"""ChoiceBox keyword argument carrying the menu entries on this image: session.open(ChoiceBox, ..., **choice_list(x))."""
	return {_spec().get("choicebox_list", "choiceList"): items}
