# تقرير هندسي مرجعي — LiiS8 FHD Plus 2.0 (Enigma2 Skin + LiiS8Config)

> **نوع الوثيقة:** تحليل ثابت (Static Analysis) لحزمة مرجعية، لصالح مشروع CineView FHD.
> **التاريخ:** 2026-10-03 · **المحلل:** Claude (جلسة مشروع Enigma2 Master Engineering)
> **الحالة:** تحليل مكتمل برمجيًا فقط — **لم يُشغَّل أي شيء على جهاز Enigma2 حقيقي.** كل ما يخص السلوك التشغيلي مصنّف صراحة كفرضية أو كنتيجة مستنتجة من الشيفرة المصدرية للصور.

---

## 0. بطاقة التحليل وقابلية إعادة الإنتاج

| البند | القيمة |
|---|---|
| الملف | `enigma2-plugin-skins-liis8fhdplus_2.0_all.ipk` (12,457,180 بايت) |
| SHA-256 | `9d31740188c0bbcd7df332234c06be614354cd7462c9d5d3b2d9c3c79e23555c` |
| الصيغة | Debian binary 2.0 (`debian-binary` + `control.tar.gz` + `data.tar.gz`) — استُخرج بالكامل بلا أخطاء |
| المحتوى | 1464 ملفًا / ~20MB: 1301 PNG، 103 Python، 24 XML، 19 TTF + 12 OTF، 3 JPG، 1 PSD |
| Package | `enigma2-plugin-skins-liis8fhdplus` 2.0، `Architecture: all`، `Replaces: liis8-fhd-plus`، **بلا Depends** |
| التحقق الثابت المنفّذ | تحليل XML لكل الملفات (24/24 سليمة)، `py_compile` تحت Python 3.13 (103/103 سليمة)، فهرسة AST للاستيرادات، إسناد ترافقي للـ Renderers/Converters/الألوان/الخطوط/الـ panels/الصور |
| مراجع الصور (مصدر حقيقي، sparse clone) | OpenViX `enigma2@Developer` 74810f9 (2026-10-02) · OpenATV `master` 13e055d (2026-10-02) · OpenBH `Python3.14` e8799f7 (2026-09-27) · OpenPLi `scarthgap` 0cc9ad7 (2026-10-02) |
| مرجع CineView للمقارنة | `habeb-s/CineView-FHD@main` 729ab1a (2026-09-27)، snapshot `openvix-final-20260923` (أرشيفي، ليس بالضرورة الحالة الحيّة) |
| ما **لم** يُنفّذ | Python 2 (غير متوفر في البيئة؛ الشيفرة تستخدم f-strings فهي Py3 فقط أصلًا)، أي تشغيل على جهاز، أي اختبار شبكي للـ APIs |

**ملاحظة:** لم يكن هناك أي ملف تعذّرت قراءته. لم يُفترض أي محتوى.

---

## 1. الخلاصة التنفيذية

1. **LiiS8 سكين FHD (1920×1080) مبني على ثلاث طبقات:** XML مقسّم بـ `include`، طبقة Python ضخمة (50 Renderer + 42 Converter + 7 Tools)، وبلجن تهيئة (`LiiS8Config`) يبدّل أنماط InfoBar / SecondInfoBar / ChannelSelection.
2. **أقوى فكرة معمارية فيه — وهي الأهم لـ CineView:** تبديل الأنماط عبر **نسخ ملف جزئي صغير** (`sample/IB-x.xml` → `infobar.xml`) يُضمَّن في `skin.xml`، بدل توليد نسخ كاملة من السكين، مع **مفاتيح تفعيل حيّة** (Poster/Stars/Backdrop/Weather) تُقرأ داخل الـ Renderer وقت التشغيل دون إعادة تحميل السكين. CineView OpenViX (snapshot 2026-09-23) يحمل **30 نسخة كاملة ~187KB لكل منها (~5.6MB)** لتمثيل 3 خيارات بتوليفاتها — وهذا تحديدًا ما يحلّه نمط LiiS8.
3. **السكين مستهدف لهجة OpenATV:** 350 استخدامًا لخصائص `scrollbarRadius/scrollbarBackgroundColor/scrollbarBorder*` غير موجودة في `skin.py` لـ OpenViX/OpenBH/OpenPLi (تُتجاهل مع سطر خطأ في السجل، لا كراش).
4. **`skin_compat.xml` (619KB، 664 شاشة) مقتطع من سكينات أخرى:** 515 مرجع صورة لـ `MX_Slim-Line_NP/` و216 لـ `Estuary/` — **كلها غير موجودة في الحزمة** (118 ملف صورة فريد مفقود)، وألوان `bgbutton`/`button` (1343 استخدامًا) **غير معرّفة**.
5. **أخطاء ملموسة في الحزمة:** الـ InfoBar الرئيسي يستدعي Converter غير موجود (`LiiS8WeatherAlert`) وpanels غير معرّفة (`weather-infobar`، `infobar_Poster`)؛ اختيار `IB-6` في البلجن بلا ملف عيّنة؛ مسار `noposter` يشير لمجلد غير موجود.
6. **مخاطر تشغيلية في Python (فرضيات تحتاج إثباتًا على الجهاز):** استدعاء `eTimer.start()` من خيوط عاملة؛ طلب HTTP متزامن (حتى 3 ثوانٍ) داخل `getText()` على خيط الواجهة في 6 عناصر من الـ InfoBar الافتراضي؛ اعتبار `/media/hdd` قابلًا للكتابة دون التحقق من أنه mount حقيقي (خطر الكتابة على الفلاش)؛ تعطيل التحقق من TLS (`verify=False`) في 42 موضعًا؛ مفاتيح API مضمّنة في الشيفرة.
7. **في جانب البوستر، CineViewPosterX الحالي أكثر أمانًا من LiiS8** في اختيار التخزين (جدول mounts، استبعاد multiboot، `rw`) وفي عزل الخيوط عن الواجهة. ما يستحق الأخذ من LiiS8 هو: **مجمّع عمّال محدود + طابور محدود**، **ZapContext بعدّاد جيل**، **ذاكرة SQLite للبيانات الوصفية**، **خاصية `context`**، **تنظيف العناوين والنص العربي RTL**، وليس آلية التخزين ولا آلية الإرسال للواجهة.
8. **ترخيص:** ملفان على الأقل يحملان رخصًا تمنع التشغيل على غير أجهزة Dreambox / تمنع الاستخدام التجاري، والخطوط Neo Sans Std وVerdana تجارية. **لا يُنسخ أي كود أو خط حرفيًا إلى CineView** — تُنقل الأنماط الهندسية فقط.

---

## 2. بنية الحزمة والتثبيت

### 2.1 المسارات المثبّتة
```
/usr/share/enigma2/LiiS8/                       ← السكين (XML + صور + خطوط)
/usr/lib/enigma2/python/Components/Renderer/    ← 50 ملف LiiS8*.py
/usr/lib/enigma2/python/Components/Converter/   ← 42 ملف LiiS8*.py
/usr/lib/enigma2/python/Tools/                  ← 7 ملفات LiiS8*.py (كاش /proc، طقس، طلبات)
/usr/lib/enigma2/python/Plugins/Extensions/LiiS8Config/  ← البلجن
```

### 2.2 سكربتات التحكم
- **preinst:** إعلامي فقط، لا يحذف شيئًا. التعليق يوثّق أن نهج "احذف ثم ثبّت" سبّب سابقًا فشل إقلاع على صور فيها حزمة مصنع `liis8-fhd-plus` — لذلك اعتمد `Replaces:` للاستيلاء ملفًا بملف. **نمط جيد لـ CineView.**
- **postinst:** `chmod` للمجلدات/الملفات، فحص وجود sqlite3 (CLI أو وحدة Python)، و**لا يعيد تشغيل enigma2 عمدًا** لتجنّب قتل العملية من داخل مدير حزم enigma2 نفسه. **نمط صحيح يُنصح بتبنّيه.**
- **نواقص:** لا يوجد `prerm`/`postrm` → لا إزالة نظيفة، ولا استرجاع للسكين الافتراضي إذا كان LiiS8 نشطًا عند الإزالة. لا `Depends` رغم الاعتماد على `requests`, `urllib3`, `PIL`, `sqlite3`. `Installed-Size: 0` غير صحيح.
- **تعارض مع الترقية:** الحزمة تشحن `infobar.xml/secondinfobar.xml/channelselection.xml` (= IB-1/SIB-4/CH-1). أي ترقية تكتب فوق اختيار المستخدم بينما يبقى `config.plugins.LiiS8.*Style` على القيمة القديمة → عدم تطابق صامت بين الإعداد والواجهة. (ملاحظة: `secondinfobar.xml` الحالي يطابق `SIB-4` حجمًا وليس `SIB-1` الافتراضي.)

---

## 3. معمارية XML

### 3.1 شجرة التضمين (الملفات المحمّلة فعليًا)
```
skin.xml (299KB, 254 screen)
 ├─ <output>/<colors 126>/<fonts 22+13 alias>/<subtitles>/<parameters 32>/<windowstyle id=0,1>
 ├─ include infobar.xml           ← هدف حيّ (يُستبدل من sample/IB-n)
 ├─ include channelselection.xml  ← هدف حيّ (CH-n)
 ├─ include menu.xml
 ├─ include panels.xml            ← قوالب الشاشات المشتركة (28)
 ├─ include plugins.xml           ← 87 شاشة بلجنات
 ├─ (شاشات InfoBar/ChannelSelection… داخل skin.xml)
 ├─ include secondinfobar.xml     ← هدف حيّ (SIB-n)
 └─ include skin_compat.xml       ← 664 شاشة (في آخر الملف)
غير محمّلة: vertical_EPG.xml (لا يضمّنها أحد)، keymap.xml (نسخة keymap صورة؛ لا دليل على تحميلها)، Components/ServiceScan.py داخل مجلد السكين (لا يُستورد).
```
إجمالي 1010 اسم شاشة فريد في مجموعة التحميل.

### 3.2 أسبقية الشاشات المكررة — مُتحقَّق من المصدر
في `skin.py` لـ OpenViX (`loadSkin` سطر 167–200 و`loadSingleSkinData` سطر 1011): الـ `include` تُعالَج **قبل** تسجيل شاشات الملف الأب، والتسجيل `domScreens[name] = …` بالكتابة فوق. إذن:
- الشاشات الـ 15 المكررة بين `skin.xml` و`skin_compat.xml` (مثل `PluginManager`, `ParentalControlSetup`, `NetworkBrowser`…) → **نسخة `skin.xml` هي الفائزة**، ونسخ compat ميتة.
- `EMCPlaylistSetup` (plugins.xml ↔ skin_compat.xml) → الأخيرة تضمينًا (compat) تفوز.
- `IMDB` و`imdbSetup` مكررتان داخل `plugins.xml` نفسه → الثانية تفوز.

### 3.3 نظام القوالب (screen-as-panel)
`<panel name="X"/>` يستدعي `<screen name="X">` كقالب. أُحصي 74 هدف panel. القالب المحوري:
```xml
<screen name="LiiS8Chrome">        <!-- panels.xml:204 — 234 استخدامًا -->
    <panel name="SChLiiS8"/>       <!-- الخلفية/الإطار/التدرج -->
    <panel name="rgyb_all"/>       <!-- الأزرار الملونة الأربعة -->
    <panel name="pig"/>            <!-- نافذة الصورة المصغرة -->
</screen>
```
هذا "هيكل موحّد" تُبنى عليه معظم الصفحات العامة → **مطابق تمامًا لمتطلب CineView "صفحات عامة موحدة + footer وأزرار ملونة موحدة".** ثم قوالب وظيفية: `Setup` (139)، `QuickMenu` (75)، `Info` (72)، `cnfg`، `foot`، `intr`، `clk`، `datetime`.

**12 panel مُستدعى بلا تعريف** (بحسب `processPanel` في OpenViX سطر 1677–1683: يُطبع خطأ ويُتابَع، لا كراش): `weather-infobar` و`infobar_Poster` (داخل InfoBar نفسه!)، `FullscreenTitlePanel`، `title`، `cnf`، `cfg`، `rgyb`، `ButtonBarAuto2/3`، `__RcPanel__`، `wizard_rc_template`، `InfoBarTemplateBlank`.

### 3.4 تركيب الشاشات الأساسية (النمط الافتراضي)
| الشاشة | عدد العناصر | التكوين البارز |
|---|---|---|
| InfoBar (IB-1) | 87 | 22 أيقونة `Pixmap/LiiS8ServiceInfo` (HD/UHD/Dolby/Crypt…)، 6 حقول `LiiS8CamServerInfo`، 6 `LiiS8Access`، 4 عدادات دائرية `LiiS8CircleProgress/LiiS8Signal`، بوستر `LiiS8PosterX` + نجوم `LiiS8StarX` |
| SecondInfoBar (SIB-4) | 46 | **27** `LiiS8InfoEvents` (بيانات وصفية TMDB)، 3 بوسترات + 3 نجوم بـ `nexts=0/1/2` و`context="secondinfobar"`، `LiiS8BackdropX`، `LiiS8PrimeTime` |
| ChannelSelection (CH-1) | 79 | 4 عدادات إشارة، 3 بوسترات بـ `context="channelselection"` |

**ملاحظة تصميمية مهمة:** بوستر ChannelSelection مربوط بـ `source="session.CurrentService"` → يعرض بوستر **القناة المشغّلة** لا القناة **المؤشَّر عليها** في القائمة. CineView يحتاج `ServiceEvent` للعنصر المحدد (الـ Renderer يدعم `ServiceEvent` في `_get_ref` سطر 148، لكن الـ XML لا يستخدمه).

### 3.5 الألوان والخطوط
- **126 لونًا مسمّى** في كتلة واحدة؛ تسميات مختصرة غير دلالية (`b10`, `fc`, `p1..p9`, `cep`) مع بعض الأسماء الدلالية (`LiiS8TitleBlue`, `selbar`, `background`). **لا يوجد نظام ثيمات** — لون واحد ثابت، ولا آلية لتبديل لوحة الألوان (مجلد `mySkin_off` فارغ).
- **19 اسم لون مستخدم وغير معرّف**: أبرزها `bgbutton` (755) و`button` (588) و`transparent2` (98) في compat، و`layer-b-background` (3) في `skin.xml`. السلوك (من المصدر):
  - OpenViX/OpenBH (`parseColor` سطر 377): يُستبدل **بصمت** بـ `#00FFFFFF` (أبيض). مع `transparent="1"` غالبًا لا يظهر، لكن أي عنصر غير شفاف يظهر بخلفية بيضاء.
  - OpenATV: نفس الاستبدال + رسالة خطأ.
  - OpenPLi: `raise SkinError` → يُسقط العنصر.
- **الخطوط:** Neo Sans Std (عائلة كاملة TTF + نسخ OTF مكررة غير مستخدمة ~848KB). `font="verdanab; 45"` مستخدم في InfoBar وكل عيّنات IB (عرض قيمة الإشارة) **رغم أن `verdanab` غير مسجّل في `<fonts>`** (الملف موجود في `fonts/`). في OpenViX يُستبدل بـ `Body`، و`Body` غير معرّف في LiiS8 → يعتمد على skin_fallback للصورة. **النتيجة على الجهاز تحتاج تحقق.**

### 3.6 الأصول (Assets)
- مراجع مفقودة داخل حزمة LiiS8 نفسها: 74 في `skin.xml` (مثل `LiiS8/icons/scan-[cst].png`, `LiiS8/images/progress/…`, ومسار مكسور `LiiS8/images/progress/images/progress/prgrs_8.png`)، 20 في `panels.xml` (منها `rgyb3_*.png` للأزرار الملونة)، 15 في `plugins.xml`، و118 فريدًا في `skin_compat.xml`.
- **سلوك OpenViX (مُتحقَّق):** `loadPixmap` (سطر 488–497) يرفع `SkinError` عند غياب الملف، ويُمسك في حلقة العناصر (سطر 1670–1675) → **يُسقط ذلك العنصر فقط** مع traceback في السجل.
- ~391 PNG لا يُشار إليها باسمها (حد أعلى تقريبي؛ كثير منها مثل `key_*.png` و`vkey_*.png` تُحمَّل من نواة enigma2 بالاسم الافتراضي).

---

## 4. محرك الأنماط LiiS8Config

### 4.1 الآلية (مُتحقَّق من الشيفرة)
```
config.plugins.LiiS8.{InfobarStyle, SecondInfobar, ChannSelector}
          │ keySave()
          ▼
shutil.copyfile(sample/<ID>.xml → infobar.xml | secondinfobar.xml | channelselection.xml)
          ▼
if config.usage.fastSkinReload: skin.reloadSkins(); session.reloadDialogs()
else: "A GUI restart is required"
```
وبالتوازي **مفاتيح حيّة** لا تحتاج إعادة تحميل:
```
plugin.py: apply_plugin_config(config.plugins.LiiS8) عند التحميل وعند الحفظ
        → LiiS8Converlibr._runtime_cfg {POSTER_LEFT, STAR_RIGHT, BACKDROPX_ENABLED, WEATHER_ENABLED, BIG_POSTER_*, …}
        → كل Renderer يستدعي get_cfg(KEY) داخل changed() فيُخفي/يُظهر/يغيّر الحجم فورًا
```
وخاصية `context="infobar|channelselection|secondinfobar"` في XML تحدد **أي مفتاح** يُستشار، لأن `nexts` يعني يسار/يمين في InfoBar لكنه يعني الحدث الحالي/التالي في الشاشات الأخرى. **هذا فصل نظيف بين "موضع العنصر" و"دلالة الفهرس".**

### 4.2 عيوب
| # | العيب | الدليل |
|---|---|---|
| 1 | خيار `IB-6` معروض ولا يوجد `sample/IB-6.xml` ولا صورة معاينة → الحفظ يفشل برسالة خطأ | `plugin.py:108`، مجلد `sample/` |
| 2 | النسخ غير ذرّي (`copyfile` مباشرة على الهدف الحي) — انقطاع الكهرباء أثناء الكتابة = `infobar.xml` تالف = فشل تحميل السكين | `liis8_config.py:305–316` |
| 3 | `fastSkinReload` اسم إعداد خاص ببعض الصور؛ غير موجود يعني الرجوع لرسالة "أعد التشغيل" (سلوك آمن) | `liis8_config.py:371` |
| 4 | الترقية تكتب فوق الأهداف الحيّة (انظر 2.2) | `control`/data |
| 5 | الخصائص المخصّصة (`nexts`, `mode`, `context`) تُمرّر لـ `Renderer.applySkin` بدل حذفها من `skinAttributes` → أسطر "not implemented" في السجل، و`mode` يصطدم بـ `AttributeParser.mode` الموجود فعلًا في OpenViX | `LiiS8PosterX.py:106–131` |

---

## 5. طبقة Python

### 5.1 الاستخدام الفعلي
- Renderers: **50 مشحونًا، 8 فقط مستخدمة في XML** (`LiiS8InfoEvents` 63، `LiiS8CircleProgress` 45، `LiiS8PosterX` 25، `LiiS8RunningText` 23، `LiiS8StarX` 17، `LiiS8CryptoPixmap` 7، `LiiS8PrimeTime` 3، `LiiS8BackdropX` 3). الباقي (42) مكتبات مساعدة أو كود ميت (عائلة EMC الكاملة: `LiiS8[BCILPSX]EMC`, `LiiS8EMC*Thread`، الطقس، الصوت…).
- Converters: **42 مشحونًا، 15 مستخدمًا** (`LiiS8ServiceInfo` 152، `LiiS8Signal` 53، `LiiS8ServiceName2` 50، `LiiS8DiskInfos` 34، `LiiS8Access` 33، `LiiS8NetworkInfo` 32، `LiiS8EventInfo` 28، `LiiS8CamServerInfo` 24…). 27 غير مستخدمة.
- **كل الملفات Python 3 فقط** (f-strings). لا تعمل على صور Py2 — غير مهم لـ OpenViX 6.x.

### 5.2 مكونات خارجية يستدعيها XML وغير مشحونة
| المكوّن | النوع | الشاشات | OpenViX | OpenATV | OpenBH | OpenPLi |
|---|---|---|---|---|---|---|
| `LiiS8WeatherAlert` | Converter | **InfoBar** | ✗ | ✗ | ✗ | ✗ |
| `MSNWeather` / `MSNWeatherPixmap` | C/R | MSNWeatherPlugin، SubsMenu، DeviceMountPanelConf… | ✗ (من بلجن WeatherPlugin) | ✗ | ✗ | ✗ |
| `MetrixHDXPicon` | R | EPGvertical* | ✗ | ✗ | ✗ | ✗ |
| `Cover` | R | MoviePlayer، MovieSelection | ✗ | ✓ | ✗ | ✗ |
| `VRunningText` | R | — | ✗ | ✓ | ✗ | ✗ |
| `EMCEventName`/`EMCMovieInfo` | C | EMCSelection | (من بلجن EMC) | | | |
| `FNCsvcInfo2`/`FNCsvcpos` | C | MerlinMusicPlayer، FNCyify | ✗ | ✗ | ✗ | ✗ |
| `CoolNextEvent` | R | CoolChannelGuide | ✗ | ✗ | ✗ | ✗ |
| `RunningText` / `MovieReference` | R/C | — | ✓ | ✓ | ✓ | ✗ |

(✓/✗ = وجود الملف في `lib/python/Components/{Renderer,Converter}` عند الـ commit المذكور في §0؛ مكونات البلجنات الخارجية لا تظهر في مستودع enigma2.)

**سلوك المفقود (مُتحقَّق):** OpenViX `readSkin` سطر 1577–1591 يرفع `SkinError("Converter '…' not found")`، يُمسك لكل عنصر على حدة → يُسقط العنصر وتستمر الشاشة. لذلك **الـ InfoBar لن ينهار لكنه سيفقد عنصر تنبيه الطقس، وسيسجّل traceback عند كل بناء للشاشة.** (يُحتمل أن الحزمة تفترض وجود ملفات من حزمة المصنع `liis8-fhd-plus` — يذكر preinst هذه الحزمة صراحة.)

### 5.3 منظومة البوستر/البيانات الوصفية (أهم جزء مرجعي)
```
LiiS8PosterX / LiiS8StarX / LiiS8InfoEvents / LiiS8BackdropX  (Renderers، خيط الواجهة)
        │ changed() → get_zap_context(service_ref)  ← ZapContext + عدّاد جيل generation
        │            → convtext()/clean_name()      ← تنظيف العنوان (JUNK_WORDS، الصيني، الأرقام اللاحقة، العربية)
        │            → is_news_or_weather_channel() ← تخطي قنوات الأخبار/الرياضة + كلمات المستخدم
        ▼
queue_live(clean_title)  → queue.Queue(maxsize=200)  → N عامل (افتراضي 6، حد أدنى 2)
        │   requests.Session + HTTPAdapter(pool=4)  ← TMDB/OMDB/TheTVDB/Fanart/TVmaze/elcinema/molotov…
        │   تنزيل إلى .part → PIL Image.verify() → os.replace() ذرّي
        │   SQLite LiiS8Data.db (check_same_thread=False, timeout=10) أو :memory: كاحتياط
        ▼
queue_gui_callback(cb) → _ready_queue (+lock) → _trigger_drain() → eTimer 20ms → cb() على خيط الواجهة
```
**نقاط قوة قابلة لإعادة الاستخدام (كنمط):**
- طابور محدود + مجمّع عمّال محدود (يمنع انفجار الخيوط؛ CineView حاليًا يُنشئ خيطًا لكل عنوان: `CineViewPosterX.py:408`).
- كتابة ذرّية + التحقق من سلامة الصورة قبل الاستبدال.
- `ZapContext` بعدّاد جيل: يُسقط النتائج المتأخرة لقناة سابقة بعد التنقل السريع (zapping) → يمنع "بوستر خاطئ لحدث سابق" — **وهو بالضبط عطل تاريخي في CineView SecondInfoBar.**
- كاش وجود الملفات بزمن صلاحية 5 ثوانٍ (`file_exists_cached`) لتقليل `stat()` على الـ HDD.
- تنسيق نص RTL للنبذات العربية (`_is_rtl`, `_wrap_rtl` بعرض 70).
- `register_nxts_slot`: كل Renderer يسجّل فهرس الحدث الذي يحتاجه، فيُجلب فقط عدد الأحداث القادمة المطلوب فعلًا من EPG.

**مخاطر (مرتبة):**
| الخطورة | المشكلة | الدليل | التصنيف |
|---|---|---|---|
| عالية | `_trigger_drain` يستدعي `eApp.isGuiThread()` — **غير موجودة في نواة OpenATV/OpenViX** (لم يُعثر عليها في `lib/base`, `main`, `lib/python/*.i`). الاستثناء يُبتلع ثم يُستدعى `eTimer.start()` **من الخيط العامل**. eTimer ليس آمنًا بين الخيوط → سباق على قائمة مؤقتات الحلقة الرئيسية. | `LiiS8Converlibr.py:304–312` | فرضية قوية من الشيفرة — تحتاج إعادة إنتاج (تنقل سريع مع تحميل بوسترات، مراقبة segfault) |
| عالية | `_get_base_path()` يعتمد `os.path.exists('/media/hdd') and os.access(W_OK)` — نقطة التركيب موجودة على rootfs حتى دون HDD → **كتابة البوسترات على الفلاش**. يُستدعى `makedirs` مع كل طلب مسار. ويُنشئ `/media/hdd/LiiS8` تلقائيًا عند الاستيراد دون موافقة | `LiiS8Converlibr.py:112–155` | مُتحقَّق منطقيًا من الشيفرة |
| عالية | `LiiS8CamServerInfo.getText()` (بلا `@cached`) → `get_server_info()` → `urlopen(..., timeout=3)` إلى OSCam webif **على خيط الواجهة**، مع Poll كل 5 ثوانٍ، و6 عناصر في InfoBar الافتراضي | `LiiS8CamServerInfo.py:347–369, 397–410, 486` | مُتحقَّق من الشيفرة؛ أثر التجميد يحتاج قياسًا على الجهاز |
| متوسطة | `verify=False` في 42 موضعًا + `urllib3.disable_warnings` → لا تحقق من شهادات TLS | DownloadThreads، MediaInfo، EMC* | مُتحقَّق |
| متوسطة | مفاتيح API مضمّنة في الشيفرة (TMDB افتراضي + قاموس `_DEFAULT_API_KEYS`) — مشتركة بين كل المستخدمين وقابلة للإلغاء | `LiiS8Converlibr.py:66, 1254` | مُتحقَّق (لم تُنسخ القيم إلى هذا التقرير) |
| متوسطة | خيوط تبدأ عند **استيراد** الوحدة (`threading.Thread(...).start()` على مستوى الوحدة) حتى لو الميزة معطّلة | `LiiS8PosterXDownloadThread.py:1010` | مُتحقَّق |
| متوسطة | `LiiS8EcmInfo` ينفّذ `os.system('ln -s ... Components/Converter/bitratecalc.so')` عند الاستيراد (تعديل ملفات نظام كأثر جانبي) — الملف غير مستخدم في XML حاليًا | `LiiS8EcmInfo.py:23–26` | مُتحقَّق |
| منخفضة | `noposter` يُبحث عنه في `/usr/share/enigma2/<skin>/main/` — المجلد غير موجود في الحزمة → لا صورة بديلة | `LiiS8PosterX.py:50–60` | مُتحقَّق |

### 5.4 مكونات أخرى جديرة بالدراسة
- **`LiiS8Signal`**: `SNRdB` يقرأ `source.snr_db` (مقياس dB×100) — **نفس العقد المستخدم في `FrontendInfo` الأصلي لـ OpenViX** (سطر 63–64) — مع احتياط تقديري؛ ومعالجة القيمة الحارسة `0xFFFFFFFF` لـ BER. مرجع جيد لصفحة الإشارة في CineView (مع إبقاء العقد الأصلي هو المرجع).
- **`LiiS8CircleProgress`** (أصل digiteng): عدّاد دائري من شريط صور مسبقة الرسم (`circleProgress/`) فوق `eWidget` مع `ePixmap`+`eLabel` — بديل خفيف لرسم الأقواس. يحتاج `pixmapCircle`, `pixmapCircleBack`, `scale`.
- **`LiiS8InfoEvents`**: `eLabel` بحقول وصفية (تقييم، نوع، ممثلين، نبذة) مع تمرير تلقائي (scroll) ومؤقت إعادة محاولة EPG.
- **كاش `/proc`** (`Tools/LiiS8ProcMemCache`, `LiiS8ProcResCache`, `LiiS8CpuFreqCache`): قراءة واحدة مشتركة بين عدة Converters بدل قراءة متكررة — نمط جيد للأداء.
- **السجلات** كلها في `/tmp` (RAM) مع تدوير (`RotatingFileHandler` 512KB، trace 4MB، `TRACE_ENABLED=False` افتراضيًا) — سليم.

---

## 6. مصفوفة التوافق مع الصور (من `skin.py` الحقيقي)

خصائص XML المستخدمة في LiiS8 وغير المدعومة في `AttributeParser` لبعض الصور (الخصائص التي تقرأها مكونات القوائم نفسها مثل `Entry*`/`Cool*`/`serviceNameFont` مستبعدة من الحكم لأنها تُستهلك داخل `applySkin` للمكوّن):

| الخاصية | الاستخدامات | OpenViX | OpenATV | OpenBH | OpenPLi |
|---|---|---|---|---|---|
| `scrollbarBackgroundColor` | 350 | ✗ | ✓ | ✗ | ✗ |
| `scrollbarRadius` | 350 | ✗ | ✓ | ✗ | ✗ |
| `scrollbarBorderWidth` / `scrollbarBorderColor` | 339 | ✗ | ✓ | ✗ | ✗ |
| `itemSpacing` / `spacingColor` | 40 / 39 | ✗ | ✓ | ✗ | ✗ |
| `verticalAlignment` / `horizontalAlignment` | 13 / 6 | ✗ | ✓ | ✗ | ✗ |
| `backgroundGradient` | 58 | ✓ | ✓ | ✓ | ✗ |
| `cornerRadius` | — | ✓ | ✓ | ✓ | ✓ |

**سلوك غير المدعوم في OpenViX (سطر 542–549):** "Attribute … is not implemented!" في السجل، لا كراش. **الاستنتاج:** LiiS8 سكين بلهجة OpenATV؛ على OpenViX سيعمل لكن ستفقد أشرطة التمرير تنسيقها، وسيمتلئ السجل.

**ميزة مكتشفة مفيدة لـ CineView (مُتحقَّق وجودها في المصدر للصور الأربع):**
```xml
<include filename="parts/compat_openvix.xml" conditional="..."/>
```
`loadSingleSkinData` يقيّم `conditional` بـ `eval` (OpenViX:1011–1015، OpenATV:1496–1500، OpenBH:1011، OpenPLi:887). `skin.py` في OpenViX يستورد `BoxInfo` صراحةً "for use in the include conditional" (سطر 9). أي يمكن **لحزمة واحدة** أن تضمّن طبقة توافق خاصة بكل صورة وقت التحميل.
- **تحذيرات:** OpenATV فقط يحيط `eval` بـ try؛ في الصور الأخرى استثناء في الشرط قد يُفشل تحميل السكين كله. و`config.plugins.<X>` لا يكون معرّفًا وقت تحميل السكين (قبل استيراد البلجنات) → **لا تستخدم إعدادات البلجن في الشرط**؛ استخدم `BoxInfo`/`SystemInfo` فقط، وتحقق من أسماء المفاتيح (`distro`, `imageversion`…) على كل صورة.

---

## 7. مقارنة مباشرة مع CineView (snapshot openvix-final-20260923)

| المحور | LiiS8 2.0 | CineView OpenViX (أرشيف) | الحكم |
|---|---|---|---|
| تبديل الأنماط | 3 ملفات جزئية تُنسخ إلى أهداف include + مفاتيح حيّة | 30 نسخة `skin.layout-XYZ-{oa,msn,none}.xml` كاملة (~187KB لكل منها) | **LiiS8 أفضل بوضوح** |
| تفعيل البوستر/النجوم/الخلفية | `get_cfg()` حي داخل الـ Renderer | ملفات `skin.withposters/noposters/safe-noposterx*` | **LiiS8 أفضل** |
| اختيار التخزين | `exists+access` (خطر الفلاش) | جدول mounts، `rw`، أجهزة `/dev/`، استبعاد multiboot و tmpfs/شبكي | **CineView أفضل** — لا تستبدله |
| عزل الخيوط عن الواجهة | طابور + eTimer لكن يُشغَّل من الخيط العامل | العامل لا يلمس الواجهة؛ كل Renderer يستطلع بمؤقته على خيط الواجهة | **CineView أسلم** |
| عدد الخيوط | مجمّع محدود (2–6) + طابور 200 | خيط لكل عنوان (غير محدود) | **LiiS8 أفضل** |
| الكتابة الذرية | `.part` + `os.replace` + `PIL.verify` | `.part` + `os.rename` + فحص أبعاد JPEG | متكافئ تقريبًا |
| مزودو البيانات | متعدد (TMDB/OMDB/TVDB/Fanart…) بمفاتيح | TVmaze + iTunes + IMDb suggestion بلا مفاتيح | قرار منتج؛ نهج CineView بلا مفاتيح أبسط صيانة |
| البيانات الوصفية | SQLite + 27 حقل InfoEvents | لا يوجد ما يعادله في الـ snapshot | **LiiS8 مرجع جيد** |
| حماية من نتائج قناة سابقة | ZapContext + generation | — (العطل التاريخي "Wrong Second InfoBar posters") | **تبنَّ الفكرة** |

---

## 8. ما يُعاد استخدامه في CineView — كأنماط تُعاد كتابتها، لا كود يُنسخ

### أولوية 1 — معمارية التخطيط (تحل مشكلة "too many layout XML variants")
1. استبدال الـ 30 نسخة بملف `skin.xml` واحد يضمّن **أهدافًا حيّة صغيرة**: `cv_infobar.xml`, `cv_secondinfobar.xml`, `cv_channelselection.xml`، تُملأ من `parts/` عند الحفظ.
2. الكتابة **ذرّية**: `write tmp → fsync → os.replace` مع نسخة احتياطية `*.bak` واستعادتها إن فشل `reloadSkins()`.
3. نقل كل مفاتيح "مع/بدون بوستر، weather oa/msn/none" إلى **إعدادات حيّة** يقرؤها الـ Renderer/Converter (نمط `apply_plugin_config` + `get_cfg`)، فتختفي مضاعفة الملفات 2ⁿ×3.
4. `postinst` لا يكتب فوق الأهداف الحيّة إن وُجدت؛ أو يعيد توليدها من الإعداد المحفوظ — لحل تعارض الترقية في §2.2.
5. طبقة التوافق لكل صورة عبر `<include conditional="BoxInfo…">` **بعد** التحقق على الجهاز من أسماء مفاتيح BoxInfo لكل صورة.

### أولوية 2 — منظومة البوستر (تحسين CineViewPosterX دون المساس بنقاط قوته)
1. إبقاء `_cineview_poster_cache_root()` كما هو (أسلم من LiiS8).
2. استبدال "خيط لكل عنوان" بـ `queue.Queue(maxsize=N)` + 2–4 عمّال يبدؤون **عند أول طلب** لا عند الاستيراد.
3. إضافة **عدّاد جيل للتنقل** (ZapContext): كل طلب يحمل `generation`؛ الـ Renderer يتجاهل أي نتيجة جيلها أقدم.
4. خاصية `context` في XML لفصل دلالة `nexts` بين InfoBar/ChannelSelection/SecondInfoBar، **مع حذف الخصائص المخصصة من `skinAttributes` قبل `Renderer.applySkin`**.
5. في ChannelSelection: ربط البوستر بـ `ServiceEvent` للعنصر المحدد، لا `CurrentService`.
6. الإرسال للواجهة: إمّا البقاء على نمط CineView (استطلاع بمؤقت الـ Renderer)، أو `ePythonMessagePump`/`eFixedMessagePump` — **لا** `eTimer.start()` من خيط عامل.

### أولوية 3 — نظام التصميم الموحّد
1. قالب "هيكل" واحد على غرار `LiiS8Chrome` (خلفية + أزرار ملونة + footer + pig) تستدعيه كل الصفحات العامة — يحقق متطلب "footer وأزرار ملونة موحدة".
2. **لوحة ألوان دلالية مركزية** (عكس LiiS8): أسماء مثل `cv.bg`, `cv.surface`, `cv.accent`, `cv.text`, `cv.textDim`, `cv.selBg` فقط، وكل ثيم = ملف `colors_<theme>.xml` يُضمَّن (هدف حي واحد)، مع **فحص آلي يمنع أي لون غير معرّف** (لأن OpenViX يحوّله بصمت إلى أبيض — وهو تفسير محتمل لـ "صفحات زرقاء/فاتحة تبقى بعد تغيير الثيم").
3. تسجيل كل خط مستخدم + تعريف `Body` صراحة.

### أولوية 4 — صفحة الإشارة ومعلومات الخدمة
- `SNRdB` من `source.snr_db`، معالجة BER الحارسة، كاش `/proc` المشترك، وعدادات دائرية بشريط صور — كمرجع تصميم، مع ربطها بالعقد الأصلي `FrontendInfo` للصورة.

### ما **لا** يُؤخذ
- `skin_compat.xml` (مقتطفات MX_Slim-Line_NP/Estuary بأصول غير موجودة)؛ أي ملف بترخيص Dream/CC-NC (`LiiS8EventList.py`, `LiiS8VolumeText.py`)؛ الخطوط التجارية (Neo Sans Std، Verdana)؛ مفاتيح API المضمّنة؛ `verify=False`؛ أي استدعاء شبكي أو `subprocess` داخل `getText()`.

---

## 9. أداة الفحص الثابت المقترحة لـ CineView (مستخلصة من هذا التحليل)
السكربتات التي بُني عليها هذا التقرير قابلة لأن تصبح **بوابة CI** لكل build:
1. تحليل XML لكل ملف.
2. كل `render=`/`convert type=` موجود إمّا في الحزمة أو في `Components/` **للصورة المستهدفة** (مقابل commit محدد).
3. كل اسم لون/خط مستخدم معرّف.
4. كل `<panel name>` له `<screen name>`.
5. كل مسار صورة موجود.
6. كل خاصية مدعومة في `skin.py` للصورة المستهدفة (مع قائمة استثناءات خصائص المكونات).
7. لا شاشة مكررة إلا بقصد موثق.

هذا **فحص ثابت لا يغني عن الاختبار على الجهاز**، لكنه كان سيكشف كل عيوب §3–§5 قبل النشر.

---

## 10. الترخيص والملكية
- `LiiS8EventList.py`: رخصة Dream Property — تمنع التوزيع/التشغيل على أجهزة غير مرخصة من Dream.
- `LiiS8VolumeText.py`: CC BY-NC-SA 3.0 (+ بند Dream Multimedia).
- مكونات منسوبة إلى digiteng، Lululla/MNASR (AGP)، xDreamy، RAED، MCelliotG، vlamo، markusw.
- خطوط Neo Sans Std (Monotype) وVerdana (Microsoft) تجارية؛ إعادة توزيعها في CineView غير مقبولة دون ترخيص.
- **السياسة:** يُعاد تنفيذ الأنماط بكود CineView أصلي، مع ذكر المصدر المرجعي في التوثيق.

---

## 11. حالة البنود (وفق بروتوكول التسليم)

| البند | الحالة |
|---|---|
| استخراج الحزمة وفهرستها | مكتملة ومختبرة برمجيًا فقط |
| صحة XML (24 ملف) وترجمة Python 3 (103 ملف) | مكتملة ومختبرة برمجيًا فقط |
| الإسناد الترافقي (مكونات/ألوان/خطوط/panels/صور) | مكتملة ومختبرة برمجيًا فقط |
| مصفوفة التوافق مقابل مصدر OpenViX/OpenATV/OpenBH/OpenPLi | مكتملة برمجيًا (مقابل commits محددة؛ قد تختلف عن الإصدار المثبت فعليًا على الجهاز) |
| سلوك الأخطاء (لون/خط/صورة/converter مفقود) | مستنتج من الشيفرة المصدرية — يحتاج تأكيدًا من سجل enigma2 على الجهاز |
| خطر `eTimer` من خيط عامل، تجميد CamServerInfo، كتابة الفلاش | فرضيات قوية — تحتاج إعادة إنتاج على الجهاز |
| توصيات CineView | تصميم هندسي — غير منفّذ |
| تثبيت LiiS8 على جهاز | لم يُنفّذ (لا يُنصح به على slot الإنتاج؛ إن لزم فعلى slot اختبار multiboot مع نسخة احتياطية) |

### خطة تحقق مقترحة على الجهاز (عند الطلب)
1. slot اختبار OpenViX على USB؛ نسخة احتياطية للـ slot.
2. تثبيت LiiS8، تفعيله، جمع `enigma2 debug log`: عدّ أسطر `[Skin] Error` (يتوقع: Converter `LiiS8WeatherAlert`، panels `weather-infobar`/`infobar_Poster`، خصائص scrollbar، صور MX/Estuary).
3. فصل HDD والتحقق إن أُنشئ `/media/hdd/LiiS8` على rootfs (`df /media/hdd`, `mount`).
4. إيقاف OSCam webif/جعله بطيئًا وقياس استجابة InfoBar.
5. تنقل سريع (20 قناة) أثناء تنزيل البوسترات، مراقبة الكراش و`/tmp/liis8_trace.log` (بعد تفعيل TRACE).
6. الإزالة والعودة للسكين السابق، والتحقق من نظافة النظام.

---

## 12. ملحق — إعادة الإنتاج
```sh
ar x enigma2-plugin-skins-liis8fhdplus_2.0_all.ipk
mkdir data control && tar xzf data.tar.gz -C data && tar xzf control.tar.gz -C control
# صحة XML
for f in $(find data -name '*.xml'); do python3 -c "import xml.etree.ElementTree as E,sys;E.parse(sys.argv[1])" $f; done
# ترجمة Python 3
find data -name '*.py' -exec python3 -m py_compile {} \;
# مصادر الصور (sparse)
git clone --depth 1 --filter=blob:none --sparse https://github.com/OpenViX/enigma2.git vix
cd vix && git sparse-checkout set --no-cone /lib/python/skin.py '/lib/python/Components/Converter/*' '/lib/python/Components/Renderer/*' '/lib/python/Tools/*'
```
