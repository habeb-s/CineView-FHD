#!/usr/bin/env python3
# Phase B static gate: Posters ON in the new build must show exactly the elements of the old build
# (same position/size multiset per screen); report the OFF elements and that every file parses.
import sys, collections, xml.etree.ElementTree as ET
old, new = sys.argv[1], sys.argv[2]
ok = True
for sec in ("infobar", "secondinfobar", "eventview", "channelselection", "epg"):
    f = "usr/share/enigma2/CineView_FHD_MLA/layouts/%s/classic/screens.openatv.xml" % sec
    a, b = ET.parse(old + "/" + f).getroot(), ET.parse(new + "/" + f).getroot()
    key = "config.plugins.cineviewmla.poster_%s" % sec
    sa = {s.get("name"): s for s in a.iter("screen")}
    for s in b.iter("screen"):
        n = s.get("name")
        def geo(e):
            return (e.get("position"), e.get("size"))
        on, off = collections.Counter(), []
        for e in s:
            show = [c.text for c in e.findall("convert") if c.get("type") == "CineViewMLAShowIf" and (c.text or "").startswith(key)]
            if show and ",Invert" in show[0]:
                off.append(geo(e))
            else:
                on[geo(e)] += 1
        ref = collections.Counter(geo(e) for e in sa[n] if not any(c.get("type") == "CineViewMLAShowIf" and (c.text or "").startswith(key) and ",Invert" in c.text for c in e.findall("convert")))
        if on != ref:
            ok = False
            print("MISMATCH", sec, n, "missing:", dict(ref - on), "extra:", dict(on - ref))
        elif off:
            print("ok %-16s %-22s ON == old (%d elements), OFF variants %d" % (sec, n, sum(on.values()), len(off)))
print("POFF_STATIC", "PASS" if ok else "FAIL")
