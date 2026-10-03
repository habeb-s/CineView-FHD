# CineView MLA — تقرير التنفيذ: P0b → P3 (Slot 8، OpenATV 8.0.1)

> **التاريخ:** 2026-10-03 · **الفرع:** `dev/mla-openatv` (main لم يُلمس: `729ab1a`)
> **الحالة الإجمالية:** MLA مثبّت ومفعّل في Slot 8 ويحمّل التصميم الأصلي (Classic) — **بوابة التكافؤ البصري M7 قيد التنفيذ** (انظر §7).

## 1. البيئة — مُتحقَّق على الجهاز
| البند | النتيجة الفعلية |
|---|---|
| الجهاز | Vu+ Duo 4K SE (`box_type=vuduo4kse`) |
| الصورة | OpenATV **8.0.1** build **20261003**، Python **3.14.7** |
| enigma2 | `8.0.1+git35583+57b7a5127d` = فرع `8.0` commit **57b7a51** (2026-10-02) |
| الـ slot النشط | **Slot 8**: `/proc/cmdline` → `root=/dev/sdb1 rootsubdir=linuxrootfs8`؛ `/boot/STARTUP` يشير إلى linuxrootfs8 |
| HDD | `/dev/sda1` — KINGSTON SA400S3 (SATA، removable=0) — **UUID `ea5ccf03-15cf-4db3-af92-e7b7cf77abe9`** → `/media/hdd` |
| USB | `/dev/sdb1` — SanDisk Ultra USB 3.0 (removable=1) — **UUID `3cfb20d7-18b5-42b9-ad97-80f41f99dc72`** → `/` (linuxrootfs8) و`/media/usb` |
| Flash | `mmcblk0p9` (UUID 55065d07…) مركّب rw على `/boot`؛ يحوي Slot 1 (OpenBH) وSlot 2 (OpenATV 7.6) وSlot 3 (OpenATV 8.0.0-beta) — **لم يُكتب عليه شيء** |
| `/tmp` | رابط إلى `/var/volatile/tmp` = **tmpfs** (797MB متاحة) — تحققتُ قبل أي كتابة |
| الاتصال | Desktop Commander → ai-agent → SSH (`root@192.168.1.250`، مفتاح `vuplus_aiagent`) |

## 2. النسخ الاحتياطي — مُتحقَّق
- أرشيف: `/media/usb/cineview-mla/backups/slot8-pre-mla-20261003-115646.tar.gz` (166.6MB، GNU tar، `--one-file-system --numeric-owner`)، SHA-256 `268b95b1…f9457`، `gzip -t` OK.
- **اختبار استعادة فعلي**: فك الأرشيف في مجلد منفصل على USB ومقارنة شجرية (نوع، صلاحيات، مالك، حجم، SHA-256، أهداف الروابط) مع Slot 8: **19318/19318 مدخلًا متطابقًا**؛ الفرق الوحيد `home/root/logs/messages` (نما بعد النسخ). 8 sockets تُخطّى بطبيعتها.
- نسخ إعدادات قبل كل تغيير: `/media/usb/cineview-mla/state/settings-backups/`.

## 3. العقود من الإصدار المثبت فعليًا
- الجهاز يشحن `.pyc` فقط. ترجمتُ مصدر `57b7a51` **على الرسيفر نفسه** بنفس Python وقارنت الـ bytecode: **428/428 وحدة متطابقة** (مع `-O`؛ مع `-O0` اختلفت 16 وحدة تحوي `assert` فقط ⇒ الصورة مبنية بـ `-O`).
- `contracts/openatv-8.0.1-57b7a51.json` (1003 class) + `tools/mla/contracts.py`. فحص شاشات الأقسام في النسخة الذهبية: كلها مطابقة؛ الاستثناءات مُفسَّرة (timeline ديناميكي، InfoBarEventView يُمرَّر اسمه ديناميكيًا، SecondInfoBarSimple/TimeshiftLive غير مستخدمتين في 8.0.1).
- فروق 57b7a51 عن 45414bc لا تمس عقود MLA؛ و`reloadSkins()` في 8.0.1 **لا يعيد بناء أنماط ChannelSelection** (تأكيد).

## 4. مرجع التصميم المعتمد
- `skin.xml` الحي في **Slot 3 (OpenATV 8.0.0-beta)** مطابق بايتيًا للنسخة الذهبية `openatv-final-20260926` (SHA `73d7cd9f9425`)، وكل ملفات السكين متطابقة؛ الفرق الوحيد `CineViewControl/plugin.py` 2.3.4 (زر تحديث أونلاين).
- Slot 2 (7.6) ونسخة USB 2026-10-01 سلالة مختلفة (`skin.master.xml`/`layout.off.*`) — **لم تُعتمد**؛ أحتاج تأكيدك إن كانت إحداهما هي المعتمدة.
- **تثبيت مرجعي في Slot 8** (`CineView_FHD`) من الذهبية بلا CineViewControl، مع تعديل سطر واحد في `CineViewPosterX` (مسار الكاش ⇒ USB). سبب استبعاد CineViewControl: `sessionstart` يشغّل `smartdeps.sh` تلقائيًا (يثبت حزمًا ثم يستدعي `activate.sh` الذي يعيد كتابة `skin.xml`) ⇒ **توسيع لنتيجة ISS-02: يحدث تلقائيًا عند الإقلاع في حالات، لا عند Save فقط**.
- مكونات البيئة المعتمدة: ثبّتُّ `oaweather` و`bitrate` من feed OpenATV 8.0.1 الرسمي (كانت مثبتة في Slot 3).
- لقطات مرجعية فعلية (Nova HR HD 16.0E، حدث بـ EPG): InfoBar، SecondInfoBar، ChannelSelection، EPG، EventView، Menu، Plugins، Setup — `~/cineview-mla/shots/ref/` على ai-agent.

## 5. ما بُني (فرع dev/mla-openatv)
| المكوّن | الملف | الحالة |
|---|---|---|
| تعريف الأقسام كبيانات | `mla/sections.json` | مكتمل |
| نقل Classic | `tools/mla/migrate_classic.py` — 540 شاشة فعّالة (ترتيب تحميل OpenATV مُحاكى)؛ 29 شاشة في 6 أقسام + 511 في core؛ `~/` ⇒ مسار مطلق مكافئ | مكتمل |
| الثيمات | 6 ثيمات من `palette()` الأصلية؛ **navy = ألوان الذهبية بايتًا ببايت** | مكتمل |
| المكوّنات | `CineViewMLA*` (نسخ معاد تسميتها، إعدادات `config.plugins.cineviewmla`)، كاش البوستر بقائمة منع HDD بـ `st_dev` | مكتمل |
| محرك التركيب | `mla/engine/composer.py`: أجيال مختومة SHA-256، تبديل ذري برابط، سجل معاملات، rollback، recover | مكتمل |
| حارس الإقلاع | `mla/guardian/guardian.sh` عبر `/usr/bin/enigma2_pre_start.sh` الأصلي | مكتمل |
| بلجن التشغيل | `CineViewMLA`: إشارة سليمة 60 ث + علامة خروج نظيف | مكتمل (واجهة الإعدادات لاحقًا) |
| أدوات | build.py، deploy.sh (يرفض أي مسار خارج MLA)، test_engine.py، test_guardian.sh، parity_compare.py | مكتمل |

## 6. نتائج الاختبارات الفعلية على الرسيفر
| الاختبار | النتيجة | الحالة |
|---|---|---|
| محرك التركيب مع حقن أعطال (توقف عند stage/seal/switch، قتل أثناء الكتابة، ملف تالف في الجيل النشط، lkg تالف، رابط مكسور، journal تالف، احتفاظ) على USB ext4 + py3.14 | **18/18** | RUNTIME TESTED |
| حارس الإقلاع (تسلسل الانهيار 3/5/7، خروج نظيف، عدم التأثير على سكين آخر، فشل Python ⇒ shell، كتابة مقطوعة) | **11/11** | RUNTIME TESTED |
| إقلاع Enigma2 الحقيقي بـ MLA: الحارس يعمل قبل البدء (`boot.count=1`)، تحميل `active/*` بالترتيب الصحيح | ناجح | DEVICE VERIFIED |
| إيقاف نظيف ⇒ `clean_exit` يُكتب؛ الإقلاع التالي يعيد العدّاد إلى 1 | ناجح | DEVICE VERIFIED |
| أخطاء السكين في السجل | نفس 4 تحذيرات المرجع فقط (`progressPercentWidth`, `piconMargin` — موروثة) | DEVICE VERIFIED |
| المدقق على الجهاز بالمكوّنات الحقيقية | VALID؛ تحذير وحيد موروث (`PermanentClockMenu → KeyExit` غير معرّف في الذهبية أيضًا) | DEVICE VERIFIED |
| عزل HDD: البوسترات في `/media/usb/cineview-mla/dev-cache/*`؛ `/media/hdd/poster` لم يتغير (mtime 01:31) | ناجح | DEVICE VERIFIED |

## 7. ما زال قيد التنفيذ
- **M7 التكافؤ البصري**: لقطات OSD-only للمرجع وMLA ومقارنة بكسلية (الأداة جاهزة) + مراجعتك.
- **M8 التكافؤ الوظيفي** (أزرار ملونة، تنقل، بيانات حيّة).
- T14 (ISS-01) وT15 (ISS-02) على Slot 8.
- خط أساس HDD metadata (يعمل في الخلفية؛ أول محاولة فشلت بأسماء ملفات غير UTF-8 وأُصلحت).

## 8. مشكلات اكتُشفت وأُصلحت
| # | المشكلة | الإصلاح |
|---|---|---|
| 1 | المدقق اعتبر مكونات بلجنات غير مثبتة (MyTube, CSFD…) أخطاء مانعة | فصل: أخطاء شاشات الأقسام مانعة، شاشات core تحذيرات |
| 2 | الثيم الافتراضي `golden` غير موجود بعد التوليد | الافتراضي `navy` (= الذهبية) |
| 3 | `config.crash.enabledebug` يُحذف عند حفظ enigma2 | استخدام `config.crash.debugLevel=4` |
| 4 | INFO لا يفتح SecondInfoBar في 8.0.1 | ليس عيبًا: العقد الأصلي OK مرتين (`toggleShow`) |
| 5 | خط أساس HDD: أسماء غير UTF-8 | `surrogateescape` |

## 9. تنبيهات تحتاج قرارك
1. **EMC مثبت في Slot 8 ويتصفح `/media/hdd/movie` مباشرة** — اختبارات PVR تعرض محتوى HDD. أقترح ضبط مسار أفلام EMC داخل Slot 8 على مجلد اختبار في USB (تعديل إعداد داخل Slot 8 فقط).
2. **الطبق متحرك (USALS)**: كل الاختبارات على 16.0°E فقط؛ لن أنتقل لقمر آخر دون موافقتك.
3. اعتماد سلالة التصميم: اعتمدتُ Slot 3 = الذهبية 0926.
