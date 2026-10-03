#!/usr/bin/env python3
"""Offline test of the T6 watchdog patched into CineViewMLABitrate (built tree).

usage: test_bitrate_watchdog.py <build root>
Stubs the Enigma2 modules the converter imports, then drives _BitrateSetupEngine with a fake
navigation/service and a fake eConsoleAppContainer, feeding `bitrate` output lines.
"""
import importlib.util
import os
import sys
import time
import types


class FakeContainer:
	def __init__(self):
		self.appClosed, self.dataAvail = [], []
		self.started, self.killed = [], 0

	def execute(self, cmd):
		self.started.append(cmd)
		return 0

	def kill(self):
		self.killed += 1


def stub_modules():
	enigma = types.ModuleType("enigma")
	enigma.eConsoleAppContainer = FakeContainer
	enigma.iServiceInformation = types.SimpleNamespace(sVideoPID=1, sAudioPID=2)
	sys.modules["enigma"] = enigma
	for name in ("Components", "Components.Converter"):
		sys.modules[name] = types.ModuleType(name)
	conv = types.ModuleType("Components.Converter.Converter")
	conv.Converter = type("Converter", (), {"__init__": lambda self, t: None, "changed": lambda self, w: None})
	sys.modules["Components.Converter.Converter"] = conv
	poll = types.ModuleType("Components.Converter.Poll")
	poll.Poll = type("Poll", (), {"__init__": lambda self: None})
	sys.modules["Components.Converter.Poll"] = poll
	el = types.ModuleType("Components.Element")
	el.cached = lambda f: f
	sys.modules["Components.Element"] = el
	nav = types.ModuleType("NavigationInstance")
	sys.modules["NavigationInstance"] = nav
	return nav


class Ref:
	def __init__(self, s):
		self.s = s

	def toString(self):
		return self.s


class Service:
	def __init__(self, vpid, apid):
		self.vpid, self.apid = vpid, apid

	def stream(self):
		return None

	def info(self):
		return types.SimpleNamespace(getInfo=lambda k: self.vpid if k == 1 else self.apid)


def main(build):
	nav = stub_modules()
	path = os.path.join(build, "usr/lib/enigma2/python/Components/Converter/CineViewMLABitrate.py")
	spec = importlib.util.spec_from_file_location("cvb", path)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	eng = mod._ENGINE
	clock = [1000.0]
	mod.time.time = lambda: clock[0]
	res = []

	def check(name, ok):
		res.append(ok)
		print(("PASS " if ok else "FAIL ") + name)

	def set_service(ref, vpid, apid):
		nav.instance = types.SimpleNamespace(getCurrentService=lambda: Service(vpid, apid), getCurrentlyPlayingServiceReference=lambda: Ref(ref))

	def feed(v, a, n):
		for _ in range(n):
			eng._data(("%d %d %d %d\n%d %d %d %d\n" % (v, v, v, v, a, a, a, a)).encode())
			clock[0] += 1
			eng.ensure()

	set_service("svc:A", 2838, 2614)
	eng.ensure()
	check("reader started for a video service", len(eng.container.started) == 1 and eng.container.started[-1].endswith("2838 2614"))
	feed(0, 126, 3)
	check("no restart before 5 zero-video samples", eng.container.killed == 0)
	feed(0, 126, 4)
	check("stuck reader (video 0, audio ok) is killed by the watchdog", eng.container.killed == 1)
	eng.ensure()
	check("no new reader within 1 s of the kill", len(eng.container.started) == 1)
	clock[0] += 1.1
	eng.ensure()
	check("fresh reader started after 1 s", len(eng.container.started) == 2)
	feed(4500, 126, 3)
	check("healthy reader: values parsed (4.63 Mbps)", eng.vcur == 4500 and eng.acur == 126 and eng.container.killed == 1)
	feed(0, 126, 3)
	check("short zero-video burst (<5 samples): no restart", eng.container.killed == 1)
	set_service("radio:B", 0, 2614)
	eng.ensure()
	clock[0] += 1.1
	eng.ensure()
	before = eng.container.killed
	feed(0, 126, 12)
	check("radio service (no video PID): never restarted", eng.container.killed == before)
	set_service("svc:C", 2001, 2002)
	k0, s0 = eng.container.killed, len(eng.container.started)
	eng.ensure()
	check("service change kills old reader and waits before starting the new one", eng.container.killed == k0 + 1 and len(eng.container.started) == s0)
	clock[0] += 1.1
	eng.ensure()
	check("new service reader started after the wait", len(eng.container.started) == s0 + 1 and eng.container.started[-1].endswith("2001 2002"))
	print("%d/%d" % (sum(res), len(res)))
	return 0 if all(res) else 1


if __name__ == "__main__":
	sys.exit(main(sys.argv[1]))
