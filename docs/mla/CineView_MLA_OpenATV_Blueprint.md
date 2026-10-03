# CineView FHD — مخطط إعادة الهندسة: Multi-Layout Architecture على OpenATV

> **النسخة:** 1.1 (مخطط تقني — لم يبدأ التنفيذ) · **التاريخ:** 2026-10-03
> **تعديلات 1.1 (بطلبك):** (1) حارس إقلاع مستقل عن Enigma2 — §2.8 · (2) معاملة تبديل مقاومة لانقطاع الكهرباء — §2.4/§2.9 · (3) عزل كامل للتطوير والبوسترات والكاش عن HDD والمستقر — §7 · (4) مرجع التصميم = الملفات الحية + لقطات فعلية من الجهاز، واختبار بصري ووظيفي — §4 · (5) تثبيت قاعدة "تصميم جديد لأي قسم دون إعادة هندسة" — §2.2 · وتحديثات من أدلة P0: عقد إصدار الجهاز الفعلي 45414bc (§1.1)، والمشكلتان في §8.
> **الصورة المستهدفة الحصرية في هذه المرحلة:** OpenATV (لا OpenViX، لا OpenBH)
> **الحالة الإجمالية:** UNDER INVESTIGATION → جاهز لبدء المرحلة P0 بعد موافقتك وتوفر الوصول للجهاز.
> **مراجع هذا المخطط:** `claude/references/LiiS8_FHD_Plus_2.0_Reference_Analysis.md` · مصدر OpenATV `enigma2@master` 13e055d (2026-10-02) · CineView `main` 729ab1a، snapshot `openatv-final-20260926` (SHA-256 مُتحقَّق: `1101ccdb…02a6`).

---

## 0. القرارات المعتمدة (من طلبك) وكيف ينعكس كل منها

| القرار | الانعكاس الهندسي |
|---|---|
| OpenATV حصريًا | كل عقد، وكل اختبار، وكل حزمة تُبنى مقابل OpenATV فقط. ملفات OpenViX/OpenBH (`openbh_compat.py`، `vix_skin.xml`، snapshots الأخرى) **خارج نطاق البناء** ولا تُستورد. |
| تصاميم مستقلة متعددة لكل قسم | "حزم تصاميم" (Layout Packs) لكل قسم، تُكتشف تلقائيًا من مجلدها، وتُفعَّل بمحرك تركيب ذرّي. |
| تصميم CineView الحالي ضمن الخيارات | يُنقل كما هو إلى حزم `classic` لكل قسم، مع **بوابة تكافؤ 0-فرق** مقابل النسخة الذهبية. |
| LiiS8 مرجع للتصاميم الجديدة | **أفكار وظيفية فقط.** لا ترخيص صريح في XML الخاص بـ LiiS8 ⇒ يُعامل كـ "كل الحقوق محفوظة": لا إحداثيات، لا أصول، لا كود. (§9) |
| واجهة تحكم بمعاينة | CineViewControl 3: اختيار لكل قسم + صورة معاينة + "تجربة حيّة مع تراجع تلقائي". |
| قابلية OpenViX لاحقًا دون تعقيد الآن | فاصل محوّل (Adapter seam) بواجهة واحدة؛ **يُنفَّذ محوّل OpenATV فقط.** ملفات الحزم تُسمّى `screens.openatv.xml` من اليوم الأول. |
| نسخة تطوير مستقلة، والمستقرة دون مساس | Slot اختبار multiboot + مجلد سكين `CineView_FHD_MLA` منفصل + مكونات Python بأسماء جديدة لا تكتب فوق المستقرة. (§7) |
| اختبار فعلي على OpenATV | مصفوفة اختبار على الجهاز مع لقطات شاشة آلية عبر OpenWebif، لا الاكتفاء بالفحص الثابت. (§8) |

---

## 1. ما الذي تعلّمناه من دراسة العقود الفعلية (Evidence)

### 1.1 عقود OpenATV الأصلية ذات الصلة (من الشيفرة المصدرية، commit 13e055d)

| الآلية | الدليل | الاستخدام في المعمارية |
|---|---|---|
| **ترتيب التحميل:** emergency skin → subtitle → primary skin → `mySkin/skin_*.xml` → `skin_user_<Skin>.xml` | `skin.py:InitSkins` 99–170 | نعرف بدقة من يكتب فوق من. |
| **`<include>` يُعالَج قبل `<colors>` و`<windowstyle>` للملف الأب، وشاشات الأب تكتب فوق شاشات المُضمَّن** | `loadSingleSkinData` 1496–1527، `loadSkin` 180–222 | ⇒ **لا ألوان في `skin.xml` الجذري أبدًا**؛ الألوان فقط في ملف الثيم المُضمَّن، وإلا كتب الأب فوقها. |
| **ملف include مفقود أو شرط خاطئ = خطأ مُسجَّل لا فشل** (OpenATV يحيط `eval` بـ try) | 1497–1507 | شبكة أمان طبيعية؛ لكن لا نعتمد عليها — المحرك يضمن وجود الملفات. |
| **`<include conditional="…">`** مدعوم | 1499 | متاح لاحقًا لطبقة OpenViX (بشرط `BoxInfo` فقط). |
| **إعادة تحميل السكين الأصلية:** `reloadSkins()` + `WHERE_SKINCHANGE` + `session.reloadDialogs(exclude=…)` + `ChannelSelectionSetup.updateSettings` | `Screens/SkinSelection.py:104–123`، `config.usage.fastSkinReload` (افتراضي False) | المحرك يعيد استخدام **نفس التسلسل الأصلي** حرفيًا، لا يخترع تسلسلًا خاصًا. |
| **خطاف الاستعادة عند الإقلاع:** `/etc/.restore_skins` → `Plugins/Extensions/*/ActivateSkinSettings.py` → `ActivateSkinSettings().WriteSkin(True)` | `InitSkins` 102–118 | يعيد توليد الملفات المفعّلة بعد استعادة إعدادات/تحديث صورة. **يحل مشكلة "الترقية تكتب فوق اختيار المستخدم".** |
| **(P0) إصدار الجهاز المسجّل:** `enigma2 8.0.0-beta+git35513+45414bc` = فرع `8.0` commit **45414bc** (2026-09-19)، Python 3.14.7 — **هذا هو مرجع العقود، لا master**. اختلافات مؤثرة: في 45414bc **`reloadSkins()` لا يعيد بناء خيارات أنماط ChannelSelection** (تُبنى مرة عند الإقلاع في `UsageConfig` 339–356) ⇒ إضافة نمط ChannelSelection جديد تتطلب إعادة تشغيل الواجهة | `snapshots/openatv-final-20260923` meta + `git log origin/8.0` | يُعاد التحقق من الإصدار على الجهاز في P0b. |
| **(P0) خطاف ما قبل الإقلاع الأصلي:** `enigma2.sh` يشغّل `/usr/bin/enigma2_pre_start.sh` (إن كان قابلًا للتنفيذ) **قبل كل تشغيل لـ Enigma2**، وEnigma2 يُعاد تشغيله تلقائيًا (respawn) | `tools/enigma2.sh.in@45414bc` | نقطة ارتكاز حارس الإقلاع المستقل (§2.8). |
| **أنماط ChannelSelection أصلية:** أي شاشة بـ `base="ChannelSelection" label="…"` تظهر خيارًا في `config.channelSelection.screenStyle`؛ وقوالب `serviceList` من `skinTemplates.xml` تظهر في `widgetStyle` | `UsageConfig.refreshChannelSelectionStyleChoices` 34–63، `ChannelSelection.py:2404–2411` | **ChannelSelection لا يحتاج تبديل ملفات**: كل التصاميم تُحمَّل معًا ويُختار بينها بالآلية الأصلية. |
| **سلاسل skinName (fallback)** | InfoBar: `["InfoBarLite","InfoBar"]`؛ SecondInfoBar: `SecondInfoBarECM` إذا `show_second_infobar=="3"` وإلا `SecondInfoBar`؛ EPG: `EPGSelection`، `EPGSelectionMulti`، `QuickEPG`، `GraphicalEPG(PIG)`، `GraphicalInfoBarEPG`، `EPGvertical(PIG)`؛ PVR: `["MovieSelectionSlim","MovieSelection"]`، `MoviePlayer`، `PVRState`، `TimeshiftState/Live`؛ EventView: `[skin,"EventView"]` | `InfoBar.py`، `InfoBarGenerics.py:2074`، `EpgSelection.py`، `MovieSelection.py:238` | الشاشات ذات الاسم الثابت تُبدَّل **بتركيب الملف المفعّل**؛ ChannelSelection بالآلية الأصلية. |
| ميزات لهجة OpenATV | `scrollbarRadius/BackgroundColor/Border*`، `itemSpacing`، `cornerRadius`، `backgroundGradient`، ألوان gradient بفاصلة، `<layouts>`، `<constant-widgets>`، `<variables>` | `skin.py` | مسموحة داخل ملفات `*.openatv.xml` فقط (انظر §6). |

### 1.2 حالة CineView الذهبية على OpenATV (snapshot 2026-09-26) — نتائج مُتحقَّقة

| البند | النتيجة | الأثر على المخطط |
|---|---|---|
| مجموعة XML الحية | `skin.xml` (196 شاشة) + `skin_templates.xml` (56) + `skin_plugins.xml` (302) + `openatv_skin.xml` (33) | مصدر الترحيل. |
| **22 شاشة مكررة** عبر 3–4 ملفات (EPG×7، SecondInfoBar×2، PluginBrowser×3، MessageBox×2…) | بقاعدة "الأب يفوز" ⇒ نسخ `skin.xml` هي الفعّالة؛ ~44 نسخة ميتة | الترحيل يحذف الميت بعد إثبات أنه ميت. |
| 30 نسخة كاملة `skin.layout-XYZ-{oa,msn,none}.xml` + 4 `safe-noposterx` + 2 + 6 نسخ `.before-*` | المذكرة تقول "cleaned" لكن الأرشيف ما زال يحويها | تُستبدل كلها. |
| **ما تغيّره النسخ فعليًا:** مفتاح البوستر يغيّر **شاشتين فقط** (InfoBar: عنصران، ChannelSelection: 5 عناصر)؛ مزود الطقس يغيّر **InfoBar فقط** | مقارنة شجرية بين `layout-000` و`111` و`none` | ⇒ 30 ملفًا تُختزل إلى **مفاتيح حيّة + "فتحة" طقس صغيرة**. |
| **مفتاح "Posters – Second InfoBar" بلا أثر في XML** (شاشة SecondInfoBar متطابقة بين 000 و111) | نفس المقارنة | يُصلح في المحرك الجديد (مفتاح حي حقيقي). |
| **التصميم المعتمد موجود فقط كناتج سلسلة ترقيع:** `skin.xml` الحي يختلف عن مصدره الاسمي `layout-111-oa` بـ ~3300 سطر و30 شاشة؛ ناتج `theme.py`→`timeformat.py`→`compat.py`→`openatv_v5.py`→`openatv_auditfix.py`→`openatv_plugin_ui.py` | diff | **مصدر الحقيقة للترحيل هو `skin.xml` الحي، لا ملفات النسخ.** |
| **مسار الحفظ من واجهة CineViewControl لا يشغّل `openatv_v5/auditfix/plugin_ui`** (يشغّلها `activate.sh` فقط) | `plugin.py:keySave` | فرضية قوية: الحفظ من الواجهة قد يُسقط التحسينات المعتمدة. **تحقق على الجهاز في P0.** |
| **`apply_timeout()` يكتب مهلة الثواني في `config.usage.show_second_infobar`** (وهو **وضع** العرض 0–3) بدل `second_infobar_timeout` | `plugin.py:apply_timeout` + `UsageConfig.py:408–414` + `ConfigSelection.setValue` (قيمة خارج الخيارات ⇒ الافتراضي "1" = Event Info؛ و"0" ⇒ Off) | **عيب منطقي مؤكد من الشيفرة**: عند كل إقلاع قد يتحول INFO من SecondInfoBar إلى EventView. يُتحقق منه في P0 ويُصلح في P5. |
| `activate.sh` يعدّل `/etc/enigma2/settings` بـ `sed` | قد يُكتب فوقه عند حفظ enigma2 لإعداداته | يُلغى؛ الإعدادات عبر `configfile` فقط. |
| `killall -9 enigma2` كاحتياط، و`smartdeps.sh --install` يثبّت حزمًا في الخلفية تلقائيًا | `plugin.py` | يُستبدل بإعادة تشغيل أصلية (`TryQuitMainloop 3`) وتثبيت يطلبه المستخدم صراحة. |
| تعديل ملف بلجن آخر: `EnhancedMovieCenter/CoolSkin/EMCSelection_left_pig_1080.xml` | محتوى الأرشيف | يُنقل إلى حزمة PVR داخل السكين إن ثبت أن EMC يقرأ شاشة السكين (تحقق P1). |
| `LukaPosterXEMC` يستورد `LukaPosterXDownloadThread` **غير موجود في الأرشيف** | رأس الملف | اعتماد خفي على ملف في الجهاز؛ يُحصر في P0. |
| المكونات المستخدمة: كلها أصلية في OpenATV عدا `CineView*` (5 Converters + PosterX) و`OAWeather*` (بلجن OpenATV) | إسناد ترافقي مقابل `Components/` | CineView نظيف من حيث الاعتماد (أنظف من LiiS8). |
| الخطوط: Liberation Sans (رخصة حرة) | — | آمن. |

### 1.3 ما يُؤخذ من LiiS8 (أفكار هندسية، يُعاد تنفيذها بكود CineView)
1. تبديل التصميم بتركيب **ملف صغير مُضمَّن** بدل نسخ السكين الكامل.
2. **مفاتيح حيّة** يقرؤها الـ Renderer وقت التشغيل (بوستر/نجوم/خلفية/طقس) دون إعادة تحميل.
3. خاصية **`context`** لفصل دلالة `nexts` بين الشاشات.
4. **ZapContext بعدّاد جيل** لإسقاط نتائج القناة السابقة.
5. **مجمّع عمّال محدود + طابور محدود**، وكتابة ذرية مع تحقق من سلامة الصورة.
6. قالب "هيكل" موحّد (خلفية + أزرار ملونة + footer) تستدعيه الصفحات العامة.
7. أفكار تصميم وظيفية (أي معلومات تُعرض: تقييم بنجوم، نوع، نبذة، backdrop، عدادات إشارة دائرية) — **تُصمَّم من الصفر**.

**ما لا يُؤخذ:** آلية الإرسال للواجهة (`eTimer.start` من خيط عامل)، اختيار التخزين (CineView أسلم)، `verify=False`، مفاتيح API المضمّنة، أي HTTP داخل `getText()`، أي XML/صور/خطوط/أيقونات VClouds (غير تجارية).

---

## 2. المعمارية الجديدة (CineView MLA)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ L5  CineViewControl 3 (Plugin)  — UI: أقسام / معاينة / تجربة+تراجع / ملفات تعريف │
├──────────────────────────────────────────────────────────────────────────┤
│ L4  Composition Engine (Python, بلا GUI)                                   │
│     Registry ← manifests · Validator · Composer (staging→atomic swap)      │
│     Reloader (تسلسل OpenATV الأصلي) · Rollback · Boot Restore Hook         │
├───────────────┬──────────────────────────────────┬───────────────────────┤
│ L3 Themes     │ L2 Layout Packs (لكل قسم)         │ L4' Runtime Config     │
│ themes/<id>/  │ layouts/<section>/<id>/          │ CineViewRuntime        │
│ theme.xml     │ manifest.json, screens.openatv.xml│ (مفاتيح حيّة للـRenderers)│
├───────────────┴──────────────────────────────────┴───────────────────────┤
│ L1  Core Skin: skin.xml رفيع + core/ (chrome, common, plugins) + active/   │
├──────────────────────────────────────────────────────────────────────────┤
│ L0  Image Adapter: OpenATVAdapter (الوحيد المنفَّذ)  ← فاصل OpenViX لاحقًا   │
│     عقود الشاشات · تسلسل إعادة التحميل · آلية ChannelSelection · خطاف الإقلاع │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.1 شجرة الملفات على الجهاز (نسخة التطوير)
> **تعديل 1.1:** `active/` لم يعد مجلدًا يُعاد تسميته، بل **رابطًا رمزيًا** يشير إلى جيل مكتمل غير قابل للتعديل داخل `generations/` — انظر §2.9.
```
/usr/share/enigma2/CineView_FHD_MLA/
├── skin.xml                     ← رفيع: output, fonts, parameters, windowstyle (يشير لرموز)، includes فقط. لا <colors>.
├── core/
│   ├── chrome.openatv.xml       ← قوالب panels: CVChrome, CVHeader, CVFooter, CVColorKeys, CVPig
│   ├── common.openatv.xml       ← الصفحات العامة الموحدة (Setup, MessageBox, Menu, PluginBrowser*, Hotkey, Language, MultiBoot…)
│   └── plugins.openatv.xml      ← شاشات بلجنات طرف ثالث
├── layouts/
│   ├── infobar/{classic,…}/           manifest.json, screens.openatv.xml, preview.png, assets/
│   ├── secondinfobar/{classic,…}/
│   ├── channelselection/{classic,…}/  ← تُحمَّل كلها معًا (آلية OpenATV الأصلية)
│   ├── epg/{classic,…}/
│   ├── pvr/{classic,…}/
│   ├── eventview/{classic,…}/
│   └── slots/weather/{oa,msn,none}/   ← "فتحات" صغيرة داخل التصاميم
├── themes/{black,navy,graphite,burgundy,green,purple}/theme.xml + theme.json
├── skinTemplates.xml            ← مولَّد: قوالب serviceList المجمعة من حزم channelselection (ملف أصلي في OpenATV)
├── active -> generations/g000123     ← رابط رمزي؛ التبديل = rename ذري لرابط
├── generations/
│   ├── g000000/   ← "Classic المصنع": يُشحن في الحزمة، لا يُحذف أبدًا (ملاذ أخير)
│   ├── g000122/   ← آخر جيل مؤكَّد سليم (last-known-good)
│   └── g000123/   ← الجيل الحالي
│       ├── theme.xml infobar.xml secondinfobar.xml channelselection.xml epg.xml pvr.xml eventview.xml weather.xml
│       ├── skinTemplates.part.xml
│       └── MANIFEST.sha256   ← بصمة كل ملف + معرّف الجيل؛ يُكتب آخرًا (= علامة اكتمال الجيل)
└── (skinTemplates.xml رابط رمزي إلى active/skinTemplates.part.xml)

/etc/enigma2/cineview_mla/            ← حالة صغيرة على rootfs (ليست HDD)
├── txn.json        ← سجل المعاملة: PREPARING → STAGED → SWITCHED → TRIAL → COMMITTED
├── lkg             ← معرّف آخر جيل سليم
├── boot.count      ← عدّاد الحارس
├── healthy         ← طابع آخر إقلاع سليم
└── profiles/       ← ملفات تعريف المستخدم (JSON)
```
يُحتفظ بآخر 3 أجيال + g000000 فقط (تنظيف تلقائي بعد COMMITTED).
ترتيب `include` في `skin.xml`:
```xml
<include filename="active/theme.xml"/>          <!-- الألوان أولًا (لا ألوان في الأب) -->
<include filename="core/chrome.openatv.xml"/>
<include filename="core/common.openatv.xml"/>
<include filename="core/plugins.openatv.xml"/>
<include filename="active/weather.xml"/>
<include filename="active/infobar.xml"/>
<include filename="active/secondinfobar.xml"/>
<include filename="active/channelselection.xml"/>
<include filename="active/epg.xml"/>
<include filename="active/pvr.xml"/>
<include filename="active/eventview.xml"/>
```
**قاعدة عدم التكرار:** كل اسم شاشة يُعرَّف في **ملف واحد فقط** عبر المجموعة المحمّلة كلها (يفرضها المدقق). هذا يُنهي مشكلة الـ 22 شاشة المكررة نهائيًا.

### 2.2 حزمة التصميم (Layout Pack) — العقد
`manifest.json`:
```json
{
  "schema": 1,
  "id": "classic",
  "section": "infobar",
  "name": "CineView Classic",
  "version": "1.0.0",
  "author": "habeb-s",
  "license": "CineView-Proprietary",
  "origin": "migrated:openatv-final-20260926",
  "targets": { "openatv": { "file": "screens.openatv.xml", "min_version": "7.6" } },
  "provides_screens": ["InfoBar", "InfoBarLite", "RadioInfoBar"],
  "requires": { "renderers": ["CineViewPosterX3"], "converters": ["CineViewBitrate3"], "optional_plugins": ["OAWeather"] },
  "slots": ["weather"],
  "features": { "poster": true, "stars": false, "backdrop": false },
  "preview": "preview.png"
}
```
- **قسم = مجموعة أسماء شاشات ثابتة**؛ الحزمة يجب أن تعرّف **كل** أسماء شاشات قسمها (المدقق يرفض الناقصة) حتى لا تبقى شاشة من تصميم آخر.
- الصور داخل الحزمة تُشار بمسار من جذر السكين: `CineView_FHD_MLA/layouts/infobar/classic/assets/…`.
- **إضافة تصميم مستقبلي = إضافة مجلد (أو IPK صغير يثبّت المجلد) فقط.** لا إعادة بناء للسكين.
- **(1.1) قاعدة التوسع الملزمة:** القسم نفسه بيانات لا كود — `sections.json` يعرّف كل قسم (المعرّف، أسماء الشاشات الإلزامية والاختيارية، آلية التبديل `compose|native-channelselection`). إضافة **قسم** جديد (مثل Volume أو EventView أو صفحة الإشارة) = سطر في `sections.json` + حزمة classic له، دون تعديل المحرك أو الواجهة. الواجهة تبني قائمة الأقسام والحزم وصور المعاينة ديناميكيًا من الـ Registry.
- **(1.1) إعدادات خاصة بكل تصميم:** `manifest.json: options[]` (نوع، افتراضي، تسمية) تُعرض تلقائيًا في الواجهة تحت ذلك التصميم، وتُخزَّن في `config.plugins.cineview3.layout.<section>.<id>.<option>`، ويقرؤها الـ Renderer حيًّا عبر CineViewRuntime. مثال: "عدد أسطر النبذة" أو "إظهار النجوم".

### 2.3 الأقسام والشاشات المغطاة (OpenATV)
| القسم | الشاشات (يجب أن توفرها كل حزمة) | آلية التبديل |
|---|---|---|
| infobar | `InfoBar`، `InfoBarLite`(اختياري)، `RadioInfoBar` | تركيب `active/infobar.xml` |
| secondinfobar | `SecondInfoBar`، `SecondInfoBarECM`، `SecondInfoBarSimple` | تركيب |
| channelselection | شاشات بأسماء فريدة `CV_CS_<id>` مع `base="ChannelSelection" label="…"` + قوالب `serviceList` | **أصلية**: `config.channelSelection.screenStyle/widgetStyle` |
| epg | `EPGSelection`، `EPGSelectionMulti`، `QuickEPG`، `GraphicalEPG`، `GraphicalEPGPIG`، `GraphicalInfoBarEPG`، `EPGvertical`، `EPGverticalPIG` (+`GraphMultiEPG*` إن وُجد البلجن) | تركيب |
| pvr | `MovieSelection`، `MovieSelectionSlim`(اختياري)، `MoviePlayer`، `PVRState`، `TimeshiftState`، `TimeshiftLive`، (EMC اختياري) | تركيب |
| eventview | `EventView`، `EventViewSimple`، `InfoBarEventView`، `EventViewEPGSelect` | تركيب |
| قابل للتوسيع | `Volume`، `NumberZap*`، `ChannelSelection` الأصغر (`SimpleChannelSelection`)… | نفس العقد |

> القائمة نهائية فقط بعد P1: تُستخرج أسماء الشاشات وسلاسل `skinName` و`self["…"]` آليًا من **إصدار OpenATV المثبّت فعليًا على الجهاز** (ليس من `master`).

### 2.4 محرك التركيب (Composition Engine) — المعاملة الذرية (محدَّث 1.1)
```
apply(selection):
  1. resolve      ← Registry يقرأ manifests (تجاهل الحزم التالفة مع سبب)
  2. validate     ← المتطلبات موجودة؟ الشاشات كاملة؟ لا تكرار أسماء؟ لا ألوان/خطوط غير معرّفة؟ الصور موجودة؟
  3. PREPARING    ← txn.json {id:g000124, from:g000123, state:PREPARING} + fsync
  4. stage        ← كتابة generations/g000124/* + fsync لكل ملف
  5. seal         ← كتابة MANIFEST.sha256 آخرًا + fsync للملف وللمجلد ⇒ txn=STAGED
  6. verify       ← إعادة قراءة الجيل من القرص ومطابقة البصمات + XML parse + المدقق الثابت
  7. switch       ← ln -s generations/g000124 active.tmp ; rename(active.tmp → active) ; fsync(dir) ⇒ txn=SWITCHED
  8. reload       ← OpenATVAdapter.reload(): نفس تسلسل SkinSelection الأصلي إن fastSkinReload، وإلا TryQuitMainloop(3)
  9. TRIAL        ← مؤقت تأكيد داخل الواجهة + حارس الإقلاع (§2.8) كشبكة أمان خارجية
 10. COMMITTED    ← بعد تأكيد المستخدم + "إقلاع سليم" ⇒ lkg=g000124
  ✗ أي فشل قبل 7  ← حذف الجيل الناقص فقط؛ active لم يتغير أصلًا
  ✗ أي فشل بعد 7  ← rename رابط إلى lkg، إعادة التحميل، تسجيل السبب
```
السجل في `/tmp/cineview-mla.log` (RAM) + ملخص دائم صغير في `/etc/enigma2/cineview_mla/history.log` (مدوَّر، ≤64KB).
- **عند الإقلاع:** `ActivateSkinSettings.WriteSkin()` (الخطاف الأصلي) + فحص بصمات `state.json`؛ إن كانت `active/` ناقصة أو تالفة يُعاد توليدها من الإعدادات المحفوظة.
- **postinst** لا يكتب فوق `active/` إن كانت موجودة؛ يشحن `active.default/` (= Classic) ويُنسخ فقط عند غياب `active/`.
- **لا `sed` على settings، لا `killall -9`، لا تثبيت حزم تلقائي في الخلفية.**

### 2.8 حارس الإقلاع المستقل (CineView Guardian) — جديد 1.1
**الهدف:** استعادة تلقائية حتى لو انهار Enigma2 أثناء الإقلاع ولم تظهر أي واجهة أو نافذة تأكيد.
- **المكان:** سكربت `sh` صغير (POSIX/busybox، بلا Python وبلا Enigma2) يُستدعى من الخطاف الأصلي `/usr/bin/enigma2_pre_start.sh` الذي ينفّذه `enigma2.sh` **قبل كل تشغيل** لـ Enigma2 (بما فيه كل إعادة تشغيل تلقائية بعد الانهيار).
  - إن كان `enigma2_pre_start.sh` موجودًا لحزمة أخرى على الجهاز: **لا يُستبدل**؛ يُستخدم ملف تجميع (`/usr/bin/enigma2_pre_start.d/` إن وُجد آلية كهذه) أو يُضاف سطر استدعاء واحد قابل للإزالة بعد موافقتك — يُقرَّر في P0b بعد فحص الجهاز.
- **الخوارزمية:**
  1. إن لم يكن السكين المفعّل (`config.skin.primary_skin` في settings) هو `CineView_FHD_MLA` ⇒ لا يفعل شيئًا (لا يؤثر على المستقر أو أي سكين آخر).
  2. **فحص التركيب غير المكتمل (§2.9)** أولًا.
  3. `boot.count += 1` (كتابة ذرية: ملف مؤقت + `mv`).
  4. إن `boot.count ≥ 3` (أي إقلاعان فاشلان متتاليان بلا `healthy`) ⇒ تراجع إلى `lkg`؛ وإن `≥ 5` ⇒ تراجع إلى `g000000`؛ وإن `≥ 7` ⇒ **آخر ملاذ:** تبديل `config.skin.primary_skin` إلى السكين الافتراضي للصورة (Enigma2 متوقف في هذه اللحظة فلا تعارض مع حفظه للإعدادات) + نسخة احتياطية من settings قبلها.
  5. كل قرار يُسجَّل في `history.log`.
- **مؤشر السلامة:** CineView يكتب `healthy` ويصفّر العدّاد بعد **60 ثانية** من ظهور InfoBar دون انهيار (مؤقت في `WHERE_SESSIONSTART`)، وفي وضع TRIAL فقط بعد تأكيد المستخدم.
- **حماية من حلقة لا نهائية:** الحارس لا يكتب إلا ملفات CineView ورابط `active` (والسطر الواحد في settings في الملاذ الأخير)؛ لا يحذف أي ملف.
- **الإزالة:** `prerm` يزيل استدعاء الحارس ويعيد السكين الافتراضي إن كان MLA مفعّلًا.
- **يُثبت فعليًا في الاختبارات** بإدخال جيل يسبب انهيارًا متعمّدًا (Renderer يرفع استثناء في `__init__`) على slot الاختبار فقط.

### 2.9 التبديل المقاوم لانقطاع الكهرباء — جديد 1.1
**المبدأ:** لا يُعدَّل أي ملف قيد الاستخدام أبدًا. الجيل الجديد يُكتب بالكامل في مجلد جديد، ويُختم بـ `MANIFEST.sha256` آخرًا، ثم يحدث التبديل بعملية واحدة ذرية (`rename` لرابط رمزي على نفس نظام الملفات) يليها `fsync` للمجلد.
| لحظة الانقطاع | الحالة بعد الإقلاع | الإجراء (الحارس ثم Python) |
|---|---|---|
| أثناء الكتابة (PREPARING) | `active` يشير للجيل القديم السليم؛ جيل ناقص بلا MANIFEST | حذف الجيل الناقص؛ لا تغيير |
| بعد الختم قبل التبديل (STAGED) | `active` قديم | حذف أو إبقاء الجيل (لا يُفعَّل تلقائيًا) |
| أثناء `rename` | POSIX يضمن أن `active` إما القديم أو الجديد كاملًا | التحقق من MANIFEST للهدف |
| بعد التبديل قبل التأكيد (SWITCHED/TRIAL) | `active` جديد غير مؤكد | يُعامَل كتجربة: العدّاد يعمل؛ بلا تأكيد خلال إقلاعين ⇒ lkg |
| `active` يشير إلى جيل تالف (فشل التحقق من البصمة أو رابط مكسور) | — | فورًا إلى lkg، ثم g000000 |
| `txn.json` نفسه تالف | — | يُعاد بناؤه من الأجيال الموجودة؛ أحدث جيل مختوم وسليم ومُدرج في lkg يُعتمد |
**يتطلب التحقق على الجهاز (P0b):** نوع نظام ملفات rootfs على Duo 4K SE (ext4 متوقع، `mtdrootfs=mmcblk0p9`)، دعم الروابط الرمزية في مسار include، وتوفر `sha256sum` في busybox. **اختبار فعلي:** قطع التيار في كل مرحلة على slot الاختبار (يدويًا منك، بتوقيت يحدده سكربت يطبع المرحلة).

### 2.5 نظام الثيمات
- رموز دلالية فقط في التصاميم: يُحتفظ بأسماء CineView الحالية (`steThemePrimary/Panel/PanelAlt/Top/Overlay/OverlayStrong/Selected/Text/Muted/Accent`، `steSecondInfoBG`) لضمان تكافؤ الترحيل، وتُضاف رموز جديدة عند الحاجة (`cvKeyRed/Green/Yellow/Blue`، `cvPosterFrame`، `cvProgress…`).
- `themes/<id>/theme.xml` = كتلة `<colors>` فقط؛ تُولَّد الستة الحالية من دالة `palette()` الموجودة **وتُطابَق رقميًا** مع قيم navy الحالية.
- **فحص آلي يمنع أي لون حرفي `#…` أو اسم غير معرّف داخل حزم التصاميم** (عدا ألوان الأزرار الأصلية المحددة).
- إلغاء نسخ PNG لكل ثيم قدر الإمكان: استبدالها بعناصر لونية (`cornerRadius`، `backgroundGradient` — مدعومة في OpenATV). ما يبقى صورًا يُعرَّف في `theme.json: assets`.
- تغيير الثيم = تركيب `active/theme.xml` + إعادة تحميل؛ لا regex على ملفات السكين.

### 2.6 طبقة البيانات الحيّة (Runtime)
- `Tools/CineViewRuntime.py`: يقرأ `config.plugins.cineview.*` ويعرض `get(key)` للـ Renderers/Converters؛ يُحدَّث عند الحفظ بلا إعادة تحميل.
- **CineViewPosterX3** (اسم جديد، لا يكتب فوق `CineViewPosterX` المستقر):
  - يحتفظ بمنطق التخزين الحالي (جدول mounts، استبعاد multiboot، `/media/hdd/poster` أولًا، `/tmp` احتياط) وبالكتابة الذرية وفحص الأبعاد.
  - يضيف: طابورًا محدودًا + 2–4 عمّال يبدؤون عند أول طلب؛ عدّاد جيل للتنقل؛ خاصية `context`؛ حذف الخصائص المخصصة من `skinAttributes`؛ دعم `ServiceEvent` في ChannelSelection (بوستر القناة **المؤشَّر عليها**)؛ مفاتيح حيّة لكل قسم.
  - الإرسال للواجهة: يبقى نمط CineView (استطلاع بمؤقت الـ Renderer على خيط الواجهة)؛ لا `eTimer` من خيط عامل.
- Converters الحالية (`CineViewBitrate/CPUTemp/CamInfo/IMDb/Transponder*`) تُراجَع ثم تُنسخ بأسماء `*3` مع قاعدة: **لا I/O شبكي أو `subprocess` في `getText()`**.
- **فتحة الطقس:** `slots/weather/{oa,msn,none}` تُختار آليًا حسب المزوّد المطلوب والمثبّت (منطق `effective_weather()` الحالي).

### 2.7 واجهة التحكم CineViewControl 3
| الشاشة | المحتوى |
|---|---|
| الرئيسية | حالة التركيب الحالي، بصمة `state.json`، تحذيرات المتطلبات الناقصة |
| التصاميم | قائمة الأقسام ← قائمة الحزم المتاحة + **صورة المعاينة** (`preview.png` بلقطة حقيقية من الجهاز) + وصف + المتطلبات |
| الثيمات | 6 ثيمات حالية + معاينة لون (عيّنات) |
| البوسترات | تشغيل/إيقاف لكل قسم (InfoBar، SecondInfoBar، ChannelSelection، EPG، PVR)، الحجم، النجوم، مكان التخزين (عرض فقط + تغيير عبر LocationBox)، مسح الكاش (بتأكيد) |
| المعلومات الإضافية | مزود الطقس، وضع معلومات الـ CAM (full/profile/hide — الحالي)، تنسيق الوقت، bitrate، حرارة المعالج |
| SecondInfoBar | **الوضع** (`show_second_infobar`) و**المهلة** (`second_infobar_timeout`) كإعدادين منفصلين — إصلاح العيب §1.2 |
| ملفات التعريف | تصدير/استيراد JSON إلى `/etc/enigma2/cineview/profiles/` |
| التشخيص | تشغيل المدقق على الجهاز وعرض التقرير |

**المعاينة قبل التطبيق — مستويان:**
1. **ثابتة:** `preview.png` لكل حزمة (لقطة حقيقية مأخوذة أثناء QA).
2. **تجربة حيّة:** "جرّب" ⇒ تطبيق مؤقت ⇒ عدّاد 20 ثانية "احتفظ / تراجع" ⇒ تراجع تلقائي إن لم يُؤكَّد. إن تطلب التطبيق إعادة تشغيل الواجهة (`fastSkinReload` معطّل): يُحفظ `pending_trial` في `state.json`، وبعد الإقلاع يظهر نفس الحوار، والتراجع يعيد `active.prev` ويعيد التشغيل.
> استقرار `reloadSkins()` المتكرر على OpenATV **غير مُثبت** — يُقاس في P6 قبل اعتماده افتراضيًا.

**حفظ إعدادات المستخدم:** `config.plugins.cineview.*` عبر `configfile` الأصلي فقط، مع ترحيل المفاتيح الحالية: `theme`، `poster_infobar/second/channels`، `weatherprovider`، `servermode`، `timeformat`؛ `secondtimeout` يُرحَّل إلى `config.usage.second_infobar_timeout` (مع قص القيم 30/60 غير الموجودة في خيارات OpenATV إلى 20).

---

## 3. فاصل OpenViX المستقبلي (يُصمَّم الآن، لا يُنفَّذ)
- واجهة `ImageAdapter`: `detect()`، `contracts()`، `screen_sections()`، `reload(session)`، `channelselection_mode()` (أصلي/تركيب)، `boot_restore_hook()`، `pack_file_key()` (`openatv`).
- **المنفَّذ الآن:** `OpenATVAdapter` فقط. لا كود شرطي لـ OpenViX في أي مكان آخر.
- الحزم تحمل ملفًا لكل صورة (`screens.openatv.xml`)؛ لاحقًا يُضاف `screens.openvix.xml` بجانبه عند إثبات العقد على OpenViX، دون لمس ملف OpenATV.
- ميزات OpenATV الحصرية مسموحة داخل `*.openatv.xml`؛ **قاعدة واحدة فقط** لا تكلّف شيئًا الآن: `core/chrome` يستخدم panels (screen-as-panel، آلية مشتركة بين الصور) لا `constant-widgets`، لأنه المكوّن الذي سيُعاد استخدامه أكثر.

---

## 4. خطة نقل تصميم CineView الحالي إلى المعمارية الجديدة

| الخطوة | العمل | معيار القبول |
|---|---|---|
| M0 تجميد (محدَّث 1.1) | **مرجع التصميم = الملفات الحية على الجهاز + لقطات فعلية**، بعد التحقق من نسخة الجهاز: (أ) سحب الملفات الحية للقراءة فقط إلى أرشيف `golden-live-<date>` مع SHA-256 و`image-version` و`opkg list-installed`؛ (ب) مقارنتها بـ `openatv-final-20260926`؛ (ج) **التقاط لقطات مرجعية فعلية** لكل شاشة في كتالوج الاختبار (§8) من النسخة المستقرة على slot الإنتاج عبر OpenWebif `/grab` (قراءة فقط، لا تثبيت). النسخة الذهبية في المستودع **لا تُعدَّل إطلاقًا**؛ أي اختلاف يُوثَّق كأرشيف جديد بجانبها | بصمات + لقطات + تقرير اختلاف |
| M1 تطبيع | تحميل المجموعة الذهبية بمحاكاة ترتيب OpenATV (الأب يفوز) ⇒ "الشاشة الفعّالة" لكل اسم؛ حذف النسخ الميتة | قائمة 196+… شاشة فعّالة بلا تكرار |
| M2 تجميد سلسلة الترقيع | `skin.xml` الحي هو ناتج السلسلة؛ يُعتمد كما هو. قواعد `openatv_v5/auditfix/plugin_ui` (مثل GraphicalEPG = 1920×1080 عند 0,0؛ PluginBrowser/QuickMenu/PackageAction FHD مع أزرار ملونة) تتحول إلى **اختبارات تأكيد** في المدقق، والسكربتات تتقاعد | كل قاعدة مُعبَّر عنها كاختبار ينجح على الذهبية |
| M3 تقسيم | توزيع الشاشات الفعّالة: أقسام ⇒ `layouts/<section>/classic/`؛ الباقي ⇒ `core/common` و`core/plugins`؛ ChannelSelection ⇒ `CV_CS_classic` مع `base=` | كل شاشة في مكان واحد |
| M4 الثيم | استخراج `<colors>` إلى `themes/*`؛ الستة من `palette()` | navy المولّد = navy الحالي بايتًا بايت |
| M5 البوستر والطقس | استبدال نسخ البوستر بمفاتيح حيّة (العناصر الإضافية في InfoBar/ChannelSelection تبقى في الحزمة وتُخفى حيًا)؛ الطقس ⇒ فتحة | تطابق بصري عند تشغيل/إيقاف كل مفتاح |
| M6 بوابة التكافؤ الثابتة (شرط لازم غير كافٍ) | تركيب (classic + الثيم المسجّل على الجهاز + إعدادات البوستر المسجلة + الطقس) ثم مقارنة دلالية لكل شاشة مع **الملفات الحية** | 0 فروق (عدا إعادة تسمية ChannelSelection الموثّقة) |
| M7 **بوابة التكافؤ البصري (القبول الفعلي)** | على slot الاختبار: نفس القناة/الحدث/الإعدادات، لقطة `/grab` لكل شاشة ⇒ مقارنة بكسلية مع اللقطة المرجعية من المستقر (فرق مطلق ومناطق الاختلاف مظللة)، ثم **مراجعتك البصرية** | لا فرق خارج المناطق الديناميكية (الوقت، الإشارة، البوستر، نص الحدث) المعرَّفة مسبقًا لكل شاشة |
| M8 **بوابة التكافؤ الوظيفي** | لكل شاشة: الأزرار الملونة، التنقل، OK/EXIT، INFO (وضع SecondInfoBar)، تحديث البيانات الحية بتغيير القناة، البوستر يظهر ويتغير، EPG يتحرك | قائمة فحص لكل شاشة بنتيجة موثقة بلقطات |

---

## 5. التصاميم الجديدة (بعد اكتمال Classic)
مبدأ: **تصاميم أصلية** مستوحاة وظيفيًا من LiiS8، على شبكة 1920×1080 موحدة (هوامش 48px، خط أساس 8px، أحجام خط محددة في `parameters`).
| القسم | المقترح الأول | الفكرة الوظيفية المستوحاة |
|---|---|---|
| InfoBar | **Cinema**: بوستر بارز + تقييم نجوم + نوع + سنة، شريط تقني مختصر | بوستر+نجوم+بيانات وصفية |
| SecondInfoBar | **Details**: الحالي/التالي مع نبذة طويلة قابلة للتمرير وbackdrop خافت | InfoEvents + backdrop + nexts=0/1 |
| ChannelSelection | **Poster List** (نمط أصلي `base=`) + قالب `serviceList` بديل | بوستر القناة المؤشَّر عليها |
| EPG | Graphical بلوحة تفاصيل جانبية مع بوستر | — |
| PVR | MovieSelection بغلاف + معلومات ملف | — |
| الإشارة | صفحة إشارة بعدادات دائرية مرسومة بعناصر (لا صور مأخوذة) | CircleProgress (الفكرة فقط) |
كل تصميم جديد: مواصفة مكتوبة (wireframe بإحداثيات) **تُعتمد منك قبل التنفيذ**.

---

## 6. المدقق الثابت (بوابة CI) — يعمل على الحاسوب وعلى الجهاز
1. XML صالح لكل ملف.
2. **عقد OpenATV:** كل `render=`/`convert type=` موجود في `Components/` لإصدار الجهاز أو ضمن حزم CineView؛ كل `widget name=` موجود في `self[…]` لشاشة الـ Python المقابلة (مستخرج بـ AST من مصدر الإصدار المطابق).
3. كل لون/خط/panel معرّف؛ كل صورة موجودة.
4. لا اسم شاشة مكرر في المجموعة المحمّلة.
5. كل حزمة توفر كل شاشات قسمها.
6. اختبارات التأكيد الموروثة من سلسلة الترقيع (M2).
7. حدود الشاشة: لا عنصر يتجاوز 1920×1080.
> **ثابت فقط.** لا يُعتبر دليل عمل.

---

## 7. فصل التطوير عن المستقر
| الطبقة | المستقر (لا يُلمس) | التطوير |
|---|---|---|
| المستودع | `main` + وسم `stable/openatv-20260926` | فرع `dev/mla-openatv` (هذه الجلسة تملك قراءة فقط للمستودع حاليًا؛ الدفع يتطلب ربطه بصلاحية كتابة أو أن تدفع أنت) |
| الجهاز | slot الإنتاج الحالي | **slot multiboot منفصل على USB ext4** بـ OpenATV بنفس الإصدار، مع نسخة احتياطية قبل أي تثبيت |
| مجلد السكين | `CineView_FHD` | `CineView_FHD_MLA` |
| مكونات Python | `CineViewPosterX`، `CineView*`، `CineViewControl` | `CineViewPosterX3`، `CineView*3`، `CineViewControl3` — **لا ملف مشترك** |
| الإعدادات | `config.plugins.cineview.*` | `config.plugins.cineview3.*` حتى الإصدار النهائي (ثم ترحيل) |
| الكاش والبوسترات (محدَّث 1.1) | `/media/hdd/poster` (سلوك المستقر الحالي — لا يُمس) | **لا مشاركة.** مجلد التطوير على وحدة USB الاختبارية فقط: `<usb-test-mount>/cineview-mla-dev/{poster,backdrop,meta,logs}`، والاحتياط `/tmp/cineview-mla-dev/`. |

**قواعد العزل الإلزامية (1.1):**
1. **قائمة منع صريحة للـ HDD في كود التطوير:** محلّل التخزين في PosterX3 يرفض أي مسار يقع على نفس جهاز الكتلة (`st_dev`) لنقطة تركيب HDD المحددة في P0b بمعرّفها (UUID)، **مهما كان اسم المسار** (`/media/hdd`، `/hdd`، رابط رمزي…). المسار يُحدَّد صراحة بالإعداد، لا بالاكتشاف التلقائي.
2. **لا كتابة من أي سكربت تثبيت/اختبار على HDD:** كل سكربتات P1+ تمر عبر دالة `safe_write()` واحدة تفرض قائمة المنع وتفشل فورًا عند المخالفة.
3. **مراقبة إثباتية:** قبل/بعد كل جولة اختبار تُؤخذ بصمة "metadata فقط" للـ HDD (قائمة الملفات وأحجامها وأوقات تعديلها، **دون فتح أو تعديل أي ملف**)، والفرق يجب أن يكون صفرًا من مصدر CineView MLA. (يُنفَّذ فقط بموافقتك، لأنه قراءة لبيانات HDD.)
4. **(خيار يحتاج موافقتك)** تعطيل التركيب التلقائي للـ HDD داخل slot الاختبار فقط، لمنع أي برنامج آخر في ذلك الـ slot من الكتابة عليه. هذا تعديل إعدادات داخل slot الاختبار، لا على HDD نفسه.
5. **المستقر:** لا ملفات مشتركة، لا مسارات مشتركة، أسماء Python ومجلدات وإعدادات مختلفة (الجدول أعلاه)؛ وslot الاختبار منفصل كليًا عن slot الإنتاج.

---

## 8. خطة الاختبار على الجهاز (OpenATV فعلي)
**أدوات:** SSH + OpenWebif (`/api/remotecontrol` للتنقل الآلي، `/grab` للقطات) — **وجودهما ودقة أوامرهما يُتحقق منهما في P0**.
| المستوى | ما يُختبر | الدليل المطلوب |
|---|---|---|
| T1 تحميل | الإقلاع بكل تركيبة؛ `grep "[Skin] Error"` في السجل | سجل نظيف أو أخطاء موثقة ومقبولة |
| T2 بصري | لكل حزمة × كل شاشة في قسمها: فتح الشاشة الحقيقية ولقطة | لقطات PNG مؤرشفة + مراجعة قص/تداخل/z-order |
| T3 تبديل | كل تصميم ⇄ كل تصميم في كل قسم؛ تجربة+تراجع؛ تراجع عند فشل مصطنع (ملف تالف) | سلوك مطابق للمعاملة الذرية |
| T4 ثيمات | 6 ثيمات × شاشات العيّنة | لا صفحة بلون ثيم سابق |
| T5 بوسترات | تشغيل/إيقاف لكل قسم؛ HDD موجود/مفصول؛ تنقل سريع 20 قناة؛ قناة بلا EPG؛ ChannelSelection يعرض بوستر العنصر المؤشَّر | لا بوستر خاطئ، لا كتابة على rootfs (`df`)، لا تجمد |
| T6 بيانات حيّة | bitrate/تردد/إشارة/CAM تتغير بتغيير القناة | قيم متغيرة فعليًا (قاعدة Dynamic-data) |
| T7 إعدادات | إعادة تشغيل كاملة؛ الإعدادات محفوظة؛ `show_second_infobar` لا يتغير | قيم `settings` قبل/بعد |
| T8 الترقية والإزالة | تثبيت فوق تثبيت؛ الإزالة تعيد السكين الافتراضي ولا تحذف الكاش | نظام نظيف |
| T9 انحدار | الشاشات العامة (Setup، PluginBrowser، Hotkey، Language، MultiBoot) والأزرار الملونة | لقطات مطابقة لـ M7 |
| T10 أداء | CPU/الذاكرة أثناء التنقل مع البوسترات | قياسات موثقة |
| T11 حارس الإقلاع (1.1) | جيل يسبب انهيارًا متعمّدًا ⇒ عودة تلقائية إلى lkg بعد إقلاعين، ثم g000000، ثم السكين الافتراضي | `history.log` + لقطات + سجلات enigma2 |
| T12 انقطاع الكهرباء (1.1) | قطع التيار في كل مرحلة من مراحل المعاملة (§2.9) | الإقلاع التالي دائمًا على جيل سليم مختوم |
| T13 العزل (1.1) | بصمة metadata للـ HDD قبل/بعد = لا فرق من MLA؛ لا مسار تطوير على HDD (`lsof`/مراجعة) | تقرير مقارنة |
| T14 مشكلة SecondInfoBar (ISS-01) | إثبات السبب على الجهاز **قبل** أي إصلاح: (أ) قراءة `show_second_infobar` المحفوظ في settings؛ (ب) قيمته الحية بعد الإقلاع عبر OpenWebif `/api/settings`؛ (ج) سلوك زر INFO فعليًا؛ (د) تكرار مع `secondtimeout=0` | إثبات/نفي السبب، ثم إصلاح في فرع dev واختبار انحدار |
| T15 مسار الحفظ (ISS-02) | على **slot الاختبار فقط** مع نسخة من الملفات الحية المستقرة: لقطات قبل ⇒ ضغط Save في CineView Control (الحالي) ⇒ لقطات بعد + مقارنة الملفات | إثبات/نفي فقدان الشاشات المعتمدة |

---

## 9. بوابات الترخيص (إلزامية قبل أي دمج)
| العنصر | الحالة | القرار |
|---|---|---|
| LiiS8 XML/التصاميم | لا ترخيص صريح | أفكار وظيفية فقط؛ أو إذن مكتوب من المؤلف إن أردت نقل تصميم بعينه |
| LiiS8 `LiiS8EventList.py` / `LiiS8VolumeText.py` | Dream-only / CC-NC | ممنوع |
| أيقونات VClouds (LiiS8) | غير تجارية | ممنوعة |
| خطوط Neo Sans / Verdana | تجارية | ممنوعة؛ نبقى على Liberation Sans أو خط حر آخر |
| `LukaPosterXEMC` (CineView الحالي) | إشعار digiteng يسمح بالاستخدام مع حفظ الحقوق | يُحتفظ بالإشعار؛ يُراجع الملف المفقود `LukaPosterXDownloadThread` |
| `OAWeather` | بلجن OpenATV | يُستخدم كاعتماد اختياري، لا يُعاد توزيعه |

---

## 10. المراحل والتسليمات وبوابات الخروج
| المرحلة | العمل | التسليم | بوابة الخروج | يتطلب الجهاز |
|---|---|---|---|---|
| **P0a** فحص بلا جهاز (منجز) | المستودع، اللقطات المخزنة، الاعتماديات، العقود من مصدر 45414bc، إثبات السبب ثابتًا للمشكلتين | تقرير P0 | — | لا |
| **P0b** فحص الجهاز للقراءة فقط | الإصدار/البناء/Python؛ الملفات الحية + بصماتها؛ لقطات مرجعية؛ تقسيمات USB والنسخ الاحتياطية؛ نقاط التركيب وهوية HDD؛ `enigma2_pre_start.sh`؛ نظام ملفات rootfs؛ T14 (أ–د) | تقرير P0b + أرشيف | موافقتك على خطة بيئة الاختبار | نعم (قراءة فقط) |
| **P0c** إنشاء بيئة الاختبار | slot الاختبار (بعد موافقة منفصلة) | slot جاهز + نسخ احتياطية مُتحقَّقة | موافقتك | نعم |
| **P1** العقود | أداة استخراج عقود OpenATV بـ AST من **commit إصدار الجهاز**؛ مصفوفة شاشات/عناصر للأقسام الستة؛ مقارنة بـ CineView الذهبي وLiiS8 | `contracts/openatv-<build>.json` + تقرير | المصفوفة مكتملة | قراءة فقط |
| **P2** الهيكل | فرع dev، بنية المجلدات، Registry، Composer، Validator، OpenATVAdapter، CI | كود + اختبارات وحدة | المدقق يعمل على الذهبية | لا |
| **P3** ترحيل Classic | M1–M6 | حزم classic + ثيمات | **0 فروق دلالية** | لا |
| **P4** تكافؤ على الجهاز | M7 + T1/T2/T9 | لقطات قبل/بعد | تطابق مع مراجعتك | نعم |
| **P5** المكونات الحيّة | CineViewRuntime، PosterX3، Converters3، فتحة الطقس، إصلاح SecondInfoBar | كود | T5/T6/T7 | نعم |
| **P6** واجهة التحكم | CineViewControl3، معاينة، تجربة+تراجع، ملفات التعريف | بلجن | T3/T4 + قياس استقرار reload | نعم |
| **P7** تصاميم جديدة | مواصفة لكل تصميم ⇒ موافقتك ⇒ تنفيذ ⇒ لقطة معاينة | حزم جديدة | T2/T3 لكل حزمة | نعم |
| **P8** التغليف والانحدار | IPK أساسي + IPK لكل حزمة تصميم اختيارية؛ postinst/prerm نظيفان؛ T8/T10 | حزم + تقرير QA | كل الاختبارات موثقة | نعم |
| **P9** مرشح الإصدار | مراجعة نهائية | RELEASE CANDIDATE | موافقتك | — |

---

## 11. المخاطر
| الخطر | الاحتمال | المعالجة |
|---|---|---|
| إصدار OpenATV على الجهاز يختلف عن `master` المدروس | مرتفع | P1 يستخرج العقود من commit الإصدار المثبّت |
| `reloadSkins()` غير مستقر مع التبديل المتكرر | متوسط | إعادة تشغيل واجهة كمسار افتراضي إن لم يثبت الاستقرار |
| ChannelSelection الأصلي (`base=`) يتطلب `widgetStyle` من `skinTemplates.xml` وإلا يعمل بوضع Legacy | متوسط | دعم الوضعين؛ اختبار T3 |
| تكلفة تصميم 6 أقسام × عدة تصاميم | مرتفع | Classic أولًا ثم تصميم واحد جديد لكل قسم، ثم التوسع |
| EMC يقرأ ملفات من مجلده لا من السكين | غير معروف | تحقق في P1 قبل نقل شاشته |
| مشاركة كاش البوستر بين المستقر والتطوير | منخفض | مجلد فرعي منفصل إن اختلفت التسمية |

---

## 12. حالة البنود الآن
| البند | الحالة |
|---|---|
| دراسة عقود OpenATV من المصدر (master 13e055d) | مكتملة برمجيًا — تحتاج مطابقة مع إصدار الجهاز |
| جرد CineView الذهبي على OpenATV ومقارنته | مكتمل برمجيًا (snapshot 2026-09-26) |
| اكتشاف عيب `apply_timeout` ومسار الحفظ | ROOT CAUSE IDENTIFIED (ثابتًا) — يحتاج تأكيدًا على الجهاز |
| المعمارية وخطة الترحيل وخطة الاختبار | مكتملة كمخطط — **لم يبدأ التنفيذ** |
| أي تعديل على المستودع أو الجهاز | لم يحدث |

## 13. (أُرشف — حلّت محله قرارات 1.1 وتقرير P0) ما كان مطلوبًا لبدء P0
1. **الموافقة على هذا المخطط** (أو التعديلات).
2. **الجهاز:** هل هو Vu+ Duo 4K SE نفسه؟ ما إصدار وبناء OpenATV المثبّت الآن (8.0.0-beta 20260922 أم أحدث)؟
3. **الوصول:** وسيلة SSH/OpenWebif المتاحة الآن (IP، أو عبر حاسوبك المتصل بهذه الجلسة).
4. **الموافقة على إنشاء slot اختبار** على وحدة USB ext4 المخصصة للـ multiboot (دون لمس HDD).
5. **المستودع:** هل أربط المستودع بصلاحية دفع لإنشاء فرع `dev/mla-openatv`، أم تفضّل أن أسلّمك الحزم والتغييرات وتدفعها بنفسك؟
