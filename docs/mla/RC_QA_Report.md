# CineView MLA 1.0.0~rc2 — تقرير QA لمرشح الإصدار (غير معتمد نهائيًا)

**الجهاز:** Vu+ Duo 4K SE · OpenATV 8.0.1 (build 20261003) · enigma2 57b7a51 · Python 3.14.7 · Slot 8 على USB فقط · 16.0°E فقط
**الفرع:** `dev/mla-openatv` (لم يُدمج شيء في `main`) · **الحزمة:** `enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc2_all.ipk`
**الحالة العامة:** RELEASE CANDIDATE — ينتظر اعتمادك البصري وقرارين (انظر «قرارات مطلوبة»). لا يُنشر كإصدار نهائي.

## 1. ما في الحزمة
| المكوّن | الوصف |
|---|---|
| Classic (6 أقسام) | التصميم المعتمد (20:02) بلا تغيير في التخطيط |
| Details | InfoBar + SecondInfoBar، عائلة مستقلة (`layouts/*/details`) |
| Cinema | InfoBar + SecondInfoBar، عائلة مستقلة (`layouts/*/cinema`) |
| 6 ثيمات | Navy (افتراضي)، Black، Graphite، Burgundy، Green، Deep Purple — ألوان + 7 أصول نقطية لكل ثيم |
| CineView Designs | واجهة التحكم: اختيار لكل قسم، ثيم، بوسترات لكل قسم، معاينة، تجربة مع تأكيد وتراجع تلقائي، Factory، ملفات تعريف (MENU) |
| المحرك + الحارس | توليدات مختومة، lkg، استعادة عند الإقلاع، حارس حلقة الأعطال (pre-start hook) |
| محرك البوستر الموحّد | موجود و**غير مفعّل افتراضيًا** (`runtime.json: poster_engine=identity`) |

## 2. الاختبارات الفعلية على الجهاز (هذه الجلسة)
| # | الاختبار | البناء | النتيجة | الحالة |
|---|---|---|---|---|
| 1 | Details: جولة 5 قنوات (IB + SIB بعد 3 و15 ث) | 18، 20 | قيم حية تتغير بالقناة؛ تتفق مع webif | DEVICE VERIFIED |
| 2 | Details: عربي طويل (بوسترات تعمل/متوقفة) | 18، 20 | محاذاة يمين، أول سطر يظهر أولًا، لا قص | DEVICE VERIFIED |
| 3 | Details: إيقاف البوسترات | 18، 20 | البوستر والإطار يختفيان والنص يتمدد | DEVICE VERIFIED |
| 4 | Details: الثيمات الست | 19 | بقايا navy ≤ 0.16% | DEVICE VERIFIED |
| 5 | Cinema: نفس المصفوفة + الثيمات الست | 19، 20 | بقايا navy ≤ 0.71% (اللوحة شبه الشفافة) | DEVICE VERIFIED |
| 6 | الاستقلال: Classic IB + Details/Cinema SIB | 19، 20 | كل قسم بتصميمه | DEVICE VERIFIED |
| 7 | تحقق نهائي للعائلتين (3 قنوات) | 22 | 0 tracebacks؛ لا تقييم IMDb للأخبار/الرياضة | DEVICE VERIFIED |
| 8 | الواجهة: حفظ ملف تعريف ← RED لا يطبّق ← تحميل ← GREEN تجربة ← إعادة تشغيل ← «نعم» ← ثابت ← حذف ← Factory | 22 | كل خطوة كما يجب | DEVICE VERIFIED |
| 9 | P6 (مُختبر سابقًا): تراجع المهلة، كراش الواجهة، SIGKILL، فشل التحقق | 13/14 | 7/7 | DEVICE VERIFIED |
| 10 | T8: تثبيت جديد 0.9.19 ← ترقية إلى rc1 (إعادة بناء اختيار Details) ← رفض الإزالة أثناء الاختيار ← إزالة ← إقلاع بالسكين الافتراضي ← إعادة تثبيت | 19→22 | ناجح؛ وُجدت 11 بقايا .pyc بعد الإزالة ← أُصلح postrm | DEVICE VERIFIED |
| 11 | T8b: ترقية rc1 ← rc2 في مكانها، إزالة، إعادة تثبيت | 22→23 | لا بقايا بعد الإزالة؛ الحالة في `/etc/enigma2/cineview_mla` محفوظة | DEVICE VERIFIED |
| 12 | محرك البوستر الموحّد على العائلتين، 12 قناة × 2 | 21 | خطأ واحد («Bilo jednom u Gazi» ← «…u Trubaru») ← أُصلح المطابق | أُعيد الاختبار في #13 |
| 13 | إعادة اختبار المحرك الموحّد بالمطابق الجديد (ذاكرة هوية فارغة، 12 قناة × 2) | 23 | 6 مطابقات صحيحة (Ad Astra، Licorice Pizza، Double Jeopardy، The Last Duel، Indiana Jones 4، Love Island Adria)، 0 خاطئة؛ «Bilo jednom u Gazi» مرفوض الآن (similar-title-only) | DEVICE VERIFIED |
| 14 | شريط EventView الفارغ | 18 | السبب للقطات: تمزّق قراءة grab أثناء إعادة الرسم (40 لقطة) | ROOT CAUSE IDENTIFIED (ظهوره على التلفاز غير مُتحقق) |
| 15 | العنوان العربي بسطر واحد | — | `rtltest`: RunningText في 57b7a51 يقيس RTL أفقيًا خطأ؛ الحل: تقليب عمودي بسطر كامل | DEVICE VERIFIED |
| 16 | انحدار Classic بعد تثبيت rc2 من الحزمة: InfoBar، SecondInfoBar، EventView، EPG، القنوات، PVR (EMC)، القائمة، البلجنات، CineView Designs | 23 | تفتح وتُرسم، 0 tracebacks | DEVICE VERIFIED |
| 17 | رابط التثبيت من الرسيفر نفسه (`wget` من GitHub) | rc2 | تنزيل ناجح، SHA256 مطابق | DEVICE VERIFIED |

اختبارات برمجية لكل بناء: المحرك 28/28، ShowIf 13/13، مطابقة البوستر (كل الحالات + حالة Gaza)، فحص `_` gettext، فحص الهندسة (لا تداخل، داخل 1920×1080).

## 3. أخطاء اكتُشفت وأُصلحت في هذه الجلسة
D-1 نصف سطر (ارتفاع السطر الحقيقي مُقاس: 22→25، 23→26) · D-2/D-9 العناوين بسطر واحد · D-3 وصف «التالي» عند إيقاف البوسترات · D-4 مربع رمادي ← صورة افتراضية · D-5/D-11 لا «-- --» ولا تقييم للأخبار والرياضة (`,hide` + تعرّف الفيلم/المسلسل من نص EPG) · D-6 شرطة بلا وقت · D-7 شريط التقدم يتبع الثيم · D-8 أسماء الخدمات تبدأ ظاهرة · C-1 «SNR» و«IMDb» كعناوين في Cinema · C-2 فراغ قبل الوقت · C-3 «NOW ON» · C-4 اسم المدينة · P5 العناوين المتشابهة · P8 بقايا .pyc بعد الإزالة.

## 4. مشكلات متبقية (غير مخفية)
| # | المشكلة | الأثر | الحالة |
|---|---|---|---|
| R-1 | **المحرك القديم للبوستر (الافتراضي)** يعرض بوسترات خاطئة: Dnevnik 3 ← Dog Days، Movie top ten ← Top 10 Hamsters، Skener 7 ← Scream 7، Nitko ← Nitro Circus | يخالف قاعدة «لا بوستر غير موثوق» | **قرار مطلوب** |
| R-2 | تقييم IMDb يعتمد على البحث بالعنوان؛ قد يخطئ لفيلم/مسلسل بعنوان مترجم | مخفّف (لا تقييم بلا تعرّف) | متبقٍ |
| R-3 | محرك enigma2 يكسر السطر الأول من النص العربي الملتف مبكرًا (السطر الأول أقصر) | النص كامل، الشكل فقط | قيد المنصة (وكذلك Classic) |
| R-4 | شريط التقدم يُرسم فارغًا حين لا يوجد حدث EPG | شكلي | متبقٍ (طفيف) |
| R-5 | ظهور «الشريط الفارغ» على التلفاز نفسه | غير مُتحقق | يحتاج نظرة بشرية |
| R-6 | HDMI-CEC عُطّل مؤقتًا في Slot 8 أثناء الاختبارات (التلفاز أطفأ الرسيفر) | — | **أُعيد** (01:08، السطر حُذف = الحالة قبل الاختبارات) |
| R-7 | أدوات التطوير CineViewMLATextTest/TextTest2 | — | **أُزيلت** من Slot 8 (01:08). بقي من مراحل سابقة: `CineView_FHD_1001` و`CineViewControl` (مرجع، Slot 8 فقط) |
| R-8 | P1/P2/P3 بنود ثانوية (CI workflow، Adapter، M2) | لا تؤثر على التشغيل | مؤجلة |

## 5. قرارات مطلوبة منك
1. **محرك البوستر الافتراضي:** أ) يبقى القديم (كما اعتمدت Classic) مع خطر البوسترات الخاطئة (4 أمثلة موثقة + فيلم 2025 ← بوستر 1997)، أو ب) يصبح المحرك الموحّد افتراضيًا (6/6 صحيحة، 0 خاطئة في #13؛ الصورة الافتراضية عند الشك). التوصية الهندسية: (ب).
   - سؤال تابع: هل يُطبَّق على Classic أيضًا إخفاء تقييم IMDb لغير الأفلام والمسلسلات؟ (Classic يعرض 7.9/10 لبرنامج رياضي).
2. **الاعتماد البصري** للعائلتين Details وCinema (المقارنة المصورة).

## 6. التثبيت والاستعادة
- تثبيت (من الرسيفر):
  ```
  wget -O /tmp/cineview-mla.ipk "https://github.com/habeb-s/CineView-FHD/raw/dev/mla-openatv/release/rc/enigma2-plugin-skins-cineview-fhd-mla_1.0.0~rc2_all.ipk"
  opkg install /tmp/cineview-mla.ipk
  ```
  SHA256: `d6d2e90f0d0a1b6205910fe921e35c19557ceead98af949ca808fea24fac3eca`. ثم اختر السكين وأعد تشغيل الواجهة.
- الحزمة ترفض أي صورة غير OpenATV 8.0.x، وترفض استبدال `enigma2_pre_start.sh` إن كان لغيرها.
- ترقية: يُعاد بناء اختيارك تلقائيًا بالحزم الجديدة؛ إن فشل يُفعَّل Factory.
- إزالة: اختر سكينًا آخر أولًا (الإزالة تُرفض أثناء الاختيار)، ثم `opkg remove enigma2-plugin-skins-cineview-fhd-mla`. ملفات التعريف والحالة تبقى في `/etc/enigma2/cineview_mla`؛ احذفها يدويًا إن أردت إزالة كاملة.
- نسخ احتياطية على USB: `/media/usb/cineview-mla/state/backup-*` (settings، حالة MLA، ملفات MLA قبل كل نشر)، و`backup-t8`/`backup-t8b`.

## 7. حالة الجهاز عند نهاية الجلسة (Slot 8)
- الحزمة `1.0.0~rc2` مثبتة عبر opkg (`install ok installed`)، السكين المختار CineView_FHD_MLA، التصميم Factory (Classic + Navy)، البوسترات تعمل، `poster_engine` غير مفعّل (القديم)، 0 tracebacks بعد آخر إقلاع.
- لم يُلمس: Slot 1/3، الفرع `main`، HDD، إعدادات Multiboot، التونر والطبق.

## 8. الأدلة
`docs/mla/evidence/`: `p7_details_build19`، `p7_details_build20`، `p7_cinema_build20`، `p9_final_build22`، `p8_ui_profiles_t3`، `p8_t8_package`، `p8_t8b_package_rc2`، `p8_regression_rc2`، `p5_identity_rc2` (مع سجل قرارات المطابقة)، و`EventView_band_evidence.md`، `P7_Designs_Acceptance.md`. سكربتات الجهاز: `tools/mla/devtools/device/`.
