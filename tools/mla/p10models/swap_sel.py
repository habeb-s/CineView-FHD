#!/usr/bin/env python3
"""Make a model-mockup data set whose selected channel matches a real video frame (2026-10-04 night: the HBO grabs
were corrupted, so the first mockups paired HBO data with a Cinemax frame).  Replaces data["sel"], the selected
list row and data["video"] with the given channel's OpenWebif now/next JSON, its picon and tuner values read from
the receiver's own InfoBar at the same time.  The poster is set only when the identity engine resolved one (path
argument); otherwise the mockup shows the placeholder, exactly like the receiver.
usage: swap_sel.py data.json now.json next.json picon.png video.png num name tech live_tech chips(|-separated) [poster] > out.json"""
import json
import os
import sys
import time

os.environ["TZ"] = "Asia/Riyadh"
time.tzset()
data_p, now_p, next_p, picon, video, num, name, tech, live, chips = sys.argv[1:11]
poster = sys.argv[11] if len(sys.argv) > 11 else None
D = json.load(open(data_p, encoding="utf-8"))
ev = lambda p: json.load(open(p, encoding="utf-8"))["events"][0]
n, x = ev(now_p), ev(next_p)
hm = lambda t: time.strftime("%H:%M", time.localtime(t))
t_grab = os.path.getmtime(video)
nb, ne = n["begin_timestamp"], n["begin_timestamp"] + n["duration_sec"]
clean = lambda s: (s or "").replace(" ", " ").strip()
now = {"title": clean(n["title"]), "times": "%s – %s  ·  %d min" % (hm(nb), hm(ne), n["duration_sec"] // 60), "times_short": "%s – %s" % (hm(nb), hm(ne)),
	"progress": max(0.0, min(1.0, (t_grab - nb) / float(n["duration_sec"]))), "genre": clean(n.get("genre")) or None, "rating": None,
	"desc": clean(n.get("longdesc")) or clean(n.get("shortdesc")), "poster": poster}
xb = x["begin_timestamp"]
nxt = {"title": clean(x["title"]), "start": hm(xb), "times": "%s – %s" % (hm(xb), hm(xb + x["duration_sec"])),
	"desc": clean(x.get("longdesc")) or clean(x.get("shortdesc")), "poster": None}
D["sel"] = {"num": int(num), "name": name, "picon": picon, "tech": tech, "live_tech": live, "chips": chips.split("|"), "now": now, "next": nxt}
row = D["rows"][D["selected"]]
row.update({"num": int(num), "name": name, "picon": picon, "event": now["title"], "progress": now["progress"]})
D["video"] = video
D["clock"] = hm(t_grab)
print(json.dumps(D, ensure_ascii=False, indent=1))
