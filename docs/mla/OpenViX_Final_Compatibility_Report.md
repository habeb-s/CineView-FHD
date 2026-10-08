# CineView MLA — تقرير توافق OpenViX 6.9 النهائي (Slot 4)

**التاريخ:** 2026-10-08
**الجهاز:** Vu+ Duo 4K SE
**الصورة:** OpenViX 6.9.002، وفيها enigma2 من نسخة OpenViX/enigma2 `d3f089af4e`
- إثبات الإصدار: بصمات ملفات `.pyc` تطابقت مع المصدر في 409 ملفات من 409.
- Python 3.14.7.
- الـSlot: Slot 4 على USB، المسار `duo4kse/linuxrootfs4`.

**الحزمة:** `enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openvix1_all.ipk`
- SHA256: `955d102826bf30854003a7f5cd8e5d75b4f9e808b783bfe1fb53571acfa76d87`

**الحالة:** DEVICE VERIFIED + REGRESSION VERIFIED على OpenViX 6.9 (Slot 4).
- لم يُنشر شيء.
- لم يُدفع (push) شيء إلى GitHub.

**HDD:** لم يحدث أي تعديل.
- الحادثة الوحيدة: أمر قراءة واحد `ls /media/hdd` نُفّذ بالخطأ داخل أمر فحص حالة، قبل تعليماتك بمنع القراءة. تم الإفصاح عنه.
- بعد التعليمات لم يحدث أي وصول إلى HDD.
- كل التسجيلات والكاش واللوجات كانت على USB الخاص بـSlot 4 أو على `/tmp`.

---

## الملخص

| البند | النتيجة |
|---|---|
| OpenViX 6.9 compatibility | **PASS**: كل الوظائف المتفق عليها مختبرة فعلياً على الرسيفر |
| اختلافات OpenViX الحقيقية | **3**، وكلها معالجة دون تغيير أي تصميم (الجدول أدناه) |
| Crashes | **0**: لا يوجد أي crash log طوال اليوم |
| Tracebacks من CineView | **0** |
| Skin errors من CineView | **0** |
| Tracebacks/Skin errors من مكوّنات أخرى | تتبّعتها كلها وتأكدت أنها ليست من CineView: (أ) 53 رسالة `InputHotplug connectionLost` من twisted، واحدة عند كل إيقاف للواجهة. (ب) خطآن في **سكين شاشة LCD الخاص بالصورة** `OE-A_LCDSkin_9`. الحزمة لا تحتوي أي ملف للشاشة الأمامية |
| OpenATV static parity | **PASS** عند البناء (ملفات تصاميم OpenATV المعتمدة مطابقة) |
| OpenBH | لم يتغير: لا تعديل على Slot 5 ولا على حزمة OpenBH النهائية |
| Rollback | متاح: نسخة الإعدادات محفوظة على Slot 4، وحزمة الإزالة مختبرة (L2) |

---

## اختلافات OpenViX الفعلية (مقابل OpenBH) وطريقة معالجتها

| # | الاختلاف المُثبت | الدليل | المعالجة | النطاق |
|---|---|---|---|---|
| 1 | PluginBrowser في OpenViX لا يحتوي `self["key_menu"]` | `contracts.py` مقابل مصدر OpenViX: الفرق الوحيد بين العقدين | ملف `common.openvix.xml` هو نسخة من `common.openbh.xml` بدون widget `key_menu` | OpenViX فقط |
| 2 | شريط التقدم الافتراضي في قائمة القنوات **يمين** في OpenViX (`barright`)، بينما هو يسار في OpenBH | `UsageConfig.py:317` | لا يحتاج تعديلاً. حل أسماء القنوات يغطي الحالتين. تم اختبار المصفوفة كاملة بالوضعين | — |
| 3 | الترجمة العربية في OpenViX للزر الأحمر قصيرة أصلاً ("بحث IMDb") | `ar.po` الخاص بـOpenViX، ولقطة `arabic.jpg` | لا يحتاج `label_overrides`، فمحوّل OpenViX لا يحتوي هذا الإعداد | OpenViX فقط |

**ملفات OpenViX (موجودة محلياً فقط على الفرع `dev/mla-openvix`):**
- `mla/plugin/CineViewMLA/image_adapter.py`: أُضيف مدخل `openvix`، وهو نفس عائلة OpenBH:
  - `ChoiceBox(list=)`.
  - autostart shutdown hook.
  - PluginDownloadBrowser.
  - name_clip `complexcolumn`.
- `mla/images/openvix/core/common.openvix.xml`
- `mla/images/openvix/sections.openvix.json`
- `mla/images/openvix/transform.py`: يعيد استخدام `../openbh/transform.py` بدل نسخه.
- `tools/mla/package_ipk.py`:
  - شرط الصورة: `openvix` بإصدار `6.9` أو `6.9.*`.
  - إعادة تشغيل السكربتات تحت BusyBox، لأن `/bin/sh` هو bash على OpenViX أيضاً.
- `tools/mla/build_openvix.sh`: يبدأ بفحص parity، ثم يبني، ثم يجمّع `.pyc` بـPython الخاص بالرسيفر، ثم يحزم.
- `tools/mla/test_image_adapter.py`: أُضيفت فحوص openvix. النتيجة PASS.

**Common Core:** لم يتغير. كود الـPython والتصاميم كما هي. الإضافة الوحيدة مدخل في جدول المحوّلات.

---

## الاختبارات الفعلية على الرسيفر

| المجموعة | النطاق | النتيجة |
|---|---|---|
| التثبيت الأول | نسخة احتياطية، تثبيت، تثبيت كاش البوستر على `/tmp` قبل أول تشغيل، تفعيل السكين | PASS: الحالة `install ok installed`، وبدء التشغيل بلا Traceback |
| الشاشات الأساسية (t106) | InfoBar، SIB، ChannelSelection، العلامة، التمرير، Grid/Single/Multi/IB EPG، EventView/Simple، PVR، Plugin Browser، Install/Remove Plugins، Console، Designs، Setup، MessageBox: **23 خطوة** | PASS. خطوة Console فيها خطأ واحد من سكين LCD الخاص بالصورة (ليس CineView) |
| أسماء القنوات الطويلة | 6 تصاميم × الشريط (يمين الافتراضي ويسار) × باقة طويلة وقصيرة: **24 تشغيلاً**. الاسم المستخدم "AL MALAKOOT SAT – THE KINGDOM SAT الملكوت سات" | PASS: لا تداخل ولا التصاق. مع الشريط يسار يظهر الاسم كاملاً في Classic |
| أسماء القنوات: وظيفي | zap من صف مختصر في الوضعين | PASS: الخدمة المشغّلة وOpenWebif وlastservice كلها بالاسم الكامل |
| أسماء القنوات: قائمة All | 12,637 صفاً | PASS: 3.4 إلى 3.5 ثانية. الباقات العادية بين 7 و13 ms |
| النماذج الخمسة | Classic، Details، Cinema، Modern، Minimal × 10 شاشات: **50** | PASS |
| الثيمات الستة | × 5 شاشات: **30** | PASS |
| البوسترات تشغيل/إيقاف | Classic وDetails: **10** | PASS، وإعادة التوزيع صحيحة |
| EPG بدون PiG | 5 حزم × 4 شاشات: **20** | PASS: كل حزمة تعرض شاشتها الخاصة |
| العربية (ar_AE) | **13** شاشة | PASS: RTL، و"بحث IMDb" كامل، وأزرار Plugin Browser سليمة |
| CineView Designs | F0 نموذج Modern ثم Apply ثم Keep. F1 Profiles: حفظ، ثم تحميل، ثم حذف | PASS |
| الثيم والرجوع التلقائي | F2 Keep. F3 بدون رد يرجع تلقائياً إلى g000038 | PASS |
| Factory | F4 | PASS: Classic + Navy |
| Guardian | التشغيل الثالث غير النظيف يرجع إلى last-known-good | PASS: السجل يُظهر `guardian: count=3: rollback` |
| PVR بتسجيل حقيقي | تسجيل حقيقي 90 ثانية لقناة HBO HD المشفّرة (41 MB) في `/home/root/cvmla-testmedia` على USB، ثم القائمة وINFO والتنقل والتشغيل في MoviePlayer والإيقاف، ثم تخطيطات Cover وCinema وModern وMinimal، ثم حذف ملفات الاختبار | PASS. `timers.xml` مطابق للنسخة الاحتياطية. عند تشغيل MoviePlayer ظهر خطأ واحد `IsHDHDR` في سكين LCD الخاص بالصورة |
| CAM/ECM | الأوضاع Full وProfile وHide مع ncam يعمل | PASS. عنوان السيرفر محجوب في الأدلة |
| CAM في التصاميم | Classic وDetails وCinema: InfoBar وSIB وEventView، 7 لقطات لكل منها | PASS |
| تمرير حقل CAM | Details وCinema على دورة كاملة | PASS، والإعدادات أُعيدت كما كانت |
| Bitrate | قيمة حية | PASS: تغيّرت بين 0.44 و3.36 Mbps مع تغيّر المحتوى |
| L1 دورة الحزمة: حماية الإزالة | `prerm` يرفض الإزالة والسكين مفعّل | PASS: الملفات باقية |
| L2 الإزالة | سكين آخر، ثم الإزالة | PASS: ملفات MLA أُزيلت، وحالة المستخدم باقية، والواجهة تعمل على CineView_FHD بلا أخطاء |
| L3 الاسترجاع | إعادة التثبيت ثم التفعيل | PASS |
| L4 إعادة التثبيت | `--force-reinstall` | PASS |
| preinst ×100 (التشغيل الأول، ضمن t108v) | حلقة `seq 1 100`، والعدّ وحده بلا سجل لكل تشغيل | 0/100 انهيار |
| **preinst ×100 (إعادة موثقة، ضمن t109v I10)** | **100 تشغيل فعلي، وكل تشغيل مسجّل برقمه وكود خروجه** (`I10_preinst_runs.txt`)، ومدتها 12 ثانية | **100 من 100 بكود خروج 0، و0 انهيار (كود ≥ 128)** |

**توضيح preinst:** نُفّذ 100 تشغيل فعلي، وليس 10. الرقم 10 في التقرير يخص "البوسترات تشغيل/إيقاف: 10" فقط. التشغيل الأول لم يسجّل كل محاولة على حدة، لذلك أعدته مع سجل لكل تشغيل.

**ملاحظة عن العدّ:** خانة "missing" و"notimpl" في السجلات **مطابقة لـOpenBH المعتمد**:
- رسائل "Skin is missing element" من الشاشات الأصلية لعناصر اختيارية.
- `halign` على ePixmap في EventView وقائمة القنوات.
- `ePicLoad ... (Function not implemented)` من نظام التشغيل.

---

## Smart Installer 1.1.0 (مع OpenViX): مختبر فعلياً على Slot 4

**الملفات:** `release/openvix-6.9/` على الفرع المحلي `dev/mla-openvix`، ونسخة في `~/cineview-mla/release_openvix/` على الـagent.

| الملف | SHA256 |
|---|---|
| `enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openvix1_all.ipk` | `955d102826bf30854003a7f5cd8e5d75b4f9e808b783bfe1fb53571acfa76d87` |
| `cineview-install.sh` (1.1.0) | `40e4cccacbd433202539db6fab94932c7155fa7d0dac4e657fac98019c258709` |
| `cineview-uninstall.sh` | `563b67acde741d6ea75314b1a16dd10da61bd3587c5010965d2545889ccfd756` |

**الأساس:** المثبّت 1.0.0 الخاص بإصدار OpenBH، من CineView-MLA بالـcommit `08f09b9`.

**التعديلات:** تُطبَّق بـ`mkvix.py`، وكل استبدال فيه دقيق ويتوقف إن لم يجد النص المستهدف مرة واحدة بالضبط.

**كشف الصورة:**
- الاسم من `enigma.info` (`distro`)، مع تأكيد مستقل من عقد شاشة PluginBrowser الخاص بالصورة.
- OpenATV: `PackageAction`.
- OpenBH: `PluginDownloadBrowser` مع `key_menu`.
- **OpenViX:** `PluginDownloadBrowser` بدون `key_menu`.
- الدليل: مصادر enigma2 للصور الثلاث، و`.pyc` المثبت على Slot 4.
- **شرط `key_menu` في فرع OpenBH جديد.**
  - بدونه، صورة OpenViX يقول `enigma.info` فيها "openbh 5.6" كانت تُعرَّف على أنها OpenBH. الاختبار N2b أثبت ذلك قبل الإصلاح.
  - التحقق: ثابت فقط، من مصدر OpenBH (`PluginBrowser.py` يحتوي `key_menu`، والنسخة المترجمة تحتويه).
  - اختبار المثبّت على OpenBH نفسه معلّق، لأن Slot 5 لم يُقلع.

**كشف الجهاز:**
- من `machinebuild` في `enigma.info`، مع مقارنته بملف الجهاز الخاص بتعريف Vu+ (`/proc/stb/info/vumodel`) عند وجوده.
- إذا اختلفا يتوقف المثبّت.
- **`/proc/stb/info/model` لا يُستخدم أبداً.** على هذا الجهاز يعطي `dm8000`، وهي قيمة خاطئة.

**الإصدار:**
- OpenViX 6.9 مدعوم.
- أقدم من 6.9: يتوقف ("too old").
- 7.x وما بعده: يتوقف ("not checked").

**Python:** يشترط 3.14.

**الحماية:**
- التحقق من SHA256 قبل أي تغيير.
- نقطة استرجاع قبل كل تثبيت (settings + حالة CineView).
- إصلاح التثبيت الناقص.
- محاولة واحدة إضافية فقط عند انهيار shell الصورة.
- الرجوع لإصدار أقدم يحتاج `FORCE=1`، ويتم بـ`--force-downgrade`.
- كاش البوستر المثبّت يبقى كما هو.

**عنوان الحزمة:** ما زال placeholder (`@OPENVIX_URL@`)، لأن الحزمة غير منشورة.
- التشغيل العادي يتوقف برسالة "not released yet" دون أي تغيير.
- الاختبارات استخدمت ملف الحزمة على الرسيفر عبر متغيرات الاختبار في المثبّت (`CVMLA_PKG_URL` و`CVMLA_PKG_SHA` و`CVMLA_VERSION`).
- SHA256 الحزمة الحقيقية مثبّت داخل المثبّت.

| # | السيناريو (`sh cineview-install.sh` على الرسيفر) | النتيجة |
|---|---|---|
| I1 | التشغيل العادي، والحزمة غير منشورة | يتوقف، ولا يتغير شيء |
| I1b | `DRYRUN=1` | كل الفحوص PASS: الجهاز Vu+ Duo4K SE، OpenViX 6.9، Python 3.14، المساحة، الكاش (إعدادك، باقٍ) |
| N1 | `enigma.info` يقول openatv | يتوقف: الشاشات ليست شاشات OpenATV |
| N2 | يقول openbh | يتوقف: الشاشات ليست شاشات OpenBH |
| N2b | يقول openbh 5.6 | قبل الإصلاح: يُعرَّف خطأً على أنه OpenBH 5.6. **بعد الإصلاح: يتوقف** |
| N3 | بلا اسم صورة | يتوقف |
| N4 | openvix 6.8 | يتوقف (too old) |
| N5 | openvix 7.0 | يتوقف (not checked) |
| N6 | موديل Vu+ مختلف (vuuno4kse) | يتوقف (الموديل غير محدد بثقة) |
| N7 | `enigma.info` غير موجود | يتوقف |
| بعد N1–N7 | حالة الحزمة، وبصمة settings، والتصميم | **مطابقة للبداية** |
| I2 | الإصدار نفسه مثبّت | "already installed and verified" |
| I3 | SHA256 خاطئ | يتوقف، ولا يتغير شيء (الحالة مطابقة) |
| I4 | ترقية من openvix1 إلى openvix2 (حزمة اختبار بنفس المحتوى ورقم إصدار أعلى) مع `RESTART=1` | PASS: نقطة استرجاع، وإعادة تشغيل الواجهة، والتصميم باقٍ |
| I5 | انهيار shell الصورة (signal 11) مرتين، بحزمة اختبار يُسقط فيها الـpreinst نفسه | محاولة واحدة إضافية فقط، ثم توقف برسالة واضحة، والحالة `half-installed`. لا حلقة متكررة |
| I6 | التشغيل التالي | يكتشف التثبيت الناقص، ويصلحه بإعادة تثبيت موثقة، والحالة `install ok installed` |
| I7 | الرجوع إلى openvix1 (`FORCE=1`) | PASS: `--force-downgrade`، وإعادة تشغيل الواجهة، والتصميم باقٍ |
| I8 | `cineview-uninstall.sh` والسكين مفعّل | PASS: إيقاف الواجهة، الرجوع لسكين الصورة الافتراضي، الإزالة، تشغيل الواجهة. الحالة والملفات الشخصية باقية |
| I9 | تثبيت جديد بالمثبّت، ثم اختيار السكين | PASS (التصميم الافتراضي Classic + Navy حسب تصميم الحزمة) |
| I9b | تحقق | "already installed and verified" |
| I10 | preinst ×100 مع سجل لكل تشغيل | 100 من 100 بكود خروج 0 |

**عن الاختبارات:**
- I4 إلى I9 نُفّذت بالمثبّت قبل إضافة شرط `key_menu` لفرع OpenBH. مسار OpenViX لم يتغير بعدها.
- بعد الإضافة أُعيدت كل الحالات غير المغيِّرة (I1 وI1b وI2 وN1 إلى N7 وN2b) بالمثبّت النهائي. النتائج أعلاه، والحالة بقيت دون تغيير.
- لا انهيار في أي إعادة تشغيل للواجهة.
- حزمتا الاختبار (openvix2 وحزمة الانهيار) لم تبقيا على الرسيفر، والنهائي openvix1.

**ملاحظة صوت:**
- `config.audio.volume` تغيّر من 55 إلى 40 أثناء نافذة I4، بين نقطتي الاسترجاع 16:26:46 و16:28:13. القيمة الحية الآن 40.
- أدواتي لم ترسل أي زر صوت؛ أرسلت فقط EXIT (174) وOK (352).
- لم أغيّره. أستطيع إرجاعه إلى 55 إن أردت.

## ملاحظات أصلية في OpenViX (موثقة فقط، دون تعديل نظام الصورة)

1. **سكين شاشة LCD الخاص بالصورة (`OE-A_LCDSkin_9`):**
   - الخطأ الأول: `ConsoleSummary` يطلب `parent.summary_description`، وهو غير موجود في Console على OpenViX.
   - الخطأ الثاني: `InfoBarMoviePlayerSummary` يطلب `IsHDHDR`، وهو غير موجود في محوّل ServiceInfo على OpenViX. يظهر عند فتح MoviePlayer.
   - النتيجة: الشاشة الرئيسية لا تتأثر.
   - هذا سكين OpenATV للشاشة الأمامية مستخدم على OpenViX، وليس جزءاً من CineView.
2. **زر INFO** في OpenViX يفتح Graphical EPG، وهذا إعداد الصورة الأصلي. EventView نفسه مختبر من مدخله.
3. **عنوان EventView بالعربي أحياناً:**
   - OpenViX يضع `event.getEventName()` كعنوان للشاشة (`EventView.setEvent`).
   - بيانات EPG على Slot 4 تأتي من إضافات طرف ثالث (ترجمة واستيراد EPG).
   - التسجيل نفسه حُفظ بنفس الاسم في `.eit`. ليس من CineView.
4. **RunningText** (اسم القناة في لوحة Posterlist ونصوص الأحداث) يتوقف عند آخر النص بعد دورة "swimming":
   - الـRenderer الأصلي مطابق حرفياً بين OpenViX وOpenBH (البصمة نفسها `277c1eb0`).
   - السلوك نفسه المعتمد.
5. **رفض `prerm` للإزالة** يترك الحالة `deinstall ok installed`. هذا سلوك opkg العام، والملفات باقية، والتثبيت التالي يعيد الحالة إلى `install`.
6. **إعادة التثبيت بعد إزالة كاملة** تبدأ بالتصميم الافتراضي (Classic + Navy). هذا تصميم `postinst` الموحد في كل الصور.

---

## الحالة النهائية لـ Slot 4 بعد التنظيف

**ما بقي (بعد اختبارات المثبّت أيضاً):**
- الحزمة `1.0.0~openvix1`، والسكين المفعّل `CineView_FHD_MLA` (Classic + Navy).
- نقاط الاسترجاع التي أنشأتها اختبارات المثبّت أُرشفت على الـagent، ثم حُذفت من الرسيفر.
- الفرق مع الإعدادات الأصلية:
  - السكين المختار.
  - `startCounter`.
  - `config.audio.volume` (انظر ملاحظة الصوت).
- حالة المستخدم في `/etc/enigma2/cineview_mla`.
- كاش البوستر مثبّت على `/tmp/CINEVIEW-MLA/poster` حتى لا يُستخدم HDD.
- النسخة الاحتياطية `/home/root/mla-backup-20261008-openvix/`، وفيها `settings` وقائمة الحزم.

**ما حُذف (ملفات الاختبار فقط):**
- أداة الاختبار `CineViewMLAScreenOpen`.
- `/tmp/cvmla*`.
- مجلد التسجيل التجريبي.
- لوجات debug الخاصة بالاختبار، بعد أرشفتها على الـagent.
- أسطر الإعدادات التي أضافتها الاختبارات:
  - `enabledebug`
  - `last_movie_played`
  - `show_event_progress_in_servicelist`

**الفرق مع الإعدادات الأصلية:**
- `config.skin.primary_skin=CineView_FHD_MLA/skin.xml` (مقصود).
- `startCounter` (عداد طبيعي).

**الخدمة الحالية:** HBO HD، وهي آخر خدمة قبل الاختبار.

**الإقلاع:** STARTUP ما زال على **Slot 5 (OpenBH 5.6)**. أي إعادة تشغيل أو انقطاع كهرباء يعيد الرسيفر إلى OpenBH.

---

## التثبيت والاسترجاع

**بالمثبّت الذكي (بعد نشر الحزمة وتعبئة عنوانها):**
```
sh cineview-install.sh
```
- `DRYRUN=1`: فحص فقط.
- `RESTART=1`: يعيد تشغيل الواجهة في النهاية.
- `FORCE=1`: إعادة تثبيت أو رجوع لإصدار أقدم.

**الإزالة:**
```
sh cineview-uninstall.sh
```
- إذا كان السكين مفعّلاً، يرجع لسكين الصورة أولاً.

**التثبيت اليدوي على OpenViX 6.9:**
```
opkg install enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openvix1_all.ipk
```
- الـpreinst يتوقف على أي صورة غير openvix 6.9.
- بعد التثبيت: Menu > Setup > User Interface > Skin، ثم اختر CineView_FHD_MLA.

**الاسترجاع:**
1. اختر سكيناً آخر (السابق كان `CineView_FHD/skin.xml`).
2. نفّذ:
   ```
   opkg remove enigma2-plugin-skins-cineview-fhd-mla
   ```
   (اختُبر في L2.)
3. النسخة الأصلية من الإعدادات موجودة في `/home/root/mla-backup-20261008-openvix/settings`.

---

## الأدلة

**مكان الأدلة:** `docs/mla/evidence/openvix_slot4/`
- عناوين IP محجوبة.
- عنوان سيرفر CAM مغطى في لقطة وضع Full.

**الصور:**
- `first_run_sections.jpg`
- `names_default.jpg`
- `names_barleft.jpg`
- `models.jpg`
- `themes.jpg`
- `epg_posters.jpg`
- `arabic.jpg`
- `designs_f.jpg`
- `pvr.jpg`
- `cam_modes_full_profile_hide_masked.jpg`
- `final_state_infobar.jpg`

**السجلات (`*.log`):** ملخص كل تشغيل، وفيها عدّادات `tb`، و`skinerr`، و`missing`، و`notimpl`.

---

## ما زال معلّقاً (خارج مرحلة OpenViX)

- **OpenATV Slot 8 Runtime Regression:** يحتاج إقلاعاً بموافقتك. الفحص الثابت PASS.
- **شرط `key_menu` الجديد في فرع OpenBH من المثبّت:** تحقق ثابت فقط. يُختبر على OpenBH عند إقلاع Slot 5.
- **عنوان حزمة OpenViX في المثبّت:** placeholder حتى يُنشأ المستودع الخاص وتُنشر الحزمة فيه.
- **الرفع والنشر:** لا رفع ولا نشر إلى GitHub قبل موافقتك. الفرع `dev/mla-openvix` محلي فقط.

---

## الأرشيف الخاص (2026-10-08 16:44)

- **المستودع:** https://github.com/habeb-s/CineView-MLA-OpenViX
  - **Private:** نعم، ومحقق: الوصول بدون توثيق يعطي 404 من API وraw والويب.
  - **الفروع:** `openvix-6.9` (الافتراضي) و`main`.
- **الإصدار:** Tag `openvix-6.9-final-1.0.0-openvix1`، وRelease خاص بعنوان "CineView MLA 1.0.0~openvix1 (OpenViX 6.9) - private".
  - الأصول: ipk، و`cineview-install.sh`، و`cineview-uninstall.sh`، و`SHA256SUMS`.
  - GitHub يغيّر "~" إلى "." في اسم ملف الأصل فقط.
- **التحقق بعد إعادة التنزيل:**
  - الـclone يطابق الـsnapshot بايتاً ببايت (1603 ملفاً).
  - `sha256sum -c` نجح لكل الملفات.
  - الحزمة في المستودع وفي الـRelease مطابقة (`cmp`) للحزمة المختبرة على Slot 4 (`955d1028…`).
  - السكربتات وSHA256SUMS في الـRelease مطابقة لملفات المستودع.
- **رابط التحميل العام:** غير مفعّل (`@OPENVIX_URL@`).
- **شرط كشف OpenBH الجديد:** يحتاج Runtime Regression على Slot 5.
- **المستودعات الأخرى:** CineView-FHD وCineView-MLA وCineView-MLA-OpenBH لم تُلمس. آخر push لها كان قبل 09:00 UTC.

---

## تنظيف CineView FHD القديم من Slot 4 (2026-10-08، من 16:50 إلى 17:30)

### الجرد قبل التنظيف

| الفئة | العنصر | المالك (دليل) | القرار |
|---|---|---|---|
| **CineView القديم** | حزمة `enigma2-plugin-skins-cineview-fhd-offline-openvix` 2.1.20260923-r1 | opkg. تملك فقط `/usr/share/cineview-fhd-offline/openvix/payload.tar.gz`. بلا prerm/postrm | أُزيلت |
| **CineView القديم** | حزمة `enigma2-plugin-skins-cineview-fhd-universal-offline` 2.1.20260923-r1 | opkg. تملك فقط payloads في `/usr/share/cineview-fhd-offline/universal/` | أُزيلت |
| **CineView القديم** | `/usr/share/enigma2/CineView_FHD/` (السكين القديم، 362 ملفاً) | فكّه postinst الحزمتين من الـpayload. كل ملفاته من الـpayload | أُزيل |
| **CineView القديم** | `Plugins/Extensions/CineViewControl/` (البلجن "CineView Control") | من الـpayload. ظهر في Plugin Browser | أُزيل |
| **CineView القديم** | Converters: `CineViewBitrate`، `CineViewCPUTemp`، `CineViewCamInfo`، `CineViewIMDb`، `CineViewTransponder`، `CineViewTransponderInfo` (`.py`/`.pyc`). Renderer: `CineViewPosterX` (`.py`/`.pyc`) | من الـpayload. بلا حزمة مالكة (`opkg search`) | أُزيلت (13 ملفاً) |
| **CineView القديم** | `/usr/share/enigma2/CineView_FHD.rollback-broken-20260922/` | نسخة احتياطية قديمة للسكين القديم | أُزيلت |
| **CineView القديم** | `/etc/enigma2/CineView_FHD-before-latest-merge-20260922-221719/` و`/etc/enigma2/CineViewControl-before-update-20260922-185907.tar.gz` | نسخ احتياطية قديمة | أُزيلت |
| **CineView القديم** | `/root/cineview-openvix-backups/` (10.5 MB) | نسخ احتياطية قديمة للنسخة القديمة | أُزيلت |
| **CineView القديم** | إعدادات `config.plugins.cineview.poster_infobar` و`config.plugins.cineview.theme` | namespace البلجن القديم (`CineViewControl/plugin.py:27`) | أُزيلت |
| **CineView القديم** | `Plugins/Extensions/CineViewControl` داخل `config.misc.pluginbrowser.plugin_order` | مرجع لبلجن محذوف | أُزيل هذا العنصر وحده من القائمة |
| **CineView MLA** | `enigma2-plugin-skins-cineview-fhd-mla` 1.0.0~openvix1، `/usr/share/enigma2/CineView_FHD_MLA/`، `Plugins/Extensions/CineViewMLA/`، `Components/CineViewMLA*`، `Converter/CineViewMLA*`، `Renderer/CineViewMLA*`، `/etc/enigma2/cineview_mla/` | opkg (الحزمة الحالية) | **أُبقي** |
| **CineView MLA** | `/usr/bin/enigma2_pre_start.sh` (يستدعي guardian) | opkg: `enigma2-plugin-skins-cineview-fhd-mla` | **أُبقي** |
| **إضافات أخرى** | `Renderer/PosterX.py` | opkg: `enigma2-plugin-extensions-youvixpostersettings` | **أُبقي** |
| **إضافات أخرى** | `Renderer/AglarePosterX.py` و`Renderer/LukaPosterX.py` وملفات `Aglare`/`Luka` | opkg: `skins-aglare-fhd` و`skins-luka-fhd` | **أُبقيت** |
| **ملكية غير مؤكدة** | `Renderer/iPosterX.py` و`iPosterXDownloadThread.py` | بلا حزمة مالكة، وليست من payload CineView القديم، ولا تحمل اسمه | **أُبقيت ووُثّقت** (ممنوع حذف المشكوك فيه) |
| **إضافات أخرى** | `/etc/enigma2/skin_user_YouViX-PosterX.xml` | تخص سكين YouViX | **أُبقي** |
| **الصورة** | `/etc/enigma2/profile` (يذكر "plugin CineViewControl") | ملف توقيت الإقلاع الذي يكتبه Enigma2 نفسه | **أُبقي**، ويتجدد تلقائياً |
| **نسخ الاختبار** | `/home/root/mla-backup-20261008-openvix/` و`/home/root/oldcv-backup-20261008/` | نسخ احتياطية لهذه المرحلة | **أُبقيت** للاسترجاع |

**التحقق قبل الحذف:**
- لا يوجد أي مرجع لمكونات CineView القديم داخل CineView MLA، ولا في أي سكين أو بلجن آخر. تم البحث في `/usr/share/enigma2` و`/usr/lib/enigma2/python` و`/etc/enigma2`، وفي حزمة MLA المبنية.
- لا cron، ولا init، ولا symlinks تشير إلى CineView القديم.
- الـpayloadان متطابقان في قائمة الملفات (390 مدخلاً).
- كل ملفات `CineView_FHD/` و`CineViewControl/` الموجودة على القرص مصدرها الـpayload.

### النسخة الاحتياطية قبل الحذف

**المكان على Slot 4:** `/home/root/oldcv-backup-20261008/`
- `oldcv-files.tgz`: 1637 مدخلاً، 24.6 MB. SHA256 `dfeec0ce37bd4061afc50ab75804d2449ba42929eec073c13ae6b69fe8fa3f8b`.
- `settings`: SHA256 `fff2fc0f7b761157…`.
- `opkg-info/`: ملفات control وlist وpostinst وpreinst للحزمتين، مع حالة opkg لكل منهما.

**نسخة مطابقة على الـagent:** `~/cineview-mla/oldcv/`، بنفس البصمة.

**الاسترجاع إن لزم:**
```
tar -C / -xzf /home/root/oldcv-backup-20261008/oldcv-files.tgz
```
- إذا لزمت السطور الحذوفة من `settings`، تُستعاد مع إيقاف الواجهة.

### التنفيذ

- تم مع إيقاف الواجهة (`init 4`)، ثم أُعيد تشغيلها (`init 3`).
- الحذف بمسارات صريحة فقط، دون wildcard يمكن أن يصل إلى `CineViewMLA*`.
- **النتيجة:** opkg أزال الحزمتين، ثم حُذف 13 ملفاً و5 مجلدات، وأُزيل سطرا الإعدادات. بقي 0 مرجع قديم في `settings`.

**الجرد بعد التنظيف:**
- حزمة CineView الوحيدة المثبتة: `enigma2-plugin-skins-cineview-fhd-mla 1.0.0~openvix1`.
- في `/usr/share/enigma2` لا يوجد إلا `CineView_FHD_MLA` من CineView.
- لا يوجد أي ملف `CineView*` غير MLA في `Components`.
- لا يوجد `CineViewControl`.
- Plugin Browser لم يعد يعرض "CineView Control".

### الاختبار الفعلي بعد التنظيف

| الاختبار | النتيجة |
|---|---|
| بدء Enigma2 بعد الحذف | PASS: لا Traceback، و`missing`/`notimpl` مطابقة لما قبل الحذف |
| t106v (18 خطوة): InfoBar، SIB، ChannelSelection، العلامة، التمرير، Grid/Single/Multi/IB EPG، EventView/Simple، PVR، Plugin Browser، Install/Remove Plugins، CineView Designs، Setup، MessageBox | **PASS**: 0 Traceback و0 Skin Error في كل الخطوات. البوسترات تظهر، والكاش فيه 124 ملفاً في `/tmp` |
| CineView Designs (t106fv): F0 نموذج Modern مع Keep، F1 Profiles، F2 ثيم مع Keep، F3 رجوع تلقائي، F4 Factory، R Guardian | **PASS** (كلها) |
| PVR بتسجيل حقيقي 90 ثانية على USB، ثم القائمة وINFO والتشغيل في MoviePlayer والإيقاف | **PASS**، وحُذفت ملفات الاختبار، و`timers.xml` مطابق للأصل |
| أخطاء السجل | فقط أخطاء سكين LCD الأصلي `OE-A_LCDSkin_9`، الموثقة سابقاً: `IsHDHDR` عند MoviePlayer، و`RemainingToText` بوسيط فارغ في الأسطر 211 و925 و1164 من `skin_display.xml` |
| Crash logs | **0** |

### الحالة النهائية بعد التنظيف

**تنظيف بعد الاختبار:**
- حُذفت أداة الاختبار، وسطر `enabledebug`، ولوجات الاختبار بعد أرشفتها.
- القناة الحالية HBO HD.

**الفرق في settings مقارنة بما قبل التنظيف:**
- حذف عنصر `CineViewControl` من `plugin_order`.
- حذف سطري `config.plugins.cineview.*`.
- `startCounter` (عداد طبيعي).
- `config.audio.volume` (انظر أدناه).

**الصوت:**
- تغيّر `config.audio.volume` من 40 إلى 5.
- **السبب مثبت من سجل Enigma2:**
  - في 17:14:32–17:14:33 وصلت 7 ضغطات `KEY_VOLUMEDOWN` من مدخل الريموت الفعلي (InfoBarGenerics Make/Break بفواصل بشرية تقريباً 0.2 ثانية).
  - لم يكن معها أي طلب `/api/remotecontrol` من OpenWebif.
- أدوات الاختبار ترسل الأزرار عبر OpenWebif فقط، ولم ترسل أي زر صوت.
- الأرجح أن شخصاً عند الرسيفر استخدم الريموت.
- **لم أغيّر القيمة.**
- **البند المفتوح:** تغيّر 55→40 أثناء اختبار المثبّت (I4) لم أتحقق من مصدره، لأن سجلات debug كانت متوقفة وقتها.
