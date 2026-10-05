"""EPG family — design spec (proposal for visual approval, 2026-10-04 evening).

Original CineView designs for the 'epg' section, 1920x1080 grid (outer margin 40, gutter 20, baseline 8).
Every box is a real skin box; the layout pack will be generated from the same numbers after approval.

Contract (enigma2 57b7a51, lib/python/Screens/EpgSelection.py + Components/EpgList.py, verified in source):
  GraphicalEPG / GraphicalEPGPIG  list (native EPGList graph grid: service column, event cells, colours and fonts
                     are EPGList.applySkin attributes), timeline_text, timeline_now (pixmap), Event / Service
                     sources of the HIGHLIGHTED cell, date, key_red..key_blue, bouquetlist
  EPGvertical      list1..list5 (one EPGList per column), currCh1..5 (channel names), piconCh1..5 (Picon sources),
                   Active1..5 (highlight of the active column), Event / Service, key_*  -> device contract check
                   (openVerticalEPG) BEFORE any implementation
  CineViewMLAPosterX on Event (ours, already used by Classic EPG); CineViewMLAShowIf for posters on/off;
  CineViewMLAIMDb rating only for a recognised film/series (P7 rule: never show unavailable data)
"""
W, H = 1920, 1080


def pitch(size):
	import math
	return int(round(size * 1854 / 2048.0)) + int(math.ceil(size * 434 / 2048.0))


HEADER = {"title": (40, 28, 1100, 48, 34), "date": (1300, 36, 360, 32, 22), "clock": (1680, 22, 200, 56, 44)}
FOOTER = (40, 980, 1840, 60)

GRAPHICAL_PLUS = {
	"id": "graphicalplus",
	"name": "Graphical Plus",
	"rows": 10,
	"service_w": 250,
	"posters_on": {
		"timeline": (40, 96, 1290, 40),
		"grid": (40, 140, 1290, 800),
		"panel": (1350, 96, 530, 844),
		"poster": (1374, 120, 240, 360),
		"ch_picon": (1634, 120, 140, 70),
		"ch_name": (1634, 198, 222, 30, 22),
		"times": (1634, 240, 222, 30, 24),
		"duration": (1634, 276, 222, 28, 22),
		"genre": (1634, 312, 222, 28, 21),
		"rating": (1634, 348, 222, 30, 22),
		"title": (1374, 500, 482, 82, 34),  # 2 lines x 39
		"desc": (1374, 600, 482, 312, 23),  # 12 lines x 26
	},
	# posters ON, highlighted event WITHOUT a poster: same screen and panel, no poster slot (No Poster layout instead
	# of a placeholder, user decision 2026-10-05 22:03).  The picon keeps its one place (ch_picon above): a Picon
	# cannot have hidden variants (t57b).
	"posters_on_noposter": {
		"ch_name": (1374, 140, 250, 30, 22),
		"title": (1374, 206, 482, 82, 34),
		"times": (1374, 298, 482, 30, 24),
		"duration": (1374, 334, 482, 28, 22),
		"genre": (1374, 370, 482, 28, 21),
		"rating": (1374, 406, 482, 30, 22),
		"desc": (1374, 450, 482, 468, 23),  # 18 lines x 26
	},
	"posters_off": {
		"timeline": (40, 96, 1540, 40),
		"grid": (40, 140, 1540, 800),
		"panel": (1600, 96, 280, 844),
		"ch_name": (1620, 116, 240, 30, 22),
		"title": (1620, 156, 240, 70, 30),  # 2 lines x 35 (device t37: 3 lines left a hole under one-line titles)
		"times": (1620, 236, 240, 30, 24),
		"duration": (1620, 272, 240, 28, 22),
		# genre / IMDb are empty for most events (device t40): as a footer they no longer leave a hole between the
		# duration and the description (user 2026-10-05: the panel must use its space evenly)
		"desc": (1620, 312, 240, 550, 22),  # 22 lines x 25, left-aligned (justified 240 px = wide word gaps, t37)
		"genre": (1620, 872, 240, 28, 21),
		"rating": (1620, 902, 240, 30, 22),
	},
}

COLUMNS = {
	"id": "columns",
	"name": "Columns",
	"cols": 5,
	"col_w": 352,
	"col_gap": 20,
	"col_head": (96, 72),  # y, h
	"col_list": (176, 584),  # y, h -> 8 rows x 73
	"row_h": 73,
	"posters_on": {
		"card": (40, 780, 1840, 180),
		"poster": (56, 792, 104, 156),
		"title": (180, 794, 1180, 40, 30),
		"times": (1380, 800, 480, 30, 24),
		"meta": (180, 838, 1680, 28, 21),
		"desc": (180, 870, 1680, 75, 22),  # 3 lines x 25
	},
	"posters_off": {
		"card": (40, 780, 1840, 180),
		"title": (56, 794, 1304, 40, 30),
		"times": (1380, 800, 480, 30, 24),
		"meta": (56, 838, 1804, 28, 21),
		"desc": (56, 870, 1804, 75, 22),
	},
}
