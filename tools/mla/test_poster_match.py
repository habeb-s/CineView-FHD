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

# 10. Device case 2026-10-04 00:05: similar title + year off by one must not match.
g = M.identify("Bilo jednom u Gazi", "", "(Palestina/Francuska/Njemačka/Portugal/Saudijska Arabija/Egleska/Jordan/Katar, 2025, film) Gaza, 2007. Yahya...")
trubar = {"provider": "imdb", "id": "tt2", "title": "Bilo jednom u Trubaru", "year": 2026, "year_end": 2026, "kind": "movie", "url": "t", "rank": 7}
best, conf, why = M.choose(g, [trubar])
check("similar title + year+-1 rejected (%s)" % why, best is None)
# 11. Polish EPG (device 2026-10-09, Octagon SF8008, 13.0E): the description names the original title.
er = M.identify("Ostry dyżur 6 (odc. 22)", "Po strzelaninie w szkole Kovac i Benton opatruja napastnika...",
	"Tytuł oryginalny: ER\nUS, 2000\nReżyseria: Jonathan Kaplan\nWystępują: Anthony Edwards, Noah Wyle")
check("PL: original title + country/year line (%s)" % er["key"], er["orig"] == "ER" and er["year"] == 2000 and er["kind"] == "series")
er_c = {"provider": "imdb", "id": "tt0108757", "title": "ER", "year": 1994, "year_end": 2009, "kind": "series", "url": "er", "rank": 0}
bardzo = {"provider": "imdb", "id": "tt9", "title": "Bardzo ostry dyzur", "year": 2000, "year_end": 2000, "kind": "series", "url": "b", "rank": 1}
best, conf, why = M.choose(er, [bardzo, er_c])
check("PL: 'Ostry dyżur' -> ER (%s)" % why, best is er_c)
ch = M.identify("Czarodziejki 5 (odc. 1)", "", "Syrena Mylie zwraca się z prośbą o pomoc do czarodziejek...Tytuł oryginalny: Charmed\nUS, 2002\nReżyseria: James L. Conway")
c98 = {"provider": "imdb", "id": "tt0158552", "title": "Charmed", "year": 1998, "year_end": 2006, "kind": "series", "url": "c1", "rank": 0}
c18 = {"provider": "imdb", "id": "tt6394324", "title": "Charmed", "year": 2018, "year_end": 2022, "kind": "series", "url": "c2", "rank": 1}
best, conf, why = M.choose(ch, [c18, c98])
check("PL: original title glued to the previous sentence; 2002 picks the 1998 series (%s)" % why, ch["orig"] == "Charmed" and best is c98)
rc = M.identify("Królewskie święta 1 (odc. 5)", "", "Książę, przebywający z misją w Nowym Jorku, poznaje ambitną dziennikarkę...\nTytuł oryginalny: A Royal Christmas Holiday\nUS, 2023\nReżyseria: Fred Olen Ray\nWystępują: Brittany Underwood, Jonathan Stoddard")
rch = {"provider": "imdb", "id": "tt28", "title": "A Royal Christmas Holiday", "year": 2023, "year_end": 2023, "kind": "movie", "url": "r", "rank": 0, "stars": "Brittany Underwood, Jonathan Stoddard"}
rc14 = {"provider": "imdb", "id": "tt3", "title": "A Royal Christmas", "year": 2014, "year_end": 2014, "kind": "movie", "url": "r2", "rank": 1}
best, conf, why = M.choose(rc, [rc14, rch])
check("PL: '(odc. 5)' is a soft kind - the film with the original title and year matches (%s)" % why, rc["kind_soft"] and best is rch)
pea = M.identify("Peacock", "", "John Skillpa cierpi na zaburzenie...Tytuł oryginalny: Peacock\nUS, 2010\nWystępują: Cillian Murphy, Ellen Page")
p24 = {"provider": "imdb", "id": "tt29730305", "title": "Peacock", "year": 2024, "year_end": 2024, "kind": "movie", "url": "p1", "rank": 0}
p10 = {"provider": "imdb", "id": "tt1188113", "title": "Peacock", "year": 2010, "year_end": 2010, "kind": "movie", "url": "p2", "rank": 1}
best, conf, why = M.choose(pea, [p24, p10])
check("PL: same original and Polish title: year line still read, 2010 film chosen (%s)" % why, pea["orig"] == "" and pea["year"] == 2010 and best is p10)
same = M.identify("Ranczo 2 (odc. 13)", "", "Tytuł oryginalny: Ranczo\nPL, 2007")
check("PL: Polish production keeps its own key (%s)" % same["key"], same["key"] == "ranczo~series~2007")
for raw, orig in (("Piłka nożna: Premier League: Fulham - Arsenal", "Football: Premier League"), ("Tenis: WTA 1000 - China Open", "Tennis: China Open"),
		("Przerwa w programie", "Przerwa w programie")):
	e = M.identify(raw, "", "Tytuł oryginalny: %s\nGB, 2026" % orig)
	check("PL generic: %r -> %s" % (raw, e["generic"]), e["generic"] in ("generic-word", "sport"))
pep = M.identify("Świnka Peppa: odc.48", "", "serial animowany (Wielka Brytania, 2004) odc.48\nOd lat: 0")
check("PL: 'serial animowany (Wielka Brytania, 2004)' -> series/2004 (%s)" % pep["key"], pep["kind"] == "series" and pep["year"] == 2004 and not pep["kind_soft"])
hrt = M.identify("21 Jump Street", JS_DESC, JS_EXT)
check("Croatian EPG unchanged (%s)" % hrt["key"], hrt["key"] == a["key"] and not hrt["orig"])

# 12. Polish EPG without an original title: a localised series needs IMDb's top answer + year in the run + cast.
fr = M.identify("Przyjaciele 4: odc.17", "", "serial komediowy (USA, 1997) odc.17\nWystępują: Jennifer Aniston, Courteney Cox, Lisa Kudrow, Matt LeBlanc, Matthew Perry, David Schwimmer")
friends = {"provider": "imdb", "id": "tt0108778", "title": "Friends", "year": 1994, "year_end": 2004, "kind": "series", "url": "f", "rank": 1, "stars": "Jennifer Aniston, Courteney Cox"}
pl = {"provider": "imdb", "id": "tt1", "title": "Przyjaciele", "year": 2008, "year_end": 2009, "kind": "series", "url": "p", "rank": 0, "stars": "Anna Dereszowska"}
best, conf, why = M.choose(fr, [pl, friends])
check("PL: 'Przyjaciele' + cast -> Friends (%s)" % why, best is friends)
fr2 = M.identify("Przyjaciele 4: odc.17", "", "serial komediowy (USA, 1997) odc.17")
best, conf, why = M.choose(fr2, [pl, friends])
check("PL: same without cast -> no poster (%s)" % why, best is None)
hd = M.identify("Harmidom 6: odc.22", "", "serial animowany (USA, 2022) odc.22")
loud = {"provider": "imdb", "id": "tt4", "title": "The Loud House", "year": 2015, "year_end": None, "kind": "series", "url": "l", "rank": 0, "stars": "Grey Griffin"}
best, conf, why = M.choose(hd, [loud])
check("PL: animation without cast or original title -> no poster (%s)" % why, best is None)

# 13. Replay of 1648 Polish events (2026-10-09): soft kind must not let a similar film in; sport only by prefix.
gf = M.identify("Ghostforce 1 (odc. 47)", "", "Tytuł oryginalny: GhostForce\nFR, 2021")
gfs = {"provider": "imdb", "id": "tt1", "title": "Ghostforce", "year": 2021, "year_end": None, "kind": "series", "url": "g1", "rank": 0}
gfm = {"provider": "imdb", "id": "tt2", "title": "Ghostface", "year": 2021, "year_end": 2021, "kind": "movie", "url": "g2", "rank": 1}
best, conf, why = M.choose(gf, [gfs, gfm])
check("soft kind: 'Ghostforce (odc.)' -> the series, not the film 'Ghostface' 2021 (%s)" % why, best is gfs)
rs = M.identify("RESET: odc.2", "", "")
rss = {"provider": "imdb", "id": "tt3", "title": "Reset", "year": 2022, "year_end": None, "kind": "series", "url": "r1", "rank": 0}
rsm = {"provider": "imdb", "id": "tt4", "title": "Reset", "year": 2017, "year_end": 2017, "kind": "movie", "url": "r2", "rank": 1}
best, conf, why = M.choose(rs, [rss, rsm])
check("soft kind prefers the series with the same title (%s)" % why, best is rss)
check("'Galactik Football' is not sport", not M.identify("Galactik Football: odc.14", "", "serial animowany (Francja, 2006) odc.14")["generic"])
check("'Koszykówka: Euroliga' is sport", M.identify("Koszykówka: Euroliga: Real - Barcelona", "", "")["generic"] == "sport")
check("original title 'Football: Premier League' is sport", M.identify("Premier League: Fulham - Arsenal", "", "Tytuł oryginalny: Football: Premier League\nGB, 2026")["generic"] == "sport")

for raw in ("MMA: ONE Championship: Gala ONE Friday Fights 128", "Wrestling: All Elite Wrestling: All In 1 (odc. 2)", "Sport"):
	check("sport/service: %r -> %s" % (raw, M.identify(raw, "", "")["generic"]), bool(M.identify(raw, "", "")["generic"]))

print("RESULT: %s" % ("all passed" if FAIL == 0 else "%d failed" % FAIL))
sys.exit(1 if FAIL else 0)
