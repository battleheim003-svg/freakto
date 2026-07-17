# اجرای ابری

در GitHub به Actions → `Freakto Paper Cloud Cycle` → `Run workflow` بروید. Workflow canonical دارای schedule، concurrency، تست هدفمند، restore از `paper-state`، چرخه، dashboard، artifact و push retry-safe است. State در main ذخیره نمی‌شود. زمان‌بندی `9 0,4,8,12,16,20 * * *` است.

