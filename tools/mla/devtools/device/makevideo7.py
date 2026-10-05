#!/usr/bin/env python3
# Approval video 2026-10-05 midday (Slot 8, build51-build60): Modern 6/6, Minimal 6/6, Columns, PVR on EMC, Feature.
# Numbers on the cards come from the test logs (t53..t60, t54b, t57b); SOAK is filled from t60.log.
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video7_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_models_review_2026-10-05.mp4")
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
def rec(d, label):
    src = os.path.join(H, d); fs = sorted((int(x[:-4]), x) for x in os.listdir(src) if x.endswith(".jpg"))
    lst = os.path.join(T, "c%03d.txt" % len(segs))
    with open(lst, "w") as fh:
        for i, (t, n) in enumerate(fs):
            fh.write("file '%s'\nduration %.4f\n" % (os.path.join(src, n), (fs[i + 1][0] - t) / 1e9 if i + 1 < len(fs) else 0.4))
        fh.write("file '%s'\n" % os.path.join(src, fs[-1][1]))
    o = os.path.join(T, "seg%03d.mp4" % len(segs)); tag = label.replace(":", "\\:").replace("'", "")
    ff("-f", "concat", "-safe", "0", "-i", lst, "-vf", "fps=25,scale=%d:%d,drawtext=fontfile=%s:text='%s':x=w-tw-18:y=12:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8" % (W, HH, FB, tag), *ENC, o)
    segs.append(o); return (fs[-1][0] - fs[0][0]) / 1e9, len(fs)
def binclip(path, t_from, t_to, lab, tag, good=None):
    """EventView description-box framebuffer recording (fbrec2: 480x261 RGB, 5 fps), real timing"""
    d = open(os.path.join(H, path), "rb").read(); w, h, n = struct.unpack("<III", d[6:18]); ts = struct.unpack("<%dd" % n, d[18:18 + 8 * n]); off = 18 + 8 * n
    idx = [i for i in range(n) if t_from <= ts[i] - ts[0] <= t_to]
    lst = os.path.join(T, "b%03d.txt" % len(segs))
    with open(lst, "w") as fh:
        for j, i in enumerate(idx):
            fr = Image.fromarray(np.frombuffer(d[off + i * w * h * 3: off + (i + 1) * w * h * 3], dtype=np.uint8).reshape(h, w, 3))
            fr = fr.resize((w * 2, h * 2), Image.LANCZOS)
            im = Image.new("RGB", (W, HH), BG); im.paste(fr, ((W - fr.width) // 2, 110))
            im = caption_img(im, lab, tag, good); dd = ImageDraw.Draw(im)
            dd.text((24, HH - 44), "t = %.1f s" % (ts[i] - ts[0]), font=f(FR, 22), fill=MUT)
            p = os.path.join(T, "b%03d_%04d.png" % (len(segs), j)); im.save(p)
            dur = (ts[idx[j + 1]] - ts[i]) if j + 1 < len(idx) else 0.4
            fh.write("file '%s'\nduration %.4f\n" % (p, dur))
        fh.write("file '%s'\n" % p)
    o = os.path.join(T, "seg%03d.mp4" % len(segs))
    ff("-f", "concat", "-safe", "0", "-i", lst, "-vf", "fps=25", *ENC, o); segs.append(o)

def C(t, n, lab, tag, good=True, secs=3.2):
    p = S(t, n)
    if os.path.exists(p):
        still(caption(p, lab, tag, good), secs)
    else:
        print("missing", t, n)

still(card("CineView MLA — مراجعة النماذج", "Slot 8 · build51 ← build60 · لقطات فعلية من الرسيفر",
           ["Modern بأقسامه الستة · Minimal بأقسامه الستة", "Columns · Cover Library وModern PVR على EMC", "EventView Feature · الأداء"]), 6)

still(card("1. Modern — 6/6 أقسام", "البطاقات المستديرة · الثيمات · Posters On / Off", ["الاعتماد البصري النهائي لك"]), 4)
C("t57", "ib_navy_on", "InfoBar", "ON"); C("t57", "ib_navy_off", "InfoBar — بلا بوستر", "OFF")
C("t57b", "sib_navy_on_hbo", "SecondInfoBar — NOW / NEXT", "ON"); C("t57b", "sib_green_off", "SecondInfoBar — بلا بوستر (green)", "OFF")
C("t57", "cs_navy_on_down1", "قائمة القنوات — البطاقة تتبع المؤشر", "ON"); C("t57", "cs_navy_off_open", "قائمة القنوات — بلا بوستر", "OFF")
C("t57", "cs_green_on_open", "قائمة القنوات — green", "THEME", None)
C("t57", "epg_navy_on_right", "EPG", "ON"); C("t57", "epg_navy_off_open", "EPG — بلا بوستر", "OFF")
C("t65", "ev_on_784", "EventView المباشر — شعار القناة في مكان ثابت", "ON"); C("t65", "ev_off_784", "EventView المباشر — بلا بوستر", "OFF")
C("t57", "ev_navy_on_simple", "EventView من الدليل", "ON"); C("t57", "ev_navy_on_infobar", "InfoBarEventView", "ON")
C("t61", "emc_modern_navy_on_down2", "PVR على EMC (زر PVR) — Modern", "ON"); C("t61", "emc_modern_off_down2", "PVR على EMC — بلا غلاف", "OFF")
C("t61", "ms_modern_on_down1", "MovieSelection الأصلي — Modern", "ON")

still(card("الأداء — accelAlloc", "السبب: أسطح البوسترات الكبيرة في Modern (240×360 · 300×450 · 400×600)",
           ["بلا بوسترات: 0 تحذير في كل الشاشات", "مع البوسترات: ينتقل البوستر إلى الذاكرة العادية — لم يُفقد أي بوستر",
            "Modern 25 دقيقة: الذاكرة ثابتة ~152 MB · المعالج ثابت · بلا أعطال", "القرار لك: قبول، أو تصغير بوسترات Modern"]), 7)

still(card("2. Minimal — 6/6 أقسام", "بلا بطاقات · طباعة ومسافات · لون إبراز واحد · نص فوق طبقة لونية ثابتة",
           ["الاعتماد البصري النهائي لك"]), 4.5)
for n, lab in (("ib", "InfoBar"), ("sib", "SecondInfoBar"), ("cs", "قائمة القنوات"), ("epg", "EPG"), ("ev", "EventView المباشر"), ("emc", "PVR على EMC"), ("ms", "MovieSelection")):
    on = n + "_navy_on" + ("_live" if n == "ev" else "") + ("_down2" if n == "emc" else "") + ("_down1" if n == "ms" else "")
    off = n + "_navy_off" + ("_live" if n == "ev" else "") + ("_down2" if n == "emc" else "") + ("_down1" if n == "ms" else "")
    C("t63", on, "Minimal — " + lab, "ON", True, 3)
    C("t63", off, "Minimal — " + lab + " — بلا بوستر", "OFF", True, 3)
C("t63", "ev_navy_on_simple", "Minimal — EventView من الدليل", "ON")
for t in ("black", "burgundy", "graphite", "green", "purple"):
    C("t63", "sib_%s_on" % t, "Minimal SecondInfoBar — ثيم " + t, "THEME", None, 2)
for t in ("burgundy", "green"):
    C("t63", "cs_%s_on" % t, "Minimal قائمة القنوات — ثيم " + t, "THEME", None, 2)

still(card("3. Columns", "على Vertical EPG الأصلي في OpenATV", ["بطاقة الحدث تتبع العمود والحدث · بلا التفاف يفسد الأعمدة"]), 4)
C("t58", "col_navy_on_open", "Columns", "ON"); C("t58", "col_navy_on_right2_down1", "يمين ثم أسفل", "ON"); C("t58", "col_burgundy_off_down3", "بلا بوستر — burgundy", "OFF")

still(card("4. PVR — Cover Library على EMC", "زر PVR يفتح EMC: الشاشة صُممت على عناصر EMC الحقيقية",
           ["الغلاف: صورة بجانب التسجيل ← بحث بعنوان التسجيل ← الصورة الافتراضية", "Classic يترك EMC بشكله الأصلي (fallback آمن) · مجلد USB فقط"]), 6)
for n, lab, tag in (("emc_cover_navy_on_down1", "Harry Potter — غلاف محلي بجانب التسجيل", "ON"), ("emc_cover_navy_on_down2", "Ples malog pingvina — من عنوان التسجيل", "ON"),
                    ("emc_cover_navy_on_down3", "Dnevnik — برنامج عام: الصورة الافتراضية", "ON"), ("emc_cover_off_down1", "بلا غلاف — قائمة عريضة", "OFF"),
                    ("ms_cover_on_down1", "MovieSelection الأصلي — Cover Library", "ON"), ("emc_classic_down1", "Classic — EMC بشكله الأصلي", "FALLBACK")):
    C("t61", n, lab, tag)

still(card("5. Cinema — EventView Feature", "الوصف كان فارغًا: طبقة التعتيم فوق نص ScrollLabel", ["أُصلحت (build60) · أداة الفحص تكشفها الآن"]), 5)
for n, lab, tag in (("ev_feature_navy_on_live", "Feature — INFO المباشر", "ON"), ("ev_feature_navy_on_simple", "Feature — من الدليل", "ON"),
                    ("ev_feature_burgundy_off_simple", "Feature — بلا بوستر", "OFF"), ("ev_feature_navy_on_infobar", "Feature — InfoBarEventView", "ON")):
    C("t64b", n, lab, tag)

still(card("بانتظار قرارك", "لا نشر ولا دمج في main",
           ["الاعتماد البصري: Modern · Minimal · Columns · Cover Library · Feature", "accelAlloc في Modern: قبول أو تصغير البوسترات"]), 6)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB")
