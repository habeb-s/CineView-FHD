#!/usr/bin/env python3
# Assemble data.json for render_cs.py from real receiver material:
#   /tmp/csraw.json (OpenWebif epgnow/epgnext/services of the Max TV bouquet), shots/poff/on_channels.png
#   (native list rows -> picon crops), on_infobar.png (big HBO picon), video_hbo.png, posters from the
#   identity-engine cache on USB.  usage: mkcsdata.py <outdir>
import json, os, sys, time, datetime, subprocess
from PIL import Image
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
S = os.path.expanduser("~/cineview-mla/shots/poff")
raw = json.load(open("/tmp/csraw.json"))
OFF = 92  # displayed number = bouquet pos + 92 (146 HBO HD on the receiver)
now = {e["sref"]: e for e in raw["now"]}
nxt = {e["sref"]: e for e in raw["next"]}
svcs = raw["services"]
i0 = [k for k, s in enumerate(svcs) if s["servicename"].startswith("24 Kitchen")][0]
grab = Image.open(os.path.join(S, "on_channels.png")).convert("RGBA")
rows = []
for gi, s in enumerate(svcs[i0:i0 + 17]):
    top = 118 + 43 * gi
    r = {"num": "" if s["pos"] == 0 else s["pos"] + OFF, "name": s["servicename"].rstrip("."), "marker": s["pos"] == 0}
    if not r["marker"]:
        c = grab.crop((156, top + 4, 236, top + 39))
        p = os.path.join(out, "picon_%d.png" % r["num"]); c.save(p); r["picon"] = p
        e = now.get(s["servicereference"])
        if e and e.get("title"):
            r["event"] = e["title"]
            if e.get("duration_sec"):
                r["progress"] = max(0, min(1, (time.time() - e["begin_timestamp"]) / e["duration_sec"]))
    rows.append(r)
sel = [k for k, r in enumerate(rows) if str(r["name"]).startswith("HBO HD")][0]
hbo = [s for s in svcs if s["servicename"].startswith("HBO HD")][0]["servicereference"]
n, x = now[hbo], nxt[hbo]
def hm(t): return datetime.datetime.fromtimestamp(t).strftime("%H:%M")
big = Image.open(os.path.join(S, "on_infobar.png")).convert("RGBA").crop((170, 858, 430, 928)); big.save(os.path.join(out, "picon_big.png"))
Image.open(os.path.join(S, "video_hbo.png")).convert("RGB").save(os.path.join(out, "video.png"))
def poster(title):
    t = title.lower()
    r = subprocess.run(["/home/aiadmin/cineview-mla/r.sh", "ls /media/usb/cineview-mla/dev-cache/reference/poster/id/"], capture_output=True, text=True).stdout.splitlines()
    import unicodedata; key = "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)); m = [f for f in r if f.startswith(key + "~") and f.endswith(".jpg")]
    if not m: return None
    p = os.path.join(out, "poster_%s.jpg" % t.replace(" ", "_")[:30])
    with open(p, "wb") as fh:
        fh.write(subprocess.run(["/home/aiadmin/cineview-mla/r.sh", "cat '/media/usb/cineview-mla/dev-cache/reference/poster/id/%s'" % m[0]], capture_output=True).stdout)
    return p
desc = (n.get("longdesc") or n.get("shortdesc") or "").replace("\n", " ")
ndesc = (x.get("longdesc") or x.get("shortdesc") or "").replace("\n", " ")
data = {
    "bouquet": "16,0 E - Max TV", "clock": subprocess.run(["/home/aiadmin/cineview-mla/r.sh", "date +%H:%M"], capture_output=True, text=True).stdout.strip(), "date": subprocess.run(["/home/aiadmin/cineview-mla/r.sh", "date \"+%a %d %b\""], capture_output=True, text=True).stdout.strip(),
    "keys": ["All Services", "Reception Lists", "Providers", "Bouquets"],
    "rows": rows, "selected": sel, "video": os.path.join(out, "video.png"),
    "sel": {"num": 146, "name": "HBO HD", "picon": os.path.join(out, "picon_big.png"),
            "tech": "16.0°E  ·  DVB-S2  11636 H  30000  5/6  8PSK",
            "live_tech": "Live: SNR 75 %  ·  12.1 dB  ·  AGC 75 %  ·  1920x1080  ·  3.19 Mbps",
            "now": {"title": n["title"], "times": "%s – %s  ·  %d min" % (hm(n["begin_timestamp"]), hm(n["begin_timestamp"] + n["duration_sec"]), n["duration_sec"] // 60),
                    "times_short": "%s – %s" % (hm(n["begin_timestamp"]), hm(n["begin_timestamp"] + n["duration_sec"])),
                    "progress": max(0, min(1, (time.time() - n["begin_timestamp"]) / n["duration_sec"])),
                    "genre": n.get("genre") or "Film", "desc": desc, "poster": poster(n["title"])},
            "next": {"title": x["title"], "start": hm(x["begin_timestamp"]), "times": "%s – %s" % (hm(x["begin_timestamp"]), hm(x["begin_timestamp"] + x["duration_sec"])),
                     "desc": ndesc, "poster": poster(x["title"])}},
}
json.dump(data, open(os.path.join(out, "data.json"), "w"), ensure_ascii=False, indent=1)
print("rows", len(rows), "selected", sel, "now", n["title"], "next", x["title"], "posters", data["sel"]["now"]["poster"], data["sel"]["next"]["poster"])
