#!/usr/bin/env python3
"""CineViewCPUTemp (classic 2.3.5) against simulated receivers.

Every sensor layout is a temporary root; /sys and /proc paths are redirected into it.  With --compare OLD.py ...
the 2.3.4 converters are run on the same layouts, to show what changes (only receivers that showed nothing)."""
import builtins, glob as _glob, os, sys, tempfile, types

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "components", "Converter", "CineViewCPUTemp.py")

# minimal Enigma2 stubs (the device test runs against the image's real modules instead)
for name in ("Components", "Components.Converter", "Components.Converter.Converter", "Components.Converter.Poll",
             "Components.Element", "Components.Converter.CineViewHardware"):
	sys.modules[name] = types.ModuleType(name)
class Converter(object):
	def __init__(self, t): pass
class Poll(object):
	def __init__(self): pass
sys.modules["Components.Converter.Converter"].Converter = Converter
sys.modules["Components.Converter.Poll"].Poll = Poll
sys.modules["Components.Element"].cached = lambda f: f

SF8008 = ("CPU: freq = 1600000(kHz), current volt = 1190(mv) \nCPU: AVS = On, hpm offset = 0 hpm target = 0x153 \n"
          "Tsensor: temperature = 45 degree \nCPU: Temp Control is Quit \n")


def run(src, files, meta=""):
	root = tempfile.mkdtemp()
	for p, content in files.items():
		full = root + p; os.makedirs(os.path.dirname(full), exist_ok=True); open(full, "w").write(content)
	ns = {"__name__": "cputemp"}
	real_exists, real_isfile, real_open, real_glob = os.path.exists, os.path.isfile, builtins.open, _glob.glob
	R = lambda p: root + p if str(p).startswith(("/sys/", "/proc/")) else p
	os.path.exists = lambda p: real_exists(R(p))
	os.path.isfile = lambda p: real_isfile(R(p))
	builtins.open = lambda p, *a, **k: real_open(R(p), *a, **k)
	_glob.glob = lambda pat: [g[len(root):] for g in real_glob(R(pat))]
	try:
		hw = os.path.join(os.path.dirname(src), "CineViewHardware.py")  # 2.3.4 OpenViX package helper
		if os.path.basename(src) != "CineViewCPUTemp.py" or real_exists(hw):
			mod = sys.modules["Components.Converter.CineViewHardware"]
			if real_exists(hw):
				exec(compile(real_open(hw).read(), hw, "exec"), mod.__dict__)
		exec(compile(real_open(src).read(), src, "exec"), ns)
		c = ns["CineViewCPUTemp"]("Short")
		out = c.getText()
		if meta == "change":  # value changes before the next poll -> the label follows
			for p in files:
				if p.startswith("/proc/hisi"):
					real_open(root + p, "w").write("Tsensor: temperature = 53 degree \n")
			out += " -> next poll: " + c.getText()
		elif meta == "switch":  # the source that answered disappears -> re-probe the others
			for p in files:
				if p.startswith("/proc/stb"):
					os.remove(root + p)
			out += " -> source gone: " + c.getText()
	except Exception as e:  # an old converter may not even load outside its image
		out = "ERROR %s" % type(e).__name__
	finally:
		os.path.exists, os.path.isfile, builtins.open, _glob.glob = real_exists, real_isfile, real_open, real_glob
	return out


cases = [
	({"/proc/hisi/msp/pm_cpu": SF8008}, "", "Octagon SF8008 real pm_cpu (4 lines)", "CPU: 45°C"),
	({"/proc/hisi/msp/pm_cpu": "Tsensor: temperature = 48 degree \n"}, "change", "HiSilicon: value updates on next poll", "CPU: 48°C -> next poll: CPU: 53°C"),
	({"/proc/hisi/msp/pm_temp": "Temperature control is On\nTsensor: temperature = 51 degree\n"}, "", "HiSilicon variant: pm_temp only", "CPU: 51°C"),
	({"/proc/stb/fp/temp_sensor": "44\n"}, "", "Vu+ style /proc/stb/fp/temp_sensor", "CPU: 44°C"),
	({"/sys/class/thermal/thermal_zone0/temp": "51608\n"}, "", "thermal_zone0 millidegrees (Vu+ 4K)", "CPU: 52°C"),
	({"/proc/stb/sensors/temp0/value": "47", "/proc/stb/sensors/temp0/unit": "C"}, "", "sensors/temp0 Celsius", "CPU: 47°C"),
	({"/proc/stb/sensors/temp0/value": "122", "/proc/stb/sensors/temp0/unit": "F"}, "", "sensors/temp0 Fahrenheit -> Celsius", "CPU: 50°C"),
	({"/sys/class/thermal/thermal_zone1/temp": "61000", "/sys/class/thermal/thermal_zone1/type": "cpu-thermal"}, "", "only thermal_zone1 (cpu)", "CPU: 61°C"),
	({"/proc/stb/fp/temp_sensor_avs": "39"}, "", "temp_sensor_avs only", "CPU: 39°C"),
	({"/proc/stb/fp/temp_sensor": "41", "/proc/hisi/msp/pm_cpu": "Tsensor: temperature = 46 degree"}, "switch", "answering source disappears", "CPU: 41°C -> source gone: CPU: 46°C"),
	({"/proc/stb/fp/temp_sensor": "0\n"}, "", "sensor reports 0 -> not a reading", "CPU: N/A"),
	({"/proc/stb/fp/temp_sensor": "0\n", "/proc/hisi/msp/pm_cpu": "Tsensor: temperature = 46 degree"}, "", "0 on one sensor, valid on another", "CPU: 46°C"),
	({"/proc/hisi/msp/pm_cpu": "garbage without a number"}, "", "unreadable content", "CPU: N/A"),
	({"/proc/hisi/msp/pm_cpu": "Tsensor: temperature = 255 degree"}, "", "implausible 255 -> rejected", "CPU: N/A"),
	({}, "", "no sensor at all", "CPU: N/A"),
]

olds = sys.argv[sys.argv.index("--compare") + 1:] if "--compare" in sys.argv else []
npass = 0
for files, meta, label, expect in cases:
	got = run(SRC, files, meta)
	ok = got == expect
	npass += ok
	line = "%s  %-40s %-34s" % ("PASS" if ok else "FAIL", label, got)
	for old in olds:
		line += " | %s: %s" % (os.path.basename(os.path.dirname(old)) or old, run(old, files, meta))
	print(line)
print("RESULT pass=%d fail=%d" % (npass, len(cases) - npass))
sys.exit(0 if npass == len(cases) else 1)
