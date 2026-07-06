"""
learning_config_dashboard.py

Freakto Learning Config Advisor - v3.3.0

اجرا:
    python learning_config_dashboard.py
    python learning_config_dashboard.py --refresh
    python learning_config_dashboard.py --stage
    python learning_config_dashboard.py --send

این اسکریپت خروجی Self-Learning را به یک فایل تنظیمات advisory/staging تبدیل می‌کند.
هیچ تغییری را خودکار در Decision Engine اعمال نمی‌کند.
"""

import argparse

from telegram_notifier import send_telegram_message
from engine.learning_config import (
    build_learning_config_plan,
    format_learning_config_console,
    format_learning_config_telegram,
    save_learning_config_plan,
    save_learning_config_report,
    stage_learning_overrides,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Rebuild self-learning recommendations before creating config advisory.",
    )
    parser.add_argument(
        "--stage",
        action="store_true",
        help="Write config/learning_overrides.json as a disabled staging file.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send learning config advisory summary to Telegram.",
    )
    args = parser.parse_args()

    plan = build_learning_config_plan(refresh=args.refresh)
    print(format_learning_config_console(plan))

    config_path = save_learning_config_plan(plan)
    report_path = save_learning_config_report(plan)

    print(f"🧩 Learning config advisory ذخیره شد: {config_path}")
    print(f"📝 Learning config report ذخیره شد: {report_path}")

    if args.stage:
        staged_path = stage_learning_overrides(plan)
        print(f"🧪 Learning overrides staging ذخیره شد: {staged_path}")
        print("⚠️ این فایل disabled است؛ Decision Engine v3.3 فقط در صورت enabled=true، auto_apply=true و داشتن نمونه کافی آن را اعمال می‌کند.")

    if args.send:
        ok = send_telegram_message(format_learning_config_telegram(plan))
        if ok:
            print("✅ گزارش Learning Config به تلگرام ارسال شد")
        else:
            print("⚠️ گزارش Learning Config به تلگرام ارسال نشد")


if __name__ == "__main__":
    main()
