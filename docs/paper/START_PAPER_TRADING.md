# شروع معاملات آزمایشی

۱. Python 3.10 و وابستگی‌ها را نصب کنید: `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
۲. فایل `.env` را محلی نگه دارید. برای Telegram فقط `TELEGRAM_BOT_TOKEN` و `TELEGRAM_CHAT_ID` لازم‌اند؛ هیچ کلید معاملاتی وارد نکنید.
۳. `start_paper_trading.bat` را اجرا کنید. این launcher ابتدا preflight، سپس arm حالت `RESEARCH_PAPER`، یک چرخه فوری و loop زمان‌بندی‌شده را اجرا می‌کند.
۴. اجرای محلی اختیاری است؛ GitHub Actions نیز می‌تواند چرخه را اجرا کند.
۵. فعال بودن را با `show_paper_status.bat`، معاملات باز/بسته را در `logs/paper_trades.csv` و `logs/paper_trade_evaluations.csv` و عملکرد را با `show_paper_dashboard.bat` بررسی کنید.

`STRATEGY_PAPER` تا زمان عبور candidate ثابت از Holdout، walk-forward و Fresh OOS مسدود می‌ماند. `NO_ELIGIBLE_NEW_OBSERVATIONS` یعنی در این چرخه سیگنال تازه‌ای که همه gateها را پاس کند وجود نداشته؛ خطای Live نیست. چرخه Cloud شش بار در روز، ۹ دقیقه پس از مرز کندل چهارساعته UTC اجرا می‌شود و ممکن است به‌دلیل صف GitHub کمی تأخیر داشته باشد.
