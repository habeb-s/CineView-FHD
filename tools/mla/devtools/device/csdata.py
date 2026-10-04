#!/usr/bin/env python3
# Collect real receiver data (OpenWebif, read-only) for the Channel Selection mockups.
import json, time, urllib.parse, urllib.request, sys
B = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.buket_maxtv.tv" ORDER BY bouquet'
W = "http://192.168.1.250"
def get(p):
    return json.load(urllib.request.urlopen(W + p, timeout=20))
q = urllib.parse.quote(B)
now = get("/api/epgnow?bRef=%s" % q)["events"]
nxt = get("/api/epgnext?bRef=%s" % q)["events"]
svcs = get("/api/getservices?sRef=%s" % q)["services"]
json.dump({"now": now, "next": nxt, "services": svcs, "t": time.time()}, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print(len(now), len(nxt), len(svcs))
print([ (s.get("pos"), s.get("servicename")) for s in svcs[:40]])
