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
from Components.Renderer.RunningText import RunningText, SWIMMING, TOP


class CineViewMLALineText(RunningText):
	def __init__(self):
		RunningText.__init__(self)
		self._cv_restart = False

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
