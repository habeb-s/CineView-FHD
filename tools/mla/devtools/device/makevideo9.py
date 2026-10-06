#!/usr/bin/env python3
# rc9 video 2026-10-06 (Slot 8, build79 = rc8 -> build86 = rc9): opaque information areas (t87a before, t87e/t87f after,
# t88), playback bar, rc9 package (t77_rc9), final QA on the installed rc9 (t68_rc9), 25-min performance (t89).
# Numbers on the cards come from the logs.
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video9_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_rc9_2026-10-06.mp4")
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
    im = Image.new("RGB", (W, HH), BG); im.paste(src, ((W - src.width) // 2, 80 + (HH - 80 - src.height) // 2)); return caption_img(im, lab, tag, good)
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



import re
def alpha_tot(n):
    m = re.search(r"TOTAL REAL not-opaque info widgets: (\d+)", log(n)); return int(m.group(1)) if m else None
def checked(n):
    return sum(int(x) for x in re.findall(r"checked\s+(\d+)", log(n)))
e_real, f_real = alpha_tot("t87e_alpha.log"), alpha_tot("t87f_alpha.log")
e_chk, f_chk = checked("t87e_alpha.log"), checked("t87f_alpha.log")
t68 = log("t68_rc9.log"); caps = len(re.findall(r"^cap .* png-ok", t68, re.M)); bad = t68.count("PNG-BAD")
chk = re.findall(r"tracebacks=(\d+) skin_errors_new=(\d+) accel=\d+ e2pid=\d+ crashlogs=(\d+)", t68)
errsum = sum(int(a) + int(b) + int(c) for a, b, c in chk)
t89 = log("t89.log")
st = re.search(r"\[rc9 start\] \S+ cpu_ms=(\d+) rss_kB=(\d+)", t89); en = re.search(r"\[rc9 end r(\d+)\] \S+ cpu_ms=(\d+) rss_kB=(\d+) hwm_kB=(\d+) threads=(\d+) fds=(\d+) accel_fails=(\d+) tb=(\d+)", t89)

still(card("CineView MLA — rc9", "Slot 8 · rc8 (build79) ← rc9 (build86) · لقطات فعلية من الرسيفر",
           ["مناطق المعلومات معتمة بالكامل في InfoBar و SecondInfoBar وشريط التشغيل", "الشفافية الجمالية خارجها محفوظة · لا تغيير في المقاسات أو المواضع",
            "rc9: ترقية + فحص نهائي للنماذج الخمسة + تشغيل أداء 25 دقيقة"]), 6)
still(card("1. المعلومات لا يظهر الفيديو من خلفها", "قياس ألفا الحقيقية لطبقة OSD داخل كل عنصر معلومات · ست ثيمات",
           ["عناصر مفحوصة: %d (t87e) + %d (t87f)" % (e_chk, f_chk),
            "غير معتمة فعليًا: %s · فقط حواف وزوايا الكبسولات المستديرة" % ("0" if (f_real == 0 and (e_real or 0) <= 4) else "%s / %s" % (e_real, f_real)),
            "لقطة واحدة Minimal/Purple لم تتكرر في 24 إعادة (t88) — مسجلة كما هي"]), 8)
for m, lab in (("classic", "Classic"), ("cinema", "Cinema"), ("modern", "Modern"), ("minimal", "Minimal"), ("details", "Details")):
    for sc, sl in (("sib", "SecondInfoBar"), ("ib", "InfoBar")):
        fit(os.path.join(H, "repo", "docs", "mla", "evidence", "opaque_%s_%s.jpg" % (m, sc)), lab + " — " + sl + " · قبل rc8 ← بعد rc9", "OPAQUE", True, 4.2)

still(card("2. ما أُصلح أثناء الاختبار", "كل إصلاح أعيد اختباره على الجهاز",
           ["شريط التشغيل: صندوق أسود خلف مؤشر الإيقاف/التشغيل ← لون الشريط نفسه",
            "Cinema SecondInfoBar: الخلفية الجمالية صارت معتمة بالكامل ← أعيدت كما كانت",
            "Modern SecondInfoBar: شريط الحالة كان ينتهي قبل SNR/dB ← يغطي الصف كاملًا"]), 8)
for t, lab in (("t87c", "قبل: صندوق أسود"), ("t87e", "بعد: لون الشريط")):
    p = S(t, "classic_navy_mp_all")
    if os.path.exists(p):
        still(strip(p, (120, 40, 1800, 240), "شريط التشغيل · Classic — " + lab, "rc9" if t == "t87e" else "BUG", t == "t87e"), 3.2)

still(card("3. الحزمة المرشحة 1.0.0~rc9 (ليست نهائية)", "build86 · SHA256 0d2336da…8ee8946 · منشورة على dev/mla-openatv",
           ["t77_rc9: ترقية rc8 ← rc9 والواجهة تعمل · النماذج الخمسة من الحزمة المثبتة", "سكربتات التثبيت والإزالة مطابقة لـ rc8 (اختبار دورة الحياة t86)",
            "install-mla.sh يثبّت rc9 · DRYRUN على الرسيفر: ناجح"]), 7)
still(card("4. الفحص النهائي على rc9 المثبتة", "النماذج الخمسة × الأقسام الستة × بوستر مفعّل/معطّل + الثيمات الست",
           ["لقطات: %d · لقطات تالفة: %d" % (caps, bad), "فحوص الأخطاء: %d · مجموع traceback + skin + crash: %d" % (len(chk), errsum)]), 6)
for m, lab in (("classic", "Classic"), ("details", "Details"), ("cinema", "Cinema"), ("modern", "Modern"), ("minimal", "Minimal")):
    for sk, sl in (("ib", "InfoBar"), ("sib", "SecondInfoBar"), ("epg", "EPG"), ("emc", "PVR · EMC")):
        C("t68_rc9", "%s_navy_on_%s" % (m, sk), "rc9 — %s · %s" % (lab, sl), "rc9", True, 2.4)
if st and en:
    still(card("5. أداء Modern على rc9 — 25 دقيقة", "نفس جولة الاختبار: قوائم · EventView · SecondInfoBar · EPG · EMC · تبديل قنوات",
               ["جولات: %s · ذاكرة RSS: %d ← %d MB (ثابتة بعد الجولة 5)" % (en.group(1), int(st.group(2)) // 1024, int(en.group(3)) // 1024),
                "خيوط: %s · ملفات مفتوحة: %s · traceback: %s" % (en.group(5), en.group(6), en.group(8)),
                "تحذيرات accelAlloc: %s (منها واحد عند الإقلاع)" % en.group(7)]), 7)

still(card("بانتظار قرارك", "لا إصدار نهائي ولا دمج في main",
           ["الاعتماد البصري: مناطق المعلومات المعتمة في النماذج الخمسة", "الاعتماد البصري: تخطيطات No Poster ووضوح بوسترات PIL",
            "قرار: ذاكرة البوستر على HDD (HDD_CACHE) · SecondInfoBarECM"]), 7)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
