#!/usr/bin/env python3
"""ISS-01 fix for the stable CineViewControl (OpenATV) — apply to plugin.py.

Root cause (proven on OpenATV 8.0.1 Slot 8, see docs/mla/ISS-01_ISS-02_evidence.md):
  apply_timeout() writes the Second-InfoBar *timeout* (seconds) into
  config.usage.show_second_infobar, which is the Second-InfoBar *mode* (0..3).
  ConfigSelection.setValue() replaces an unknown value by the default "1" (Event Info),
  so after every boot INFO/OK opens EventView instead of the CineView SecondInfoBar
  ("0" switches the Second InfoBar off).

Fix: write the timeout to the native timeout setting config.usage.second_infobar_timeout
(choices "0".."20" on OpenATV 8.0.1) and never touch the mode setting.

usage: ISS-01_apply_timeout.py <plugin.py>   (rewrites the file in place, keeps a .orig copy)
"""
import re
import shutil
import sys

FIXED = '''def apply_timeout(save=False):
    # ISS-01 fix: the timeout belongs to config.usage.second_infobar_timeout; the MODE
    # (config.usage.show_second_infobar) is the user's own choice and is never touched.
    try:
        if hasattr(config, 'usage') and hasattr(config.usage, 'second_infobar_timeout'):
            target = config.usage.second_infobar_timeout
            value = str(config.plugins.cineview.secondtimeout.value)
            valid = [str(c[0]) if isinstance(c, (tuple, list)) else str(c) for c in target.choices]
            if value not in valid:
                numeric = sorted(int(v) for v in valid if v.isdigit() and int(v) > 0)
                value = str(numeric[-1]) if numeric and value.isdigit() and int(value) > numeric[-1] else target.default
            target.value = value
            if save:
                target.save()
    except Exception:
        pass
'''


def main(path):
	src = open(path, encoding="utf-8").read()
	pat = re.compile(r"def apply_timeout\(save=False\):\n(?:    .*\n|\n)*?(?=\ndef |\nclass )")
	if src.count("def apply_timeout(") != 1 or not pat.search(src):
		raise SystemExit("apply_timeout() not found exactly once — refusing to patch")
	shutil.copy2(path, path + ".orig")
	open(path, "w", encoding="utf-8").write(pat.sub(FIXED, src, count=1))
	print("patched", path)


if __name__ == "__main__":
	main(sys.argv[1])
