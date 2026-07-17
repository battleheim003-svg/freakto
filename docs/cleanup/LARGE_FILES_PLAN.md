# برنامه فایل‌های بزرگ

ZIP کپی پروژه از source tree حذف شد. خروجی چرخه و dashboard باید GitHub Artifact باشد؛ State کوچک در `paper-state`، replay بزرگ در object storage و Git LFS فقط برای asset ضروری و نسخه‌پذیر استفاده شود.

برای پاک‌سازی تاریخی ZIP می‌توان پس از backup و هماهنگی تیم از `git filter-repo --path freakto_source.zip --invert-paths` و force-push کنترل‌شده استفاده کرد. این دستور در این مأموریت اجرا نشده و اجرای آن نیازمند درخواست صریح است.

