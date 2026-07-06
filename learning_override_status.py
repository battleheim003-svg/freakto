"""
learning_override_status.py

Freakto Learning Override Status - v3.3.0

اجرا:
    python learning_override_status.py

این ابزار نشان می‌دهد config/learning_overrides.json توسط Safe Loader چگونه دیده می‌شود.
در این نسخه هیچ تغییری در فایل config اعمال نمی‌کند.
"""

from engine.learning_overrides import (
    load_learning_override_state,
    format_learning_override_status_console,
)


def main():
    state = load_learning_override_state()
    print(format_learning_override_status_console(state))


if __name__ == "__main__":
    main()
