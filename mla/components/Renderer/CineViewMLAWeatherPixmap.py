# -*- coding: utf-8 -*-
# CineView MLA - weather icon of the CineView designs (with Converter CineViewMLAWeather "weathericon,current").
# Design & Development by habeb-s (c) 2026.  Own code.
# Shows the picture file the converter names (source.iconfilename), scaled into the widget with its aspect ratio
# kept and centred; hidden while there is no icon.  The file is loaded again only when its name changes.
from enigma import ePixmap

from Components.Renderer.Renderer import Renderer

try:
	from enigma import BT_HALIGN_CENTER, BT_KEEP_ASPECT_RATIO, BT_SCALE, BT_VALIGN_CENTER
	SCALE_FLAGS = BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER
except ImportError:
	SCALE_FLAGS = None


class CineViewMLAWeatherPixmap(Renderer):
	GUI_WIDGET = ePixmap

	def __init__(self):
		Renderer.__init__(self)
		self.file = ""

	def postWidgetCreate(self, instance):
		try:
			if SCALE_FLAGS is None:
				instance.setScale(1)
			elif hasattr(instance, "setPixmapScale"):
				instance.setPixmapScale(SCALE_FLAGS)
			else:
				instance.setPixmapScaleFlags(SCALE_FLAGS)
		except Exception as e:
			print("[CineViewMLAWeatherPixmap] scaling: %s" % e)
		self.changed((self.CHANGED_DEFAULT,))

	def changed(self, what):
		if not self.instance:
			return
		name = ""
		if what[0] != self.CHANGED_CLEAR and self.source is not None:
			try:
				name = self.source.iconfilename or ""
			except Exception:
				name = ""
		if not name:
			self.instance.hide()
			return
		if name != self.file:
			self.instance.setPixmapFromFile(name)
			self.file = name
		self.instance.show()
