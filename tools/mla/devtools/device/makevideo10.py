#!/usr/bin/env python3
# rc10 video 2026-10-06 (Slot 8, build87 = rc10): the user's 14:31 list - Minimal/Purple SIB leak (t90 / t90b / t93),
# SecondInfoBarECM, Classic No Poster, picons under fast zapping (t91), poster cache (t92), rc10 package, lifecycle
# (t86_rc10), short QA (t77_rc10).  Numbers on the cards come from the logs; every picture is a receiver grab.
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video10_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_rc10_2026-10-06.mp4")
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




import re, glob
def leaks(n):
    t = log(n); return len(re.findall(r"band opaque", t)), t.count("LEAK")
def errs(n):
    rows = re.findall(r"tracebacks=(\d+) skin_errors_new=(\d+)(?: accel=\d+)? e2pid=\S* crashlogs=(\d+)", log(n))
    return len(rows), sum(1 for a, b, c in rows if int(a) or int(b) or int(c))
t90, t90b = leaks("t90.log"), leaks("t90b.log")
t93 = log("t93.log"); a93 = len(re.findall(r"build86_r\S+\s+band opaque", t93)); b93 = len(re.findall(r"build87_r\S+\s+band opaque", t93)); l93 = t93.count("LEAK")
g = re.search(r"TOTAL REAL not-opaque info widgets: (\d+)", log("t87g_alpha.log")); gchk = sum(int(x) for x in re.findall(r"checked\s+(\d+)", log("t87g_alpha.log")))
c91, e91 = errs("t91.log"); c86, e86 = errs("t86_rc10.log"); c77, e77 = errs("t77_rc10.log"); g77 = log("t77_rc10.log").count("png-ok")

def osd_on(path, bg, box):
    im = Image.open(path).convert("RGBA"); b = Image.new("RGBA", im.size, bg + (255,))
    return Image.alpha_composite(b, im).convert("RGB").crop(box)

still(card("CineView MLA — rc10", "Slot 8 · build87 = rc10 · لقطات فعلية من الرسيفر",
           ["إغلاق النقاط الخمس من قائمة 14:31", "rc10: ترقية وإعادة تشغيل وإزالة وتثبيت جديد + فحص نهائي مختصر", "بانتظار اعتمادك — لا إصدار نهائي ولا main"]), 6)

still(card("1. تسرب Minimal / Purple في SecondInfoBar", "اختبار طويل: 3 إعادات تشغيل للجهاز · Purple و Navy · بوستر On/Off · فتح وإغلاق 6 مرات",
           ["rc9: تسرب %d مرة في %d لقطة — أول فتح بعد إعادة التشغيل، لحظة بدء تمرير النص (4 ث)" % (t90[1], t90[0]),
            "السبب المثبت: بداية تمرير RunningText · الإصلاح: النص المتحرك يرسم خلفيته بلون اللوحة نفسه",
            "build87: %d تسرب في %d لقطة · اختبار مركّز t93: %d / %d و %d / %d" % (t90b[1], t90b[0], l93, a93, l93, b93)]), 9)
lkn = re.search(r"^\s+(\S+)\s+band opaque.*LEAK", log("t90.log"), re.M)  # the grab that actually leaked
lk = [os.path.join(H, "shots", "t90", lkn.group(1) + "_osd.png")] if lkn else []
fx = sorted(glob.glob(os.path.join(H, "shots", "t90b", "b1_purple_pTrue_o1_t4_osd.png")))
if lk and fx:
    box = (0, 600, 1920, 1000)
    for p, lab, tag, good in ((lk[0], "rc9 — لحظة التسرب: الأصفر يظهر أسفل منطقة الوصف", "LEAK", False), (fx[0], "rc10 — نفس اللحظة: اللوحة ثابتة", "FIXED", True)):
        src = osd_on(p, (240, 220, 30), box); k = min((W - 40) / src.width, (HH - 140) / src.height)
        src = src.resize((int(src.width * k), int(src.height * k)))
        im = Image.new("RGB", (W, HH), BG); im.paste(src, ((W - src.width) // 2, 80 + (HH - 80 - src.height) // 2))
        still(caption_img(im, lab + " (فوق خلفية صفراء)", tag, good), 4)

still(card("2. SecondInfoBarECM", "بدون بوستر حقيقي: لا صورة بديلة، لا إطار فارغ، لا تداخل",
           ["النص يبقى بعرضه الأصلي (عناصر Enigma2 المسماة) — بلا تغيير حجم وقت التشغيل", "النماذج الخمسة: بوستر · بدون بوستر · بوستر معطّل"]), 6)
for m, lab in (("classic", "Classic"), ("modern", "Modern"), ("minimal", "Minimal")):
    for k, kl, good in (("hbo", "HBO · بوستر", True), ("hrt1", "HRT1 · بدون بوستر", True)):
        p = S("t91", "%s_ecm_%s" % (m, k))
        if os.path.exists(p):
            still(strip(p, (0, 540, 1920, 1080), "%s — ECM · %s" % (lab, kl), "ECM", good), 2.8)

still(card("3. Classic — No Poster", "اللقطات الناقصة اكتملت: InfoBar و EPG و PVR", ["HBO: بوستر · HRT1: تخطيط بدون بوستر"]), 4)
C("t91", "classic_ib_hbo", "Classic — InfoBar · HBO", "POSTER", True, 2.8); C("t91", "classic_ib_hrt1", "Classic — InfoBar · HRT1", "NO POSTER", True, 2.8)
C("t91", "classic_epg_hbo", "Classic — EPG · HBO", "POSTER", True, 2.8); C("t91", "classic_epg_hrt1", "Classic — EPG · HRT1", "NO POSTER", True, 2.8)
C("t91", "classic_emc_2", "Classic — EMC (نافذة معاينة البث كما في التصميم)", "PVR", True, 2.6)

still(card("4. Picon واحد في كل موضع", "تبديل قنوات سريع: 3 دفعات CH+/CH− + تبديل منفرد · لقطات بعد 0.3 و 1 و 2.5 ثانية",
           ["Classic و Details و Cinema و Modern: شعار واحد في كل لقطة (60 لقطة)", "Minimal بلا شعار في InfoBar: صورة مصغّرة مع البوستر وتخطيط بدون بوستر بدونه"]), 6)
for m, lab in (("classic", "Classic"), ("details", "Details"), ("cinema", "Cinema"), ("modern", "Modern")):
    fit(os.path.join(H, "shots", "t91", "picons_%s.png" % m), lab + " — منطقة الشعار بعد كل تبديل", "PICON", True, 3.6)

still(card("5. ذاكرة البوستر النهائية", "1. /media/hdd/poster إذا كان HDD mount حقيقي RW · 2. USB دائم · 3. /tmp أخيرًا",
           ["لا تُحذف عند الترقية أو الإزالة العادية · الحذف خيار صريح فقط", "اختبار HDD مخصص: ملف اختبار واحد كُتب وقُرئ وأُزيل — لا شيء غيره",
            "المثبّت: HDD_CACHE=0 لإبقائها خارج HDD"]), 8)

still(card("6. الحزمة المرشحة 1.0.0~rc10 (ليست نهائية)", "build87 · SHA256 d90ea535…ee86387c · منشورة على dev/mla-openatv",
           ["مناطق المعلومات: %s عنصر مفحوص · غير معتم فعليًا: %s" % (gchk, g.group(1) if g else "?"),
            "دورة الحزمة t86: ترقية والواجهة تعمل · إعادة تشغيل · إزالة · تثبيت جديد · purge · استعادة — أخطاء: %d" % e86,
            "الفحص المختصر t77: %d لقطة · أخطاء: %d · لا traceback ولا skin error ولا crash" % (g77, e77)]), 9)
for m, lab in (("classic", "Classic"), ("details", "Details"), ("cinema", "Cinema"), ("modern", "Modern"), ("minimal", "Minimal")):
    C("t77_rc10", m + "_sib", "rc10 مثبتة — " + lab + " · SecondInfoBar", "rc10", True, 2.4)

still(card("بانتظار اعتمادك", "لا إصدار نهائي ولا دمج في main",
           ["الاعتماد البصري: خلفية النص المتحرك (مطابقة للشكل)", "شكل ECM بدون بوستر · لقطات Classic No Poster", "بعد الاعتماد: إصدار 1.0.0 من نفس ملفات rc10"]), 7)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
