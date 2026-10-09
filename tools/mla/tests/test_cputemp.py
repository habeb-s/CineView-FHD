#!/usr/bin/env python3
"""cputemp.py against simulated receivers: every sensor layout is a temporary root; paths are redirected into it."""
import builtins, glob as _glob, os, sys, tempfile, types
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "patches", "cputemp.py")
# minimal Enigma2 stubs
for name in ("Components", "Components.Converter", "Components.Converter.Converter", "Components.Converter.Poll", "Components.Element"):
	sys.modules[name] = types.ModuleType(name)
class Converter(object):
	def __init__(self, t): pass
class Poll(object):
	def __init__(self): pass
sys.modules["Components.Converter.Converter"].Converter = Converter
sys.modules["Components.Converter.Poll"].Poll = Poll
sys.modules["Components.Element"].cached = lambda f: f

def run(files, label, expect):
	root = tempfile.mkdtemp()
	for p, content in files.items():
		full = root + p; os.makedirs(os.path.dirname(full), exist_ok=True); open(full, "w").write(content)
	ns = {"__name__": "cputemp"}
	code = open(SRC).read()
	real_exists, real_open, real_glob = os.path.exists, builtins.open, _glob.glob
	R = lambda p: root + p if p.startswith(("/sys/", "/proc/")) else p
	os.path.exists = lambda p: real_exists(R(p))
	builtins.open = lambda p, *a, **k: real_open(R(p), *a, **k)
	_glob.glob = lambda pat: [g[len(root):] for g in real_glob(R(pat))]
	try:
		exec(compile(code, SRC, "exec"), ns)
		c = ns["CineViewMLACPUTemp"]("Short")
		got = c.getText()
		extra = ""
		if "change" in files.get("__meta__", ""):  # value changes on the next poll -> the label follows
			for p in list(files):
				if p.startswith("/proc/hisi"):
					real_open(root + p, "w").write("Tsensor: temperature = 53 degree \n")
			extra = " -> next poll: " + c.getText()
	finally:
		os.path.exists, builtins.open, _glob.glob = real_exists, real_open, real_glob
	full = got + extra
	ok = full == expect
	print("%s  %-46s %s" % ("PASS" if ok else "FAIL", label, full))
	return ok

cases = [
	({"/proc/hisi/msp/pm_cpu": "Tsensor: temperature = 48 degree \nCPU: Temp Control is Quit \n"}, "Octagon SF8008 / HiSilicon pm_cpu", "CPU: 48°C"),
	({"/proc/hisi/msp/pm_cpu": "Tsensor: temperature = 48 degree \n", "__meta__": "change"}, "HiSilicon: value updates on next poll", "CPU: 48°C -> next poll: CPU: 53°C"),
	({"/proc/hisi/msp/pm_temp": "Temperature control is On\nTsensor: temperature = 51 degree\n"}, "HiSilicon variant: pm_temp only", "CPU: 51°C"),
	({"/proc/stb/fp/temp_sensor": "44\n"}, "Vu+ style /proc/stb/fp/temp_sensor (unchanged)", "CPU: 44°C"),
	({"/sys/class/thermal/thermal_zone0/temp": "52300\n"}, "thermal_zone0 millidegrees (unchanged)", "CPU: 52°C"),
	({"/proc/stb/sensors/temp0/value": "47", "/proc/stb/sensors/temp0/unit": "C"}, "sensors/temp0 Celsius (unchanged)", "CPU: 47°C"),
	({"/proc/stb/sensors/temp0/value": "122", "/proc/stb/sensors/temp0/unit": "F"}, "sensors/temp0 Fahrenheit -> Celsius", "CPU: 50°C"),
	({"/sys/class/thermal/thermal_zone1/temp": "61000", "/sys/class/thermal/thermal_zone1/type": "cpu-thermal"}, "only thermal_zone1 (cpu)", "CPU: 61°C"),
	({"/proc/stb/fp/temp_sensor_avs": "39"}, "temp_sensor_avs", "CPU: 39°C"),
	({"/proc/stb/fp/temp_sensor": "0\n"}, "sensor reports 0 -> not a reading", "CPU: N/A"),
	({"/proc/stb/fp/temp_sensor": "0\n", "/proc/hisi/msp/pm_cpu": "Tsensor: temperature = 46 degree"}, "0 on one sensor, valid on another", "CPU: 46°C"),
	({"/proc/hisi/msp/pm_cpu": "garbage without a number"}, "unreadable content", "CPU: N/A"),
	({"/proc/hisi/msp/pm_cpu": "Tsensor: temperature = 255 degree"}, "implausible 255 -> rejected", "CPU: N/A"),
	({}, "no sensor at all", "CPU: N/A"),
]
res = [run(f, l, e) for f, l, e in cases]
print("RESULT pass=%d fail=%d" % (sum(res), len(res) - sum(res)))
