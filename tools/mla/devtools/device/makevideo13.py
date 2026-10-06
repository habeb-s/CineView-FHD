#!/usr/bin/env python3
# Final 1.0.0 video 2026-10-06: build88 - plugin icon A, rights + version line, light protection (.pyc by the receiver's
# Python 3.14, version.json).  Motion = the receiver's own frames recorded by t95; numbers from t95.log.
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video13_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_1.0.0_final_2026-10-06.mp4")
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
L = log("t95.log")
L2 = ""
F = os.path.join(H, "shots", "t95_final100b", "frames")
def errs():
    rows = re.findall(r"tracebacks=(\d+) skin_errors_new=(\d+)(?: accel=\d+)? e2pid=\S* crashlogs=(\d+)", L + L2)
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


chk, bad = errs()
pl = re.findall(r"plugin load errors: (\d+)", L)
py = re.findall(r"\.py left in plugin / components: (\d+)", L); pc = re.findall(r"CineViewMLA \.pyc: (\d+)", L)
ex = re.findall(r"exit (\d+)", L)
still(card("CineView MLA 1.0.0 — اللمسات الأخيرة", "build88 · الحزمة النهائية 1.0.0 · SHA256 622c69b0…bb502545",
           ["أيقونة البلجن والشعار: الخيار A المعتمد", "الحقوق: Design & Development by habeb-s © 2026 — في CineView Designs وبيانات البلجن فقط",
            "حماية خفيفة: ملفات Python الحساسة ‎.pyc‎ (Python 3.14 الخاص بالرسيفر) · version.json · بلا تشفير ولا تفعيل"]), 8)
still(card("1. التثبيت والواجهة تعمل", "opkg أزال ملفات ‎.py‎ القديمة وثبّت ‎.pyc‎",
           ["ملفات CineViewMLA ‎.pyc‎: %s" % (pc[0] if pc else "?"), "أخطاء تحميل البلجنات: %s" % (pl[0] if pl else "?"),
            "ملف ‎.py‎ متبقٍ واحد: CineViewMLAPicon.py من نشر تطوير قديم — ليس في الحزمة ولا يستخدمه أي سكين (نُقل للنسخة الاحتياطية)"]), 7)
motion("3_pluginbrowser", "Plugin Browser — أيقونة CineView Designs الجديدة (A)", "ICON", 3)
motion("3_cineviewdesigns", "CineView Designs — سطر الإصدار والحقوق أسفل الحالة", "RIGHTS", 4)
P = os.path.join(H, "shots", "t95_final100b", "3_cineviewdesigns.png")
if os.path.exists(P):
    still(strip(P, (0, 860, 960, 1000), "تكبير — CineView MLA 1.0.0 · build88 · Design & Development by habeb-s © 2026", "RIGHTS", True), 4)
P = os.path.join(H, "shots", "t95_final100b", "3_pluginbrowser.png")
if os.path.exists(P):
    still(strip(P, (1040, 100, 1400, 280), "تكبير — الأيقونة في Plugin Browser", "ICON", True), 3.5)
still(card("2. مرور سريع على النماذج الخمسة", "المحوّلات والمعرِضات الآن ‎.pyc‎", ["InfoBar · SecondInfoBar · قائمة القنوات"]), 3.5)
for m, lab in (("classic", "Classic"), ("details", "Details"), ("cinema", "Cinema"), ("modern", "Modern"), ("minimal", "Minimal")):
    motion("4_%s_1ib" % m, lab + " — InfoBar", "1.0.0", 3)
    motion("4_%s_2sib" % m, lab + " — SecondInfoBar", "1.0.0", 5)
    motion("4_%s_3cs" % m, lab + " — قائمة القنوات", "1.0.0", 4)
still(card("3. إعادة تشغيل الجهاز", "Slot 8", ["بعد الإقلاع: Plugin Browser و CineView Designs"]), 3)
motion("5_pluginbrowser", "بعد إعادة التشغيل — Plugin Browser", "REBOOT", 3)
motion("5_cineviewdesigns", "بعد إعادة التشغيل — CineView Designs", "REBOOT", 4)
still(card("النتيجة", "1.0.0 النهائي على Slot 8 · Classic Navy",
           ["فحوص الأخطاء: %d · فيها traceback أو skin error أو crash: %d" % (chk, bad),
            "فحص Python: نسخة 3.12 وهمية → رفض (exit %s) · Python الحقيقي → قبول (exit %s)" % (ex[0] if ex else "?", ex[1] if len(ex) > 1 else "?"),
            "المتبقي: النشر و main بعد موافقتك"]), 8)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
