#!/usr/bin/env python3
"""Offline tests for mla/components/_lib/CineViewMLAPosterMatch.py (device-observed cases)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mla", "components", "_lib"))
sys.dont_write_bytecode = True
import CineViewMLAPosterMatch as M  # noqa: E402

FAIL = 0


def check(name, cond):
	global FAIL
	print(("PASS " if cond else "FAIL ") + name)
	FAIL += 0 if cond else 1


JS_DESC = "Smušeni policijski dvojac dobije zadatak da se infiltrira među srednjoškolce kako bi otkrili tko stoji iza prodaje..."
JS_EXT = "(SAD, 2012, film) Kad se policajci Schmidt i Jenko pridruže tajnoj jedinici Jump Street..."
film = {"provider": "imdb", "id": "tt1232829", "title": "21 Jump Street", "year": 2012, "year_end": 2012, "kind": "movie", "url": "u1", "rank": 0}
series = {"provider": "imdb", "id": "tt0092312", "title": "21 Jump Street", "year": 1987, "year_end": 1991, "kind": "series", "url": "u2", "rank": 1}
series_tvm = {"provider": "tvmaze", "id": 1, "title": "21 Jump Street", "year": 1987, "year_end": 1991, "kind": "series", "url": "u3", "rank": 0}

# 1. Same event, both screens: with or without ", film" in the title -> same identity key.
a = M.identify("21 Jump Street", JS_DESC, JS_EXT)
b = M.identify("21 Jump Street, film", JS_DESC, JS_EXT)
check("identity: year+kind from description", a["year"] == 2012 and a["kind"] == "movie")
check("identity: ', film' suffix gives the same key", a["key"] == b["key"])
best, conf, why = M.choose(a, [series, film, series_tvm])
check("21 Jump Street (2012, film) -> film poster (%s)" % why, best is film and conf >= M.THRESHOLD)

# 2. No year/kind -> a film and a series with the same name are ambiguous -> no poster (default image).
c = M.identify("21 Jump Street", "", "")
best, conf, why = M.choose(c, [film, series, series_tvm])
check("ambiguous title without event data -> no poster (%s)" % why, best is None)

# 3. Localised film title + year: IMDb answers the Croatian title with the English one.
hp = M.identify("Harry Potter i kamen mudraca", "Na 11. rođendan Harry Potter saznaje...", "(Engleska/SAD, 2001, film) Na 11. rođendan... Uloge: Daniel Radcliffe, Rupert Grint, Emma Watson")
hpc = {"provider": "imdb", "id": "tt0241527", "title": "Harry Potter and the Sorcerer's Stone", "year": 2001, "year_end": 2001, "kind": "movie", "url": "hp", "rank": 0, "stars": "Daniel Radcliffe, Rupert Grint"}
hp2 = {"provider": "imdb", "id": "tt0295297", "title": "Harry Potter and the Chamber of Secrets", "year": 2002, "year_end": 2002, "kind": "movie", "url": "hp2", "rank": 1}
best, conf, why = M.choose(hp, [hpc, hp2])
check("localised title + year -> correct film (%s)" % why, best is hpc)

# 4. Generic programmes never query providers.
for t in ("Vijesti", "Vrijeme", "Vreme", "HAK - promet info", "Regionalni dnevnik", "RTL Danas", "Studio 4: U fokusu",
		"Agenda: Svijet, vanjskopolitički magazin"):
	check("generic: %s" % t, M.identify(t)["generic"] is not None)
for t in ("21 Jump Street", "Columbo", "Harry Potter i kamen mudraca", "Druga strana"):
	check("not generic: %s" % t, M.identify(t)["generic"] is None)

# 5. Wrong poster seen on device: "Vrijeme" -> "'t Vrije Schaep" must be rejected even if not generic.
v = M.identify("Vrijeme sudbine")
best, conf, why = M.choose(v, [{"provider": "tvmaze", "id": 9, "title": "'t Vrije Schaep", "year": 2014, "year_end": None, "kind": "series", "url": "x", "rank": 0}])
check("dissimilar title rejected (%s)" % why, best is None)

# 6. Series with an episode year inside the run is accepted; outside the run rejected.
co = M.identify("Columbo", "", "(SAD, 1989, serija) Poručnik Columbo...")
cs = {"provider": "imdb", "id": "tt1466074", "title": "Columbo", "year": 1971, "year_end": 2003, "kind": "series", "url": "c", "rank": 0}
cf = {"provider": "imdb", "id": "tt9", "title": "Columbo", "year": 1989, "year_end": 1989, "kind": "movie", "url": "cf", "rank": 1}
best, conf, why = M.choose(co, [cs, cf])
check("series year inside run, film of same year rejected by kind (%s)" % why, best is cs)

# 7. Kind contradiction rejects.
best, conf, why = M.choose(M.identify("21 Jump Street", "", "(SAD, 1987, serija)"), [film])
check("series event never gets the film (%s)" % why, best is None)

# 8. Episode markers -> series, removed from the title.
e = M.identify("Columbo 9,")
check("trailing number/comma cleaned: %r" % e["title"], e["title"] == "Columbo 9")
e = M.identify("Kosti S05E12")
check("SxxEyy -> series, title cleaned (%s/%s)" % (e["title"], e["kind"]), e["kind"] == "series" and e["title"] == "Kosti")

# 9. Device cases 2026-10-03 21:40 (identity engine on Slot 8)
i = M.identify("Nitko", "", "(SAD, 2021, film) Hutch Mansell... Uloge: Bob Odenkirk, Connie Nielsen, Christopher Lloyd.")
wrong = {"provider": "imdb", "id": "tt1", "title": "No One Gets Out Alive", "year": 2021, "year_end": 2021, "kind": "movie", "url": "x", "rank": 0, "stars": "Cristina Rodlo, Marc Menchaca"}
right = {"provider": "imdb", "id": "tt7888964", "title": "Nobody", "year": 2021, "year_end": 2021, "kind": "movie", "url": "y", "rank": 1, "stars": "Bob Odenkirk, Aleksey Serebryakov"}
best, conf, why = M.choose(i, [wrong])
check("localised title without cast confirmation rejected (%s)" % why, best is None)
best, conf, why = M.choose(i, [wrong, right])
check("cast in description confirms the right film (%s)" % why, best is right)
for raw, title, kind, year in (
		("Indijski začin na francuski način, američko-francuski film (2014.) (12) (R)", "Indijski začin na francuski način", "movie", 2014),
		("Francuska s Evom Longorijom, dokumentarna serija ( )", "Francuska s Evom Longorijom", "series", None),
		("Clarksonova farma (3): Buđenje, dokumentarna serija ( )", "Clarksonova farma: Buđenje", "series", None),
		("Love Island Adria, . reality show", "Love Island Adria", "series", None),
		("Chicago u plamenu 10, . serija", "Chicago u plamenu", "series", None),
		("Prijatelji 7, . serija", "Prijatelji", "series", None)):
	e = M.identify(raw)
	check("clean %r -> %r/%s/%s" % (raw, e["title"], e["kind"], e["year"]), (e["title"], e["kind"], e["year"]) == (title, kind, year))

print("RESULT: %s" % ("all passed" if FAIL == 0 else "%d failed" % FAIL))
sys.exit(1 if FAIL else 0)
