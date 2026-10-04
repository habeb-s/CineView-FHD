#!/usr/bin/env python3
"""Assemble data.json for render_epg.py from real receiver material (runs on ai-agent):
  epgmock_raw.json (OpenWebif epgmulti/epgservice/getservices of the Max TV bouquet, read-only),
  csmock/in picon crops (native list rows), posters from the identity-engine cache on USB (read-only).
usage: mkepgdata.py <raw.json> <csmock/in dir> <outdir>"""
import datetime
import json
import os
import subprocess
import sys
import time
import unicodedata

raw_p, cs_in, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
raw = json.load(open(raw_p))
cs = json.load(open(os.path.join(cs_in, "data.json")))
R = os.path.expanduser("~/cineview-mla/r.sh")
now = raw["t"]

picon_by_name = {}
for r in cs["rows"]:
	if r.get("picon"):
		picon_by_name[r["name"].rstrip(". ")] = os.path.abspath(os.path.join(cs_in, os.path.basename(r["picon"])))

events = {}
for e in raw["multi"].get("events", []):
	events.setdefault(e.get("sref"), []).append(e)

svcs = [s for s in raw["services"] if s.get("pos")]
start = [i for i, s in enumerate(svcs) if s["servicename"].startswith("HBO HD")][0]

cache = subprocess.run([R, "ls /media/usb/cineview-mla/dev-cache/reference/poster/id/"], capture_output=True, text=True).stdout.splitlines()


def poster(title):
	t = title.lower()
	key = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))
	m = [f for f in cache if f.startswith(key + "~") and f.endswith(".jpg")]
	if not m:
		return None
	p = os.path.join(out, "poster_%s.jpg" % t.replace(" ", "_")[:30])
	if not os.path.isfile(p):
		with open(p, "wb") as fh:
			fh.write(subprocess.run([R, "cat '/media/usb/cineview-mla/dev-cache/reference/poster/id/%s'" % m[0]], capture_output=True).stdout)
	return p


def hm(t):
	return datetime.datetime.fromtimestamp(t).strftime("%H:%M")


chans = []
for s in svcs[start:start + 10]:
	name = s["servicename"].rstrip(". ")
	evs = sorted(events.get(s["servicereference"], []), key=lambda e: e["begin_timestamp"])
	chans.append({"num": s["pos"] + 92, "name": name, "picon": picon_by_name.get(name),
		"events": [{"title": e.get("title", ""), "begin": e["begin_timestamp"], "dur": e.get("duration_sec", 0),
			"genre": e.get("genre", ""), "desc": (e.get("longdesc") or e.get("shortdesc") or "").replace("\n", " ")} for e in evs]})

# highlighted cell = the event running now on HBO HD (first channel)
sel = [e for e in chans[0]["events"] if e["begin"] <= now < e["begin"] + e["dur"]][0]
sel = dict(sel, channel=chans[0]["name"], picon=chans[0]["picon"], times="%s – %s" % (hm(sel["begin"]), hm(sel["begin"] + sel["dur"])),
	duration="%d min" % (sel["dur"] // 60), poster=poster(sel["title"]))
for c in chans:
	for e in c["events"]:
		if e["begin"] <= now < e["begin"] + e["dur"]:
			e["poster"] = poster(e["title"])
data = {
	"bouquet": "16,0 E - Max TV",
	"clock": hm(now), "date": datetime.datetime.fromtimestamp(now).strftime("%a %d %b"),
	"now": now, "keys": ["IMDb Search", "Add Timer", "EPG Search", "Add AutoTimer"],
	"channels": chans, "selected": sel,
}
json.dump(data, open(os.path.join(out, "data.json"), "w"), ensure_ascii=False, indent=1)
print("channels", [c["name"] for c in chans], "selected", sel["title"], sel["times"], "poster", sel["poster"],
	"picons", sum(1 for c in chans if c["picon"]))
