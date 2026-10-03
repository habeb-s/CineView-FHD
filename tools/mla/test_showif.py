#!/usr/bin/env python3
"""Offline tests of mla/components/Converter/CineViewMLAShowIf.py against stubs of the 57b7a51 Element/Converter
base classes (copied behaviour: downstream_elements list, changed() pushes downstream)."""
import os
import sys
import types

sys.dont_write_bytecode = True
SETTINGS = {}

# --- stubs of the enigma2 modules the converter imports
comp = types.ModuleType("Components")
cfg = types.ModuleType("Components.config")
cfg.configfile = types.SimpleNamespace(getResolvedKey=lambda k, silent=True: SETTINGS.get(k))
conv_pkg = types.ModuleType("Components.Converter")
conv_mod = types.ModuleType("Components.Converter.Converter")


class Element:
	def __init__(self):
		self.downstream_elements = []
		self.source = None

	def connectDownstream(self, d):
		self.downstream_elements.append(d)

	def changed(self, *a):
		for d in self.downstream_elements:
			d.changed(*a)


class Converter(Element):
	def __init__(self, args):
		Element.__init__(self)


conv_mod.Converter = Converter
sys.modules.update({"Components": comp, "Components.config": cfg, "Components.Converter": conv_pkg, "Components.Converter.Converter": conv_mod})
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mla", "components", "Converter"))
from CineViewMLAShowIf import CineViewMLAShowIf  # noqa: E402


class Renderer:
	def __init__(self):
		self.visible = True
		self.seen = None

	def changed(self, what):
		self.seen = self.src.text if hasattr(self.src, "text") else None


class Src:
	def __init__(self, text="", boolean=True, value=500):
		self.text, self.boolean, self.value, self.range = text, boolean, value, 1000


FAIL = 0


def check(name, cond):
	global FAIL
	print(("PASS " if cond else "FAIL ") + name)
	FAIL += 0 if cond else 1


def make(args, src):
	c = CineViewMLAShowIf(args)
	c.source = src
	r = Renderer()
	r.src = c
	c.connectDownstream(r)
	c.changed((2,))
	return c, r


K = "config.plugins.cineviewmla.poster_infobar"
SETTINGS[K] = "True"
c, r = make(K + ",True,dir=ltr", Src("Hello"))
check("ltr text, key True -> visible + text", r.visible and r.seen == "Hello")
c, r = make(K + ",True,dir=rtl", Src("Hello"))
check("rtl variant hidden for ltr text and gets EMPTY text (no hidden animation)", not r.visible and r.seen == "")
c, r = make(K + ",True,Invert,dir=ltr", Src("Hello"))
check("wide (Invert) variant hidden while posters on", not r.visible and r.seen == "")
c, r = make(K + ",True,dir=rtl", Src("مرحبا"))
check("arabic -> rtl variant visible", r.visible and r.seen == "مرحبا")
c, r = make("always,True,dir=ltr", Src("Hi"))
check("'always' direction-only mode", r.visible)
c, r = make(K + ",True,bool", Src("", boolean=False))
check("bool AND: boolean False -> hidden", not r.visible)
c, r = make(K + ",True,bool", Src("", boolean=True))
check("bool AND: boolean True -> visible", r.visible)
c, r = make(K + ",True,text=NEXT", Src(""))
check("text= literal when visible", r.visible and r.seen == "NEXT")
c, r = make(K + ",True,Invert,text=NEXT", Src(""))
check("text= literal hidden variant gets empty text", (not r.visible) and r.seen == "")
c, r = make(K + ",True", Src(value=300))
check("value/range pass through (Progress)", c.value == 300 and c.range == 1000)
c.visible = False  # what 57b7a51 EventInfo(Progress).changed does on its first downstream element
check("upstream sets visible=False -> renderer hidden (crash 21:51 fixed)", c.visible is False and r.visible is False)
c.visible = True
check("upstream sets visible=True -> renderer follows our condition", r.visible is True)
SETTINGS[K] = "False"
c.changed((2,))
check("poster switch off -> narrow variant hidden", r.visible is False)
print("RESULT: %s" % ("all passed" if not FAIL else "%d failed" % FAIL))
sys.exit(1 if FAIL else 0)
