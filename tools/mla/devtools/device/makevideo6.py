#!/usr/bin/env python3
# Video of the morning run 2026-10-05 (Slot 8, build44-build54): real receiver grabs only.
# Numbers on the cards come from the test logs (t53..t60, t54b, t57b); SOAK is filled from t60.log.
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video6_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_morning_tests_2026-10-05.mp4")
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

import json
SOAK = json.load(open(os.path.join(H, "t60_summary.json"))) if os.path.exists(os.path.join(H, "t60_summary.json")) else {}
IB = (0, 740, 1920, 1080)
BOT = (0, 760, 1920, 1080)

still(card("CineView MLA — اختبارات الصباح", "Slot 8 · build44 ← build54 · لقطات فعلية من الرسيفر",
           ["إصلاح شارتي HD و16:9 من الجذور", "Graphical Plus · Modern بأقسامه · Columns",
            "Cover Library · EventView Feature · Modern PVR · الأداء"]), 6)

still(card("1. شارتا HD و16:9", "السبب: لا يصل حدث حجم الفيديو بعد فتح الشاشة في بعض الإقلاعات",
           ["المحوّل الأصلي يبقى على قيمة لحظة الاتصال (قبل تشغيل الخدمة) = مخفي",
            "الإصلاح: CineViewMLAServiceInfo — إعادة تقييم عند بدء الخدمة والمعلومات + فحصان لاحقان",
            "قبل: 5 من 24 عيّنة مفقودة · بعد: 36 من 36 ظاهرة"]), 7)
still(strip(S("t53", "modern_r1_black"), BOT, "قبل (t53) — Modern: الشارتان مفقودتان رغم 1920×1080", "BEFORE", False), 4)
still(strip(S("t53", "classic_r2_navy"), BOT, "قبل (t53) — Classic: أيقونتا HD و16:9 مفقودتان أيضًا", "BEFORE", False), 4)
still(strip(S("t56", "modern_r1_purple"), BOT, "بعد (t56) — نفس ظرف الفشل (بلا حدث حجم فيديو) والشارتان ظاهرتان", "AFTER", True), 4.5)
still(strip(S("t56", "classic_r2_navy"), BOT, "بعد (t56) — Classic", "AFTER", True), 3.5)

still(card("2. Graphical Plus", "التنقل السريع والبطيء يعطيان النتيجة نفسها",
           ["عند إخفاء البوستر: التذييل للنوع وIMDb والوصف تحت المدة مباشرة", "العناوين الملتفة تكسر الكلمات في الخلايا القصيرة — يُنصح بالافتراضي"]), 5)
still(caption(S("t55", "a1_off_start"), "البوسترات مخفية — 3 ساعات + لوحة بلا فراغات", "OFF", True), 4)
still(caption(S("t55", "a2_on_start"), "العناوين الملتفة (خيار أصلي) — كسر الكلمات في الخلايا القصيرة", "OPTION"), 4)
still(caption(S("t55", "c_fast_k9"), "سريع 0.25 ث/مفتاح — المفتاح 9", "FAST", True), 2.5)
still(caption(S("t55", "c_slow_k9"), "بطيء 2.5 ث/مفتاح — نفس الحدث والبوستر", "SLOW", True), 2.5)

still(card("3. Modern — بقية الأقسام", "SecondInfoBar · قائمة القنوات · EPG · EventView · PVR", ["الشكل بانتظار اعتمادك"]), 4)
for n, lab, tag in (("sib_navy_on", "SecondInfoBar — NOW / NEXT", "ON"), ("sib_navy_on_hbo", "SecondInfoBar — HBO", "ON"), ("sib_green_off", "SecondInfoBar — بلا بوستر (ثيم green)", "OFF")):
    if os.path.exists(S("t57b", n)): still(caption(S("t57b", n), lab, tag, True), 3.5)
for n, lab, tag in (("cs_navy_on_open", "قائمة القنوات — تمييز مستدير والمعلومات تتبع المؤشر", "ON"),
                    ("cs_navy_on_down1", "المؤشر على HBO 2 — البطاقة تتبعه", "ON"),
                    ("cs_navy_off_open", "قائمة القنوات — بلا بوستر", "OFF"),
                    ("cs_burgundy_on_open", "ثيم burgundy", "THEME"), ("cs_green_on_open", "ثيم green", "THEME"),
                    ("epg_navy_on_right", "EPG — البطاقة تتبع الخلية", "ON"), ("epg_navy_off_open", "EPG — شبكة أعرض بلا بوستر", "OFF"),
                    ("ev_navy_on_simple", "EventView من الدليل", "ON"), ("ev_navy_off_simple", "EventView — بلا بوستر", "OFF"),
                    ("ev_navy_on_infobar", "InfoBarEventView", "ON")):
    still(caption(S("t57", n), lab, tag, tag != "THEME" or None), 3)
if os.path.exists(S("t57b", "ev_navy_on_live")): still(caption(S("t57b", "ev_navy_on_live"), "EventView المباشر — شعار القناة من مصدر الشاشة", "FIX", True), 3.5)
for n, lab, tag in (("pvr_modern_on_open", "Modern PVR — بطاقتان مستديرتان", "ON"), ("pvr_modern_on_down2", "المؤشر — الغلاف والتفاصيل تتبعه", "ON"), ("pvr_modern_off_open", "Modern PVR — بلا غلاف", "OFF")):
    if os.path.exists(S("t59", n)): still(caption(S("t59", n), lab, tag, True), 3.5)

still(card("4. Columns", "على Vertical EPG الأصلي في OpenATV — خمس قنوات جنبًا إلى جنب", ["بطاقة الحدث تتبع العمود والحدث المحدد"]), 4)
for n, lab, tag in (("col_navy_on_open", "Columns — البوسترات ظاهرة", "ON"), ("col_navy_on_right2_down1", "يمين ثم أسفل — Peter Pan", "ON"),
                    ("col_burgundy_off_down3", "بلا بوستر — ثيم burgundy", "OFF"), ("col_navy_on_info", "INFO — الحدث المحدد", "OK")):
    still(caption(S("t58", n), lab, tag, True), 3.5)

still(card("5. Details — Cover Library", "قائمة التسجيلات الأصلية + غلاف التسجيل المحدد", ["قراءة فقط من الـHDD — لا تشغيل ولا حذف"]), 4)
for n, lab, tag in (("pvr_cover_on_open", "Cover Library", "ON"), ("pvr_cover_on_down2", "المؤشر — الغلاف يتبعه", "ON"), ("pvr_cover_off_open", "بلا غلاف — هندسة Classic", "OFF")):
    if os.path.exists(S("t59", n)): still(caption(S("t59", n), lab, tag, True), 3.5)
still(card("6. Cinema — EventView Feature", "بوستر كبير · عنوان 56 · الوصف في ScrollLabel الأصلي", []), 4)
for n, lab, tag in (("ev_feature_navy_on_live", "Feature — INFO المباشر", "ON"), ("ev_feature_navy_on_simple", "Feature — من الدليل", "ON"),
                    ("ev_feature_burgundy_off_simple", "Feature — بلا بوستر", "OFF"), ("ev_feature_navy_on_infobar", "Feature — InfoBarEventView", "ON")):
    if os.path.exists(S("t59", n)): still(caption(S("t59", n), lab, tag, True), 3.5)

if SOAK:
    still(card("7. الأداء بعد التصاميم الجديدة", "Modern %s دقيقة · Classic %s دقائق للمقارنة" % (SOAK.get("modern_min", "25"), SOAK.get("classic_min", "10")), SOAK.get("lines", [])), 7)

still(card("بانتظار قرارك", "لا نشر ولا دمج في main قبل اعتمادك",
           ["شكل Modern في أقسامه الستة", "نماذج Minimal (الصفحة المنشورة)", "Columns · Cover Library · EventView Feature"]), 6)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB")
