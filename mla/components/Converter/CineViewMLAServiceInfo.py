# -*- coding: utf-8 -*-
# CineView MLA — native ServiceInfo with a reliable update for the video-geometry tokens (IsHD, 16:9, ...).
#
# Root cause (device t53, 2026-10-05, enigma2 57b7a51 on Vu+ Duo 4K SE): the native converter re-evaluates
# IsHD / IsWidescreen / Is4K / IsSD ... ONLY on iPlayableService.evVideoSizeChanged (and evVideoGammaChanged).
# After an Enigma2 start the decoder sometimes emits no video-size event at all after the screen's converters
# are connected (the picture size does not change for the driver), so the converter keeps the value it computed
# at connect time, when no service was playing yet (False) -> HD / 16:9 icons stay hidden while VideoSize (which
# reads the size on every change) and HasTeletext (evUpdatedInfo) are correct.  Classic native icons and the
# Modern chips fail the same way (t53: classic_r1_graphite, classic_r2_navy, modern_r1_black).
#
# Fix (CineView side only, no Enigma2 file changed): same converter, same tokens, same result logic (inherited),
# but the video-geometry tokens are also re-evaluated on evStart / evUpdatedInfo / evVideoFramerateChanged /
# evVideoProgressiveChanged / evVideoGammaChanged, and once more 1.5 s and 4 s after evStart / evUpdatedInfo
# (the native fallback eAVControl reads the running decoder when sVideoInfo is still -1).
# usage: <convert type="CineViewMLAServiceInfo">IsHD</convert>  (build.py rewrites the video tokens of the skin)
from enigma import eTimer, iPlayableService

from Components.Converter.ServiceInfo import ServiceInfo

VIDEO_TOKENS = ("Is1080", "Is480", "Is4K", "Is576", "Is720", "IsHD", "IsHDHDR", "IsHDR", "IsHDR10", "IsHLG",
	"IsNotWidescreen", "IsSD", "IsSDR", "IsWidescreen", "VideoHeight", "VideoWidth", "Progressive", "FrameRate", "Framerate")
EXTRA_EVENTS = (iPlayableService.evStart, iPlayableService.evUpdatedInfo, iPlayableService.evVideoSizeChanged,
	iPlayableService.evVideoFramerateChanged, iPlayableService.evVideoProgressiveChanged, iPlayableService.evVideoGammaChanged)
RECHECK_MS = (1500, 4000)


class CineViewMLAServiceInfo(ServiceInfo):
	def __init__(self, argument):
		ServiceInfo.__init__(self, argument)
		self._video = argument in VIDEO_TOKENS
		self._timer = None
		self._steps = []
		if self._video:
			# the native ServiceInfo keeps its event filter under an image-specific name (OpenATV: interestingEvents,
			# OpenBH/OpenViX: interesting_events); extend whichever one the base class created
			for name in ("interestingEvents", "interesting_events"):
				if hasattr(self, name):
					setattr(self, name, tuple(set(tuple(getattr(self, name) or ()) + EXTRA_EVENTS)))
					break

	def _recheck(self):
		ServiceInfo.changed(self, (self.CHANGED_ALL,))
		if self._steps:
			self._timer.start(self._steps.pop(0), True)

	def changed(self, what):
		ServiceInfo.changed(self, what)
		if self._video and what[0] == self.CHANGED_SPECIFIC and what[1] in (iPlayableService.evStart, iPlayableService.evUpdatedInfo):
			if self._timer is None:
				self._timer = eTimer()
				self._timer.callback.append(self._recheck)
			first = RECHECK_MS[0]
			self._steps = [b - a for a, b in zip(RECHECK_MS, RECHECK_MS[1:])]
			self._timer.start(first, True)
