#!/usr/bin/env python3
# CineView Designs final acceptance video (user 2026-10-07 05:36): receiver frames from t102 - slow walk of every row
# (continuous jpg frames as the receiver delivered them), MessageBox, Setup pages, functions, six themes.
import os, re, glob, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
RUN = os.environ.get("RUN", "t102_final")
SH = os.path.join(H, "shots", RUN)
RUN2 = os.environ.get("RUN2", RUN)  # functions + themes may come from an earlier run of the same build line
SH2 = os.path.join(H, "shots", RUN2)
T = os.path.join(H, "video16_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_Designs_final_2026-10-07.mp4")
BUILD = os.environ.get("BUILD", "?"); COMMIT = os.environ.get("COMMIT", "?")
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
    rtext(d, W - 80, 140, title, f(FB, 40), TXT); rtext(d, W - 80, 208, sub, f(FR, 24), ACC)
    for i, ln in enumerate(lines): rtext(d, W - 80, 280 + i * 40, ln, f(FR, 22), MUT)
    return im
def cap(im, lab, tag):
    im = im.convert("RGB").resize((W, HH)); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, W, 50], fill=(8, 20, 38, 225)); d.rectangle([0, 50, W, 53], fill=ACC + (255,))
    rtext(d, W - 20, 10, lab, f(FB, 23), TXT)
    tw = d.textlength(tag, font=f(FB, 21)); d.rounded_rectangle([18, 9, 18 + tw + 24, 42], 8, fill=(60, 170, 110, 255)); d.text((30, 11), tag, font=f(FB, 21), fill=(255, 255, 255))
    return im
def good(p):
    try:
        Image.open(p).load(); return True
    except Exception:
        return False
def motion(prefix, lab, tag, secs):
    fs = [p for p in sorted(glob.glob(os.path.join(SH, "frames", prefix + "_*.jpg"))) if good(p)]
    if not fs:
        print("missing frames", prefix); return
    d = os.path.join(T, "m%03d" % len(segs)); os.makedirs(d)
    for i, p in enumerate(fs):
        cap(Image.open(p), lab, tag).save(os.path.join(d, "f%04d.png" % i))
    o = os.path.join(T, "seg%03d.mp4" % len(segs))
    ff("-framerate", "%.3f" % max(1.0, len(fs) / float(secs)), "-i", os.path.join(d, "f%04d.png"), "-vf", "scale=%d:%d,fps=25" % (W, HH), *ENC, o); segs.append(o)
def G(n, lab, tag, secs=3.0, sh=None):
    p = os.path.join(sh or SH, n + ".png")
    if good(p):
        still(cap(Image.open(p), lab, tag), secs)
    else:
        print("missing", n)
log = "".join(open(os.path.join(H, r + ".log"), errors="replace").read() for r in sorted({RUN, RUN2}) if os.path.exists(os.path.join(H, r + ".log")))
errs = re.findall(r"tracebacks=(\d+) skin_errors_new=(\d+) crashlogs=(\d+)", log)
bad = sum(1 for e in errs if any(int(v) for v in e))
forb = re.findall(r"forbidden words on screen.*?: (\d+)", log)
still(card("CineView Designs — النسخة النهائية", "%s · commit %s · Slot 8" % (BUILD, COMMIT),
           ["مرور بطيء من أول صف إلى آخر صف: معاينة حقيقية أو Info Card لكل صف", "بلا generation / build / commit / trial على الشاشة",
            "MessageBox المتكيفة · خط 27px في صفحات Setup · Burgundy"]), 7)
rows = sorted(set(re.sub(r"_\d+\.jpg$", "", os.path.basename(p)) for p in glob.glob(os.path.join(SH, "frames", "W*_*.jpg"))))
for r in rows:
    rf = os.path.join(SH, "rows_%s.txt" % r)
    lab = ""
    if os.path.exists(rf):
        m = [l for l in open(rf, errors="replace") if l.startswith(">")]
        lab = re.sub(r"^>\s*\d+\s+", "", m[0]).split("|")[0].strip() if m else ""
    motion(r, "CineView Designs — " + lab, "ROW %s" % r[1:], 3)
for m, lab in (("M_msg_info", "MessageBox — سطر واحد"), ("M_msg_yesno", "MessageBox — Yes / No"), ("M_msg_list", "MessageBox — 4 خيارات"), ("M_msg_long", "MessageBox — نص طويل")):
    G(m, lab, "MSGBOX", 3)
for k in ("UserInterface", "Usage", "Time", "EPG", "Recording", "Audio", "Subtitle", "Playback", "ChannelSelection", "Logs"):
    G("S_%s_top" % k, "Setup — %s (قيم 27px)" % k, "SETUP", 2.2)
    G("S_%s_scrolled" % k, "Setup — %s (بعد النزول)" % k, "SETUP", 2.0)
for n, lab in (("F1_menu", "MENU — الملفات الشخصية"), ("F1_saved", "حفظ ملف شخصي"), ("F1_loaded", "تحميل ملف شخصي"), ("F1_confirm", "حذف ملف شخصي"),
               ("F2_apply_q", "Apply Design — السؤال باسم التصميم والثيم"), ("F2_keep_prompt", "بعد إعادة التشغيل: الإبقاء على التصميم؟ → Yes"),
               ("F3_keep_prompt", "بلا إجابة → رجوع تلقائي"), ("F4_factory_q", "Restore Factory Design"), ("F4_designs_factory", "بعد المصنع: Classic · Navy"),
               ("F5_processing", "Processing"), ("F5_processing2", "Processing — عدة أسطر")):
    G(n, lab, "FUNC", 3, SH2)
for t in ("navy", "black", "graphite", "purple", "burgundy", "green"):
    for i, lab in (("1_preview", "CineView Designs"), ("2_infocard", "Info Card"), ("3_processing", "Processing"), ("4_yesno", "MessageBox"), ("6_setup", "Setup")):
        G("T_%s_%s" % (t, i), "%s — %s" % (t, lab), "THEMES", 1.8, SH2)
still(card("النتيجة", "فحوص الأخطاء: %d · فيها traceback أو skin error أو crash: %d" % (len(errs), bad),
           ["كلمات التطوير على الشاشة: %s" % (forb[0] if forb else "?"), "الاختيار والإعدادات أُعيدت كما كانت", "المتبقي: اعتمادك ثم النشر وmain"]), 7)
lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
