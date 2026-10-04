#!/usr/bin/env python3
"""Probe skin for the Modern model's skin features (t41).  Writes the trigger JSON for CineViewMLAFeatureProbe.
Colours are enigma2 #AARRGGBB (AA 00 = opaque, FF = fully transparent).  Syntax from 57b7a51 skin.py:
cornerRadius "r" or "r;edges" (parseRadius), backgroundColor "c1,c2,vertical|horizontal,alphablend" (parseGradient),
borderWidth / borderColor.
usage: probe_modern.py <poster.jpg on the receiver>  > probe.json"""
import json
import sys

poster = sys.argv[1]
F = 'font="Regular;30" foregroundColor="#00f0f0f0" valign="center" halign="center"'
els = [
	# A opaque rounded card + text widget inside
	'<eLabel position="80,80" size="560,300" backgroundColor="#000a1d35" cornerRadius="24" zPosition="-1" />',
	'<widget source="t_a" render="Label" position="100,100" size="520,260" %s transparent="1" zPosition="10" />' % F,
	# B translucent rounded card with border
	'<eLabel position="700,80" size="560,300" backgroundColor="#330a1d35" cornerRadius="24" borderWidth="3" borderColor="#00468cdc" zPosition="-1" />',
	'<widget source="t_b" render="Label" position="720,100" size="520,260" %s transparent="1" zPosition="10" />' % F,
	# C vertical gradient with alpha blending, rounded top only
	'<eLabel position="1320,80" size="520,300" backgroundColor="#000a1d35,#d00a1d35,vertical,1" cornerRadius="24;top" zPosition="-1" />',
	'<widget source="t_c" render="Label" position="1340,100" size="480,260" %s transparent="1" zPosition="10" />' % F,
	# pills: eLabel + transparent text, and a Label widget with its own background + radius
	'<eLabel position="80,440" size="200,52" backgroundColor="#00344660" cornerRadius="26" zPosition="-1" />',
	'<widget source="t_p1" render="Label" position="80,440" size="200,52" font="Regular;24" foregroundColor="#00f0f0f0" halign="center" valign="center" transparent="1" zPosition="10" />',
	'<widget source="t_p2" render="Label" position="300,440" size="240,52" font="Regular;24" foregroundColor="#00f0f0f0" backgroundColor="#00344660" cornerRadius="26" halign="center" valign="center" zPosition="10" />',
	# rounded poster pixmap
	'<ePixmap position="80,540" size="200,300" pixmap="%s" scale="1" cornerRadius="16" alphatest="blend" zPosition="5" />' % poster,
	# bottom scrim gradient: transparent -> dark, text on it
	'<eLabel position="0,700" size="1920,380" backgroundColor="#ff000000,#30000000,vertical,1" zPosition="-1" />',
	'<widget source="t_s" render="Label" position="340,960" size="1500,60" font="Regular;40" foregroundColor="#00f0f0f0" transparent="1" zPosition="10" />',
]
skin = '<screen name="CineViewMLAFeatureProbe" position="0,0" size="1920,1080" flags="wfNoBorder" backgroundColor="transparent">\n%s\n</screen>' % "\n".join(els)
texts = {"t_a": "A opaque, cornerRadius 24", "t_b": "B 80 % + border 3, radius 24", "t_c": "C gradient alpha, radius top",
	"t_p1": "HD  16:9", "t_p2": "Label pill r26", "t_s": "Scrim gradient: transparent to dark (alphablend)"}
print(json.dumps({"skin": skin, "seconds": 40, "texts": texts}))
