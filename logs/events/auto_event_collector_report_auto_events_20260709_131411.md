==============================================================================================================
🗞️ Freakto Automatic Event Collector v6.5.0
==============================================================================================================
Status                 : AUTO_EVENTS_COLLECTED_HIGH_IMPACT
Run ID                 : auto_events_20260709_131411
Fetch Live / Apply     : True / True
Lookback Hours         : 168
Sources OK/Failed      : 4 / 3
Fetched Items          : 85
Significant Events     : 9
New Events Written     : 9
Total Auto Events      : 9
High Impact Events     : 9
Official Tier Events   : 9

Top Events:
- HIGH | BULLISH | regulatory | sec_press_releases | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- HIGH | BEARISH | regulatory | sec_press_releases | SEC Forms New Retail Fraud Working Group
- HIGH | BEARISH | macro | federal_reserve_press | Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- HIGH | BEARISH | macro | federal_reserve_press | Federal Reserve Board issues enforcement action with Small Business Bank and announces termination enforcement actions with BNP Paribas S.A., BNP Paribas USA, Inc., BNP Paribas Securities Corp., and Community Bankshares, Inc.
- HIGH | BEARISH | macro | federal_reserve_speeches | Waller, Two Thoughts on the Transmission of Monetary Policy
- HIGH | NEUTRAL | regulatory | sec_press_releases | SEC Small Business Advisory Committee to Explore Modernizing Market Access
- HIGH | NEUTRAL | regulatory | sec_press_releases | SEC Names Paul Knight as Chief Operating Officer
- HIGH | NEUTRAL | macro | federal_reserve_press | Minutes of the Federal Open Market Committee, June 16-17, 2026

Source Health:
- sec_press_releases: OK | items=25 | events=4 | TIER_1_OFFICIAL_REGULATOR
- sec_litigation_releases: FAILED | items=0 | events=0 | TIER_1_OFFICIAL_REGULATOR | err=HTTPError: HTTP Error 404: Not Found
- federal_reserve_press: OK | items=20 | events=3 | TIER_1_OFFICIAL_MACRO
- federal_reserve_speeches: OK | items=15 | events=2 | TIER_1_OFFICIAL_MACRO
- ethereum_foundation_blog: OK | items=25 | events=0 | TIER_1_OFFICIAL_PROTOCOL
- coinbase_blog: FAILED | items=0 | events=0 | TIER_2_OFFICIAL_COMPANY_BLOG | err=XMLParseError: syntax error: line 1, column 0
- binance_announcements: FAILED | items=0 | events=0 | TIER_1_OFFICIAL_EXCHANGE_NEWS | err=HTTPError: HTTP Error 400: Bad Request

Recommendations:
→ رویدادهای high-impact جمع شد؛ causal_intelligence_dashboard.py را اجرا کن تا روی تصمیم‌ها اثر context بررسی شود.
→ manual_events.csv را فقط برای رویدادهای بسیار مهمی استفاده کن که collector از دست داده یا نیاز به curated override دارند.

Warnings:
⚠️ Automatic Event Collector فقط داده و tag تحقیقاتی تولید می‌کند؛ Paper/Live فعال نمی‌کند.
⚠️ Event direction با keyword/rule ساده ساخته می‌شود و باید به عنوان catalyst context دیده شود، نه سیگنال مستقل.
⚠️ 2 منبع رسمی fail شد؛ این شکست چرخه Forward را متوقف نمی‌کند.
==============================================================================================================