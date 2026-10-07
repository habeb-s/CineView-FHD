#!/usr/bin/env python3
"""ImageAdapter (mla/plugin/CineViewMLA/image_adapter.py): image detection from enigma.info, native rows per image,
shutdown hook per image.  OpenATV must give exactly the 1.0.0 rows (labels, card texts, descriptions, order)."""
import importlib.util
import os
import sys
import tempfile
import types

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mla", "plugin", "CineViewMLA", "image_adapter.py")
# the 1.0.0 plugin.py texts (rows 325/326, cards 384/385, descriptions 433/434 of the golden plugin)
V100 = [("show_second_infobar", "Second InfoBar mode", "What the INFO key opens after the InfoBar (OpenATV setting).",
		"Second InfoBar, event information or nothing when INFO is pressed again."),
	("second_infobar_timeout", "Second InfoBar timeout", "How long the Second InfoBar stays on screen (OpenATV setting).",
		"After this time the Second InfoBar closes by itself.")]


def load(info_text):
	spec = importlib.util.spec_from_file_location("ia", SRC)
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	if info_text is None:
		m.ENIGMA_INFO = "/nonexistent/enigma.info"
	else:
		f = tempfile.NamedTemporaryFile("w", delete=False)
		f.write(info_text)
		f.close()
		m.ENIGMA_INFO = f.name
	return m


ok = True


def check(name, cond):
	global ok
	print("%-60s %s" % (name, "PASS" if cond else "FAIL"))
	ok = ok and cond


usage_atv = types.SimpleNamespace(show_second_infobar="A", second_infobar_timeout="B", infobar_timeout="C")
usage_bh = types.SimpleNamespace(show_second_infobar="A", fix_second_infobar="F", infobar_timeout="C")

m = load("checksum=x\ndistro='openatv'\nimageversion='8.0'\n")
rows = m.native_rows(usage_atv)
check("openatv detected", m.image() == "openatv")
check("openatv rows == 1.0.0 rows (keys, labels, cards, descriptions, order)", [(k, l, c, d) for k, cfg, l, c, d in rows] == V100)
check("openatv rows bound to the real config elements", [cfg for k, cfg, l, c, d in rows] == ["A", "B"])
check("openatv shutdown hook = session.onShutdown", m.shutdown_hook() == "session")
check("openatv ChoiceBox items keyword = choiceList (1.0.0 call)", m.choice_list([1]) == {"choiceList": [1]})

m = load("distro='openbh'\nimageversion='5.6'\nimagebuild='008'\n")
rows = m.native_rows(usage_bh)
check("openbh detected", m.image() == "openbh")
check("openbh: one native row show_second_infobar", [k for k, *_ in rows] == ["show_second_infobar"])
check("openbh: no OpenATV-only setting requested", all(k != "second_infobar_timeout" for k, *_ in rows))
check("openbh shutdown hook = WHERE_AUTOSTART reason 1", m.shutdown_hook() == "autostart")
check("openbh ChoiceBox items keyword = list (52dedddc314a signature)", m.choice_list([1]) == {"list": [1]})

m = load("distro='openatv'\n")
check("missing native setting is skipped, never AttributeError", [k for k, *_ in m.native_rows(usage_bh)] == ["show_second_infobar"])

m = load("distro='openvix'\n")
check("unknown image -> default spec, rows filtered by existence", m.image() == "openvix" and len(m.native_rows(usage_bh)) == 1)

m = load(None)
check("no enigma.info -> openatv (1.0.0 behaviour)", m.image() == "openatv")
print("RESULT", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
