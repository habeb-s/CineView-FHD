# -*- coding: utf-8 -*-
# CineView MLA — "line by line" description text (EventView pack classic-lines).
#
# Native RunningText (57b7a51) in movetype=swimming,direction=top reverses at the end of the text and swims back to
# the first line, one step (= one line here) per steptime.  On this receiver every one of those DOWNWARD 29-px moves
# of the scroll label left a strip of two overlapping lines (or half a box blank) for a whole step: device t39
# 2026-10-05 00:0x, English text, frames 261-269 (jumpcheck: 2 bad moves of 31, both shift -29); upward moves are
# always clean.  Enigma2 itself is not modified.  This renderer keeps RunningText unchanged except at that one
# point: when a text TALLER than its box has reached its last line, it holds for "pause" ms and then starts again
# from the first line with a full redraw (the same path as a new event: empty text, then calcMoving()).
# Short texts (fit in the box), other directions and other move types behave exactly like RunningText.
#
# Second measure (device t46 2026-10-05 01:0x, English round 3: 2 of 37 moves, both FORWARD, mid-text): after a
# line move the repaint of the label occasionally comes out wrong — one frame half blank, then two lines drawn
# over each other until the next step (1.6 s).  eWidget::move() invalidates the old and the new area (this
# receiver's desktop is not buffered, eWidgetDesktop::movedWidget() returns -1), so the fault lies in the paint
# itself (enigma2 graphics / driver; not modifiable here, cause not proven).  Mitigation: every line move is
# followed, 150 ms later, by one more full repaint of the label, so a wrong paint lasts at most one frame.
from enigma import eTimer
from Components.Renderer.RunningText import RunningText, SWIMMING, TOP

REPAINT_AFTER_MS = 150


class CineViewMLALineText(RunningText):
	def __init__(self):
		RunningText.__init__(self)
		self._cv_restart = False
		self._cv_repaint = eTimer()
		self._cv_repaint.callback.append(self._cv_invalidate)

	def _cv_invalidate(self):
		try:
			if self.scroll_label is not None and self.instance:
				self.scroll_label.invalidate()
		except Exception as err:
			if not getattr(CineViewMLALineText, "_cv_logged", False):
				CineViewMLALineText._cv_logged = True
				print("[CineViewMLALineText] repaint unavailable: %s" % err)

	def moveLabel(self, X, Y):
		RunningText.moveLabel(self, X, Y)
		if self._cv_repaint is not None:
			self._cv_repaint.start(REPAINT_AFTER_MS, True)

	def preWidgetRemove(self, instance):
		if self._cv_repaint is not None:
			self._cv_repaint.stop()
			self._cv_repaint.callback.remove(self._cv_invalidate)
			self._cv_repaint = None
		RunningText.preWidgetRemove(self, instance)

	def movingLoop(self):
		if self._cv_restart:
			self._cv_restart = False
			if self.scroll_label is not None and self.instance:
				self.scroll_label.setText("")  # invalidates the whole label where it is now
				self.calcMoving()  # first line again, startdelay, normal timer chain
			return
		if self.type == SWIMMING and self.direction == TOP and self.mStep < 0 and self.A < 0 and self.P < self.A:
			# end of a long text: the next native step would reverse the swim -> hold, then restart from the top
			self._cv_restart = True
			self.mTimer.start(max(self.mLoopTimeout, self.mStepTimeout), True)
			return
		RunningText.movingLoop(self)
