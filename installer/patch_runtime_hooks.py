#!/usr/bin/env python3
from __future__ import print_function

import io
import os
import sys


def read(path):
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def write(path, data):
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(data)


def patch_activate(path):
    s = read(path)
    old = '"$PY" "$PLUGIN/openatv_v5.py" "$SKIN/skin.xml" >/dev/null 2>&1 || true'
    new = r'''IMGLOW=$(cat /etc/image-version /etc/issue /etc/os-release 2>/dev/null | tr 'A-Z' 'a-z' | tr '\\n' ' ')
case "$IMGLOW" in
  *openatv*) "$PY" "$PLUGIN/openatv_compat.py" "$SKIN" >/dev/null 2>&1 || true ;;
  *openbh*|*openblackhole*) "$PY" "$PLUGIN/openbh_compat.py" "$SKIN" >/dev/null 2>&1 || true ;;
  *) "$PY" "$PLUGIN/openatv_v5.py" "$SKIN/skin.xml" >/dev/null 2>&1 || true ;;
esac'''
    if old in s:
        s = s.replace(old, new, 1)
    elif 'openatv_compat.py" "$SKIN"' not in s:
        raise RuntimeError("activate.sh compatibility hook not found")
    write(path, s)


def patch_plugin(path):
    s = read(path)
    old = "            shutil.copy2(src,ACTIVE); apply_theme(SKIN_DIR,config.plugins.cineview.theme.value); apply_time_format(True)\n"
    new = old + """            try:
                image_info=open('/etc/image-version','r').read().lower()
            except Exception:
                image_info=''
            try:
                if 'openatv' in image_info:
                    from . import openatv_compat
                    if not openatv_compat.patch_file(ACTIVE):
                        raise RuntimeError('OpenATV skin adaptation failed')
                elif 'openbh' in image_info or 'openblackhole' in image_info:
                    from . import openbh_compat
                    openbh_compat.main(SKIN_DIR)
            except Exception as e:
                raise RuntimeError('CineView image compatibility failed: %s' % e)
"""
    if old in s and "OpenATV skin adaptation failed" not in s:
        s = s.replace(old, new, 1)
    elif "OpenATV skin adaptation failed" not in s:
        raise RuntimeError("plugin.py save hook not found")
    write(path, s)


def main(plugin_dir):
    activate = os.path.join(plugin_dir, "activate.sh")
    plugin = os.path.join(plugin_dir, "plugin.py")
    if not os.path.isfile(activate) or not os.path.isfile(plugin):
        raise RuntimeError("CineViewControl runtime files missing")
    patch_activate(activate)
    patch_plugin(plugin)
    print("CINEVIEW_RUNTIME_HOOKS_OK")


if __name__ == "__main__":
    main(sys.argv[1])
