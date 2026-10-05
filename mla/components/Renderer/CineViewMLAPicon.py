# -*- coding: utf-8 -*-
"""CineView MLA picon renderer: the native Picon renderer (same lookup, same modes, same skin attributes) with a
memory-safe load.

Why (device t69, gAccel debug dump at the failure, enigma2 57b7a51 source):
* Components/Renderer/Picon.py calls instance.setScale(1) then instance.setPixmapFromFile(png);
* ePixmap::setPixmapFromFile passes m_scale as the accel argument (-> accelAlways when scaled) and cached=-1
  (-> PNGs cached), so every picon ever shown is pinned in the receiver's 5400 kB accelerated pool for good
  (220x132 RGBA = 116 kB each);
* Modern's Channel Selection card shows the picon of the channel under the cursor: 42 channels pinned 4.8 MB and
  every later poster / picon fell back from accelAlloc ("[gSurface] ERROR: accelAlloc failed").
Here the PNG is loaded uncached (LoadPixmap cached=False: accelAuto, freed as soon as the next picon replaces it)
and a hidden screen gives its picon back (onHide), so only the picons on screen use the pool.
Nothing else changes: picon search paths, default picon, config.usage.showpicon, DAB images."""
from os.path import exists, getmtime, getsize

from Components.config import config
from Components.Renderer.Picon import Picon, getPiconName
from Tools.LoadPixmap import LoadPixmap

try:
	from Components.Renderer.Picon import getDABImage
except ImportError:  # older images
	def getDABImage(text):
		return None


class CineViewMLAPicon(Picon):
	def _release(self):
		self.pngname = ""
		if self.instance:
			self.instance.hide()
			try:
				self.instance.setPixmap(None)
			except Exception as err:
				print("[CineViewMLAPicon] release: %s" % err)

	def onHide(self):
		Picon.onHide(self)
		self._release()

	def onShow(self):
		Picon.onShow(self)
		if self.instance:
			self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		if not self.instance:
			return
		if self.suspended:
			self._release()
			return
		if what[0] in (self.CHANGED_DEFAULT, self.CHANGED_ALL, self.CHANGED_SPECIFIC):
			pngname = getDABImage(self.source.text) or getPiconName(self.source.text, self.mode)
			if not pngname or not exists(pngname):
				pngname = self.defaultpngname
			if not config.usage.showpicon.value:
				pngname = self.nopicon
			pngkey = (pngname, getmtime(pngname), getsize(pngname)) if pngname and exists(pngname) else pngname
			if self.pngname != pngkey:
				pix = LoadPixmap(pngname, cached=False) if pngname else None
				if pix:
					self.instance.setScale(1)
					self.instance.setPixmap(pix)
					self.instance.show()
				else:
					self.instance.hide()
				self.pngname = pngkey
		elif what[0] == self.CHANGED_CLEAR:
			self._release()
