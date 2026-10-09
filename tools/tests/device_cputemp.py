#!/usr/bin/env python3
"""Run CineViewCPUTemp on a real receiver without installing it and without touching the running GUI or skin.

The converter is loaded from this directory against the image's own Components.Element / Converter / Poll and
Tools.CList.  Only enigma.eTimer is replaced (it exists only inside the enigma2 binary): the test fires the poll
timer itself every <interval> seconds, exactly as eTimer would.  A renderer-like downstream element pulls `text`
on every change, as the Label renderer does, and each value is compared with an independent read of the sensor.

usage: python3 device_cputemp.py <seconds> [load_from load_to]   (optional low-priority 1-core load window)"""
import os, re, subprocess, sys, time, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/usr/lib/enigma2/python")


class FakeTimer(object):
	instances = []

	def __init__(self):
		self.callback = []
		self.interval = None
		self.active = False
		FakeTimer.instances.append(self)

	def start(self, ms, single=False):
		self.interval, self.active = ms, True

	def stop(self):
		self.active = False


sys.modules["enigma"] = types.ModuleType("enigma")
sys.modules["enigma"].eTimer = FakeTimer

import Components.Element as E  # the image's real modules
import Components.Converter.Poll as P
import Components.Converter.Converter as C
import importlib.util

spec = importlib.util.spec_from_file_location("CineViewCPUTemp", os.path.join(HERE, "CineViewCPUTemp.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def independent():
	"""Sensor read without the converter: first source that exists, parsed by its own rule."""
	for p in ("/sys/class/thermal/thermal_zone0/temp", "/proc/stb/sensors/temp0/value", "/proc/stb/fp/temp_sensor"):
		if os.path.exists(p):
			v = float(open(p).read().split()[0])
			return p, int(round(v / 1000.0 if v > 1000 else v))
	if os.path.exists("/proc/hisi/msp/pm_cpu"):
		m = re.search(r"Tsensor: temperature = (\d+)", open("/proc/hisi/msp/pm_cpu").read())
		return "/proc/hisi/msp/pm_cpu", int(m.group(1)) if m else None
	return None, None


class Renderer(object):  # minimal downstream: pulls the text while the converter's cache is active
	def __init__(self, conv):
		self.conv, self.seen = conv, []

	def changed(self, what):
		self.seen.append((what[0], self.conv.text))


print("python", sys.version.split()[0], "| Element", E.__file__, "| Poll", P.__file__)
conv = mod.CineViewCPUTemp("Short")
assert isinstance(conv, P.Poll) and isinstance(conv, C.Converter)
r = Renderer(conv)
conv.connectDownstream(r)
timer = [t for t in FakeTimer.instances if conv.poll in t.callback][0]
conv.suspended = False  # what the screen does when the label is shown -> doSuspend(0) -> poll + timer start
print("on show: poll timer active=%s interval=%s ms; first text=%r" % (timer.active, timer.interval, r.seen[-1][1]))

dur = int(sys.argv[1]) if len(sys.argv) > 1 else 60
load = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else None
step = timer.interval / 1000.0
t0, ok, bad, values, burner = time.time(), 0, 0, [], None
while time.time() - t0 < dur:
	el = time.time() - t0
	if load and burner is None and el >= load[0]:
		burner = subprocess.Popen(["nice", "-n", "19", "sh", "-c", "while :; do :; done"])
	if burner and burner.poll() is None and el >= load[1]:
		burner.kill(); burner.wait()
	for cb in list(timer.callback):  # eTimer fires
		cb()
	what, text = r.seen[-1]
	src, ref = independent()
	m = re.match(r"CPU: (\d+)°C$", text)
	match = m is not None and ref is not None and abs(int(m.group(1)) - ref) <= 1
	ok += match; bad += not match
	values.append(text)
	print("t=%5.1fs poll(what=%d) label=%-10s sensor=%s (%s)%s %s" % (el, what, text, ref, src, " load" if burner and burner.poll() is None else "", "OK" if match else "MISMATCH"))
	time.sleep(step)
if burner and burner.poll() is None:
	burner.kill(); burner.wait()
conv.suspended = True  # label hidden -> timer stops
print("on hide: poll timer active=%s" % timer.active)
print("source used by converter:", conv._source[1] if conv._source else None)
print("distinct labels:", sorted(set(values)))
print("RESULT samples=%d match=%d mismatch=%d" % (ok + bad, ok, bad))
sys.exit(0 if bad == 0 and not timer.active else 1)
