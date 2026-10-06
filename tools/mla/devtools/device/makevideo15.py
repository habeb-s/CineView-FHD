#!/usr/bin/env python3
# CineView Designs checklist video (night 2026-10-06/07): receiver grabs from t98 (before build90 / after build91),
# t98b (functions), t99 (MessageBox / Setup experiments, base build92), t100 (six themes).  Stills only, as captured.
import os, re, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video15_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_Designs_checklist_2026-10-07.mp4")
BUILD = os.environ.get("BUILD", "build92"); COMMIT = os.environ.get("COMMIT", "?")
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
def tagbox(d, tag, good):
    col = {True: (60, 170, 110), False: (200, 70, 60)}.get(good, ACC)
    tw = d.textlength(tag, font=f(FB, 24)); d.rounded_rectangle([24, 11, 24 + tw + 28, 49], 9, fill=col + (255,)); d.text((38, 14), tag, font=f(FB, 24), fill=(255, 255, 255))
def cap(im, lab, tag, good=None):
    im = im.convert("RGB").resize((W, HH)); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, W, 58], fill=(8, 20, 38, 230)); d.rectangle([0, 58, W, 61], fill=ACC + (255,))
    rtext(d, W - 24, 12, lab, f(FB, 25), TXT); tagbox(d, tag, good); return im
def G(run, n, lab, tag, good=None, secs=3.5):
    p = os.path.join(H, "shots", run, n + ".png")
    try:
        still(cap(Image.open(p), lab, tag, good), secs)
    except Exception as e:
        print("missing", run, n, e)
def SHEET(p, lab, tag, good=None, secs=5):
    try:
        src = Image.open(p).convert("RGB")
    except Exception as e:
        print("missing", p, e); return
    k = min((W - 30) / src.width, (HH - 75) / src.height); src = src.resize((int(src.width * k), int(src.height * k)), Image.LANCZOS)
    im = Image.new("RGB", (W, HH), BG); im.paste(src, ((W - src.width) // 2, 66 + (HH - 66 - src.height) // 2)); still(cap(im, lab, tag, good), secs)
EV = os.path.join(H, "repo", "docs", "mla", "evidence", "designs")
still(card("CineView Designs — قائمة الفحص", "%s · commit %s · Slot 8 · ثيم Black" % (BUILD, COMMIT),
           ["24 بندًا: فتح الواجهة · كل صف · المعاينة · الملفات الشخصية · النماذج · التجربة والتراجع · المصنع",
            "أُصلح: القيم صغيرة · صف مقطوع · أوصاف ناقصة · زر Preview بلا وظيفة · معاينة ناقصة · عناوين",
            "قراران ينتظرانك: حجم رسائل MessageBox · خط القيم في صفحات الإعدادات"]), 8)
G("t98_p1", "D1_open", "قبل (build90) — القيم صغيرة وصف مقطوع أسفل القائمة", "BEFORE", False)
G("t98_p1b", "D1_open", "بعد — قيم مقروءة · 13 صفًا كاملًا · وصف للثيم", "AFTER", True)
G("t98_p1", "D2_row14", "قبل — صف إعداد بلا شرح ومعه زر Preview بلا وظيفة", "BEFORE", False)
G("t98_p1b", "D2_row14", "بعد — شرح للإعداد · زر Preview مخفي", "AFTER", True)
G("t99_base", "D_eventview_row", "بعد — EventView سطرًا سطرًا: صار له معاينة", "AFTER", True)
G("t98_p1b", "D3_preview_infobar", "المعاينة بملء الشاشة (YELLOW / OK)", "PASS", True, 3)
G("t99_base", "D_profiles_title", "MENU — الملفات الشخصية (العنوان CineView Designs)", "PASS", True, 3)
G("t98b_b1", "E4_models", "نموذج لكل الأقسام: Classic · Details · Cinema · Modern · Minimal", "PASS", True, 3)
G("t98b_b1", "E3_keyboard", "حفظ ملف شخصي — لوحة المفاتيح", "PASS", True, 3)
G("t98b_b1", "E6_keep_prompt", "تجربة → سؤال الإبقاء → No → رجوع تلقائي إلى Black", "PASS", True, 4)
G("t98b_b1", "E7_next_infobar", "تجربة مقبولة (Burgundy) ثم أُعيد Black بالطريقة نفسها", "PASS", True, 3)
for t in ("navy", "black", "graphite", "purple", "burgundy", "green"):
    G("t100_themes", t + "_1_designs", "الثيمات الستة — CineView Designs · " + t, "THEMES", True, 2.5)
for t in ("navy", "purple"):
    G("t100_themes", t + "_2_processing", "Processing في ثيم " + t, "THEMES", True, 2.5)
still(card("قرار 1: حجم رسائل MessageBox", "الحالي 960×520 ثابت · المقترح: النافذة بحجم النص والإجابات",
           ["يغيّر كل رسائل السكين — لذلك مطفأ (MLA_MSGBOX_FIT) حتى موافقتك", "مجرّب على الرسيفر: 0 traceback · 0 skin error"]), 5)
for m in ("msg_info", "msg_yesno", "msg_long", "msg_list"):
    SHEET(os.path.join(EV, "decision_msgbox_%s.jpg" % m), "يسار: الحالي · يمين: المقترح", "DECISION", None, 4)
still(card("قرار 2: خط القيم في صفحات الإعدادات", "القيم تُرسم بخط الصورة الافتراضي (~18px) في كل صفحات Setup",
           ["المقترح 27px في القالب المشترك ConfigTemplate (مطفأ: MLA_SETUP_VALUEFONT)", "CineView Designs لها قائمتها الخاصة وأُصلحت فعلًا"]), 5)
SHEET(os.path.join(EV, "decision_setup_valuefont.jpg"), "يسار: الحالي · يمين: المقترح", "DECISION", None, 5)
still(card("النتيجة", "كل التشغيلات: 0 traceback · 0 skin error · 0 crash", ["الإعدادات واختيارك (Black / Classic) أُعيدت كما كانت", "المتبقي: قراراك ثم الحزمة النهائية والنشر بعد اعتمادك"]), 7)
lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB", len(segs), "segments")
