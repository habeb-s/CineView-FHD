#!/usr/bin/env python3
# Classic PVR video 2026-10-06 19:35 (no new test): the t91 grabs of build87 = rc10 - Classic EMC and native MovieSelection,
# HBO recording vs HRT1 news; the top-left box is EMC's / MovieSelection's LIVE-TV window, not a poster area.
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video11_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_Classic_PVR_2026-10-06.mp4")
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





def zoom(p, box, lab, tag, good, secs):
    if os.path.exists(p):
        still(strip(p, box, lab, tag, good), secs)
    else:
        print("missing", p)

still(card("Classic — PVR / EMC", "لقطات من ملفات rc10 نفسها (t91) · بدون اختبار جديد",
           ["تسجيل HBO بملصق مقابل تسجيل HRT1 الإخباري", "ما هي المساحة أعلى اليسار؟"]), 5)
C("t91", "classic_emc_3", "Classic — EMC · تسجيل HBO: Ples malog pingvina", "HBO", None, 3.5)
C("t91", "classic_emc_4", "Classic — EMC · تسجيل HRT1 الإخباري: Dnevnik", "HRT1", None, 3.5)
S91 = lambda n: os.path.join(H, "shots", "t91", n + ".png")
zoom(S91("classic_emc_3"), (40, 80, 700, 560), "تكبير — HBO محدد: المربع يعرض البث المباشر", "LIVE", None, 3.5)
zoom(S91("classic_emc_4"), (40, 80, 700, 560), "تكبير — HRT1 محدد: نفس المربع، نفس البث المباشر", "LIVE", None, 3.5)
C("t91", "classic_ms_2", "Classic — MovieSelection الأصلي · Dnevnik", "HRT1", None, 3.2)
C("t91", "classic_ms_3", "Classic — MovieSelection الأصلي · ملف الاختبار", "TEST", None, 3.2)

still(card("النتيجة", "المربع أعلى اليسار نافذة بث مباشر (PiG) وليس مكان ملصق",
           ["EMC في Classic يستخدم سكين EMC الأصلي: render=Pig للبث المباشر", "MovieSelection في Classic يستخدم PigTemplate: بث مباشر أيضًا",
            "لا ملصق ولا صورة بديلة في Classic PVR مع أي تسجيل"]), 8)
still(card("خياران لقرارك", "لم يُنفّذ أي تعديل",
           ["1. اعتماد Classic PVR كما هو: معاينة مباشرة بلا ملصق — 1.0.0 جاهز على rc10",
            "2. إضافة مربع ملصق لـ Classic: شاشة EMC خاصة بـ CineView — ملصق لـ HBO ومربع فارغ للأخبار",
            "الخيار 2 تغيير في تصميم Classic: build جديد + اختبار قصير + RC جديد"]), 9)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
