#!/usr/bin/env python3
# Plugin / package management video 2026-10-06 (user 22:00): before (build88) / after (build90) of Plugin Browser ->
# Install Plugins (download), Remove, Update, Plugin Action Log, Processing dialog (feed texts).  Motion = the receiver's
# own frames recorded by t97 (shots/t97_before, shots/t97_after); numbers from t97_before.log / t97_after.log.
import os, re, glob, subprocess, shutil, sys
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video14_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_package_screens_2026-10-06.mp4")
BUILD = os.environ.get("BUILD", "build90"); COMMIT = os.environ.get("COMMIT", "?"); SHA = os.environ.get("SHA", "?")
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
    rtext(d, W - 80, 150, title, f(FB, 42), TXT); rtext(d, W - 80, 222, sub, f(FR, 25), ACC)
    for i, ln in enumerate(lines): rtext(d, W - 80, 295 + i * 42, ln, f(FR, 23), MUT)
    return im
def tagbox(d, tag, good):
    col = {True: (60, 170, 110), False: (200, 70, 60)}.get(good, ACC)
    tw = d.textlength(tag, font=f(FB, 24)); d.rounded_rectangle([24, 11, 24 + tw + 28, 49], 9, fill=col + (255,)); d.text((38, 14), tag, font=f(FB, 24), fill=(255, 255, 255))
def caption_img(im, lab, tag, good=None):
    im = im.convert("RGB").resize((W, HH)); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, W, 58], fill=(8, 20, 38, 230)); d.rectangle([0, 58, W, 61], fill=ACC + (255,))
    rtext(d, W - 24, 12, lab, f(FB, 26), TXT); tagbox(d, tag, good); return im
def frames(run, prefix):
    out = []
    for p in sorted(glob.glob(os.path.join(H, "shots", run, "frames", prefix + "_*.jpg"))):
        try:
            Image.open(p).verify(); out.append(p)
        except Exception:
            pass
    return out
def motion(run, prefix, lab, tag, good, secs):
    fs = frames(run, prefix)
    if not fs:
        print("missing frames", run, prefix); return
    d = os.path.join(T, "m%03d" % len(segs)); os.makedirs(d)
    for i, p in enumerate(fs):
        caption_img(Image.open(p), lab, tag, good).save(os.path.join(d, "f%04d.png" % i))
    rate = max(1.0, len(fs) / float(secs))
    o = os.path.join(T, "seg%03d.mp4" % len(segs))
    ff("-framerate", "%.3f" % rate, "-i", os.path.join(d, "f%04d.png"), "-vf", "scale=%d:%d,fps=25" % (W, HH), *ENC, o); segs.append(o)
    print("motion", run, prefix, len(fs))
def grab(run, n, lab, tag, good, secs=3.5):
    p = os.path.join(H, "shots", run, n + ".png")
    try:
        still(caption_img(Image.open(p), lab, tag, good), secs)
    except Exception as e:
        print("missing", run, n, e)
def errs(name):
    p = os.path.join(H, name); L = open(p, errors="replace").read() if os.path.exists(p) else ""
    m = re.findall(r"tracebacks=(\d+) skin_errors_new=(\d+) crashlogs=(\d+)", L)
    return m[-1] if m else ("?", "?", "?")

B, A = "t97_before", "t97_after"
eb, ea = errs("t97_before.log"), errs("t97_after.log")
still(card("شاشات إدارة البلجنات والحزم", "%s · commit %s · 1.0.0 SHA256 %s" % (BUILD, COMMIT, SHA[:8] + "…" + SHA[-8:] if len(SHA) > 16 else SHA),
           ["الشاشة الخلفية: PackageAction (Install / Remove / Update Plugins)",
            "النافذة الصغيرة: الحوار العام Processing — تصميم OpenATV الافتراضي 1280×720 لأن CineView لم يعرّفه",
            "سبب التكرار: PackageAction يضع النص في وصفه ثم يمرره نفسه إلى Processing (setWaiting)",
            "الإصلاح: Processing بتصميم CineView · نص واحد · الأزرار الملونة فقط مع وظيفة · بلا تعديل ملفات Enigma2"]), 9)
still(card("قبل — build88", "Plugin Browser ← الأخضر Install Plugins", ["نافذة Processing افتراضية + الرسالة مكررة أسفل الشاشة + أزرار فارغة + HELP"]), 4)
motion(B, "A_install_busy", "قبل — تنزيل معلومات البلجنات", "BEFORE", False, 5)
still(card("بعد — " + BUILD, "نفس الحالة على الرسيفر", ["نافذة CineView واحدة: العنوان · شريط التقدم · الرسالة", "عنوان الوضع في الترويسة · Close فقط · لا HELP أثناء الانتظار"]), 4)
motion(A, "A_install_busy", "بعد — تنزيل معلومات البلجنات", "AFTER", True, 5)
motion(A, "A_install_done", "بعد — اكتمل: 579 حزمة قابلة للتثبيت", "AFTER", True, 3)
motion(B, "B_remove_done", "قبل — Remove Plugins: أزرار خضراء/صفراء فارغة", "BEFORE", False, 3)
motion(A, "B_remove_busy", "بعد — Remove Plugins: Getting plugin information", "AFTER", True, 3)
motion(A, "B_remove_done", "بعد — Remove Plugins: 66 حزمة مثبتة", "AFTER", True, 3)
motion(A, "C_update_busy", "بعد — Update Plugins: أثناء التنزيل", "AFTER", True, 4)
motion(A, "C_update_done", "بعد — Update Plugins: اكتمل", "AFTER", True, 3)
motion(B, "D_log", "قبل — Plugin Action Log", "BEFORE", False, 2.5)
motion(A, "D_log", "بعد — Plugin Action Log (Close + HELP فقط)", "AFTER", True, 2.5)
motion(B, "E2_processing_multiline", "قبل — Processing بنص متعدد الأسطر (نص إعادة ضبط الـfeeds)", "BEFORE", False, 3)
motion(A, "E1_processing", "بعد — Processing فوق Plugin Browser (تحديث الـfeeds)", "AFTER", True, 3)
motion(A, "E2_processing_multiline", "بعد — النافذة تتمدد مع النص وتبقى في الوسط", "AFTER", True, 3.5)
still(card("النتيجة", "قبل: traceback %s · skin error %s · crash %s   |   بعد: traceback %s · skin error %s · crash %s" % (eb + ea),
           ["لا تكرار للنص (الوصف فارغ أثناء الانتظار ويعود بعده — من الـstack الحي)",
            "الحواف الدائرية للنافذة: جُرّبت وتسببت بعدم رسم الشاشة الخلفية على الرسيفر — أُلغيت (حواف مستقيمة)",
            "لا تثبيت ولا إزالة فعلية — قوائم فقط · المتبقي: النشر و main بعد موافقتك"]), 9)
lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
