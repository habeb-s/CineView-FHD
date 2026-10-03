# ISS-01 / ISS-02 — إثبات السبب والإصلاح (OpenATV 8.0.1، Slot 8)

> الجهاز: Vu+ Duo 4K SE · OpenATV 8.0.1 build 20261003 · enigma2 57b7a51 · Python 3.14.7
> المكوّن المختبَر: CineViewControl **2.3.4 الأصلي بلا تعديل** (المنسوخ من Slot 3 للقراءة فقط)، مثبّت مؤقتًا في Slot 8.

## ISS-01 — إعداد Second InfoBar

### السبب (من الشيفرة)
`plugin.py:41-46` — `apply_timeout()` تكتب `config.plugins.cineview.secondtimeout` (ثوانٍ: 5…60 أو 0) في
`config.usage.show_second_infobar` (الوضع: 0 Off / 1 Event Info / 2 2nd InfoBar INFO / 3 ECM)، وتُستدعى في `sessionstart` عند كل إقلاع.
`ConfigSelection.setValue` في OpenATV 8.0.1 يستبدل أي قيمة خارج الخيارات بالافتراضي `"1"`.

### الإثبات الفعلي على الجهاز
| التشغيل | CineViewControl | القيمة الحية `show_second_infobar` | القيمة المحفوظة | OK مرتين |
|---|---|---|---|---|
| A — ضابط | غير مثبت | 2 | 2 | **SecondInfoBar يظهر** (لقطة `A_control_okok`) |
| B/C — المشكلة | الأصلي 2.3.4 | **1** | 2 | **لا يظهر SecondInfoBar** (لقطة `B_with_cvc_okok`) |
| D0 — ضابط ثانٍ | أُزيل (parked) | 2 | 2 | — (التشغيل الضابط قبل تثبيت النسخة المصلحة) |
| **D — بعد الإصلاح** | 2.3.4 + ISS-01 fix | **2** | 2 | **SecondInfoBar يظهر** (لقطة `D_fixed_okok`)؛ `second_infobar_timeout` الحية = **20** (كانت 5 في الضابط) |

النتيجة: الإصلاح يحافظ على الوضع الذي اختاره المستخدم، والمهلة تُطبَّق على الإعداد الأصلي الصحيح.
لقطة D التقطت والاستقبال عائد على 16.0°E (HRT1 HD، SNR 66%، AGC 73%، Bitrate 6.17 Mbps حية).

القيمة الحية قُرئت من داخل Enigma2 نفسه (تشخيص CineViewMLA بعد 60 ث من الإقلاع، `/tmp/CINEVIEW-MLA/live_config.json`).
ملاحظة: ملف settings يبقى `2` لأن `apply_timeout(False)` لا تحفظ — لذلك يبدو الإعداد سليمًا للمستخدم بينما السلوك الفعلي Event Info.

### الإصلاح
- **في MLA (الحل البنيوي):** واجهة CineViewMLA تعرض **الوضع** و**المهلة** كإعدادين أصليين منفصلين (`config.usage.show_second_infobar` و`config.usage.second_infobar_timeout`) ولا تكتب أحدهما في الآخر.
- **للنسخة المستقرة:** `fixes/openatv/CineViewControl/ISS-01_apply_timeout.py` — تكتب المهلة في `second_infobar_timeout` (قيم 30/60 غير الموجودة في 8.0.1 ⇒ 20) ولا تمس الوضع. اختبار offline على `config.py` الحقيقي من 57b7a51: 7/7.

### ISS-01b — المهلة لم تكن تصمد (اكتُشف أثناء M7، مُثبت ومُصلح على الجهاز)
**العَرَض:** بعد الإصلاح v1 كانت القيمة الحية 20، لكن SecondInfoBar اختفى بعد نحو 5 ث (لقطات زمنية: ظاهر عند 3 و5 ث، مختفٍ عند 7 ث).

**التجربة الضابطة (CineViewControl مُزال):**

| التجربة | الإعداد | مدة الظهور |
|---|---|---|
| E1 | `second_infobar_timeout=20` محفوظ أصليًا | **~21 ث** |
| E3 | نفسه + `infobar_timeout=10` | **~21 ث** |

إذن العقد الأصلي سليم، و`infobar_timeout` لا يؤثر.

**السبب (من شيفرة 57b7a51):**
1. الإعداد مدرج في شاشة OSD Settings (`setup key="UserInterface"`).
2. `ConfigListScreen.closeConfigList` يرى `isChanged()` صحيحًا لأن القيمة الحية تختلف عن المحفوظة.
3. فيعرض "إغلاق دون حفظ؟" بالافتراضي No بدل الإغلاق.
4. إن أُكّد الإغلاق، يستدعي `cancelConfirm` الدالة `item.cancel()`، فتعود القيمة إلى المحفوظة (الافتراضي 5).

**الأثر:**
- الإصلاح v1 يبقى صحيحًا حتى أول مرة تُغلق فيها OSD Settings دون حفظ.
- الأصلي 2.3.4 (حي 1 ومحفوظ 2) يجعل OSD Settings تسأل "إغلاق دون حفظ؟" في كل مرة تُفتح فيها حتى لو لم يُغيَّر شيء.
- هذا الحوار هو أيضًا سبب انحراف تنقّل لقطات M7 v3، حين امتصّت الحوارات المتكررة ضغطات EXIT.

**الإصلاح v2 (4110f7d):** إذا اختلفت القيمة الحية عن المحفوظة تُستدعى `target.save()` أيضًا.
- offline: 5/5 (القيمة تصمد بعد `cancel()`، والوضع يبقى 2).
- **على الجهاز (Slot 8):**
  - بعد الإقلاع: حي 20 ومحفوظ 20، والوضع 2/2.
  - فُتحت OSD Settings ثم EXIT: أُغلقت مباشرة بلا حوار.
  - SecondInfoBar ظل **~21 ث**.
  - الحالة: **DEVICE VERIFIED**.

## ISS-02 — Save / activate.sh يستبدلان التصميم المعتمد

### السبب
- `plugin.py keySave`: `shutil.copy2(skin.layout-XYZ-*.xml, skin.xml)`.
- `activate.sh`: `cp -f skin.layout-XYZ-*.xml skin.xml` ثم سلسلة ترقيع.
- **و`sessionstart` يستدعي `smartdeps.sh --install` تلقائيًا** إذا غاب PosterX أو مزود الطقس أو `/usr/bin/bitrate`، و`smartdeps.sh` يثبّت حزمًا ثم يشغّل `activate.sh` ⇒ الاستبدال قد يحدث **عند الإقلاع دون أي ضغطة**.
- التصميم المعتمد موجود **فقط** في `skin.xml` الحي (ناتج ترقيعات حية لم تُكتب في ملفات layout الثلاثين).

### الإثبات
- محاكاة offline بالسكربتات الأصلية: Save ⇒ 30 شاشة مختلفة، activate.sh ⇒ 24 (منها SecondInfoBar: 67 عنصرًا ⇒ 12).
- **على الجهاز (T15، Slot 8، النسخة المرجعية `/usr/share/enigma2/CineView_FHD` فقط):**
  - قبل: `skin.xml` sha256 `73d7cd9f…` = النسخة المعتمدة؛ لا توجد مفاتيح `config.plugins.cineview.*` في settings.
  - تشغيل `activate.sh` الأصلي بلا تعديل اختار `SRC=skin.layout-111-oa.xml` و`THEME=black` (لأن مفتاح الثيم غير موجود ⇒ الافتراضي black وليس navy المعتمد).
  - النتيجة: **24 شاشة تغيّرت** (195 بدل 196 شاشة) و**8 ألوان تغيّرت**:
    AtileHD_Config, DVDPlayer, EPGSelection, EPGverticalPIG, EventView, GraphicalEPG, GraphicalEPGPIG, GraphicalInfoBarEPG, HotkeySetup, HotkeySetupSelect, InfoBar, InfoBarEventView, LanguageSelection, MenuHorizontal, MovieSelection, PackageActionLog, QuickEPG, QuickMenu, SecondInfoBar, SecondInfoBarECM, SecondInfoBarSimple, SkinSelection, SkinSelector, UserInterfacePositioner.
  - `SecondInfoBar` 122 ⇒ 119 عنصرًا، `SecondInfoBarECM` 15 ⇒ 119 (استُبدل بنسخة أخرى)، `InfoBar` 96 ⇒ 95.
  - settings لم يتغيّر (السكربت يقرأ فقط).
  - **لقطة فعلية (OK مرتين، نفس القناة HRT1 HD 16.0°E، نفس الحدث):** `shots/iss02/T15_pair.jpg`. بعد activate.sh: ألوان black بدل navy، إطار بوستر الحدث التالي في اللوحة اليمنى اختفى، رقم القناة (93) اختفى من InfoBar. بعد الاستعادة: التصميم المعتمد كما هو.
- **الاستعادة:** من `backups/reference-CineView_FHD-pre-iss.tgz` (sha256 `e6acb1b1…`) ⇒ `skin.xml` = `73d7cd9f…` والشجرة كاملة **مطابقة للنسخة الاحتياطية (359 ملفًا، md5)**.
- **الحارس على الجهاز:** `safe_activate.py skin.layout-111-oa.xml <نسخة من skin.xml المعتمد>` ⇒ **رفض (exit 3، 29 شاشة)** والملف لم يتغيّر؛ تعديل يخص InfoBar فقط ⇒ قُبل (exit 0) مع نسخة `.before-activate`. الاختبار على نسخ في tmpfs؛ المجلد الحي لم يُمس.
- ملاحظة: الحارس يقارن بالملف الحي قبل الترقيعات، لذا يعدّ 29 (يشمل ما تغيّره ترقيعات activate اللاحقة) بينما الناتج النهائي بعد ترقيعات activate.sh يغيّر 24.

### الإصلاح
- **في MLA:** لا يوجد نسخ ملفات تخطيط فوق السكين؛ المحرك يركّب أجيالًا مختومة من حزم Classic المأخوذة من الملف الحي المعتمد.
- **للنسخة المستقرة:** `fixes/openatv/CineViewControl/safe_activate.py` — يرفض الاستبدال إذا تغيّرت أي شاشة غير InfoBar/ChannelSelection. اختبار offline: يرفض layout-111-oa (29 شاشة) ويقبل تعديلًا يخص InfoBar فقط.

## الحالة
| البند | الحالة |
|---|---|
| ISS-01 السبب | **مُثبت على الجهاز** (A/B/C/D) |
| ISS-01 الإصلاح (CineViewControl المستقر) | v2 **DEVICE VERIFIED** في Slot 8 (الوضع: التشغيل D؛ المهلة: ISS-01b) — لم يُطبَّق على Slot 3 (بقرارك) |
| ISS-01 في MLA | منفّذ في واجهة CineViewMLA — **IMPLEMENTED — NOT RUNTIME VERIFIED** (الواجهة لم تُفتح على الجهاز بعد) |
| ISS-02 السبب | **مُثبت على الجهاز** (T15: 24 شاشة + 8 ألوان، لقطة) |
| ISS-02 الحارس `safe_activate.py` | **RUNTIME TESTED** على الجهاز كأداة مستقلة (رفض/قبول)؛ غير مدمج بعد في activate.sh/keySave للنسخة المستقرة |
| استعادة المرجع بعد T15 | مطابقة للنسخة الاحتياطية (359 ملفًا) |
