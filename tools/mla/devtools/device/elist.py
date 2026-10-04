#!/usr/bin/env python3
# compact element list of a screen: elist.py <screens.xml> <screen name> [ymin ymax]
import sys, xml.etree.ElementTree as ET
f, name = sys.argv[1], sys.argv[2]
ymin, ymax = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (-1, 99999)
r = ET.parse(f).getroot()
for s in r.iter("screen"):
    if s.get("name") != name:
        continue
    print("SCREEN", name, s.get("position"), s.get("size"), "children=%d" % len(s))
    for i, e in enumerate(s):
        p = e.get("position") or ""
        try:
            y = int(p.split(",")[1])
        except Exception:
            y = -1
        if not (ymin <= y <= ymax) and p:
            continue
        conv = "|".join((c.get("type") or "") + ":" + (c.text or "").strip()[:40] for c in e.findall("convert"))
        a = {k: v for k, v in e.attrib.items() if k in ("name", "source", "render", "pixmap", "text", "zPosition", "backgroundColor", "toggle", "halign", "font")}
        print("%3d %-7s pos=%-10s size=%-9s %s %s" % (i, e.tag, p, e.get("size") or "", " ".join("%s=%s" % kv for kv in a.items())[:150], conv[:110]))
