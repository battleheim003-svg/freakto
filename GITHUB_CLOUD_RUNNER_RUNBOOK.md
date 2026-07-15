# Freakto GitHub Cloud Runner

این بسته چرخه Paper Research را روی GitHub Actions اجرا می‌کند تا برای هر اجرا نیازی به روشن‌بودن کامپیوتر شخصی نباشد.

## رفتار اصلی

Workflow در دقیقه ۷ ساعت‌های `00, 04, 08, 12, 16, 20` به وقت UTC اجرا می‌شود. هر اجرا فقط یک چرخه `paper_research_orchestrator.py --once` را انجام می‌دهد. اجرای هم‌زمان با `concurrency` مسدود است.

این ابزار فقط Paper مجازی است:

- `LIVE_TRADING_ENABLED=false`
- `REAL_CAPITAL_ENABLED=false`
- هیچ Exchange credential برای ارسال سفارش دریافت نمی‌کند.

## فایل‌های State پایدار

Runnerهای GitHub موقت‌اند. در پایان هر اجرا، فقط Stateهای کوچک و لازم داخل `cloud_state.tar.gz` ذخیره و در شاخه `paper-state` Commit می‌شوند:

- `logs/decisions.csv`
- `history/freakto_history.db`
- `logs/paper_trading/`
- `logs/paper_launch_v2/`
- `logs/paper_cycle/`
- `logs/fresh_oos/`
- `logs/forward_test/`

فایل‌های بزرگ‌تر از ۵۰ مگابایت، Lockها، فایل‌های موقت و bytecode ذخیره نمی‌شوند.

## Secrets لازم

در GitHub Repository به مسیر زیر برو:

`Settings → Secrets and variables → Actions → New repository secret`

این دو Secret اجباری‌اند:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

این Secretها اختیاری‌اند:

- `OPENAI_API_KEY`
- `COINALYZE_API_KEY`

فایل `.env` را هرگز Commit نکن.

## فعال‌سازی Workflow

پس از Push کردن فایل‌ها:

1. وارد تب `Actions` شو.
2. Workflow با نام `Freakto Paper Cloud Cycle` را باز کن.
3. `Run workflow` را بزن.
4. نتیجه اولین اجرا را بررسی کن.
5. بعد از اولین اجرا شاخه `paper-state` خودکار ساخته می‌شود.

## اجرای دستی و زمان‌بندی‌شده

اجرای دستی از `workflow_dispatch` ممکن است. اجرای زمان‌بندی‌شده فقط روی Default Branch انجام می‌شود.

## گزارش‌ها

هر Run یک Artifact سی‌روزه شامل گزارش چرخه، وضعیت Paper و Manifest State تولید می‌کند. State اصلی مستقل از Artifact در شاخه `paper-state` نگهداری می‌شود.

## Fail-Closed

Workflow در موارد زیر متوقف می‌شود:

- Secretهای Telegram موجود نباشند.
- `paper_research_orchestrator.py` نصب نشده باشد.
- چرخه Paper خروجی غیرصفر بدهد.

حتی هنگام شکست، State و Artifact تا حد ممکن ذخیره می‌شوند و Telegram failure alert ارسال می‌شود.
