#!/usr/bin/env python3
# Night video 2026-10-05/06 (Slot 8, build71 -> build77 = rc7): accelAlloc per source (t81a/t81b/t83), PIL poster sizing A/B,
# No Poster layout (t82, t84), Classic EventView picon fix, rc7 install test (t77_rc7). Numbers on the cards come from the logs.
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video8_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_night_run_2026-10-06.mp4")
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
    rtext(d, W - 80, 170, title, f(FB, 44), TXT); rtext(d, W - 80, 245, sub, f(FR, 27), ACC)
    for i, ln in enumerate(lines): rtext(d, W - 80, 320 + i * 44, ln, f(FR, 24), MUT)
    return im
def tagbox(d, tag, good):
    col = {True: (60, 170, 110), False: (200, 70, 60)}.get(good, ACC)
    tw = d.textlength(tag, font=f(FB, 24)); d.rounded_rectangle([24, 11, 24 + tw + 28, 49], 9, fill=col + (255,)); d.text((38, 14), tag, font=f(FB, 24), fill=(255, 255, 255))
def caption_img(im, lab, tag, good=None):
    im = im.convert("RGB").resize((W, HH)); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, W, 58], fill=(8, 20, 38, 230)); d.rectangle([0, 58, W, 61], fill=ACC + (255,))
    rtext(d, W - 24, 12, lab, f(FB, 27), TXT); tagbox(d, tag, good); return im
S = lambda t, n: os.path.join(H, "shots", t, n + ".png")
def caption(p, lab, tag, good=None): return caption_img(Image.open(p), lab, tag, good)
def strip(p, box, lab, tag, good=None):
    """a horizontal band of a grab (e.g. the InfoBar) centred on a dark card"""
    src = Image.open(p).convert("RGB").crop(box); k = min((W - 40) / src.width, (HH - 140) / src.height)
    src = src.resize((int(src.width * k), int(src.height * k)))
def C(t, n, lab, tag, good=True, secs=3.2):
    p = S(t, n)
    if os.path.exists(p):
        still(caption(p, lab, tag, good), secs)
    else:
        print("missing", t, n)


def fit(p, lab, tag, good=True, secs=4.0):
    """a whole grab / sheet that is not 16:9 (A/B sheets), centred on a dark card"""
    if not os.path.exists(p):
        print("missing", p); return
    src = Image.open(p).convert("RGB"); k = min((W - 40) / src.width, (HH - 90) / src.height)
    src = src.resize((int(src.width * k), int(src.height * k)), Image.LANCZOS)
    im = Image.new("RGB", (W, HH), BG); im.paste(src, ((W - src.width) // 2, 70 + (HH - 70 - src.height) // 2))
    still(caption_img(im, lab, tag, good), secs)


def log(n):
    p = os.path.join(H, n)
    return open(p, errors="replace").read() if os.path.exists(p) else ""


def shares(n):
    import re
    t = log(n); d = {}
    for m in re.finditer(r"^\s+share\s+([\d.]+) %\s+(\d+)\s+(.+?)\s*$", t, re.M):
        k = "cv" if m.group(3).startswith("CineView") else ("picon" if "picon" in m.group(3) else "other")
        d[k] = int(m.group(2))
    return d


a, b, c = shares("t81a.log"), shares("t81b.log"), shares("t83.log")
tot = lambda d: sum(d.values())

still(card("CineView MLA — تقرير الليل", "Slot 8 · build71 ← build77 = rc7 · لقطات فعلية من الرسيفر",
           ["مصدر كل تحذير accelAlloc · إصلاح نصيب CineView", "تخطيط No Poster بدل الصورة البديلة في كل النماذج", "rc7: ترقية واختبار النماذج الخمسة من الحزمة المثبتة"]), 6)

still(card("1. accelAlloc — مصدر كل تحذير", "نفس الجولات الثماني ونفس ترتيب القنوات",
           ["CineView (أول فك للبوستر): %d ← %d ← %d" % (a.get("cv", 0), b.get("cv", 0), c.get("cv", 0)),
            "ذاكرة شعارات القنوات في Enigma2: %d ← %d ← %d" % (a.get("picon", 0), b.get("picon", 0), c.get("picon", 0)),
            "سطح Enigma2 عند الإقلاع: %d ← %d ← %d" % (a.get("other", 0), b.get("other", 0), c.get("other", 0)),
            "المجموع: %d (build71) ← %d (rc6 مثبتة) ← %d (build75)" % (tot(a), tot(b), tot(c))]), 8)
still(card("السبب في CineView", "ePicLoad.getData() يحجز نتيجته دائمًا في الذاكرة السريعة (picload.cpp:1348)",
           ["الإصلاح: نسخة بمقاس العنصر تُصنع بـ PIL من الملف الأصلي", "نفس المقاس ونفس التأطير ونفس الحواف السوداء — تُعرض من الذاكرة العادية",
            "الملف الأصلي لا يُعاد كتابته · المتبقي كله من Enigma2 نفسه"]), 7)
fit(S("t83", "AB_0"), "نفس البوستر: يسار ePicLoad · يمين PIL (أقل PSNR)", "A/B", None, 4)
fit(S("t83", "AB_1"), "نفس البوستر: يسار ePicLoad · يمين PIL", "A/B", None, 3.5)
fit(S("szcmp", "szcmp2"), "تكبير: نفس الإطار — PIL أوضح في النصوص الصغيرة", "A/B", None, 4.5)

still(card("2. No Poster — التخطيط الحقيقي بدل الصورة البديلة", "البوسترات مفعّلة: حدث بلا بوستر يأخذ ترتيب الشاشة بدون بوستر لحظتها",
           ["HBO HD: فيلم له بوستر · HRT1: أخبار بلا بوستر", "58 شاشة ديناميكية + شاشات EventView المسماة عند فتحها",
            "t82 + t84: صفر traceback · صفر أخطاء skin · صفر crash"]), 7)
MODELS = (("modern", "Modern"), ("cinema", "Cinema"), ("details", "Details"), ("minimal", "Minimal"), ("classic", "Classic"))
for m, lab in MODELS:
    still(card(lab, "مع بوستر ← بدون بوستر", []), 2.2)
    C("t84", m + "_ib_hbo", lab + " — InfoBar · HBO", "POSTER", True, 2.6); C("t84", m + "_ib_hrt1", lab + " — InfoBar · HRT1", "NO POSTER", True, 2.6)
    C("t82", m + "_hbo_sib", lab + " — SecondInfoBar · HBO", "POSTER", True, 2.8); C("t82", m + "_hrt1_sib", lab + " — SecondInfoBar · HRT1", "NO POSTER", True, 2.8)
    C("t82", m + "_hbo_ev", lab + " — EventView · HBO", "POSTER", True, 2.8); C("t82", m + "_hrt1_ev", lab + " — EventView · HRT1", "NO POSTER", True, 2.8)
    C("t82", m + "_hbo_cs", lab + " — قائمة القنوات · HBO", "POSTER", True, 2.8); C("t82", m + "_hrt1_cs", lab + " — قائمة القنوات · HRT1", "NO POSTER", True, 2.8)
    C("t84", m + "_epg_hbo", lab + " — EPG · HBO", "POSTER", True, 2.8); C("t84", m + "_epg_hrt1", lab + " — EPG · HRT1", "NO POSTER", True, 2.8)
    C("t84", m + "_emc_2", lab + " — EMC · Harry Potter (غلاف محلي)", "POSTER", True, 2.6); C("t84", m + "_emc_4", lab + " — EMC · Dnevnik (أخبار)", "NO POSTER", True, 2.6)
    C("t84", m + "_ms_1", lab + " — MovieSelection · Ples malog pingvina", "POSTER", True, 2.6); C("t84", m + "_ms_3", lab + " — MovieSelection · ملف اختبار", "NO POSTER", True, 2.6)

still(card("3. Classic — شعار القناة في شريط EventView", "كان مفقودًا (حتى في لقطات t68 المعتمدة) وأحيانًا يظهر الشعار الافتراضي",
           ["السبب: Picon الأصلي يتجاهل أول تحديث للشاشة ويُظهر نفسه عند كل تحميل", "الإصلاح في المحوّل الخاص بنا فقط — بلا تعديل في Enigma2"]), 6)
for n, lab in (("784", "HBO HD — مع بوستر"), ("786", "Cinemax HD — مع بوستر"), ("D49", "HRT1 — بدون بوستر")):
    p = S("t84", "classic_ev_" + n)
    if os.path.exists(p):
        still(strip(p, (0, 800, 1920, 1080), "Classic EventView — " + lab, "FIXED", True), 3)

still(card("4. الحزمة المرشحة 1.0.0~rc7 (ليست نهائية)", "build77 · SHA256 6d752cf8…afbca6 · منشورة على dev/mla-openatv",
           ["t77_rc7: ترقية rc6 ← rc7 · النماذج الخمسة من الحزمة المثبتة", "صفر traceback · صفر أخطاء skin · صفر crash",
            "المثبّت لا يكتب على HDD إلا مع HDD_CACHE=1"]), 7)
for m, lab in (("classic", "Classic"), ("details", "Details"), ("cinema", "Cinema"), ("modern", "Modern"), ("minimal", "Minimal")):
    C("t77_rc7", m + "_sib", "rc7 مثبتة — " + lab + " · SecondInfoBar", "rc7", True, 2.6)

still(card("بانتظار قرارك", "لا إصدار نهائي ولا دمج في main",
           ["الاعتماد البصري لتخطيطات No Poster ووضوح بوسترات PIL", "مخرجات diag-mla.sh من جهاز DM900", "اختبار ذاكرة البوستر على HDD — بعد موافقتك فقط"]), 7)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
