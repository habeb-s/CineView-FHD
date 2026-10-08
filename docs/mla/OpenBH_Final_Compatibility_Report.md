# CineView MLA — Final OpenBH 5.6 Compatibility Report

**التاريخ:** 2026-10-07، من 13:02 إلى 21:45 بتوقيت الرياض.

**الجهاز:** Vu+ Duo 4K SE، Slot 5.

**الصورة:** OpenBH 5.6.008 (BlackHole/enigma2 `52dedddc314a`)، Python 3.13.12، armv7l.

**البناء النهائي:** `enigma2-plugin-skins-cineview-fhd-mla_1.0.0~openbh10_all.ipk`، SHA256 `239a376dd0c28b2cc5a0f32a9d203ac7aa385c6ca294af8746c15f0dec490a5a`، الفرع `dev/mla-multiimage` (`e054e60`).

**الأدلة:** `docs/mla/evidence/openbh_final/` (السجلات وصور الشاشات المجمّعة) و`docs/mla/evidence/openbh_t106/`.

**الحالة:** **REGRESSION VERIFIED على OpenBH 5.6 / Slot 5.**
- لم يُنشر أي إصدار، ولا tag، ولا تغيير في الـ Smart Installer العام.
- لم يُلمس OpenATV ولا OpenViX ولا أي Slot آخر ولا STARTUP.

---

## تحديث 2026-10-08: قراراك (CAM متعدد الأسطر، وأسماء القنوات خيار ج)، وSmart Installer

**البناء:** `1.0.0~openbh12`، SHA256 `7e08d1be299579aaf06055256b4b23327f589537c91958be9c937b14ae12c112`، الفرع `dev/mla-multiimage`. **الأدلة:** `docs/mla/evidence/openbh_cam_names/` (عنوان السيرفر مخفي في السجلات والصور).

### 1) حقل CAM متعدد الأسطر داخل الصندوق نفسه: PASS
- `wrap` على الحقول العمودية فقط (Classic وDetails، في InfoBar وSIB وEventView). حقول Cinema الأفقية بلا تغيير.
- **عيب ثانٍ وُجد أثناء الاختبار وأُصلح:** المحوّل يُستطلع كل 1.5 ث ويُبلغ "تغيّر" في كل مرة، فيعيد RunningText التمرير من البداية قبل أن تنتهي مهلة البدء (2.2–2.5 ث)، فلم يكن الحقل يتحرك أبداً. صار الاستطلاع الذي لا يغيّر النص يُتجاهَل، والتغيير الحقيقي يمر فوراً. ينطبق على الصورتين.
- **النتيجة الفعلية (Full، أسوأ حالة):** Classic تُظهر الأسطر الثلاثة ثابتة. Details (صندوقا 48 و72 px) وCinema (الحقل الأفقي) تمرّر النص كاملاً داخل حدودها: CAM ثم Reader ثم Server والعنوان. لا قص دائم ولا تداخل.
- **ملاحظة:** في InfoBar، مهلة الإخفاء الأصلية 5 ث. Details يُظهر السطر الثالث خلالها. أما Cinema فتمرير العنوان كاملاً يحتاج نحو 6–8 ث، فيظهر كاملاً في SIB أو إذا كانت مهلة InfoBar أطول. لم أغيّر سرعة التمرير لأنها جزء من التصميم المعتمد.

### 2) أسماء القنوات، الشريط يمين، خيار (ج): PASS في Classic، PARTIAL في 5 تصاميم ضيقة
- يُحسب عمود الاسم لكل باقة من أطول اسم فيها، ويُضاف فاصل 32 px قبل البرنامج. يُعاد الحساب بعد كل تغيير وضع أو باقة.
- **الشريط يسار (الافتراضي):** لم يتغير شيء.
- **Classic:** الأسماء كاملة، وفاصل واضح، ولا تداخل مع الشريط.
- **Posterlist وVideofirst وVideofirst-Right وModern وMinimal (القوائم الضيقة):**
  - لا تداخل مع الشريط.
  - لكن العمود يصل إلى سقفه (68% من المساحة)، فيُقص الاسم الأطول عند حافة العمود ويلاصق نص البرنامج، مثل "CineStar TV Action and Thri│Tabu".
- **السبب (من كود OpenBH الأصلي، `listboxservice.cpp`):**
  - مساحة رسم الاسم تساوي عرض العمود بالضبط، والبرنامج يبدأ عند حافته.
  - لا يوجد في المحرك أي فاصل أو "…" للاسم المقصوص.
  - الطرق الوحيدة لصنع فاصل هي أوضاع الأيقونات (mode 2)، وهي إعدادات المستخدم وتنقل الأيقونات.
- **الصورة:** `names_barright_6_designs.jpg` و`names_posterlist_barright_capped.jpg`.
- **يحتاج قرارك (انظر أسفل الملخص).**

### 3) Smart Installer لـ OpenBH: جاهز، غير منشور
- الفرع `dev/openbh-installer` في `CineView-MLA` (`08f09b9`). `main` والإصدار العام لم يُلمسا.
- اكتشاف الصورة من `enigma.info`، مع تأكيد من بنية الصورة الفعلية (PackageAction لـ OpenATV، وPluginDownloadBrowser لـ OpenBH). يتوقف عند أي تعارض، ويرفض OpenBH أقدم من 5.6.
- رابط حزمة OpenBH فارغ عمداً، فيتوقف بـ"not released yet" حتى تعتمد النشر.
- **اختبارات فعلية على Slot 5 (`o11_installer.log`):**

| # | السيناريو | النتيجة |
|---|---|---|
| I1 | التثبيت قبل النشر | يتوقف برسالة واضحة، دون أي تغيير |
| I2 | تثبيت عادي | PASS، والحالة `install ok installed` |
| I3 | إعادة تثبيت | PASS |
| I4 | انهيار shell واحد (signal 11 محاكى) | محاولة واحدة إضافية فقط ثم PASS |
| I5 | انهيار دائم | يتوقف بعد المحاولة الثانية برسالة واضحة، بلا حلقة، والحالة `half-installed` |
| I6 | تشغيل المثبّت بعد I5 | يكتشف التثبيت الناقص، ويصلح حالة CineView فقط، ثم PASS |
| I7 | `enigma.info` يقول OpenATV والبنية OpenBH | يتوقف: الصورة غير محددة بثقة |
| I8 | `enigma.info` بلا اسم صورة | يتوقف |

- بعد الاختبارات: smoke test كامل بصفر traceback وصفر skin error، وحُذفت نقاط الاستعادة التجريبية.

### إحصاءات هذه الجولة (openbh11 + openbh12)
- **Crashes:** 0.
- **Python tracebacks:** 0. عدّاد "Traceback" في السجلات = 52، وكلها رسالة OpenBH الأصلية `[InputHotplug] connectionLost` عند إيقاف الواجهة، مرة لكل إعادة تشغيل.
- **Skin errors:** 0.
- **OpenATV parity:** PASS (`parity12.log`). المختلف فقط CamInfo + `wrap` + أيقونات PVR، وكلها مسموحة بقيود.
- **HDD modifications:** NONE. انظر الحادثة 4.

---

## الملخص

| البند | النتيجة |
|---|---|
| OpenBH 5.6 compatibility | **100%** مع إعدادات الصورة الافتراضية. **94%** (29/31) عند احتساب كل الخيارات: البندان المتبقيان مرئيان وينتظران قرارك (أدناه) |
| Open issues | **2، وكلاهما قرار شكل منك.** لا توجد مشكلة هندسية مفتوحة |
| Crashes | **0**: لا crash log في كل تشغيلات اليوم |
| Tracebacks | **0** |
| Skin errors | **0** |
| Long channel names | **PASS** مع الإعداد الافتراضي (الشريط يسار) في التصاميم الستة. **PARTIAL** مع الشريط يمين في 4 تصاميم ضيقة: الإصلاح جاهز ومعلّق على قرارك |
| Native PVR real recording | **PASS**: تسجيل حقيقي 90 ثانية على USB، ثم القائمة والمعلومات (مع البوستر) والتنقل والتشغيل في MoviePlayer الأصلي والإيقاف، ثم حذف ملفات الاختبار. `timers.xml` مطابق للأصل |
| Package install / reinstall | **PASS**: ترقية و`--force-reinstall` و`--force-downgrade`، والحالة دائماً `install ok installed` |
| Guardian / rollback | **PASS**: Apply/Keep، والرجوع التلقائي بلا رد، وFactory، والحارس عند ثالث تشغيل غير نظيف |
| Common Core reuse | **97%**: الحزمتان متطابقتان في 610 من 629 ملفاً، وكود Python مطابق بالكامل |
| OpenATV static parity | **PASS** عند كل بناء |
| OpenATV runtime regression still required | **YES**: موضّح بالتفصيل في آخر التقرير |
| HDD modifications | **NONE** (انظر "الحوادث") |

---

## الوظائف وحالتها (كلها مُختبرة فعلياً على الرسيفر)

| الوظيفة | الحالة | الدليل |
|---|---|---|
| InfoBar (5 تصاميم × 6 ثيمات × بوسترات تشغيل/إيقاف) | PASS | `final_models.log`، `final_themes.log`، `final_posters.log`، `models_5.jpg` |
| SecondInfoBar | PASS | المصدر نفسه |
| ChannelSelection + لوحة المعلومات | PASS | `final10_screens.jpg` |
| السطر المعلّم في قائمة القنوات (backgroundColorMarked) | PASS | لون الثيم الأصلي، `final10_screens.jpg` (mark) |
| Single EPG | PASS | |
| Grid EPG مع PiG وبدونه، حزم EPG الخمس | PASS | `final_epgpig.log`، `epg_nopig.jpg` |
| Multi EPG | PASS | |
| InfoBar Grid EPG | PASS | |
| EventView / EventViewSimple | PASS | مع الأزرار الملونة |
| Native PVR (MovieSelection + MoviePlayer) بتسجيل حقيقي، Classic/Cover/Cinema/Modern/Minimal | PASS | `pvr_real_recording_playback.jpg`، `pvr_layouts_real_recording.jpg` |
| أيقونات رأس PVR (Classic/Cover) لم تعد فوق التاريخ | PASS على OpenBH | `final10_screens.jpg` (pvr) |
| Plugin Browser | PASS | |
| Install / Remove Plugins: شاشة CineView + رسالة انتظار واحدة تختفي بعد امتلاء القائمة | PASS | `plugin_install_remove_console.jpg` |
| Console (مخرجات opkg) | PASS | لا يوجد not-implemented |
| CineView Designs + Profiles (حفظ/تحميل/حذف) + Design model | PASS | `final10_designs.log` |
| Apply/Keep، Auto-Rollback، Factory، Guardian | PASS | المصدر نفسه |
| الثيمات الستة | PASS | |
| البوسترات تشغيل/إيقاف + إعادة التوزيع، محرك البوستر (الكاش في `/tmp`) | PASS | |
| Picons (شعار واحد) | PASS | |
| ECM/CAM: Profile وHide | PASS | |
| ECM/CAM: Full (عنوان السيرفر) | PARTIAL ← قرار | `caminfo_BEFORE_AFTER_masked.jpg` |
| العربية (ar_AE) بما فيها "بحث IMDb" كاملة RTL دون قص | PASS | `arabic_red_key.png`، `final10_arabic.log` |
| Setup / MessageBox | PASS | |
| أسماء القنوات الطويلة: الشريط يسار (الافتراضي) | PASS | `names_default_AFTER_openbh9.jpg` |
| أسماء القنوات الطويلة: الشريط يمين | PARTIAL ← قرار | `names_barright_BEFORE_openbh8.jpg` / `names_barright_AFTER_openbh9.jpg` |
| تثبيت الحزمة وسكربتات opkg | PASS | `final10_preinst.log` (0/100)، `preinst200.log` (0/200)، `reinstall9.log` |
| EMC | NOT AVAILABLE | المكوّن غير مثبت على الصورة |

**التحذيرات المتبقية في السجل لا أثر لها:** عناصر اختيارية لا يرسمها التصميم (missing element)، و`ePixmap mode="infobar"`، و`piconMargin`. لا شيء منها خطأ.

---

## قراران ينتظرانك (لا يدخلان الحزمة دون موافقتك)

### 1) حقل CAM في وضع "Full server details"
- **المشكلة:** عيب مشترك موجود أيضاً في OpenATV Golden. المحوّل يعيد سطراً لكل معلومة، لكن RunningText بلا `wrap` يحوّل الأسطر إلى سطر واحد يُقص عند 225px، فلا يظهر السيرفر أبداً.
- **الإصلاح الجاهز:** إضافة `wrap` (`MLA_CAMINFO_WRAP=1`).
- **أثره:** يعرض الأسطر كما صُمّمت داخل الصندوق نفسه. يغيّر شكل الحقل في الصورتين: CAM في سطر، وReader في سطر، وServer في سطر.
- **الصور:** `caminfo_BEFORE_AFTER_masked.jpg`، مع إخفاء عنوان السيرفر.

### 2) أسماء القنوات الطويلة مع الشريط يمين (ليس الإعداد الافتراضي في OpenBH)
- **السبب:** محرك قوائم OpenBH (`visModeComplex`) لا يحدّ عرض الاسم إطلاقاً، فالاسم الطويل يمر فوق الشريط في Videofirst وVideofirst-Right وModern وMinimal.
- **الآلية الأصلية الوحيدة:** عرض العمود (`setColumnWidth`). تحدّ الاسم، لكن نص البرنامج يبدأ عند عمود ثابت، ويتلاصق الاسم المقصوص بنص البرنامج في التصاميم الضيقة جداً. هذا تغيير شكل.
- **الحالة:** الكود موجود ومختبر، لكنه **معطّل افتراضياً** خلف ملف علم تجريبي. الصور قبل/بعد في `evidence/openbh_final/sheets/`.
- **الخيارات:**
  - (أ) الإبقاء على سلوك OpenBH الأصلي.
  - (ب) اعتماد العمود.
  - (ج) طلب شكل آخر.

---

## ما تغيّر في هذه الجولة

| # | المشكلة | السبب المُثبت | الإصلاح | النطاق |
|---|---|---|---|---|
| 1 | الزر الأحمر بالعربي (Grid/Multi/IB Grid) | ترجمة OpenBH طولها 50 حرفاً | ImageAdapter `label_overrides`: "بحث IMDb" بالعربي فقط، و`noWrap` | OpenBH فقط |
| 2 | شاشات Install/Remove Plugins بشكل قديم وبلا أزرار ملونة | OpenBH يستخدم `PluginDownloadBrowser` بدل PackageAction | شاشة بالعقد الأصلي في `common.openbh.xml`، وhook يمسح "Please wait" بعد امتلاء القائمة | OpenBH فقط |
| 3 | Console: `itemHeight` غير مدعوم | ScrollLabel في OpenBH لا يملكه | نسخة الشاشة بدونه | OpenBH فقط |
| 4 | قوائم Profiles فارغة | ChoiceBox في OpenBH يأخذ `list=` بدل `choiceList=` | ImageAdapter `choice_list()` | OpenBH. استدعاء OpenATV كما هو |
| 5 | أيقونات PVR فوق التاريخ (Classic/Cover) | موضعها على سطر التاريخ في TopTemplate | نقلها إلى سطر الساعة (1600,8 / 1660,8) | **مشترك** (OpenATV + OpenBH) |
| 6 | فشل تثبيت `openbh7` (signal 11) | bash (`/bin/sh`) في OpenBH 5.6 ينهار نادراً، حتى مع سكربت من سطرين لا علاقة له بـ CineView (1/100). BusyBox: 0/200 | سكربتات الحزمة في OpenBH تعيد تشغيل نفسها تحت BusyBox sh إن وُجد. preinst: 0/300 بعد الإصلاح | حزمة OpenBH فقط. حزمة OpenATV لم تتغير |
| 7 | فحص التطابق لم يكن يوقف البناء عند الفشل | خطأ في الـ pipe | `build_openbh.sh` يتوقف عند الفشل | أدوات |
| 8 | backgroundColorMarked | إنذار خاطئ من الفحص الثابت | لا تغيير. مدعوم أصلاً ومُختبر | — |
| — | Volume | **CLOSED — user action, not CineView** | أُزيلت المراقبة | — |

---

## الملفات الخاصة بـ OpenBH (النهائية)
- `mla/images/openbh/core/common.openbh.xml`: PluginBrowser وPluginDownloadBrowser وConsole، وخطوط ومعاملات PluginList.
- `mla/images/openbh/transform.py`: تحويل حزم EPG إلى عقد OpenBH، وتحويل `valueFont` إلى `secondfont`.
- `mla/images/openbh/sections.openbh.json`: متطلبات قسم EPG في OpenBH.
- `mla/plugin/CineViewMLA/image_adapter.py`، مدخل `openbh`:
  - صفوف الإعدادات الأصلية.
  - shutdown عبر autostart.
  - مفتاح عناصر ChoiceBox.
  - آلية رسالة انتظار الحزم.
  - name clip (معطّل، قرار).
  - label overrides.
- `tools/mla/package_ipk.py`: `IMAGE_CHECKS["openbh"]` وإعادة تشغيل سكربتات الحزمة تحت BusyBox.
- `contracts/openbh-5.6.008-52dedddc314a.json`، `contracts/openbh-6.0.003-c06a87ef4c09.json`.

## تغييرات Common Core منذ OpenATV 1.0.0 Golden

**في شجرة OpenATV (مسموحة في فحص التطابق):**
- `CineViewMLAServiceInfo.py`: `interestingEvents` / `interesting_events`.
- `CineViewMLAShowIf.py`: إخفاء الـ instance نفسه.
- `plugin.py`: نقاط ربط الـ adapter.
- `image_adapter.py`.
- `composer.py`: اكتشاف الصورة، وملف الهدف لكل صورة، وأقسام الصورة.
- `guardian.sh`: الملاذ الأخير حسب الصورة.
- `layouts/pvr/classic|cover` ونسخ الـ generation: موضعا الأيقونتين فقط.

**خارج شجرة OpenATV:** `build.py` (الـ overlay، وأيقونات PVR، ونموذج CAM wrap المعطّل افتراضياً).

**النتيجة:** OpenATV static parity = PASS. يختلف 12 ملفاً عن golden build94، وكل فرق مسموح ومقيّد. ملفات PVR يُسمح فيها بتغيير موضع الأيقونتين فقط.

## توافق Python
- OpenBH 5.6.008 = Python 3.13.12. ملفات `.pyc` تُترجم على الجهاز نفسه.
- preinst يرفض أي Python غير 3.13.
- OpenBH 6.0.003 (Python 3.14) له نفس العقود، لكنه يحتاج بناء `.pyc` منفصلاً. **لم يُختبر على جهاز.**

## معمارية الحزمة والتثبيت
- **حزمة لكل صورة** من نفس المصدر: `MLA_TARGET=openatv|openbh`.
  - preinst يتحقق من `/usr/lib/enigma.info` (distro + imageversion)، ومن إصدار Python، ومن hook الحارس.
  - لا قائمة موديلات.
- **postinst:**
  - في التثبيت الأول: factory.
  - في الترقية: إعادة تطبيق اختيار المستخدم.
- **prerm:** يرفض إزالة السكين المختار.
- **postrm:** ينظف مساحة MLA فقط.
- **OpenBH:** السكربتات تعمل تحت BusyBox sh عند وجوده.

## Smart Installer: معمارية الاكتشاف
- **الحالي (العام):** OpenATV فقط، ولم يُغيَّر.
- **المخطط (لم يُنفّذ، ينتظر الإصدار):**
  - يقرأ `distro` و`imageversion` من `enigma.info`، ويختار حزمة الصورة المطابقة.
  - يتوقف عند الغموض أو الصورة غير المدعومة.
  - لا يعتمد على موديل افتراضي.
- **تعامل opkg مع signal 11** حسب طلبك:
  - فحص قاعدة الحزم.
  - إصلاح حالة CineView فقط إن كانت `half-installed`.
  - محاولة واحدة فقط عند الأمان، وإلا يتوقف برسالة واضحة.
  - صار أقل ضرورة بعد إصلاح BusyBox.

---

## الحوادث والشفافية
1. **قراءة HDD:** في جولة اختبار سابقة فتحت شاشة PVR الأصلية مجلدها الافتراضي `/media/hdd/movie/` وعرضت قائمته، لأن مجلد USB الخاص بالاختبار كان قد حُذف.
   - قراءة فقط من Enigma2. لا كتابة ولا حذف.
   - أُصلحت أداة الاختبار: صارت تنشئ مجلد USB بنفسها، وتفتح PVR من مسار زر PVR الأصلي.
2. **Image Manager:** قبل إصلاح ChoiceBox وصلت ضغطات زر طائشة إلى Backup & Image Manager. ملف الإعدادات لم يتغير فيها، ولم يُنفَّذ أي backup أو restore أو flash (لم تُرسل الأزرار المطلوبة لذلك). لم أستعرض HDD للتحقق من ملفات النسخ الاحتياطية.
3. **GitHub:** ردّ Internal Server Error لدقائق، ثم دُفع كل شيء دون إعادة كتابة history.
4. **2026-10-08، قراءة مسار HDD:** أمر إحصاء سجلات الكراش في جولة التنظيف استخدم النمط `/media/*/logs/*crash*`، وهو يشمل `/media/hdd/logs`. قراءة اسم ملفات فقط (لم يُعثر على شيء)، بلا كتابة أو حذف. خطئي، والأدوات لا تستخدم هذا النمط.

## التنظيف النهائي على Slot 5 (تم، مرة ثانية في 2026-10-08)
- **حُذف:** أداة الاختبار، وسطرا الـ debug، وسجلات debug اليوم، و`cvmla-testmedia`، و`/tmp/cvmla`، ونسخة `settings.before-qa-20261008`.
- **الإعدادات** تطابق ما قبل الجولة، عدا `startCounter`.
- **بقي:** الحزمة `1.0.0~openbh12` مثبتة وتعمل.

**التنظيف السابق (2026-10-07):**
- **حُذف:**
  - أداة الاختبار `CineViewMLAScreenOpen`.
  - تسجيل الـ debug (عاد للافتراضي) وسجلات debug اليوم.
  - `/home/root/cvmla-testmedia`، و`/tmp/cvmla`، و`/tmp/timers.xml.before-t107p`.
  - ملف `settings.before-qa-20261007`.
  - علم النموذج التجريبي لعمود الأسماء.
- **أُعيد كما كان:**
  - آخر قناة (`lastroot` / `lastservice`).
  - `last_videodir` / `last_movie_played`.
  - `servermode`، واللغة، وشريط التقدم، و`grid.pig`، واختيار التصميم (Classic + Navy).
- **الفرق الوحيد عن ما قبل الجولة:** عدّاد تشغيل Enigma2 الأصلي `startCounter`.
- **بقي:** الحزمة `1.0.0~openbh10` مثبتة وتعمل، ومفتاح SSH للمرحلة القادمة.

---

## OpenATV Slot 8: الاختبارات المطلوبة بعد أن تقلعه أنت
أحتاج حزمة OpenATV مبنية من نفس الـ commit، وسأبنيها وأثبّتها بعد إقلاعك. ثم Runtime Regression للتغييرات المشتركة فقط:
1. **PVR Classic وCover:**
   - الأيقونتان في سطر الساعة، والتاريخ نظيف، بالإنجليزي والعربي.
   - الأيقونات تتبدل مع تغيير الترتيب والعرض.
   - Cinema/Modern/Minimal بلا تغيير.
2. **CineView Designs:** Profiles (حفظ/تحميل/حذف عبر `choiceList`)، وDesign model، وApply/Keep، والرجوع التلقائي، وFactory، والحارس (`clean_exit` عبر `session.onShutdown`)، وصفّا Second InfoBar الأصليان.
3. **ShowIf:** شعار واحد في InfoBar/SIB Classic وDetails، مع البوسترات تشغيل/إيقاف.
4. **ServiceInfo:** أيقونات HD و16:9 والدقة تتغير مع تغيير القناة (HD↔SD).
5. **قص أسماء القنوات في OpenATV** (hook ServiceListLegacy): Videofirst/Modern/Minimal.
6. **Plugin Browser → Install/Remove:** رسالة انتظار واحدة (PackageAction hook).
7. **اكتشاف الصورة:** `composer` و`guardian` يتعرّفان على openatv، وكل التصاميم تطبَّق.
8. **Smoke test نهائي:** InfoBar، SIB، ChannelSelection، EPG، EventView، PVR، Setup، MessageBox، وصفر traceback/skin error.
9. **حقل CAM (معتمد):** Classic وDetails وCinema في InfoBar وSIB وEventView، بالأوضاع Full وProfile وHide. الأسطر كلها تظهر (ثابتة أو بالتمرير) دون قص أو تداخل.
10. **Smart Installer:** مسار OpenATV بوضع DRYRUN من الفرع `dev/openbh-installer`. يجب أن يتعرف على OpenATV ويختار حزمة 1.0.0 المنشورة دون تثبيت.
