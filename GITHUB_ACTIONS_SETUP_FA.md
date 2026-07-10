# راهنمای فارسی GitHub Actions برای Freakto v5.2

این راهنما برای حالتی است که هنوز VPS نمی‌خواهی و فقط می‌خواهی Freakto روی GitHub هر چند ساعت یک‌بار اجرا شود، داده جمع کند، گزارش تلگرام بفرستد، و لاگ‌ها را ذخیره کند.

## ایده کلی

GitHub Actions مثل یک کامپیوتر موقت رایگان/ابری است که GitHub برای چند دقیقه روشن می‌کند، پروژه را اجرا می‌کند، بعد خاموش می‌شود.

مشکل مهم این است که این کامپیوتر موقت حافظه دائمی ندارد. برای همین در v5.2 این سیستم اضافه شده:

```text
main branch      = کد پروژه

data-logs branch = فقط لاگ‌ها و خروجی‌های runtime
```

هر بار workflow اجرا می‌شود:

```text
1. کد پروژه را از main می‌گیرد
2. لاگ‌های قبلی را از branch data-logs برمی‌گرداند
3. Forward Test Cycle را اجرا می‌کند
4. گزارش تلگرام می‌فرستد
5. لاگ‌های جدید را دوباره در branch data-logs ذخیره می‌کند
6. یک artifact هم از لاگ‌ها نگه می‌دارد
```

هیچ سفارش واقعی ارسال نمی‌شود. این فقط برای جمع‌آوری دیتا، Paper Gate و Validation است.

---

## مرحله 1: ساخت repository در GitHub

1. وارد github.com شو.
2. بالا سمت راست روی `+` بزن.
3. گزینه `New repository` را انتخاب کن.
4. یک نام بده، مثلاً:

```text
freakto
```

5. برای شروع می‌توانی repository را `Private` بگذاری.
6. روی `Create repository` بزن.

نکته: اگر repository خصوصی باشد، GitHub Actions سهمیه رایگان محدودتری دارد. برای شروع تست معمولاً کافی است، ولی اگر دیدی زیاد مصرف می‌شود، یا باید public کنی یا VPS بگیری.

---

## مرحله 2: آپلود پروژه روی GitHub

### راه ساده با GitHub Desktop

اگر GitHub را زیاد بلد نیستی، این راحت‌ترین راه است:

1. برنامه GitHub Desktop را نصب کن.
2. وارد اکانت GitHub شو.
3. از منو بزن:

```text
File → Add local repository
```

4. فولدر پروژه Freakto را انتخاب کن.
5. اگر گفت repository نیست، گزینه create repository را انتخاب کن.
6. فایل‌ها را commit کن.
7. روی `Publish repository` یا `Push origin` بزن.

### راه با command line

داخل فولدر پروژه:

```bash
git init
git add .
git commit -m "Initial Freakto project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/freakto.git
git push -u origin main
```

---

## مرحله 3: مطمئن شو فایل workflow وجود دارد

این نسخه این فایل را اضافه کرده:

```text
.github/workflows/freakto-forward-test.yml
```

اگر این فایل در GitHub دیده شود، از تب `Actions` قابل اجراست.

---

## مرحله 4: فعال کردن Actions

1. وارد صفحه repository شو.
2. برو به تب `Actions`.
3. اگر GitHub پرسید workflows را فعال کنم یا نه، روی Enable بزن.
4. workflow با نام زیر را پیدا کن:

```text
Freakto Forward Test Collector
```

---

## مرحله 5: اضافه کردن Secrets

Secrets یعنی مقادیر محرمانه‌ای مثل Telegram token که نباید داخل کد پروژه ذخیره شوند.

مسیر:

```text
Repository → Settings → Secrets and variables → Actions → New repository secret
```

حداقل این دو Secret را بساز:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

اگر Coinalyze یا OpenAI یا Anthropic استفاده می‌کنی، این‌ها هم اختیاری‌اند:

```text
COINALYZE_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
```

نام Secret باید دقیقاً همین باشد.

---

## مرحله 6: اجازه نوشتن به GitHub Actions

چون workflow باید لاگ‌ها را در branch `data-logs` ذخیره کند، باید اجازه write داشته باشد.

مسیر:

```text
Repository → Settings → Actions → General → Workflow permissions
```

گزینه را روی این بگذار:

```text
Read and write permissions
```

بعد Save کن.

---

## مرحله 7: اجرای دستی برای تست

1. برو به تب `Actions`.
2. workflow زیر را باز کن:

```text
Freakto Forward Test Collector
```

3. روی `Run workflow` بزن.
4. گزینه‌ها را همین‌طور بگذار:

```text
send_telegram = true
commit_logs = true
run_validation = true
```

5. Run را بزن.

اگر موفق باشد، باید در Telegram پیام بگیری و در GitHub یک اجرای سبز ببینی.

---

## مرحله 8: اجرای خودکار

Workflow هر 4 ساعت یک‌بار اجرا می‌شود:

```yaml
cron: "17 */4 * * *"
```

یعنی حدود دقیقه 17 هر 4 ساعت. GitHub ممکن است دقیقاً رأس همان ثانیه اجرا نکند، ولی برای تایم‌فریم 4h کافی است.

---

## مرحله 9: لاگ‌ها کجا ذخیره می‌شوند؟

دو جا:

### 1. Artifacts

در صفحه هر workflow run، پایین صفحه بخشی به نام Artifacts می‌بینی. آنجا فایل‌های خروجی همان اجرا قابل دانلود هستند.

### 2. Branch جدا به نام data-logs

بعد از اجرای موفق، یک branch ساخته می‌شود:

```text
data-logs
```

داخل آن branch، فقط لاگ‌ها و فایل‌های runtime ذخیره می‌شوند.

برای دیدن آن:

1. در صفحه repo، روی branch dropdown بزن.
2. به جای `main`، branch `data-logs` را انتخاب کن.
3. فولدر `logs/` را ببین.

---

## مرحله 10: چیزهایی که نباید در GitHub بگذاری

این‌ها را هرگز commit نکن:

```text
.env
API keys
Telegram token
Private keys
Exchange API secret
فایل‌های شامل پسورد
```

در v5.2 اسکریپت push logs فقط مسیرهای whitelist شده را ذخیره می‌کند، ولی باز هم خودت مراقب باش.

---

## دستور اصلی که GitHub اجرا می‌کند

درون workflow، این چرخه اجرا می‌شود:

```bash
python -X utf8 scripts/github_actions_restore_logs.py
python -X utf8 forward_test_dashboard.py --cycle --validate --continue-on-error --send
python -X utf8 validation_suite_dashboard.py
python -X utf8 scripts/github_actions_push_logs.py
```

---

## اگر workflow قرمز شد چه کنم؟

1. روی اجرای قرمز در تب Actions کلیک کن.
2. وارد job شو.
3. مرحله‌ای که fail شده را باز کن.
4. متن خطا را کپی کن و برای بررسی بده.

خطاهای رایج:

```text
Secret تنظیم نشده
requirements نصب نشده
API صرافی موقتاً جواب نداده
GitHub permission روی read-only مانده
data-logs branch conflict دارد
```

---

## وضعیت مناسب فعلی پروژه

GitHub Actions جایگزین دائمی VPS نیست، ولی برای مرحله فعلی عالی است:

```text
Forward Test Collection
Data gathering
Paper Gate
Validation Suite
Telegram report
```

وقتی پروژه به Micro Live یا اجرای واقعی نزدیک شد، VPS بهتر و امن‌تر است.

---

# بعد از اولین اجرای موفق چه کار کنم؟ — v5.2.1

اگر workflow اصلی سبز شد، یعنی GitHub Actions Collector فعال است. از اینجا به بعد این چک‌ها را انجام بده:

## 1. چک کن branch دیتای لاگ ساخته شده باشد

در صفحه GitHub repo، بالای لیست فایل‌ها روی منوی branch بزن. باید branch زیر را ببینی:

```text
data-logs
```

این branch برای کد نیست؛ فقط برای خروجی‌های runtime مثل `logs/` و `history/` است.

## 2. چک کن Artifact ساخته شده باشد

در همان run موفق، پایین صفحه Summary باید بخشی به اسم Artifacts ببینی. فایل artifact معمولاً با این اسم ساخته می‌شود:

```text
freakto-logs-<run_id>
```

این artifact بکاپ ۳۰ روزه خروجی‌های همان اجرای GitHub Actions است.

## 3. Health Check را تست کن

بعد از نصب v5.2.1 در GitHub، در تب Actions باید workflow جدید زیر را ببینی:

```text
Freakto Health Check
```

این workflow سبک است و فقط status را از لاگ‌های ذخیره‌شده می‌خواند. برای اجرای دستی:

```text
Actions → Freakto Health Check → Run workflow
```

برای بار اول `send_telegram` را می‌توانی `false` بگذاری. اگر خواستی status به تلگرام هم بیاید، آن را `true` کن.

## 4. Summary هر run را بخوان

در v5.2.1، workflow اصلی و Health Check یک خلاصه Markdown می‌سازند. در صفحه run، بخش Summary باید شامل این عنوان باشد:

```text
Freakto GitHub Actions Health Summary
```

در آنجا این‌ها را می‌بینی:

```text
Progress Score
Readiness Level
Complete Evaluations
Closed Paper Trades
Regime-labeled Samples
Forward Runs
Forward Days
Recent Runs
```

## 5. وضعیت طبیعی فعلی چیست؟

تا وقتی پروژه هنوز در فاز جمع‌آوری داده است، دیدن این وضعیت طبیعی است:

```text
Readiness Level: RESEARCH_ONLY
Live Ready: False
Paper Ready: False
```

هدف فعلی این است:

```text
Complete Evaluations >= 100
Closed Paper Trades >= 30
Regime-labeled Samples >= 30
Forward Days >= 30
```

## 6. روزانه چه چیزهایی را چک کنم؟

روزانه فقط این چهار چیز را نگاه کن:

```text
1. آخرین workflow سبز باشد
2. Telegram report آمده باشد
3. data-logs branch آپدیت شده باشد
4. Forward Runs و Forward Days کم‌کم زیاد شوند
```

## 7. اگر workflow قرمز شد چه کار کنم؟

روی workflow قرمز کلیک کن و step قرمز را باز کن. مهم‌ترین stepها:

```text
Install dependencies
Restore previous Freakto logs
Run Freakto forward cycle with Telegram
Push logs to data-logs branch
```

متن خطا را کامل کپی کن و برای بررسی بفرست.

## 8. چه چیزی را تغییر ندهم؟

این‌ها را در GitHub تغییر نده مگر دقیقاً بدانی چه می‌کنی:

```text
.github/workflows/freakto-forward-test.yml
scripts/github_actions_push_logs.py
scripts/github_actions_restore_logs.py
```

و هیچ‌وقت این فایل‌ها را به repo اضافه نکن:

```text
.env
API keys
Telegram tokens
Exchange keys
.venv
```

## خطای UnicodeDecodeError در Restore logs
اگر در workflow `Freakto Health Check` مرحله زیر قرمز شد:

```text
Restore previous Freakto logs
```

و خطا شبیه این بود:

```text
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xb6
```

یعنی نسخه قدیمی `scripts/github_actions_restore_logs.py` هنوز روی GitHub است یا patch درست push نشده. نسخه v5.2.3 را نصب کن، commit بزن، push کن و دوباره Health Check را اجرا کن.

---

## v10 — اجرای دستی Market Replay در GitHub Actions

Workflow زیر فقط با `workflow_dispatch` اجرا می‌شود و به‌صورت زمان‌بندی‌شده فعال نیست:

```text
.github/workflows/freakto-market-replay.yml
```

در تب Actions، `Freakto Market Replay v10` را انتخاب کن و Symbols، Timeframe، Years و Step را وارد کن. Dataset و گزارش‌ها به‌صورت Artifact ذخیره می‌شوند.

برای Replay سه‌ساله‌ی کامل، اجرای لوکال معمولاً پایدارتر است؛ بعضی صرافی‌ها ممکن است IP دیتاسنتر GitHub را محدود کنند. شکست یک Provider به معنی خرابی موتور نیست و باید Source attempts و data-quality report بررسی شود.
