#!/usr/bin/env python3
# Video of the autonomous night run 2026-10-04/05 (Slot 8, build35-build43): real receiver grabs, grab-loop
# recordings (~7 fps, played at their real timing) and EventView framebuffer recordings (5 fps, real timing).
import os, struct, subprocess, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video5_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_night_tests_2026-10-05.mp4")
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

# ---------------------------------------------------------------------------------------------------------------
still(card("CineView MLA — اختبارات الليل", "Slot 8 · build35 ← build43 · لقطات وتسجيلات فعلية من الرسيفر",
           ["Graphical Plus · Modern InfoBar · البوسترات مع كاش فارغ", "EventView سطرًا بسطر · EventView من دليل البرامج · Vertical EPG",
            "IMDb الموثوق · الذاكرة والأداء 30 دقيقة"]), 6)

still(card("1. Graphical Plus", "EPG جديد — البوسترات ظاهرة ومخفية والثيمات الست",
           ["عند إخفاء البوسترات يتسع الجدول إلى نحو 3 ساعات دون مساحة محجوزة", "التفاصيل تتبع الخلية المحددة"]), 4.5)
still(caption(S("t40", "gp_on"), "Graphical Plus — البوسترات ظاهرة", "ON"), 4)
still(caption(S("t40", "gp_on_right"), "المؤشر على الحدث التالي — التفاصيل تتبعه", "ON"), 3)
still(caption(S("t40", "gp_off"), "Graphical Plus — البوسترات مخفية", "OFF"), 4)
for t in ("black", "burgundy", "graphite", "green", "purple"):
    still(caption(S("t37", "b_gp_on_" + t), "Graphical Plus — ثيم " + t, "THEME"), 2)

still(card("2. Modern InfoBar", "تصميم جديد على الرسيفر — الشكل بانتظار اعتمادك",
           ["أولًا: فحص الزوايا المستديرة والتدرج على الرسيفر نفسه", "ثم الشريط: بوستر مستدير، شارات حية، خط عريض"]), 4.5)
still(caption(S("t41", "probe_all"), "فحص ميزات Modern — زوايا مستديرة وتدرج فوق فيديو حي", "PROBE"), 4)
IB = (0, 740, 1920, 1080)
still(strip(S("t43", "a_on_hbo2"), IB, "HBO 2 — Kaskader → The Fall Guy · IMDb 6.8 (هوية مؤكدة)", "ON", True), 4)
still(strip(S("t43", "a_on_hrt1"), IB, "HRT1 — بلا هوية مؤكدة: صورة افتراضية وبلا تقييم", "ON", True), 3.5)
still(strip(S("t43", "b_off_hrt1"), IB, "البوسترات مخفية — المحتوى يبدأ من حافة البطاقة", "OFF", True), 3.5)
for t in ("black", "burgundy", "graphite", "green", "purple", "navy"):
    still(strip(S("t43", "c_theme_" + t), IB, "Modern InfoBar — ثيم " + t, "THEME"), 1.8)
still(strip(S("t43", "d_long_ar_t0"), IB, "عنوان عربي طويل — محاذاة يمين", "AR", True), 3)
still(strip(S("t43", "d_long_en_t0"), IB, "Long English title", "EN", True), 3)

still(card("3. البوسترات أثناء التنقل السريع", "كاش فارغ تمامًا — التحميل يحدث أثناء التنقل",
           ["تسجيل فعلي ~7 إطارات/ث بالسرعة الحقيقية", "خطوة كل 0.15 ث ثم كل 0.35 ث على قنوات الأفلام",
            "النتيجة: 0 بوستر لقناة سابقة بعد ثبات المؤشر"]), 5)
for d, lab in (("shots/t49/rec_cold1_vfast", "Cold cache - 0.15 s/step - real downloads"), ("shots/t44/rec_cold1_fast", "Cold cache - 0.35 s/step")):
    span, n = rec(d, lab); print(d, "%.1f s, %d grabs" % (span, n))

still(card("4. EventView — سطرًا بسطر", "قبل: الرجوع في نهاية النص ترك سطرين متراكبين",
           ["بعد: العودة إلى السطر الأول برسم كامل + إعادة رسم وقائية بعد كل حركة", "290 حركة · 0 خاطئة · 21 عودة سليمة"]), 5)
binclip("shots/t39/lines2_en.bin", 49.5, 56.5, "قبل — الرجوع في نهاية النص (build35)", "BEFORE", False)
binclip("shots/t51/lines1_en.bin", 0.0, 42.0, "بعد — build43: سطر كل 1.74 ث ثم العودة للبداية", "AFTER", True)
binclip("shots/t51/lines1_ar.bin", 0.0, 24.0, "بعد — النص العربي", "AFTER", True)

still(card("5. EventView من دليل البرامج", "كان يعرض عناوين القناة المشغّلة مع بوستر حدث آخر",
           ["الآن: الحدث المحدد ببياناته وبوستره", "INFO المباشر بقي على اللوحة الكلاسيكية المعتمدة"]), 5)
still(caption(S("t42", "v3_info"), "قبل — Holland مع بوستر The Bride!", "BEFORE", False), 4)
still(caption(S("t47", "a_vertical_info"), "بعد — HBO 2 Opaki Radnik 02:58–04:50 (مطابق لـOpenWebif)", "AFTER", True), 4)
still(caption(S("t50", "c_live_info"), "INFO المباشر — اللوحة الكلاسيكية كما هي", "OK", True), 3.5)
still(caption(S("t50", "e_graph_later_info"), "حدث لاحق على القناة نفسها", "OK", True), 3)
still(caption(S("t50", "d_vertical_info_off"), "البوسترات مخفية", "OK", True), 3)

still(card("6. Vertical EPG", "الأعمدة الخمسة كانت مخفية خلف قائمة أرقام (خلل من السكين الأصلي)",
           ["الإصلاح: العقد الأصلي لـOpenATV — فهرس الصفحات بعرض صفر وتحت الأعمدة"]), 4.5)
still(caption(S("t42", "v0_start"), "Vertical EPG — الأعمدة ظاهرة", "AFTER", True), 3.5)
still(caption(S("t42", "v1_right"), "يمين — العمود النشط HBO 2 HD", "AFTER", True), 3)
still(caption(S("t42", "v2_down2"), "أسفل — الحدث التالي", "AFTER", True), 3)

still(card("7. تقييمات IMDb الموثوقة فقط", "التقييم يظهر فقط عند هوية مؤكدة للبرنامج", []), 3.5)
for n, lab in (("hbo", "HBO — Bajkeri: بلا تقييم (كان 4.7 خطأ)"), ("hbo2", "HBO 2 — Kaskader: 6.8"), ("cinemax", "Cinemax — Misija: Bijela kuća: 6.3"), ("hrt1", "HRT1 — بلا هوية مؤكدة: بلا تقييم")):
    still(strip(S("t40", "imdb_%s_infobar" % n), (0, 780, 1920, 1080), lab, "OK", True), 3)

still(card("8. الذاكرة والأداء — 30 دقيقة", "Poster List مع البوسترات · 33 جولة تنقل",
           ["الذاكرة 153.6 ← 155.1 MB ثابتة · الخيوط 15 · الملفات 105", "المعالج لكل 4 جولات 20–22 ث بلا تباطؤ · 0 أخطاء",
            "accelAlloc: ضغط على ذاكرة التسريع من كاش صور القنوات — بلا تسرب ولا أثر مرئي"]), 7)
span, n = rec("shots/t38/rec_end", "After 30 min soak - same speed as at the start"); print("soak end", span, n)

still(card("9. Video First وأسماء القنوات الطويلة", "", []), 3)
still(caption(S("t37", "a2_vfr_hrt1"), "البطاقة معتمة فوق مشهد ساطع — الفيديو ظاهر حولها", "OK", True), 3.5)
still(caption(S("t37", "a1_videofirst-right_tv"), "الاسم الطويل ينتهي قبل شريط التقدم", "OK", True), 3.5)

still(card("بانتظار قرارك", "لا نشر ولا دمج في main قبل اعتمادك",
           ["اعتماد شكل Graphical Plus", "اتجاه Modern ثم بقية شاشاته · اتجاه Minimal",
            "قبول تفسير accelAlloc دون تعديل", "أسماء الأزرار الملونة في EventView"]), 7)

lst = os.path.join(T, "all.txt")
with open(lst, "w") as fh:
    for s in segs: fh.write("file '%s'\n" % s)
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", OUT)
print("OUT", OUT, os.path.getsize(OUT) // 1024, "kB")
