#!/usr/bin/env python3
# Stage B video 2026-10-06: the 1.0.0 package (= build87 / rc10 files, version only) - upgrade with the GUI running,
# reboot, quick five-model pass.  Motion parts are the receiver's own frames (grab jpg) recorded by t94, played at the
# rate they were captured; cards carry build / commit / change / test / what remains (numbers from t94.log).
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video12_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_1.0.0_stageB_2026-10-06.mp4")
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
L = log("t94.log")
F = os.path.join(H, "shots", "t94_final100", "frames")
def errs():
    rows = re.findall(r"tracebacks=(\d+) skin_errors_new=(\d+)(?: accel=\d+)? e2pid=\S* crashlogs=(\d+)", L)
    return len(rows), sum(1 for a, b, c in rows if int(a) or int(b) or int(c))
def motion(prefix, lab, tag, secs):
    fs = sorted(glob.glob(os.path.join(F, prefix + "_*.jpg")))
    if not fs:
        print("missing frames", prefix); return
    d = os.path.join(T, "m%03d" % len(segs)); os.makedirs(d)
    for i, f in enumerate(fs):
        caption_img(Image.open(f), lab, tag, True).save(os.path.join(d, "f%04d.png" % i))
    rate = max(1.0, len(fs) / float(secs))
    o = os.path.join(T, "seg%03d.mp4" % len(segs))
    ff("-framerate", "%.3f" % rate, "-i", os.path.join(d, "f%04d.png"), "-vf", "scale=%d:%d,fps=25" % (W, HH), *ENC, o); segs.append(o)
    print("motion", prefix, len(fs), "frames at %.1f fps" % rate)

ver = re.findall(r"package: Version: (\S+)", L)
slots = re.findall(r"boot: (rootsubdir=\S+)", L)
chk, bad = errs()
sha = "33ac3843…c007a8"
still(card("CineView MLA 1.0.0 — المرحلة B", "الحزمة 1.0.0 = ملفات build87 / rc10 نفسها · commit bf30b71 · SHA256 " + sha,
           ["ما تغيّر: رقم الإصدار فقط (rc10 ← 1.0.0) · محتوى الحزمة مطابق بايتًا بايتًا (590 ملفًا) والسكربتات مطابقة",
            "الاختبار: ترقية والواجهة تعمل · إعادة تشغيل الجهاز · مرور سريع على النماذج الخمسة",
            "إطارات حقيقية من الرسيفر أثناء الاختبار"]), 8)
still(card("1. الترقية rc10 ← 1.0.0 والواجهة تعمل", "Modern محدد قبل الترقية",
           ["الإصدار بعد الترقية: %s" % (ver[2] if len(ver) > 2 else "?"), "التصميم المحدد بقي Modern"]), 4)
motion("1_upgrade_modern_ib", "بعد الترقية — Modern · InfoBar (إطارات حقيقية)", "1.0.0", 4)
still(card("2. إعادة تشغيل الجهاز", "Slot 8 فقط", ["الإقلاع: %s" % (", ".join(sorted(set(slots))) or "?")]), 3.5)
motion("2_reboot_modern_ib", "بعد إعادة التشغيل — Modern · InfoBar", "REBOOT", 4)
still(card("3. مرور سريع على النماذج الخمسة", "من الحزمة 1.0.0 المثبتة", ["InfoBar · SecondInfoBar · قائمة القنوات"]), 3.5)
for m, lab in (("classic", "Classic"), ("details", "Details"), ("cinema", "Cinema"), ("modern", "Modern"), ("minimal", "Minimal")):
    motion("3_%s_1ib" % m, lab + " — InfoBar", "1.0.0", 4)
    motion("3_%s_2sib" % m, lab + " — SecondInfoBar", "1.0.0", 6)
    motion("3_%s_3cs" % m, lab + " — قائمة القنوات", "1.0.0", 5)
still(card("النتيجة", "1.0.0 على Slot 8 · Classic Navy",
           ["فحوص الأخطاء: %d · فيها traceback أو skin error أو crash: %d" % (chk, bad),
            "المتبقي: المرحلة C فقط — النشر و main بعد موافقتك الصريحة"]), 7)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
