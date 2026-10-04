"""Channel Selection family — design spec (proposal for visual approval, 2026-10-04).

Two original CineView designs for the 'channelselection' section, on the 1920x1080 grid (outer margin 40,
gutter 16, baseline 8).  Every box is a real skin box: the renderer draws exactly these rectangles, and the
layout pack will be generated from the same numbers after approval.

Contract (verified in enigma2 57b7a51 source, lib/python/Components):
  list                     native ServiceList (rows, picons, numbers, progress = user settings + skin fonts/colours;
                           serviceItemHeight, serviceNameFont, serviceInfoFont, serviceNumberFont, colorServiceDescription,
                           progressBar ... are real ServiceList.applySkin attributes)
  ServiceEvent             event of the HIGHLIGHTED service (not the playing one)
  EventName  Name / FullDescription / NextName / NextDescription / NextTimes / Genre   (EventInfo tokens)
  EventTime  StartTime / EndTime / Progress / Duration
  ServiceName Reference / Name, ServiceOrbitalPosition, CineViewMLATransponderInfo (ours, shipped)
  CineViewMLAPosterX  nexts=0 (now) / nexts=1 (next) on ServiceEvent (ours, already used by Classic)
  CineViewMLAShowIf   posters on/off and LTR/RTL variants (ours, tested)
"""
W, H = 1920, 1080

def pitch(size):
	"""Line pitch of LiberationSans on enigma2 57b7a51 (formula fitted to device measurements 21..27)."""
	import math
	return int(round(size * 1854 / 2048.0)) + int(math.ceil(size * 434 / 2048.0))

POSTER_LIST = {
	"id": "posterlist",
	"name": "Poster List",
	"video": "dim",  # live video behind a strong overlay
	"boxes": {
		"header": (40, 40, 1840, 64),
		"list_panel": (40, 112, 944, 864),
		"list": (56, 124, 912, 840),  # 14 rows x 60
		"detail_panel": (1000, 112, 880, 864),
		"footer": (40, 992, 1840, 48),
	},
	"row_h": 60,
	"posters_on": {
		"svc_picon": (1024, 132, 150, 90),
		"svc_name": (1190, 136, 666, 40, 30),
		"svc_tech": (1190, 182, 666, 28, 20),
		"div1": (1024, 238, 832, 2),
		"now_poster": (1024, 258, 240, 360),
		"now_eyebrow": (1288, 258, 568, 26, 20),
		"now_title": (1288, 286, 568, 72, 32),  # 2 lines
		"now_times": (1288, 368, 568, 28, 22),
		"now_progress": (1288, 404, 568, 6),
		"now_genre": (1288, 420, 568, 26, 21),
		"now_desc": (1288, 456, 568, 175, 22),  # 7 lines x 25
		"div2": (1024, 646, 832, 2),
		"next_poster": (1024, 666, 160, 240),
		"next_eyebrow": (1208, 666, 648, 26, 20),
		"next_title": (1208, 694, 648, 34, 30),
		"next_desc": (1208, 740, 648, 168, 21),  # 7 lines x 24
	},
	"posters_off": {
		"svc_picon": (1024, 132, 150, 90),
		"svc_name": (1190, 136, 666, 40, 30),
		"svc_tech": (1190, 182, 666, 28, 20),
		"div1": (1024, 238, 832, 2),
		"now_eyebrow": (1024, 258, 832, 26, 20),
		"now_title": (1024, 286, 832, 72, 32),
		"now_times": (1024, 368, 832, 28, 22),
		"now_progress": (1024, 404, 832, 6),
		"now_genre": (1024, 420, 832, 26, 21),
		"now_desc": (1024, 456, 832, 175, 22),
		"div2": (1024, 646, 832, 2),
		"next_eyebrow": (1024, 666, 832, 26, 20),
		"next_title": (1024, 694, 832, 34, 30),
		"next_desc": (1024, 740, 832, 216, 21),  # 9 lines x 24
	},
}

VIDEO_FIRST = {
	"id": "videofirst",
	"name": "Video First",
	"video": "clear",  # live video stays fully visible
	"boxes": {
		"list_panel": (40, 40, 640, 1000),
		"title": (64, 56, 592, 44, 30),
		"list": (56, 112, 608, 816),  # 17 rows x 48
		"keys": (56, 944, 608, 80),  # 2x2 colour keys
		"clock": (1696, 40, 184, 72),
		"card": (696, 800, 1184, 240),
	},
	"row_h": 48,
	"posters_on": {
		"poster": (712, 816, 140, 208),
		"svc_line": (868, 816, 996, 28, 21),  # picon-less: name · number · orbital
		"now_title": (868, 846, 820, 40, 30),
		"now_times": (1700, 852, 164, 30, 22),
		"now_progress": (868, 894, 996, 6),
		"now_desc": (868, 908, 996, 48, 21),  # 2 lines x 24
		"next_line": (868, 966, 996, 28, 22),
		"tech_line": (868, 998, 996, 26, 19),
	},
	"posters_off": {
		"svc_line": (712, 816, 1152, 28, 21),
		"now_title": (712, 846, 976, 40, 30),
		"now_times": (1700, 852, 164, 30, 22),
		"now_progress": (712, 894, 1152, 6),
		"now_desc": (712, 908, 1152, 48, 21),
		"next_line": (712, 966, 1152, 28, 22),
		"tech_line": (712, 998, 1152, 26, 19),
	},
}
