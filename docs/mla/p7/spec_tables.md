
### Cinema — Main InfoBar

| element | x,y | w×h | font | Enigma2 source / renderer | contract |
|---|---|---|---|---|---|
| band | 0,730 | 1920×350 | — | ePixmap active/assets/infobar/bl80.png (theme bitmap, scaled) | used by Classic, device ✔ |
| poster_now | 60,742 | 186×279 | — | session.Event_Now → CineViewMLAPosterX (toggle poster_infobar) | used by Classic, device ✔ |
| picon | 276,786 | 220×132 | — | session.CurrentService → Picon (ServiceName Reference) | used by Classic, device ✔ |
| ch_number | 276,930 | 64×34 | Regular;26 | session.CurrentService → ChannelNumber | used by Classic, device ✔ |
| ch_name | 344,930 | 152×34 | Regular;26 | ServiceName NameOnly (RunningText) | used by Classic, device ✔ |
| now_title | 540,772 | 1010×58 | Regular;46 | session.Event_Now → EventName Name (RunningText swimming) | used by Classic, device ✔ |
| now_time | 1580,784 | 280×40 | Regular;32 | EventTime StartTime/EndTime + ClockToText | used by Classic, device ✔ |
| progress | 540,842 | 1320×6 | — | EventTime Progress (Progress renderer) | used by Classic, device ✔ |
| now_short | 540,862 | 1320×34 | Regular;25 | session.Event_Now → EventName ShortDescription (1 line; EventInfo token) | native 57b7a51 (source ✔, device ⚠) |
| next_label | 540,914 | 110×34 | Regular;24 | static text | used by Classic, device ✔ |
| next_title | 650,912 | 900×36 | Regular;29 | session.Event_Next → EventName Name | used by Classic, device ✔ |
| next_time | 1580,912 | 280×36 | Regular;27 | Event_Next EventTime + ClockToText | used by Classic, device ✔ |
| tech_snr | 540,990 | 150×30 | Regular;23 | FrontendInfo SNR | used by Classic, device ✔ |
| tech_res | 700,990 | 150×30 | Regular;23 | VideoSize | used by Classic, device ✔ |
| tech_hd | 860,988 | 60×32 | — | ServiceInfo IsHD/Is4K + ConditionalShowHide | used by Classic, device ✔ |
| tech_169 | 930,988 | 60×32 | — | ServiceInfo IsWidescreen | used by Classic, device ✔ |
| tech_bitrate | 1010,990 | 190×30 | Regular;23 | CineViewMLABitrate Mbps (T6-verified) | used by Classic, device ✔ |
| tech_cam | 1210,990 | 280×30 | Regular;23 | CineViewMLACamInfo Info | used by Classic, device ✔ |
| tech_imdb | 1500,990 | 160×30 | Regular;23 | CineViewMLAIMDb Plain | used by Classic, device ✔ |
| tech_weather | 1670,990 | 190×30 | Regular;23 | OAWeather city/temperature_current | used by Classic, device ✔ |

**Posters off:** hidden: poster_now. moved: picon -216, ch_number -216, ch_name -216, next_label -216, tech_snr -216, tech_res -216, tech_hd -216, tech_169 -216, tech_bitrate -216, tech_cam -216, tech_imdb -216. widened (to the left): now_title +216, progress +216, now_short +216, next_title +216, sep +216.

### Cinema — SecondInfoBar

| element | x,y | w×h | font | Enigma2 source / renderer | contract |
|---|---|---|---|---|---|
| dim | 0,0 | 1920×1080 | — | eLabel steThemeOverlay (full screen) | used by Classic, device ✔ |
| poster_now | 90,110 | 360×540 | — | session.Event_Now → CineViewMLAPosterX (toggle poster_secondinfobar) | used by Classic, device ✔ |
| now_label | 500,112 | 300×34 | Regular;24 | static + ServiceName NameOnly | used by Classic, device ✔ |
| now_title | 500,150 | 1330×70 | Regular;56 | Event_Now EventName Name (RunningText, RTL variant) | used by Classic, device ✔ |
| now_meta | 500,228 | 1330×36 | Regular;27 | EventTime StartTime/EndTime + EventTime Duration (EventInfo token) + CineViewMLAIMDb | native 57b7a51 (source ✔, device ⚠) |
| progress | 500,276 | 1330×6 | — | EventTime Progress | used by Classic, device ✔ |
| now_desc | 500,300 | 1330×341 | Regular;27 | Event_Now EventName FullDescription (RunningText swimming, 11×31 px lines, RTL variant) | used by Classic, device ✔ |
| next_panel | 60,690 | 1800×220 | — | eLabel steThemePanel | used by Classic, device ✔ |
| poster_next | 90,705 | 127×190 | — | CineViewMLAPosterX nexts=1 (event-chained, 83adaa3) | used by Classic, device ✔ |
| next_label | 250,712 | 200×32 | Regular;24 | static | used by Classic, device ✔ |
| next_title | 250,746 | 1250×44 | Regular;36 | Event_Next EventName Name | used by Classic, device ✔ |
| next_time | 1520,750 | 310×40 | Regular;29 | Event_Next EventTime + ClockToText | used by Classic, device ✔ |
| next_desc | 250,800 | 1580×87 | Regular;25 | Event_Next EventName FullDescription (3 lines, swimming) | used by Classic, device ✔ |
| bottom_band | 0,940 | 1920×140 | — | eLabel steThemePanelAlt | used by Classic, device ✔ |
| picon | 60,958 | 170×102 | — | Picon | used by Classic, device ✔ |
| ch | 250,966 | 400×36 | Regular;29 | ChannelNumber + ServiceName | used by Classic, device ✔ |
| tp | 250,1010 | 600×30 | Regular;23 | CineViewMLATransponderInfo | used by Classic, device ✔ |
| tech | 900,1010 | 960×30 | Regular;23 | FrontendInfo, VideoSize, ServiceInfo, CineViewMLABitrate, CamInfo | used by Classic, device ✔ |

**Posters off:** hidden: poster_now, poster_next. widened (to the left): now_label +410, now_title +410, now_meta +410, progress +410, now_desc +410, next_label +160, next_title +160, next_desc +160.

### Details — Main InfoBar

| element | x,y | w×h | font | Enigma2 source / renderer | contract |
|---|---|---|---|---|---|
| panel | 24,770 | 1872×290 | — | eLabel steThemePanel | used by Classic, device ✔ |
| picon | 44,786 | 220×132 | — | Picon | used by Classic, device ✔ |
| ch_number | 276,790 | 150×40 | Regular;34 | ChannelNumber | used by Classic, device ✔ |
| ch_name | 276,836 | 150×30 | Regular;25 | ServiceName NameOnly | used by Classic, device ✔ |
| provider | 276,870 | 150×28 | Regular;22 | ServiceName Provider | used by Classic, device ✔ |
| tp | 44,930 | 380×52 | Regular;22 | CineViewMLATransponderInfo | used by Classic, device ✔ |
| cam | 44,1000 | 380×44 | Regular;21 | CineViewMLACamInfo Info | used by Classic, device ✔ |
| poster_now | 462,790 | 105×158 | — | Event_Now CineViewMLAPosterX (toggle poster_infobar) | used by Classic, device ✔ |
| now_title | 585,786 | 600×44 | Regular;36 | Event_Now EventName Name | used by Classic, device ✔ |
| now_time | 1190,790 | 240×36 | Regular;27 | EventTime + ClockToText | used by Classic, device ✔ |
| progress | 585,836 | 845×6 | — | EventTime Progress | used by Classic, device ✔ |
| now_info | 585,850 | 845×30 | Regular;22 | EventTime Duration / Remaining + EventName Genre (EventInfo tokens), CineViewMLAIMDb | native 57b7a51 (source ✔, device ⚠) |
| now_short | 585,884 | 845×52 | Regular;22 | EventName ShortDescription (2 lines) | native 57b7a51 (source ✔, device ⚠) |
| next_label | 462,972 | 110×32 | Regular;22 | static | used by Classic, device ✔ |
| next_title | 585,970 | 600×34 | Regular;28 | Event_Next EventName Name | used by Classic, device ✔ |
| next_time | 1190,972 | 240×32 | Regular;24 | Event_Next EventTime | used by Classic, device ✔ |
| next_short | 585,1008 | 845×30 | Regular;21 | Event_Next ShortDescription (1 line) | native 57b7a51 (source ✔, device ⚠) |
| snr_l | 1470,790 | 120×28 | Regular;21 | static | used by Classic, device ✔ |
| snr_bar | 1590,801 | 180×8 | — | FrontendInfo SNR (Progress, theme bitmap window/progress.png) | used by Classic, device ✔ |
| snr_v | 1780,790 | 96×28 | Regular;21 | FrontendInfo SNR | used by Classic, device ✔ |
| db | 1470,824 | 406×28 | Regular;21 | FrontendInfo SNRdB / AGC / BER | used by Classic, device ✔ |
| video | 1470,858 | 200×28 | Regular;21 | VideoSize | used by Classic, device ✔ |
| chips | 1680,856 | 60×30 | — | ServiceInfo IsHD/Is4K | used by Classic, device ✔ |
| chips2 | 1746,856 | 60×30 | — | ServiceInfo IsWidescreen | used by Classic, device ✔ |
| chips3 | 1812,856 | 64×30 | — | ServiceInfo HasTelext | used by Classic, device ✔ |
| bitrate | 1470,894 | 406×28 | Regular;21 | CineViewMLABitrate Mbps | used by Classic, device ✔ |
| cpu | 1470,928 | 406×28 | Regular;21 | CineViewMLACPUTemp Short | used by Classic, device ✔ |
| orbital | 1470,962 | 406×28 | Regular;21 | ServiceOrbitalPosition + Provider | used by Classic, device ✔ |
| weather | 1470,1008 | 406×30 | Regular;22 | OAWeather | used by Classic, device ✔ |

**Posters off:** hidden: poster_now. widened (to the left): now_title +123, progress +123, now_info +123, now_short +123, next_short +123.

### Details — SecondInfoBar

| element | x,y | w×h | font | Enigma2 source / renderer | contract |
|---|---|---|---|---|---|
| p_now | 24,110 | 900×600 | — | eLabel steThemePanel | used by Classic, device ✔ |
| p_next | 940,110 | 610×600 | — | eLabel steThemePanel | used by Classic, device ✔ |
| p_tech | 1566,110 | 330×600 | — | eLabel steThemePanelAlt | used by Classic, device ✔ |
| now_label | 50,126 | 200×30 | Regular;23 | static | used by Classic, device ✔ |
| now_time | 600,126 | 300×30 | Regular;24 | EventTime + ClockToText | used by Classic, device ✔ |
| poster_now | 50,166 | 205×308 | — | CineViewMLAPosterX (toggle poster_secondinfobar) | used by Classic, device ✔ |
| now_title | 275,166 | 625×84 | Regular;36 | EventName Name (2 lines, RTL variant) | used by Classic, device ✔ |
| now_meta | 275,266 | 625×30 | Regular;23 | EventTime Duration + EventName Genre (EventInfo tokens), CineViewMLAIMDb | native 57b7a51 (source ✔, device ⚠) |
| progress | 275,306 | 625×6 | — | EventTime Progress | used by Classic, device ✔ |
| now_desc | 275,326 | 625×336 | Regular;24 | EventName FullDescription (12×28 px, swimming, RTL variant) | used by Classic, device ✔ |
| next_label | 966,126 | 200×30 | Regular;23 | static | used by Classic, device ✔ |
| next_time | 1230,126 | 300×30 | Regular;24 | Event_Next EventTime | used by Classic, device ✔ |
| poster_next | 966,166 | 140×210 | — | CineViewMLAPosterX nexts=1 | used by Classic, device ✔ |
| next_title | 1124,166 | 406×74 | Regular;32 | Event_Next EventName Name | used by Classic, device ✔ |
| next_desc | 966,392 | 564×270 | Regular;23 | Event_Next FullDescription (10×27 px, swimming) | used by Classic, device ✔ |
| tech_label | 1586,126 | 290×30 | Regular;21 | static | used by Classic, device ✔ |
| tech_snr | 1586,170 | 290×28 | Regular;21 | FrontendInfo SNR/SNRdB | used by Classic, device ✔ |
| tech_bar | 1586,204 | 290×8 | — | FrontendInfo SNR | used by Classic, device ✔ |
| tech_agc | 1586,222 | 290×28 | Regular;21 | FrontendInfo AGC/BER | used by Classic, device ✔ |
| tech_tp | 1586,266 | 290×72 | Regular;21 | CineViewMLATransponderInfo | used by Classic, device ✔ |
| tech_cam | 1586,352 | 290×72 | Regular;21 | CineViewMLACamInfo | used by Classic, device ✔ |
| tech_video | 1586,474 | 290×28 | Regular;21 | VideoSize, ServiceInfo | used by Classic, device ✔ |
| tech_bitrate | 1586,508 | 290×28 | Regular;21 | CineViewMLABitrate | used by Classic, device ✔ |
| tech_cpu | 1586,542 | 290×28 | Regular;21 | CineViewMLACPUTemp | used by Classic, device ✔ |
| tech_weather | 1586,650 | 290×32 | Regular;22 | OAWeather | used by Classic, device ✔ |

**Posters off:** hidden: poster_now, poster_next. widened (to the left): now_title +225, now_meta +225, progress +225, now_desc +225, next_title +158.
