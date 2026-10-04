# CineView MLA 1.0.0~rc3 — تقرير QA النهائي لمرشح الإصدار (غير معتمد نهائيًا)

**الجهاز:** Vu+ Duo 4K SE · OpenATV 8.0.1 (build 20261003) · enigma2 57b7a51 · Python 3.14.7 · Slot 8 على USB فقط · 16.0°E فقط
**الفرع:** `dev/mla-openatv` (لا دمج في `main`) · **الحزمة:** `release/rc/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc3_all.ipk`
SHA256 `e6fe24a7f74ff15cf0f1f6c00bb2159f855ab8202239e6bb0337e2e91718a9ed`
**الحالة:** RELEASE CANDIDATE — ينتظر اعتمادك البصري. `1.0.0` لن يُصدر قبله.

## 1. ما الجديد في rc3 (قراراتك 04:39)
| البند | التنفيذ | الحالة |
|---|---|---|
| المحرك الموحّد للبوستر افتراضي، والقديم بديل | `runtime.json` بلا قيمة = موحّد؛ `poster_engine=legacy` = القديم. سطر «Poster engine» في CineView Designs، يُحفظ في ملفات التعريف، ويُطبَّق بعد إعادة تشغيل الواجهة | DEVICE VERIFIED (تبديل من الواجهة والعودة، 06:05–06:08) |
| إخفاء تقييم IMDb لغير الأفلام والمسلسلات في كل التصاميم بما فيها Classic | المحوّل `…,hide`: تقييم فقط لحدث متعرَّف عليه كفيلم/مسلسل من نص EPG وليس عامًا. في Classic: شارة IMDb صارت Pixmap مشروطة في نفس الموضع والحجم، تختفي مع التقييم | DEVICE VERIFIED |
| لا تغيير لتخطيط Classic أو Details أو Cinema | لم يتغير أي موضع أو حجم | — |

## 2. الاختبار الشامل على الرسيفر (rc3، 04:53–06:18)
| # | الاختبار | النتيجة | الحالة |
|---|---|---|---|
| 1 | ترقية rc2 ← rc3 عبر opkg | ناجحة، المحرك الموحّد يعمل افتراضيًا | DEVICE VERIFIED |
| 2 | 3 إعدادات (Details IB + Cinema SIB؛ Cinema IB + Details SIB؛ Classic) × 6 ثيمات، IB وSIB | 18 إعادة تشغيل، 0 tracebacks، 0 أخطاء سكين جديدة | DEVICE VERIFIED |
| 3 | شاشات Classic الأخرى × 6 ثيمات: EventView، EPG، قائمة القنوات، PVR، القائمة الرئيسية، CineView Designs | تفتح وتُرسم وتتبع الثيم | DEVICE VERIFIED |
| 4 | إيقاف البوسترات في كل الأقسام (3 إعدادات + شاشات Classic) | البوستر والإطار والصورة الافتراضية تختفي والنص يتمدد | DEVICE VERIFIED |
| 5 | جولة 5 قنوات × 3 إعدادات مع `/api/signal` | AGC وBER متطابقة؛ SNR ضمن ±1%؛ القيم تتغير بتغيير القناة | DEVICE VERIFIED |
| 6 | نص عربي طويل: IB وSIB للإعدادات الثلاثة + EventView | Details وCinema سليمان؛ ملاحظة C-1 على Classic | DEVICE VERIFIED |
| 7 | الواجهة: خيار محرك البوستر | Legacy ← إعادة تشغيل ← لا سجل identity؛ Unified ← إعادة تشغيل ← `engine=identity` | DEVICE VERIFIED |
| 8 | ملف تعريف: حفظ (يشمل poster_engine) ← RED لا يطبّق ← تحميل ← GREEN تجربة ← إعادة تشغيل ← إبقاء ← حذف ← Factory | كل الخطوات | DEVICE VERIFIED |
| 9 | الحزمة: إعادة تثبيت النسخة نفسها مرفوضة من opkg، رفض الإزالة أثناء اختيار السكين، إزالة نظيفة (0 بقايا)، إقلاع بالسكين الافتراضي، إعادة تثبيت | كما يجب | DEVICE VERIFIED |
| 10 | الاتصال | ping/ssh/webif كل دقيقة طوال الجلسة؛ `webif=000` يظهر فقط أثناء إعادات التشغيل المقصودة | RUNTIME TESTED |

الأدلة: `docs/mla/evidence/rc3_sheets` (18 لوحة مقارنة)، `rc3_matrix` (الجولة، العربي، البوسترات المتوقفة، السجل)، `rc3_ui`، `rc3_ui_profiles`، `rc3_t8b`.
اختبارات برمجية: المحرك 28/28، ShowIf 13/13، مطابقة البوستر كلها ناجحة، فحص gettext.

## 3. شريط EventView الفارغ — النتيجة
- enigma2 57b7a51 يرسم مباشرة في صفحة الإطار المعروضة (وضع التركيب المؤجل معطّل في المصدر)، وأداة grab تقرأ الصفحة المعروضة؛ لقطة `dd` من `/dev/fb0` تطابق grab.
- قياس على الرسيفر (عينات كل 0.15–0.6 ms): أثناء تمرير الوصف يفرغ الثلث العلوي من الصندوق **فعلًا في الإطار المعروض** 2–6 ms، حتى ~1.2 مرة في الثانية؛ النص الثابت لا يفرغ أبدًا.
- إذن المشكلة ليست في التقاط الصور. هل تُرى على التلفاز كوميض لإطار واحد؟ **غير محسومة** دون مشاهدة الشاشة. التفاصيل: `EventView_band_evidence.md`.

## 4. ملاحظات على Classic (لم تُغيَّر — تحتاج موافقتك)
| # | الملاحظة | الدليل | الإصلاح المقترح |
|---|---|---|---|
| C-1 | عنوان Main InfoBar بالعربي يبدأ من آخره (نفس قيد RunningText الذي أصلحته في Details/Cinema) | `rc3_sheets/05_ib_arabic.jpg` | تقليب سطري للعناوين العربية فقط، كما في العائلتين |
| C-2 | وصف قائمة القنوات يدخل من أسفل الصندوق (`movetype=running`) فيبدو أعلاه فارغًا ثوانٍ | `rc3_sheets/15_themes_Channel_list.jpg` | يبدأ من الأعلى ثم يتحرك (`swimming`) |

## 5. مشكلات متبقية
| # | المشكلة | الحالة |
|---|---|---|
| R-1 | شريط EventView (§3) | مفتوح — يحتاج مشاهدة التلفاز |
| R-2 | تقييم IMDb يعتمد على البحث بالعنوان؛ مخفّف بقاعدة التعرّف | متبقٍ |
| R-3 | محرك enigma2 قد يجعل السطر الأول من العربي الملتف أقصر | قيد المنصة |
| R-4 | شريط التقدم يُرسم فارغًا حين لا يوجد حدث | شكلي |
| R-5 | بنود P1/P2/P3 الثانوية (CI، Adapter، M2) | مؤجلة |
| R-6 | من مراحل سابقة في Slot 8: `CineView_FHD_1001` و`CineViewControl` (مرجع) | باقية حتى تقرر |

## 6. التثبيت والاستعادة
```
wget -O /tmp/cineview-mla.ipk "https://github.com/habeb-s/CineView-FHD/raw/dev/mla-openatv/release/rc/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc3_all.ipk"
opkg install /tmp/cineview-mla.ipk
```
- يقبل OpenATV 8.0.x فقط، ولا يستبدل `enigma2_pre_start.sh` إن كان لغيره. الترقية تعيد بناء اختيارك؛ إن فشلت يُفعَّل Factory.
- الإزالة: اختر سكينًا آخر أولًا، ثم `opkg remove enigma2-plugin-skins-cineview-fhd-mla`. لا يبقى شيء من MLA إلا `/etc/enigma2/cineview_mla` (ملفات التعريف والحالة).
- محرك البوستر القديم: CineView Designs ← Poster engine ← Legacy ← GREEN ← أعد تشغيل الواجهة.
- نسخ احتياطية على USB: `/media/usb/cineview-mla/state/backup-rc3` (قبل الترقية)، `backup-t8b`، `settings.pre-finalize`، وما قبلها.

## 7. حالة الجهاز عند نهاية الجلسة (Slot 8)
`1.0.0~rc3` مثبتة عبر opkg، السكين CineView_FHD_MLA، Factory (Classic + Navy)، البوسترات تعمل، المحرك الموحّد، 0 tracebacks، HDMI-CEC على حالته الأصلية، أداة TextTest2 أُزيلت بعد الاختبار.
لم يُلمس: Slot 1/3، الفرع `main`، HDD، Multiboot، التونر والطبق.
