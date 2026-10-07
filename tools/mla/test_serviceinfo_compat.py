#!/usr/bin/env python3
"""CineViewMLAServiceInfo against both native ServiceInfo naming conventions (stubbed bases):
OpenATV 57b7a51: self.token, self.interestingEvents      OpenBH 5.6 / 6.0 (ViX family): self.type, self.interesting_events
The converter must extend the native event filter of whichever base it runs on, and behave exactly as before on OpenATV."""
import importlib.util
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "mla", "components", "Converter", "CineViewMLAServiceInfo.py")


class Ev:
	evStart, evUpdatedInfo, evVideoSizeChanged, evVideoFramerateChanged, evVideoProgressiveChanged, evVideoGammaChanged = range(6)


NATIVE = (Ev.evVideoSizeChanged,)


def base_openatv():
	class ServiceInfo:
		CHANGED_ALL, CHANGED_SPECIFIC = 1, 2

		def __init__(self, argument):
			self.token, self.interestingEvents = argument, NATIVE

		def changed(self, what):
			pass
	return ServiceInfo


def base_openbh():
	class ServiceInfo:
		CHANGED_ALL, CHANGED_SPECIFIC = 1, 2

		def __init__(self, type):
			self.type, self.interesting_events = type, NATIVE

		def changed(self, what):
			pass
	return ServiceInfo


def load(base):
	sys.modules["enigma"] = types.SimpleNamespace(eTimer=object, iPlayableService=Ev)
	sys.modules["Components"] = types.ModuleType("Components")
	sys.modules["Components.Converter"] = types.ModuleType("Components.Converter")
	sys.modules["Components.Converter.ServiceInfo"] = types.SimpleNamespace(ServiceInfo=base)
	spec = importlib.util.spec_from_file_location("cvsi", SRC)
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	return m


ok = True
for image, base, attr in (("openatv", base_openatv(), "interestingEvents"), ("openbh", base_openbh(), "interesting_events")):
	m = load(base)
	video = m.CineViewMLAServiceInfo("Is4K")
	other = m.CineViewMLAServiceInfo("HasTelext")
	got = set(getattr(video, attr))
	want = set(NATIVE) | set(m.EXTRA_EVENTS)
	r1 = got == want
	r2 = getattr(other, attr) == NATIVE  # non-video tokens untouched
	r3 = not hasattr(video, "interesting_events" if attr == "interestingEvents" else "interestingEvents")  # no foreign name
	print("%-8s video filter extended: %s | other tokens untouched: %s | no foreign attribute: %s" % (image, r1, r2, r3))
	ok = ok and r1 and r2 and r3
	if image == "openatv":  # identical to the 1.0.0 expression
		ref = tuple(set(tuple(NATIVE or ()) + m.EXTRA_EVENTS))
		print("openatv  identical to 1.0.0 expression: %s" % (getattr(video, attr) == ref))
		ok = ok and getattr(video, attr) == ref
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
