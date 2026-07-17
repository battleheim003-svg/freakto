# گزارش ممیزی مخزن Freakto

تاریخ ممیزی: ۱۴۰۵/۰۴/۲۶ — Branch: `refactor/paper-trading-consolidation`

## نتیجه baseline

- مجموعه کامل تست پیش از تغییر: **۲۵۱ تست پاس، صفر شکست، ۱۴ هشدار کتابخانه‌ای**.
- معماری فعلی یک ساختار انتقالی است: منطق فعال در `engine/`، entry pointها در root، داده و state در `logs/` و اجرای ابری در `.github/workflows/` قرار دارند.
- Paper اصلی با `paper_trade_launch_dashboard.py`، `paper_research_orchestrator.py`، `github_cloud_runner.py` و `paper_performance_dashboard.py` اجرا می‌شود.
- State ابری در Branch مستقل `paper-state` بسته‌بندی می‌شود؛ main محل state اجرایی نیست.
- Workflow اصلی Paper فایل `.github/workflows/freakto-paper-cloud.yml` با زمان‌بندی ۹ دقیقه پس از کندل‌های چهارساعته UTC است.
- ارسال تلگرام در `telegram_notifier.py` متمرکز است، اما متن‌های عملیاتی فعلی یک قرارداد کوتاه NORMAL/DEBUG ندارند.
- فایل `freakto_source.zip` یک کپی ۲۹٬۴۹۴٬۲۶۴ بایتی از پروژه است و در کد، تست، workflow، config یا مستندات فعال ارجاع ندارد.
- ۱۲۷ فایل Markdown در root وجود دارد. انتقال انبوه آن‌ها پرریسک است، چون تعدادی از تست‌ها و راهنماها نام مستقیم دارند؛ در این تغییر فقط مستندات جدید در ساختار canonical قرار می‌گیرند.
- صدها فایل زیر `logs/` track شده‌اند. بخشی fixture یا شاهد پژوهشی است؛ بدون ممیزی ردیفی حذف نمی‌شوند و در گروه `UNKNOWN_DO_NOT_DELETE` باقی می‌مانند.

## طبقه‌بندی ساختاری

| گروه | مسیرهای شاخص | تصمیم |
|---|---|---|
| `CORE_ACTIVE` | `engine/decision.py`, `engine/execution_model.py`, `engine/geometry_parser.py` | حفظ |
| `PAPER_ACTIVE` | `engine/paper_observation_v2.py`, `engine/paper_trading.py`, `paper_research_orchestrator.py` | حفظ و تجمیع رابط |
| `RESEARCH_ACTIVE` | replay، Fresh OOS، validation و calibration در `engine/` | حفظ |
| `CLOUD_ACTIVE` | `freakto-paper-cloud.yml`, `github_cloud_runner.py`, `cloud_state_sync.py` | حفظ |
| `TEST_ACTIVE` | `tests/` | حفظ کامل |
| `DOCUMENTATION_ACTIVE` | README و runbookهای ارجاع‌شده | حفظ؛ مستندات عملیاتی جدید در `docs/paper/` |
| `GENERATED_OUTPUT` | cacheها و خروجی‌های runtime | از Git ignore؛ خروجی track‌شده فقط پس از اثبات حذف |
| `LEGACY` | release noteها و wrapperهای قدیمی | فعلاً حفظ برای تاریخچه و سازگاری |
| `DUPLICATE` | آرشیو کامل `freakto_source.zip` و فهرست‌های موقت `CHANGED_FILES*.txt` | حذف کم‌ریسک |
| `UNUSED_CANDIDATE` | patch note موقت `engine/confidence_calibration.py.patch_note.txt` | حذف پس از ثبت manifest |
| `UNKNOWN_DO_NOT_DELETE` | داده‌های تاریخی `logs/`, `data/`, `archive/` | حذف ممنوع در این تغییر |

## entry pointها و قراردادهای موجود

- Preflight/arm/status/disarm: `paper_trade_launch_dashboard.py`
- اجرای چرخه: `paper_research_orchestrator.py`
- اجرای Cloud: `github_cloud_runner.py`
- ساخت dashboard: `paper_performance_dashboard.py`
- launcherهای قدیمی Windows: `run_research_paper_cycle.bat`, `run_paper_research_auto.bat`
- Telegram: `telegram_notifier.py`

## نامزدهای حذف اثبات‌شده

برای همه موارد زیر جست‌وجوی import، subprocess، workflow، test، docs و config انجام شد. هیچ موردی executable/importable نیست و workflow یا تست به آن وابسته نیست.

| مسیر | علت | import | تست | workflow | docs | جایگزین | ریسک |
|---|---|---:|---:|---:|---:|---|---|
| `freakto_source.zip` | کپی کامل و بزرگ پروژه | خیر | خیر | خیر | خیر | Git و GitHub Artifacts | کم |
| `CHANGED_FILES*.txt` | فهرست موقت تحویل‌های قبلی | خیر | خیر | خیر | فقط خودارجاع/دو اشاره تاریخی | Git history | کم |
| `engine/confidence_calibration.py.patch_note.txt` | یادداشت patch کنار فایل canonical | خیر | خیر | خیر | خیر | `engine/confidence_calibration.py` | کم |

فایل‌های با ریسک متوسط یا بالا در این مرحله حذف نمی‌شوند.

