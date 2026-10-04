#!/usr/bin/env python3
# Video of the 2026-10-04 evening fixes (build33/build34, Slot 8): real receiver grabs (before/after) and the
# fast-navigation grab-loop recordings (~7 fps, video+OSD) played at their real timing; EPG proposal mockups.
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video4_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_evening_fixes_2026-10-04.mp4")
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG, ACC, TXT, MUT = (8, 20, 38), (249, 199, 49), (240, 240, 240), (170, 182, 198)
W, HH = 1280, 720
def f(p, s): return ImageFont.truetype(p, s, layout_engine=ImageFont.Layout.RAQM)
def rtext(d, xr, y, s, font, fill):
    w = d.textlength(s, font=font, direction="rtl", language="ar"); d.text((xr - w, y), s, font=font, fill=fill, direction="rtl", language="ar")
segs = []
ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25", "-crf", "23", "-preset", "medium"]
def ff(*a): subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + list(a), check=True)
def still(img, secs):
    p = os.path.join(T, "s%03d.png" % len(segs)); img.save(p); o = os.path.join(T, "seg%03d.mp4" % len(segs))
    ff("-loop", "1", "-t", str(secs), "-i", p, "-vf", "scale=%d:%d,fps=25" % (W, HH), *ENC, o); segs.append(o)
def card(title, sub, lines=()):
    im = Image.new("RGB", (W, HH), BG); d = ImageDraw.Draw(im); d.rectangle([0, 0, W, 6], fill=ACC)
    rtext(d, W - 80, 200, title, f(FB, 46), TXT); rtext(d, W - 80, 280, sub, f(FR, 27), ACC)
    for i, ln in enumerate(lines): rtext(d, W - 80, 350 + i * 44, ln, f(FR, 24), MUT)
    return im
def caption(p, lab, tag, good=None):
    im = Image.open(p).convert("RGB").resize((W, HH)); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, W, 58], fill=(8, 20, 38, 230)); d.rectangle([0, 58, W, 61], fill=ACC + (255,))
    rtext(d, W - 24, 12, lab, f(FB, 27), TXT)
    col = {True: (60, 170, 110), False: (200, 70, 60)}.get(good, ACC)
    tw = d.textlength(tag, font=f(FB, 24)); d.rounded_rectangle([24, 11, 24 + tw + 28, 49], 9, fill=col + (255,)); d.text((38, 14), tag, font=f(FB, 24), fill=(255, 255, 255))
    return im
def rec(d, label):
    src = os.path.join(H, d); fs = sorted((int(x[:-4]), x) for x in os.listdir(src) if x.endswith(".jpg"))
    lst = os.path.join(T, "c%03d.txt" % len(segs))
    with open(lst, "w") as fh:
        for i, (t, n) in enumerate(fs):
            fh.write("file '%s'\nduration %.4f\n" % (os.path.join(src, n), (fs[i + 1][0] - t) / 1e9 if i + 1 < len(fs) else 0.4))
        fh.write("file '%s'\n" % os.path.join(src, fs[-1][1]))
    o = os.path.join(T, "seg%03d.mp4" % len(segs))
    tag = label.replace(":", "\\:").replace("'", "")
    ff("-f", "concat", "-safe", "0", "-i", lst, "-vf", "fps=25,scale=%d:%d,drawtext=fontfile=%s:text='%s':x=w-tw-18:y=12:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8" % (W, HH, FB, tag), *ENC, o)
    segs.append(o); return (fs[-1][0] - fs[0][0]) / 1e9, len(fs)
S = lambda t, n: os.path.join(H, "shots", t, n + ".png")

still(card("CineView MLA — إصلاحات المساء", "Slot 8 · build33/build34 · لقطات وتسجيلات فعلية من الرسيفر",
           ["أسماء القنوات الطويلة · خلفية Poster List · البوسترات أثناء التنقل السريع",
            "طبقات الشاشات الأساسية · accelAlloc · الانحدار · مقترحات EPG"]), 6)

still(card("1. الشاشات الأساسية", "الخلفية كانت تُرسم فوق النصوص", ["الإصلاح: الخلفية طبقة واحدة تحت النصوص، دون تغيير الأبعاد"]), 4)
for n, lab in (("pluginbrowser", "Plugin Browser — MENU / HELP"), ("quickmenu", "Quick Menu — HELP"), ("pkgremove", "شاشة الإزالة — HELP"), ("pkglog", "PackageActionLog — نص السجل")):
    still(caption(S("t34", "before_" + n), lab, "BEFORE", False), 3)
    still(caption(S("t34", "after_" + n), lab, "AFTER", True), 3)

still(card("2. أسماء القنوات الطويلة", "Video First — القائمة الضيقة", ["الاسم كان يتجاوز خانته فوق شريط التقدم (السطر 155)"]), 4)
for t, tag, g in (("t34", "BEFORE", False), ("t35", "AFTER", True)):
    still(caption(S(t, "d1_videofirst_down1"), "Video First — القائمة يسارًا", tag, g), 3.5)
for t, tag, g in (("t34", "BEFORE", False), ("t35", "AFTER", True)):
    still(caption(S(t, "d1_videofirst-right_down1"), "Video First — القائمة يمينًا", tag, g), 3.5)

still(card("3. خلفية Poster List", "لوحتان معتمتان بلون الثيم نفسه", []), 3)
still(caption(S("t30", "cs_posterlist_on_down1"), "Poster List — شبه شفافة", "BEFORE", False), 3.5)
still(caption(S("t35", "d1_posterlist_down1"), "Poster List — معتمة", "AFTER", True), 3.5)

still(card("4. البوسترات أثناء التنقل السريع", "تسجيل فعلي ~7 إطارات/ث بالسرعة الحقيقية",
           ["خطوة كل 0.35 ث ثم كل 0.15 ث", "النتيجة: 0 إطار يعرض بوستر قناة سابقة بعد استقرار المؤشر"]), 5)
for d, lab in (("shots/t34/rec_pl_fast", "Poster List - fast navigation 0.35 s/step"), ("shots/t34/rec_pl_vfast", "Poster List - very fast 0.15 s/step")):
    span, n = rec(d, lab); print(d, "%.1f s, %d grabs" % (span, n))

still(card("5. accelAlloc failed", "البوستر كان يُفك بحجمه الكامل (2.1 MB) وذاكرة التسريع 5.4 MB",
           ["الإصلاح: فك البوستر بحجم مكانه على الشاشة (ePicLoad الأصلي)",
            "الفشل في التسلسل نفسه: 31 ← 1", "ذاكرة Enigma2 أثناء التنقل: 168 MB ← 150 MB",
            "وقت المعالج دون تغيير يُذكر، ولا تسرب في الذاكرة"]), 7)

still(card("6. اختبار الانحدار", "0 أخطاء برمجية · 0 أخطاء سكين جديدة · 0 أعطال", ["البوسترات بالحجم الجديد"]), 3)
for t, n, lab in (("t36", "cinemax_infobar", "InfoBar"), ("t36", "cinemax_sib", "SecondInfoBar"), ("t36", "cinemax_eventview", "EventView"),
                  ("t36", "hbo_chsel", "قائمة القنوات Classic"), ("t36", "cinemax_epg", "Graphical EPG"), ("t34", "reg_epg_multi", "Multi EPG"),
                  ("t34", "reg_quickepg", "QuickEPG"), ("t34", "reg_infobareventview", "InfoBarEventView"), ("t34", "reg_eventviewsimple", "EventViewSimple")):
    still(caption(S(t, n), lab, "OK", True), 2.5)

still(card("7. مقترحات EPG", "نماذج ببيانات حقيقية — لم تُنفَّذ، بانتظار اعتمادك",
           ["Graphical Plus · Columns", "Single Cards حُذف: Classic فيه قائمة ولوحة حدث مع بوستر أصلًا"]), 5)
for n, lab, tag in (("graphicalplus_on", "Graphical Plus", "Posters ON"), ("graphicalplus_off", "Graphical Plus", "Posters OFF"),
                    ("columns_on", "Columns", "Posters ON"), ("columns_off", "Columns", "Posters OFF")):
    still(caption(os.path.join(H, "epgmock", "out", n + ".png"), lab + " — نموذج", tag), 4)

still(card("الحالة", "Slot 8 فقط · لا نشر · لا دمج في main",
           ["حركتا EventView محفوظتان: Classic افتراضية، وسطرًا سطرًا خيار", "النسخ الاحتياطية على USB"]), 5)
lst = os.path.join(T, "list.txt"); open(lst, "w").write("".join("file '%s'\n" % s for s in segs))
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", OUT)
print(OUT, os.path.getsize(OUT))
