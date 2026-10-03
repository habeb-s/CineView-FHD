# CineView MLA — تقرير المرحلة P0 (الفحص وجمع الأدلة)

> **التاريخ:** 2026-10-03 · **النطاق:** OpenATV فقط · **مرتبط بـ:** `CineView_MLA_OpenATV_Blueprint.md` v1.1
> **ما نُفِّذ:** فحص ثابت وجمع أدلة فقط. **لم يُثبَّت شيء على الرسيفر، ولم يُنشأ أي slot، ولم يُعدَّل الفرع الرئيسي.**
> **الحالة:** P0a مكتمل · **P0b (فحص الجهاز) متوقف: لا يوجد مسار وصول إلى الرسيفر من هذه الجلسة (انظر §1).**

---

## 1. بيئة العمل والوصول — نتائج فعلية

| البند | النتيجة | الدليل |
|---|---|---|
| ربط الجلسة بحاسوبك | **مرتبط** — Windows x64، الجهاز `desktop-hs1a71a`، تطبيق Claude 2.19675.0 | `get_device_info` |
| **Desktop Commander** | **غير متاح.** قائمة خوادم MCP المحلية على حاسوبك **فارغة** (`localMcpServers: []`)، ولا توجد أداة shell على الحاسوب في هذه الجلسة | `get_device_info` |
| مجلدات متصلة | لا يوجد | نفس المصدر |
| الوصول إلى الرسيفر | **غير ممكن حاليًا.** الحاوية السحابية لا تصل إلى شبكتك المحلية، والحاسوب لا يملك أداة تنفيذ أوامر في هذه الجلسة | — |
| **المستودع** | قراءة: ✓. **دفع: مرفوض** — "Claude doesn't have GitHub access to habeb-s/cineview-fhd" (تطبيق Claude GitHub غير مثبّت/مربوط) | `add_repo(access=push)` ⇒ `push_check: refused` |
| فرع `dev/mla-openatv` | **أُنشئ محليًا** من `main@729ab1a` وعليه commit واحد للتوثيق والأدوات. **لم يُدفع** (لا صلاحية). `main` لم يُلمس | `git` |
| الفروع البعيدة | 19 فرعًا، و`HEAD=main@729ab1a`؛ لا يوجد فرع `dev/mla-openatv` بعيد مسبقًا (لا تعارض) | `git ls-remote` |

**المطلوب لفتح P0b** (أي واحد يكفي للرسيفر):
1. تثبيت/تفعيل **Desktop Commander** في تطبيق Claude على حاسوبك، والتأكد أنه يظهر "running" — ثم أتحقق أنا من `ssh root@<ip-الرسيفر>` منه.
2. أو تزويدي بنقطة وصول أخرى تعمل من حاسوبك.
**ولصلاحية الدفع:** تثبيت تطبيق Claude على GitHub للمستودع (`github.com/apps/claude/installations/select_target`) أو إعادة ربط GitHub من إعدادات claude.ai. بديل مؤقت: أسلّمك **git bundle** للفرع لتدفعه بنفسك (مرفق).

---

## 2. سلامة النسخ الذهبية والأرشيفات (مُتحقَّق)

| الأرشيف | SHA-256 |
|---|---|
| `openatv-final-20260926/cineview-live-openatv-final-20260926.tar.gz` (الذهبية المعتمدة) | **OK** |
| `openatv-final-20260923/` (live + engineering history) | **OK** (2/2) |
| `openvix-final-20260923/` | OK (خارج النطاق) |
| `openbh-final-20260923/cineview-live-openbh-final-20260923.tar.gz` | **FAILED** — بصمة غير مطابقة (خارج نطاق OpenATV؛ يُسجَّل للمراجعة لاحقًا، لم يُلمس) |

النسخة الذهبية لم تُعدَّل؛ كل العمل جرى على نسخ في مجلد مؤقت.

---

## 3. إصدار الجهاز المرجعي (من الأدلة المخزنة — يجب التأكد على الجهاز)

من `meta/` في أرشيف 2026-09-23:
- Vu+ Duo 4K SE، `arch=cortexa15hf-neon-vfpv4`، OpenATV **8.0.0-beta build 20260922**، OE-Alliance 6.0، rootfs `mmcblk0p9`.
- `enigma2 - 8.0.0-beta+git35513+45414bc…` ⇒ **فرع `8.0` commit `45414bc` (2026-09-19)** — حدّدته في مستودع OpenATV؛ كل تحليل العقود الآن مقابل هذا الـ commit، لا master.
- **Python 3.14.7**.

**تناقضات تحتاج حسمًا على الجهاز:**
- ملفات `.pyc` في اللقطات مبنية بـ **cpython-312** بينما الجهاز 3.14 ⇒ نُسخت من بيئة تطوير، وتجاهلها Python على الجهاز (غير ضار، لكنه دليل أن الملفات نُقلت يدويًا).
- مذكرة 20260923 تذكر "OpenATV 7.6" في قسم plugin UI بينما الجهاز 8.0.0-beta.
- منذ 2026-09-23 قد يكون الجهاز حُدّث (فرع 8.0 تقدّم 53 commit بعد 45414bc حتى 2026-10-02).

---

## 4. نتائج الفحص الثابت

### 4.1 Python
- كل ملفات CineView الـ 18 (Renderers/Converters/CineViewControl) **تُحلَّل بلا أخطاء تحت Python 3.14.6** (أقرب إصدار متاح لـ 3.14.7).
- `LukaPosterXEMC.py` يستورد `Components.Renderer.LukaPosterXDownloadThread` (**غير موجود في الأرشيف الذهبي**) و`six` ⇒ اعتماد خفي على ملفات في الجهاز؛ يُتحقق في P0b.

### 4.2 العقود مقابل OpenATV 45414bc
- كل Renderers/Converters المستخدمة في المجموعة الحية موجودة في 45414bc، عدا `OAWeather`/`OAWeatherPixmap` (بلجن OpenATV اختياري — متوقع).
- 58 مرجع صورة غير موجود في الأرشيف، معظمها مسارات بلجنات خارجية (`/usr/lib/enigma2/python/Plugins/Extensions/CSFD/…`، IMDb، tmdb…) ⇒ تُحسم بقائمة البلجنات المثبتة في P0b.
- خطوط غير معرّفة مستخدمة: `0`، `1`، `FdLcD`، `buttons` — يُتحقق من أثرها في سجل الجهاز.
- **فرق عقد مهم بين 45414bc وmaster:** في 45414bc لا يعيد `reloadSkins()` بناء خيارات أنماط ChannelSelection ⇒ أضفته للمخطط (§1.1).
- **خطاف إقلاع أصلي مُتحقَّق:** `enigma2.sh` يستدعي `/usr/bin/enigma2_pre_start.sh` قبل كل تشغيل ⇒ أساس الحارس المستقل (§2.8).

### 4.3 بنية CineView الحالية على OpenATV
- 4 ملفات حية (196+56+302+33 شاشة)، **22 اسم شاشة مكرر** بين الملفات، 30 نسخة `skin.layout-*` + 4 `safe-noposterx` + 6 ملفات `.before-*`.
- `compat.py` (يُشغّله `activate.sh`) **يعيد كتابة كل ملفات XML في مجلد السكين** ويحذف عناصر نهائيًا إن غاب مكوّن اختياري ⇒ خطر فقدان تصميم دائم (حتى في ملفات المصدر). (لم يحذف شيئًا في محاكاتي لأن المكونات موجودة في 45414bc.)

---

## 5. المشكلتان المكتشفتان — إثبات السبب (ثابتًا) دون أي إصلاح

### ISS-01 — إعداد Second InfoBar
**الفرضية:** `CineViewControl.apply_timeout()` يكتب قيمة **المهلة بالثواني** في `config.usage.show_second_infobar`، وهو إعداد **وضع العرض** (0 Off / 1 Event Info / 2 2nd InfoBar INFO / 3 ECM)، ويُستدعى عند كل `sessionstart`.

**إعادة إنتاج في harness** باستخدام **`Components/config.py` الحقيقي من OpenATV 45414bc** ونفس تعريف الإعداد (`UsageConfig.py:386–392`)، مع القيمة المحفوظة في الجهاز `show_second_infobar=2` (من `settings-gui.txt`):
```
secondtimeout= 20  show_second_infobar: 2 -> 1     ← الافتراضي في CineViewControl
secondtimeout=  5/10/15/30/60  show_second_infobar: 2 -> 1
secondtimeout=  0  show_second_infobar: 2 -> 0     ← يُطفئ SecondInfoBar كليًا
```
السبب الآلي: `ConfigSelection.setValue` يستبدل أي قيمة خارج الخيارات بالافتراضي `"1"`.
**الأثر المتوقع على الجهاز:** بعد كل إقلاع، زر INFO يفتح **EventView** بدل SecondInfoBar المعتمد، بينما ملف settings يبقى `2` (لأن `apply_timeout(False)` لا يحفظ) — وهذا يفسر لماذا يظهر الإعداد سليمًا في الملف.
**الحالة:** ROOT CAUSE IDENTIFIED (harness) — **يحتاج إثباتًا على الجهاز** (T14) قبل أي إصلاح. لم يُصلح شيء.

### ISS-02 — سكربتات الحفظ / التفعيل
**محاكاة offline** على نسخة من الملفات الذهبية، بالسكربتات الأصلية بلا تعديل، ومكونات 45414bc:
| المسار | الشاشات المختلفة عن `skin.xml` الحي المعتمد |
|---|---|
| A: `activate.sh` الكامل (theme→timeformat→compat→openatv_v5→auditfix→plugin_ui) | **24** شاشة (منها InfoBar، SecondInfoBar×3، EPG×6، EventView، MovieSelection، QuickMenu…) |
| B: زر Save في CineView Control (`keySave`) | **30** شاشة |
أمثلة مما يُفقد عبر B:
- **SecondInfoBar:** المعتمد (fill، 67 عنصرًا، حالي/تالي مع إطاري بوستر) ⇒ يُستبدل بشريط قديم `0,560 1920×520` من **12 عنصرًا**.
- **InfoBar:** هوامش الإطار السفلي تتغير (16→24px).
- **GraphicalEPGPIG:** 6 عناصر timeline تختفي، و`timeline_now` ينتقل.

**الاستنتاج:** التصميم المعتمد الحالي **لا يمكن إعادة توليده** من أي ملف مصدر في الحزمة أو المستودع؛ هو نتيجة ترقيعات حية متتالية (`tools/live_openatv8_*` تعتمد على ملفات "سابقة" حية). أي تفعيل أو حفظ من CineView Control **على الجهاز** يُرجَّح أن يستبدل التصميم المعتمد.
**الحالة:** ROOT CAUSE IDENTIFIED (محاكاة ثابتة) — شرط صحتها أن الذهبية = الجهاز الآن. **يُثبت في T15 على slot الاختبار فقط.** لم يُصلح شيء.
**توصية حماية فورية (لا تنفيذ، قرارك):** تجنّب ضغط Save في CineView Control وتشغيل `activate.sh` على جهاز الإنتاج حتى P0b.

---

## 6. جاهزية المشروع

| المحور | الجاهزية | ما ينقص |
|---|---|---|
| المخطط الهندسي | **جاهز (v1.1)** | موافقتك |
| مرجع العقود | جاهز لـ 45414bc | تأكيد أن الجهاز ما زال على 45414bc |
| مرجع التصميم الحي | جزئي: ذهبية 20260926 مُتحقَّقة | **الملفات الحية + لقطات فعلية من الجهاز** |
| المشكلتان | سبب محدد ثابتًا | إثبات على الجهاز |
| المستودع | فرع dev محلي | **صلاحية دفع** |
| الوصول للجهاز | **غير متاح** | **Desktop Commander أو بديل** |
| بيئة الاختبار | خطة جاهزة (ملحق أ) | الوصول + موافقتك المنفصلة |
**الحكم:** المشروع **غير جاهز** للانتقال إلى P1 أو أي تنفيذ؛ العائق الحاسم هو الوصول إلى الرسيفر.

---

## 7. المخاطر

| # | الخطر | الاحتمال/الأثر | المعالجة |
|---|---|---|---|
| R1 | Save/activate في الإنتاج يدمّر التصميم المعتمد (ISS-02) | مرتفع/مرتفع | عدم استخدامهما حتى P0b؛ أرشفة الملفات الحية أول خطوة في P0b |
| R2 | الجهاز تغيّر عن الذهبية (تحديث صورة أو ترقيع إضافي) | متوسط/مرتفع | M0: الملفات الحية مرجعًا بعد التحقق |
| R3 | الكتابة على HDD من مكونات أو بلجنات أخرى داخل slot الاختبار | متوسط/مرتفع | قائمة منع بمعرّف الجهاز + خيار تعطيل automount داخل slot الاختبار |
| R4 | وجود `enigma2_pre_start.sh` لحزمة أخرى | غير معروف | فحص في P0b؛ لا استبدال |
| R5 | سعة/حالة USB الـ multiboot غير معروفة | غير معروف | فحص قراءة فقط في P0b |
| R6 | `LukaPosterXDownloadThread` و`six` اعتماديات خفية | متوسط/متوسط | جرد في P0b |
| R7 | فشل بصمة أرشيف OpenBH | منخفض (خارج النطاق) | تسجيل فقط |
| R8 | لا صلاحية دفع ⇒ العمل يبقى محليًا في الحاوية (ليست دائمة) | مرتفع/متوسط | git bundle مرفق؛ حل صلاحية GitHub |

---

## 8. الخطوات المطلوبة قبل السماح بالمرحلة التالية
1. **منك:** تفعيل Desktop Commander (أو بديل) وإعطائي IP الرسيفر وطريقة الدخول (SSH مفتاح/كلمة مرور — تُدخلها أنت في الأداة، لا أكتبها أنا).
2. **منك:** صلاحية GitHub (أو تدفع bundle المرفق بنفسك).
3. **مني بعد ذلك (P0b، قراءة فقط):** تنفيذ قائمة أوامر ملحق ب، وأرشفة الملفات الحية، واللقطات المرجعية، وT14 (أ–د).
4. **منك:** الموافقة على خطة بيئة الاختبار (ملحق أ) — بموافقة منفصلة لإنشاء الـ slot.

---

## ملحق أ — خطة إنشاء بيئة الاختبار (للموافقة — لا تُنفَّذ الآن)

**الهدف:** slot OpenATV مستقل على وحدة USB الـ multiboot، بنفس إصدار الإنتاج، دون لمس HDD أو slot الإنتاج.

| الخطوة | العمل | نوعه | بوابة |
|---|---|---|---|
| E1 | جرد قراءة فقط: `lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINT`، `blkid`، `cat /proc/mounts`، `df -h`، `ls -l /dev/disk/by-uuid`؛ تحديد HDD بمعرّفه (UUID) ووحدة USB بمعرّفها | قراءة | — |
| E2 | جرد multiboot: ملفات `STARTUP*` في قسم الإقلاع (تُقرأ فقط)، الـ slots الموجودة على USB، المساحة الحرة، نوع النظام | قراءة | — |
| E3 | جرد النسخ الاحتياطية الموجودة: مكانها، تاريخها، بصماتها، **وهل تحتوي slot الإنتاج كاملًا** (rootfs + kernel + settings) | قراءة | تقرير لك |
| E4 | **نسخة احتياطية جديدة لـ slot الإنتاج** بأداة OpenATV الأصلية (Image Backup) **إلى وحدة USB** (لا HDD) + نسخة settings/`/etc/enigma2` + بصمات SHA-256 + التحقق بإعادة قراءة الأرشيف | كتابة على USB فقط | **موافقتك** |
| E5 | تحديد الـ slot الهدف على USB (موجود فارغ أو قابل للاستبدال) — **لا تهيئة لأي قسم** دون تأكيدك الصريح للقسم بعينه | — | **موافقتك** |
| E6 | تثبيت OpenATV 8.0.0-beta بنفس البناء (20260922 إن كان متاحًا في feeds، وإلا أقرب بناء مع توثيق الفرق) في ذلك الـ slot عبر أداة Multiboot/Flash الأصلية في OpenATV | كتابة على USB | **موافقة منفصلة** |
| E7 | تهيئة الـ slot الاختباري: نسخ settings الأساسية (القنوات/التونر **قراءة من الإنتاج ونسخ إلى الـ slot** فقط لعرض قنوات حقيقية)، (اختياري بموافقتك) تعطيل automount للـ HDD **داخل الـ slot فقط**، إنشاء `<usb>/cineview-mla-dev/` | داخل slot الاختبار | **موافقتك** |
| E8 | تثبيت **النسخة المستقرة** (الملفات الحية المؤرشفة) في slot الاختبار ⇒ لقطات مقارنة بلقطات الإنتاج (يثبت أن الـ slot مكافئ) | داخل slot الاختبار | — |
| E9 | تنفيذ T15 (ISS-02) هنا فقط | داخل slot الاختبار | — |
| E10 | خطة العودة: اختيار slot الإنتاج من قائمة multiboot، مع تأكيد أنه يقلع سليمًا **قبل** أي عمل في slot الاختبار | — | — |

**ممنوعات ثابتة في كل الخطوات:** أي كتابة/حذف/تهيئة على HDD؛ تعديل slot الإنتاج؛ تعديل قسم الإقلاع خارج ما تفعله أداة OpenATV الأصلية لاختيار الـ slot؛ تعديل التونر/القنوات في الإنتاج.

## ملحق ب — أوامر P0b (قراءة فقط) التي سأنفذها عند توفر الوصول
```sh
cat /etc/image-version; opkg list-installed | grep -E '^enigma2 |python3 |six|cineview|oaweather|posterx|emc' ; python3 --version
uname -a; cat /proc/stb/info/model 2>/dev/null; grep -E '^config\.(skin|usage\.show_second_infobar|usage\.second_infobar_timeout|usage\.fastSkinReload|plugins\.cineview)' /etc/enigma2/settings
ls -la /usr/share/enigma2/CineView_FHD/ ; sha256sum /usr/share/enigma2/CineView_FHD/*.xml
ls -la /usr/lib/enigma2/python/Components/{Renderer,Converter}/ | grep -iE 'cineview|luka|posterx'
ls -la /usr/bin/enigma2_pre_start.sh /usr/bin/enigma2.sh 2>&1; mount; df -h; lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINT 2>/dev/null || blkid
ls -la /home/root/logs/ | tail; command -v sha256sum
tar czf /tmp/cv-golden-live-$(date +%Y%m%d).tgz /usr/share/enigma2/CineView_FHD /usr/lib/enigma2/python/Components/Renderer/CineView* /usr/lib/enigma2/python/Components/Renderer/Luka* /usr/lib/enigma2/python/Components/Converter/CineView* /usr/lib/enigma2/python/Plugins/Extensions/CineViewControl /etc/enigma2/settings
# الأرشيف يُكتب إلى /tmp (RAM) ثم يُنقل إلى حاسوبك — لا كتابة على HDD
wget -qO- 'http://127.0.0.1/api/settings' | grep -E 'show_second_infobar|second_infobar_timeout'   # القيمة الحية (T14-ب)
# اللقطات المرجعية: /grab?format=png&mode=all — بعد موافقتك على قائمة الشاشات وتسلسل أزرار الريموت
```

## ملحق ج — ملفات هذه المرحلة في فرع `dev/mla-openatv` (محلي)
- `docs/mla/CineView_MLA_OpenATV_Blueprint.md` (v1.1)
- `docs/mla/CineView_MLA_P0_Report.md`
- `tools/mla_p0/repro_iss01_secondinfobar.py` — harness ISS-01
- `tools/mla_p0/repro_iss02_save_paths.sh` — محاكاة ISS-02
