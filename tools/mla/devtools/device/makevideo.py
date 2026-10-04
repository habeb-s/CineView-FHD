#!/usr/bin/env python3
# One MP4 (1920x1080, 25 fps) of the 2026-10-04 changes: EventView line jumps (real recordings),
# Classic posters ON/OFF (real receiver shots, build26), Channel Selection proposals (mockups).
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_changes_2026-10-04.mp4")
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") else FB
BG, ACC, TXT, MUT = (8, 20, 38), (249, 199, 49), (240, 240, 240), (170, 182, 198)
def f(p, s): return ImageFont.truetype(p, s, layout_engine=ImageFont.Layout.RAQM)
def rtext(d, xy_right, y, s, font, fill):
    w = d.textlength(s, font=font, direction="rtl", language="ar")
    d.text((xy_right - w, y), s, font=font, fill=fill, direction="rtl", language="ar")
segs = []
def ff(*a): subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + list(a), check=True)
ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25", "-crf", "20", "-preset", "medium"]
def still(img, secs):
    p = os.path.join(T, "s%03d.png" % len(segs)); img.save(p)
    o = os.path.join(T, "seg%03d.mp4" % len(segs))
    ff("-loop", "1", "-t", str(secs), "-i", p, "-vf", "scale=1920:1080,fps=25", *ENC, o); segs.append(o)
def card(title, sub, lines=()):
    im = Image.new("RGB", (1920, 1080), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1920, 8], fill=ACC)
    rtext(d, 1800, 330, title, f(FB, 72), TXT)
    rtext(d, 1800, 450, sub, f(FR, 40), ACC)
    for i, ln in enumerate(lines): rtext(d, 1800, 560 + i * 62, ln, f(FR, 36), MUT)
    return im
def caption(img_path, label_ar, tag):
    im = Image.open(img_path).convert("RGB").resize((1920, 1080)); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, 1920, 86], fill=(8, 20, 38, 225)); d.rectangle([0, 86, 1920, 90], fill=ACC + (255,))
    rtext(d, 1880, 16, label_ar, f(FB, 40), TXT)
    tw = d.textlength(tag, font=f(FB, 36))
    d.rounded_rectangle([40, 16, 40 + tw + 40, 72], 12, fill=ACC + (255,)); d.text((60, 20), tag, font=f(FB, 36), fill=(26, 19, 0))
    return im
# 0 title
still(card("CineView MLA — تعديلات 4 أكتوبر 2026", "Vu+ Duo 4K SE · OpenATV 8.0.1 · Slot 8 · فرع dev/mla-openatv",
           ["EventView: القفز سطرًا كاملًا مقابل التمرير المستمر (تسجيل حقيقي)",
            "Classic عند إيقاف البوستر: إعادة التوزيع (لقطات حقيقية)",
            "قائمة القنوات: Poster List و Video First (نماذج قبل التنفيذ)",
            "لا شيء من هذا في إصدار نهائي — ينتظر اعتمادك"]), 6)
# 1 EventView recordings
still(card("1 · EventView", "يسار: Classic (تمرير مستمر) · يمين: سطر كامل كل 1.7 ث",
           ["تسجيل مباشر من الإطار المعروض على الرسيفر، 10 إطارات/ث", "نفس سرعة القراءة: 16.7 بكسل/ث"]), 4)
for c, lab in (("en_now", "وصف إنجليزي طويل — الحدث الحالي"), ("ar_now", "وصف عربي طويل — الحدث الحالي"), ("live_next", "حدث حي من EPG (Cinemax) — الحدث التالي")):
    bgimg = Image.new("RGB", (1920, 1080), BG); d = ImageDraw.Draw(bgimg)
    rtext(d, 1880, 150, lab, f(FB, 48), TXT)
    d.text((60, 830), "Classic", font=f(FB, 40), fill=MUT); d.text((1000, 830), "Line jumps (TEST)", font=f(FB, 40), fill=ACC)
    rtext(d, 1880, 900, "يسار: Classic · يمين: سطرًا سطرًا", f(FR, 34), MUT)
    p = os.path.join(T, "bg_%s.png" % c); bgimg.save(p)
    o = os.path.join(T, "seg%03d.mp4" % len(segs))
    ff("-loop", "1", "-i", p, "-i", os.path.join(H, "shots/evlines/cmp_%s.mp4" % c),
       "-filter_complex", "[1:v]scale=1840:-2:flags=lanczos,setpts=PTS-STARTPTS[v];[0:v][v]overlay=40:(H-h)/2:shortest=1,fps=25",
       *ENC, o); segs.append(o)
# 2 posters on/off
still(card("2 · Classic عند إيقاف البوستر", "لقطات حقيقية من الرسيفر — بناء تجريبي build26",
           ["Posters On: كما هو تمامًا (تحقق آلي)", "Posters Off: العناصر تتحرك وتتمدد بدل ترك فراغ"]), 4)
S = os.path.join(H, "shots/poff")
for n, lab in (("infobar", "Main InfoBar"), ("secondinfobar", "Second InfoBar"), ("eventview", "EventView"),
               ("channels", "قائمة القنوات"), ("channels_epg", "EPG — أحداث القناة"), ("epg", "Graphical EPG")):
    still(caption(os.path.join(S, "on_%s.png" % n), lab, "Posters ON"), 3)
    still(caption(os.path.join(S, "off_%s.png" % n), lab, "Posters OFF"), 4)
# 3 channel selection proposals
still(card("3 · قائمة القنوات — تصميمان مقترحان", "نماذج من المواصفة ببيانات الرسيفر الحقيقية — لم تُنفّذ بعد",
           ["Poster List: القائمة + لوحة القناة المؤشَّر عليها (الحالي والتالي ببوستر)", "Video First: الفيديو ظاهر + قائمة ضيقة + بطاقة"]), 5)
C = os.path.join(H, "csmock/out")
for n, lab, tag in (("posterlist_on", "Poster List", "Posters ON"), ("posterlist_off", "Poster List", "Posters OFF"),
                    ("posterlist_on_burgundy", "Poster List — ثيم Burgundy", "Posters ON"),
                    ("videofirst_on", "Video First — القائمة يسارًا", "Posters ON"), ("videofirst_off", "Video First — القائمة يسارًا", "Posters OFF"),
                    ("videofirst_on_right", "Video First — القائمة يمينًا", "Posters ON"), ("posterlist_on_dims", "Poster List — الأبعاد", "1920×1080")):
    still(caption(os.path.join(C, n + ".png"), lab, tag), 5)
still(card("بانتظار اعتمادك", "EventView · Classic بدون بوستر · قائمة القنوات",
           ["صفحة المراجعة: CineView Design Review"]), 4)
lst = os.path.join(T, "list.txt"); open(lst, "w").write("".join("file '%s'\n" % s for s in segs))
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", OUT)
print(OUT, os.path.getsize(OUT))
