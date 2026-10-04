#!/usr/bin/env python3
# Real-use recording of the 2026-10-04 evening build (build29): Channel Selection navigation (3 designs, posters on
# and off), EventView line by line vs continuous, Classic posters-off screens.  Grabs from the receiver ('grab'
# loop, video+OSD composite, ~7 fps) played at their real timing.
import os, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont
H = os.path.expanduser("~/cineview-mla")
T = os.path.join(H, "video2_tmp"); shutil.rmtree(T, ignore_errors=True); os.makedirs(T)
OUT = os.path.join(H, "CineView_MLA_navigation_2026-10-04.mp4")
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG, ACC, TXT, MUT = (8, 20, 38), (249, 199, 49), (240, 240, 240), (170, 182, 198)
def f(p, s): return ImageFont.truetype(p, s, layout_engine=ImageFont.Layout.RAQM)
def rtext(d, xr, y, s, font, fill):
    w = d.textlength(s, font=font, direction="rtl", language="ar"); d.text((xr - w, y), s, font=font, fill=fill, direction="rtl", language="ar")
segs = []
ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25", "-crf", "21", "-preset", "medium"]
def ff(*a): subprocess.run(["ffmpeg", "-loglevel", "error", "-y"] + list(a), check=True)
def still(img, secs):
    p = os.path.join(T, "s%03d.png" % len(segs)); img.save(p); o = os.path.join(T, "seg%03d.mp4" % len(segs))
    ff("-loop", "1", "-t", str(secs), "-i", p, "-vf", "scale=1920:1080,fps=25", *ENC, o); segs.append(o)
def card(title, sub, lines=()):
    im = Image.new("RGB", (1920, 1080), BG); d = ImageDraw.Draw(im); d.rectangle([0, 0, 1920, 8], fill=ACC)
    rtext(d, 1800, 330, title, f(FB, 66), TXT); rtext(d, 1800, 440, sub, f(FR, 38), ACC)
    for i, ln in enumerate(lines): rtext(d, 1800, 540 + i * 60, ln, f(FR, 34), MUT)
    return im
def rec(d, label):
    src = os.path.join(H, d); fs = sorted((int(x[:-4]), x) for x in os.listdir(src) if x.endswith(".jpg"))
    lst = os.path.join(T, "c%03d.txt" % len(segs))
    with open(lst, "w") as fh:
        for i, (t, n) in enumerate(fs):
            fh.write("file '%s'\nduration %.4f\n" % (os.path.join(src, n), (fs[i + 1][0] - t) / 1e9 if i + 1 < len(fs) else 0.4))
        fh.write("file '%s'\n" % os.path.join(src, fs[-1][1]))
    o = os.path.join(T, "seg%03d.mp4" % len(segs))
    tag = label.replace(":", "\\:").replace("'", "")
    ff("-f", "concat", "-safe", "0", "-i", lst, "-vf", "fps=25,scale=1920:1080,drawtext=fontfile=%s:text='%s':x=w-tw-24:y=16:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=10" % (FB, tag), *ENC, o)
    segs.append(o); return (fs[-1][0] - fs[0][0]) / 1e9, len(fs)
def caption(p, lab, tag):
    im = Image.open(p).convert("RGB").resize((1920, 1080)); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, 1920, 86], fill=(8, 20, 38, 225)); d.rectangle([0, 86, 1920, 90], fill=ACC + (255,))
    rtext(d, 1880, 16, lab, f(FB, 40), TXT); tw = d.textlength(tag, font=f(FB, 36))
    d.rounded_rectangle([40, 16, 40 + tw + 40, 72], 12, fill=ACC + (255,)); d.text((60, 20), tag, font=f(FB, 36), fill=(26, 19, 0)); return im
still(card("CineView MLA — تسجيل الاستخدام الفعلي", "build29/build30 · Slot 8 · لقطات متتالية من الرسيفر (فيديو + واجهة) بسرعة ~7 إطارات/ث",
           ["قائمة القنوات: Poster List · Video First · Video First (يمين)", "التنقل قناة بقناة ثم صعودًا بسرعة — المعلومات تتبع المؤشر",
            "EventView: سطرًا سطرًا مقارنة بالتمرير المستمر", "Classic بدون بوستر + إصلاح ترتيب الطبقات (build30)"]), 6)
for d, lab in (("shots/t30/rec_posterlist_on", "Poster List - posters ON"), ("shots/t30/rec_posterlist_off", "Poster List - posters OFF"),
               ("shots/t30/rec_videofirst_on", "Video First (list left) - posters ON"), ("shots/t30/rec_videofirst_off", "Video First (list left) - posters OFF"),
               ("shots/t30/rec_videofirst-right_on", "Video First (list right) - posters ON"), ("shots/t30/rec_videofirst-right_off", "Video First (list right) - posters OFF"),
               ("shots/t30/rec_eventview_lines", "EventView - line by line (opaque label)"), ("shots/t30/rec_eventview_classic", "EventView - Classic continuous")):
    if os.path.isdir(os.path.join(H, d)) and os.listdir(os.path.join(H, d)):
        span, n = rec(d, lab); print(d, "%.1f s, %d grabs, %.1f fps" % (span, n, n / span))
still(card("إصلاح ترتيب الطبقات", "خلفية الشاشة كانت تغطي النصوص (موروث من CineView FHD)", ["قبل: build29 — بعد: build30 (zPosition -1 للخلفية)"]), 4)
for n, lab in (("quickepg", "QuickEPG"), ("eventviewsimple", "EventViewSimple")):
    for tag, p in (("BEFORE", os.path.join(H, "shots/t30/on_%s.png" % n)), ("AFTER", os.path.join(H, "shots/t31/on_%s.png" % n))):
        if os.path.isfile(p): still(caption(p, lab, tag), 3)
S = os.path.join(H, "shots/t31")
still(card("Classic بدون بوستر", "الشاشات التي اختُبرت الآن على الرسيفر", ["Multi EPG · QuickEPG · InfoBar EPG · InfoBarEventView · EventViewSimple · SecondInfoBarECM"]), 4)
for n, lab in (("epg_multi", "Multi EPG"), ("quickepg", "QuickEPG"), ("infobarepg", "InfoBar EPG"), ("infobareventview", "InfoBarEventView"), ("eventviewsimple", "EventViewSimple"), ("sib_ecm", "SecondInfoBarECM")):
    for t in ("on", "off"):
        p = os.path.join(S, "%s_%s.png" % (t, n))
        if os.path.isfile(p): still(caption(p, lab, "Posters " + t.upper()), 3)
lst = os.path.join(T, "list.txt"); open(lst, "w").write("".join("file '%s'\n" % s for s in segs))
ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", OUT)
print(OUT, os.path.getsize(OUT))
