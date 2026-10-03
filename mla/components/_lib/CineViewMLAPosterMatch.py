# -*- coding: utf-8 -*-
# CineView MLA — one poster identity + match-confidence engine for EVERY screen (P5).
#
# Pure Python (no enigma imports): unit-testable off the receiver.  The renderer passes the EPG event
# (name, short and extended description) and an HTTP getter; this module decides
#   * the event identity  : normalised title + kind (movie/series) + year, taken from the title suffix
#                            (", film", ", TV film") and the description ("(SAD, 2012, film)") when present;
#   * whether a lookup makes sense at all (news / weather / traffic / magazines -> "generic");
#   * which provider candidate is the SAME work, with a confidence score.  Below the threshold, or when
#     the title is ambiguous (a film and a series with the same name and nothing to tell them apart),
#     no poster is chosen and the caller shows the neutral default image instead of a wrong poster.
# The cache key is the identity, not the screen: SecondInfoBar, EventView, InfoBar, EPG ... resolve the
# same event to the same file.
import re
import unicodedata
from difflib import SequenceMatcher

THRESHOLD = 0.80
AMBIGUITY_MARGIN = 0.10

_GENERIC_WORDS = {
	# news / current affairs
	"dnevnik", "vijesti", "vesti", "novosti", "news", "nachrichten", "tagesschau", "journal", "telegiornale",
	"telediario", "infojournal", "danas", "jutro", "headlines", "bulletin",
	# weather / traffic / service
	"vrijeme", "vreme", "weather", "wetter", "meteo", "prognoza", "promet", "traffic", "verkehr", "teletext",
	"teleshop", "teleshopping", "reklame", "werbung", "advertising", "najava", "trailer", "pauza", "testbild",
	# magazines / talk / studio
	"magazin", "magazine", "studio", "emisija", "talk", "kviz", "quiz", "agenda", "fokusu",
}
_GENERIC_PHRASES = ("promet info", "kraj programa", "end of programme", "program note", "u fokusu")

_MOVIE_WORDS = ("film", "tv film", "movie", "spielfilm", "igrani film", "dugometražni film", "animirani film",
	"dokumentarni film", "kinofilm")
_SERIES_WORDS = ("serija", "series", "serie", "miniserija", "humoristična serija", "dramska serija",
	"dokumentarna serija", "telenovela", "sitcom", "episode", "epizoda", "staffel")

_TITLE_KIND_SUFFIX = re.compile(r"\s*[,(\-:]\s*(tv film|film|serija|movie|series)\s*\)?\s*$", re.I)
_EPISODE = re.compile(r"(?i)\b(s\d{1,2}\s*e\d{1,3}|ep\.?\s*\d+|epizoda\s*\d+|episode\s*\d+|odc\.?\s*\d+|\d+\s*/\s*\d+)\b")
_PAREN = re.compile(r"\(([^()]{2,120})\)")
_YEAR = re.compile(r"\b(19[0-9]{2}|20[0-9]{2})\b")


def norm(text):
	text = unicodedata.normalize("NFKD", text or "")
	text = "".join(c for c in text if not unicodedata.combining(c)).lower()
	text = text.replace("&", " and ")
	text = re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)
	text = re.sub(r"\b(the|a|an|der|die|das|le|la|les|il|el)\b", " ", text)
	return re.sub(r"\s+", " ", text).strip()


def _kind_of(words):
	w = " " + words.lower() + " "
	for m in _SERIES_WORDS:
		if " " + m + " " in w or w.rstrip().endswith(" " + m):
			return "series"
	for m in _MOVIE_WORDS:
		if " " + m + " " in w or w.rstrip().endswith(" " + m):
			return "movie"
	return None


def identify(name, short="", extended="", now_year=None):
	"""-> dict(title, kind, year, key, generic, reason).  Deterministic for the same event data."""
	raw = (name or "").replace("\x86", "").replace("\x87", "").strip()
	title, kind, year = raw, None, None
	# Device-observed EPG title noise (HRT/RTL, 16.0E): "( )", "(12)", "(R)", "(2014.)", ", . serija",
	# ", dokumentarna serija", ", američko-francuski film (2014.)", ", . reality show".
	ym = re.search(r"\((19\d{2}|20\d{2})\.?\)", title)
	if ym:
		year = int(ym.group(1))
	title = re.sub(r"\((?:\s*|\d{1,2}|R|PG|PG-13|[A-Z]{1,3}|(?:19|20)\d{2}\.?)\)", " ", title)
	title = re.sub(r",\s*\.\s*", ", ", title)
	parts = [p.strip() for p in title.split(",")]
	while len(parts) > 1:
		tail = parts[-1].lower()
		k = _kind_of(re.sub(r"[-–./]", " ", tail)) or ("series" if "reality" in tail or "show" in tail else None)
		if k is None or len(tail.split()) > 5:
			break
		kind = kind or k
		parts.pop()
	title = ", ".join(parts)
	m = _TITLE_KIND_SUFFIX.search(title)
	if m:
		kind = "series" if m.group(1).lower() in ("serija", "series") else "movie"
		title = title[:m.start()]
	if _EPISODE.search(title):
		kind = kind or "series"
		title = _EPISODE.sub(" ", title)
	title = re.sub(r"\s+", " ", title).strip(" ,-:|.")
	title = re.sub(r"\s+([:,])", r"\1", title)
	if kind == "series":
		title = re.sub(r"\s+\d{1,2}$", "", title)  # season number ("Chicago u plamenu 10")
	desc = " ".join(x for x in (short or "", extended or "") if x)
	# "(SAD, 2012, film)", "(Engleska/SAD, 2001, film)", "(Hrvatska, 2019.)", "(USA 1987, Serie)"
	for inner in _PAREN.findall(desc[:600]):
		y = _YEAR.search(inner)
		k = _kind_of(re.sub(r"[,./;]", " ", inner))
		if y and (k or "," in inner or len(inner) < 40):
			year = year or int(y.group(1))
			kind = kind or k
			break
	if kind is None and desc:
		kind = _kind_of(re.sub(r"[,./;()]", " ", desc[:160]))
	if year and now_year and year > now_year + 1:
		year = None
	n = norm(title)
	words = set(n.split())
	generic = None
	if not n or len(n) < 2:
		generic = "empty"
	elif words & _GENERIC_WORDS or any(p in n for p in _GENERIC_PHRASES):
		generic = "generic-word"
	key = "%s~%s~%s" % (n[:150], kind or "", year or "")
	return {"title": title, "norm": n, "kind": kind, "year": year, "key": key, "generic": generic, "desc_norm": norm(desc)}


# ------------------------------------------------------------------ provider candidates
def _imdb_kind(row):
	q = (row.get("qid") or row.get("q") or "").lower()
	if q in ("movie", "tvmovie", "feature", "tv movie", "video", "short"):
		return "movie"
	if q in ("tvseries", "tvminiseries", "tv series", "tv mini-series", "tv mini series", "podcastseries"):
		return "series"
	return None


def _range(text):
	ys = [int(y) for y in _YEAR.findall(str(text or ""))]
	if not ys:
		return None, None
	return ys[0], (ys[1] if len(ys) > 1 else None)


def imdb_candidates(data):
	out = []
	for rank, row in enumerate((data or {}).get("d") or []):
		if not str(row.get("id") or "").startswith("tt"):
			continue
		url = ((row.get("i") or {}).get("imageUrl"))
		if not url:
			continue
		y0, y1 = _range(row.get("yr") or row.get("y"))
		kind = _imdb_kind(row)
		out.append({"provider": "imdb", "id": row.get("id"), "title": row.get("l") or "", "year": y0,
			"year_end": y1 if kind == "series" else y0, "kind": kind, "url": url, "rank": rank, "stars": row.get("s") or ""})
	return out


def tvmaze_candidates(rows):
	out = []
	for rank, row in enumerate(rows or []):
		show = (row or {}).get("show") or {}
		img = show.get("image") or {}
		url = img.get("original") or img.get("medium")
		if not url:
			continue
		y0, _ = _range(show.get("premiered"))
		y1, _ = _range(show.get("ended"))
		out.append({"provider": "tvmaze", "id": show.get("id"), "title": show.get("name") or "", "year": y0,
			"year_end": y1, "kind": "series", "url": url, "rank": rank})
	return out


def itunes_candidates(data, media):
	out = []
	for rank, row in enumerate((data or {}).get("results") or []):
		url = row.get("artworkUrl100") or row.get("artworkUrl60")
		if not url:
			continue
		url = re.sub(r"/\d+x\d+bb\.", "/600x900bb.", url)  # Apple CDN serves the requested size
		y0, _ = _range(row.get("releaseDate"))
		title = row.get("trackName") or row.get("collectionName") or ""
		if media != "movie":
			title = re.sub(r",?\s*(season|staffel|sezona)\s*\d+.*$", "", title, flags=re.I)
		out.append({"provider": "itunes", "id": row.get("trackId") or row.get("collectionId"), "title": title,
			"year": y0, "year_end": None if media != "movie" else y0, "kind": "movie" if media == "movie" else "series",
			"url": url, "rank": rank})
	return out


# ------------------------------------------------------------------ scoring
def similarity(a, b):
	a, b = norm(a), norm(b)
	if not a or not b:
		return 0.0
	if a == b:
		return 1.0
	r = SequenceMatcher(None, a, b).ratio()
	ta, tb = set(a.split()), set(b.split())
	if ta and tb and (ta <= tb or tb <= ta):
		r = max(r, 0.85 * min(len(ta), len(tb)) / max(len(ta), len(tb)) + 0.1)
	return r


def cast_hit(ident, cand):
	"""True when a lead actor of the candidate (IMDb 's' field) is named in the event description."""
	desc = " " + ident.get("desc_norm", "") + " "
	for star in (cand.get("stars") or "").split(",")[:3]:
		last = norm(star).split()
		if last and len(last[-1]) > 3 and (" " + last[-1] + " ") in desc:
			return True
	return False


def score(ident, cand):
	"""-> (confidence 0..1, reasons).  A known kind/year that contradicts the candidate rejects it."""
	reasons = []
	strong = False  # exact production year (+ similar title or cast confirmation) identifies a film by itself
	sim = similarity(ident["title"], cand["title"])
	conf = sim
	reasons.append("sim=%.2f" % sim)
	if ident["kind"] and cand["kind"]:
		if ident["kind"] != cand["kind"]:
			return 0.0, reasons + ["kind %s!=%s" % (ident["kind"], cand["kind"])]
		conf += 0.05
		reasons.append("kind=%s" % cand["kind"])
	year, y0, y1 = ident["year"], cand.get("year"), cand.get("year_end")
	if year and y0:
		if cand["kind"] == "series" or ident["kind"] == "series":
			# A description year of a series is usually the season/episode year: inside the run is fine.
			if y0 - 1 <= year <= (y1 or 9999) + 1:
				conf += 0.15
				reasons.append("year %d in %s-%s" % (year, y0, y1 or ""))
			else:
				return 0.0, reasons + ["year %d outside %s-%s" % (year, y0, y1 or "")]
		else:
			if abs(year - y0) == 0:
				# IMDb's suggestion search matched the (often localised) EPG title AND the production year
				# is identical: same film even when the canonical title differs (Croatian EPG title vs.
				# English IMDb title).  Only trusted for IMDb's top two answers; elsewhere the title must match.
				cast = cast_hit(ident, cand)
				if sim >= 0.6 or (cand["provider"] == "imdb" and cand.get("rank", 9) <= 1 and cast):
					strong = True
					# A localised title is trusted only when the cast in the EPG description confirms the
					# work (device case: "Nitko" 2021 = "Nobody", IMDb's top answer "No One Gets Out Alive").
					conf = max(conf, 0.70) + 0.25
				else:
					conf += 0.10
				reasons.append("year=%d" % year + (",cast" if cast else ""))
			elif abs(year - y0) == 1:
				conf += 0.10  # EPG year off by one (release vs. production year): a hint, never a rescue
				reasons.append("year~%d/%d" % (year, y0))
			else:
				return 0.0, reasons + ["year %d!=%d" % (year, y0)]
	if cand.get("rank", 0) > 2 and sim < 0.9:
		conf -= 0.1
		reasons.append("rank=%d" % cand["rank"])
	if not strong and sim < 0.90 and conf >= THRESHOLD:
		# Similar but different titles ("Bilo jednom u Gazi" 2025 vs "Bilo jednom u Trubaru" 2026, device 00:05):
		# hints (kind, year +-1, rank) never lift a non-identical title over the threshold.
		conf = THRESHOLD - 0.01
		reasons.append("similar-title-only")
	return min(conf, 1.0), reasons


def choose(ident, candidates):
	"""-> (best candidate or None, confidence, decision text)."""
	scored = []
	for c in candidates:
		conf, why = score(ident, c)
		scored.append((conf, c, why))
	scored.sort(key=lambda x: -x[0])
	if not scored or scored[0][0] < THRESHOLD:
		best = scored[0] if scored else None
		return None, (best[0] if best else 0.0), "no-reliable-match" + (" best=%s/%s/%s %.2f %s" % (best[1]["provider"], best[1]["title"], best[1].get("year"), best[0], ",".join(best[2])) if best else "")
	top_conf, top, why = scored[0]
	# Ambiguity: a DIFFERENT work (other kind or other year) scores almost as high and the event data
	# cannot tell them apart (e.g. "21 Jump Street" film 2012 vs. series 1987 with no year/kind in EPG).
	for conf, c, _ in scored[1:]:
		if conf < THRESHOLD or top_conf - conf > AMBIGUITY_MARGIN:
			break
		same = (c["kind"] == top["kind"] or not c["kind"] or not top["kind"]) and (not c.get("year") or not top.get("year") or abs(c["year"] - top["year"]) <= 1)
		if not same:
			return None, top_conf, "ambiguous %s/%s/%s vs %s/%s/%s" % (top["provider"], top["title"], top.get("year"), c["provider"], c["title"], c.get("year"))
	return top, top_conf, "match %s/%s/%s/%s %.2f %s" % (top["provider"], top["title"], top.get("year"), top["kind"], top_conf, ",".join(why))
