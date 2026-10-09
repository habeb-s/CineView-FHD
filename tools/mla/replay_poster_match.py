#!/usr/bin/env python3
"""Replay real EPG events through two versions of CineViewMLAPosterMatch with live provider answers.

usage: replay_poster_match.py <events.json> <old PosterMatch.py> <new PosterMatch.py> <cache dir> [report.txt]
events.json: [{"ch", "title", "short", "long"}] (OpenWebif epgnow/epgnext of the receiver's bouquets).
Provider queries mirror the renderer (tools/mla/patches/posterx_identity.py _mla_candidates): old = localised
title; new = original title from the description first, the localised title when it finds nothing.  Answers are
cached on disk so both versions see identical data.  Prints every event whose decision differs."""
import hashlib, importlib.util, json, os, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

API_IMDB = "https://v3.sg.media-imdb.com/suggestion/x/%s.json"
API_SEARCH = "https://api.tvmaze.com/search/shows"
API_ITUNES = "https://itunes.apple.com/search"


def load(path, name):
	spec = importlib.util.spec_from_file_location(name, path)
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	return m


def main(events, old_py, new_py, cache, report=None):
	O, N = load(old_py, "pm_old"), load(new_py, "pm_new")
	os.makedirs(cache, exist_ok=True)

	def get(url, params=None):
		if params:
			url = url + "?" + urllib.parse.urlencode(params)
		f = os.path.join(cache, hashlib.md5(url.encode()).hexdigest() + ".json")
		if os.path.exists(f):
			return json.load(open(f))
		data = None
		for attempt in range(3):
			try:
				req = urllib.request.Request(url, headers={"User-Agent": "CineView-FHD/2.0.2 (Enigma2 native poster renderer)"})
				data = json.load(urllib.request.urlopen(req, timeout=15))
				break
			except Exception:
				time.sleep(1 + attempt)
		json.dump(data, open(f, "w"))
		return data

	def candidates(M, ident, new):
		out, q = [], ident["title"]
		qs = [x for x in (ident.get("orig"), ident["title"]) if x] if new else [ident["title"]]
		for qq in qs:
			q = qq
			out += M.imdb_candidates(get(API_IMDB % urllib.parse.quote(q)) or {})
			if out:
				break
		soft = ident.get("kind_soft") if new else False
		if ident["kind"] != "movie" or soft:
			out += M.tvmaze_candidates(get(API_SEARCH, {"q": q}) or [])
		if not out:
			k = None if soft else ident["kind"]
			for media, entity in (("movie", "movie"), ("tvShow", "tvSeason")):
				if k and k != ("movie" if media == "movie" else "series"):
					continue
				out += M.itunes_candidates(get(API_ITUNES, {"term": q, "media": media, "entity": entity, "limit": 5, "country": "US"}) or {}, media)
		return out

	def decide(M, ev, new):
		ident = M.identify(ev["title"], ev["short"], ev["long"], now_year=2027)
		if ident["generic"]:
			return ident, None, "generic"
		best, conf, why = M.choose(ident, candidates(M, ident, new))
		return ident, best, why

	rows = json.load(open(events))
	seen, evs = set(), []
	for r in rows:
		k = (r["title"], r["short"][:80], r["long"][:200])
		if k not in seen:
			seen.add(k)
			evs.append(r)

	def both(ev):
		return ev, decide(O, ev, False), decide(N, ev, True)

	with ThreadPoolExecutor(8) as ex:
		res = list(ex.map(both, evs))
	lines = []
	stat = {"events": len(res), "old_match": 0, "new_match": 0, "gained": 0, "lost": 0, "changed": 0, "old_generic": 0, "new_generic": 0}
	for ev, (oi, ob, ow), (ni, nb, nw) in res:
		stat["old_match"] += ob is not None
		stat["new_match"] += nb is not None
		stat["old_generic"] += ow == "generic"
		stat["new_generic"] += nw == "generic"
		label = None
		if ob is None and nb is not None:
			label, stat["gained"] = "GAINED", stat["gained"] + 1
		elif ob is not None and nb is None:
			label, stat["lost"] = "LOST", stat["lost"] + 1
		elif ob is not None and nb is not None and (ob["provider"], ob["id"]) != (nb["provider"], nb["id"]):
			label, stat["changed"] = "CHANGED", stat["changed"] + 1
		if label:
			lines.append("%-7s %-24s %-44s orig=%-30s | old: %s | new: %s" % (label, ev["ch"][:24], ev["title"][:44], (ni.get("orig") or "")[:30],
				("%s/%s/%s" % (ob["provider"], ob["title"], ob.get("year"))) if ob else ow[:60],
				("%s/%s/%s" % (nb["provider"], nb["title"], nb.get("year"))) if nb else nw[:90]))
	out = "\n".join(sorted(lines)) + "\n" + json.dumps(stat) + "\n"
	print(out)
	if report:
		open(report, "w", encoding="utf-8").write(out)


if __name__ == "__main__":
	main(*sys.argv[1:])
