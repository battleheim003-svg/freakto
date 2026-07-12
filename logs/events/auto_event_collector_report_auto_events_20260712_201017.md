==============================================================================================================
🗞️ Freakto Automatic Event Collector v7.0.0
==============================================================================================================
Status                 : AUTO_EVENTS_COLLECTED_HIGH_IMPACT
Run ID                 : auto_events_20260712_201017
Fetch Live / Apply     : True / True
Lookback Hours         : 168
Sources OK/Failed      : 6 / 1
Fetched Items          : 135
Significant Events     : 12
New Events Written     : 1
Total Auto Events      : 13
High Impact Events     : 12
Official Tier Events   : 12

Top Events:
- HIGH | BULLISH | regulatory | sec_press_releases | q=SIGNIFICANT_EVENT | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- HIGH | BEARISH | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Forms New Retail Fraud Working Group
- HIGH | BEARISH | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- HIGH | BEARISH | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- HIGH | BEARISH | macro | federal_reserve_speeches | q=SIGNIFICANT_EVENT | Waller, Two Thoughts on the Transmission of Monetary Policy
- HIGH | NEUTRAL | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Office of Municipal Securities Updates FAQs for Registration of Municipal Advisors
- HIGH | NEUTRAL | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Small Business Advisory Committee to Explore Modernizing Market Access
- HIGH | NEUTRAL | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Names Paul Knight as Chief Operating Officer

Source Health:
- sec_press_releases: OK | items=25 | events=5 | TIER_1_OFFICIAL_REGULATOR
- sec_litigation_releases: OK | items=25 | events=0 | TIER_1_OFFICIAL_REGULATOR
- federal_reserve_press: OK | items=20 | events=4 | TIER_1_OFFICIAL_MACRO
- federal_reserve_speeches: OK | items=15 | events=2 | TIER_1_OFFICIAL_MACRO
- ethereum_foundation_blog: OK | items=25 | events=1 | TIER_1_OFFICIAL_PROTOCOL
- coinbase_blog: OK | items=25 | events=0 | TIER_2_OFFICIAL_COMPANY_BLOG
- binance_announcements: FAILED | items=0 | events=0 | TIER_1_OFFICIAL_EXCHANGE_NEWS | err=https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48&pageNo=1&pageSize=30 -> HTTPError: HTTP Error 400: Bad Request | https://www.binance.com/en/support/announcement/list/48 -> XMLParseError: no element found: line 1, column 0 | https://www.binance.com/en/support/announcement -> XMLParseError: no element found: line 1, column 0

Recommendations:
→ رویدادهای high-impact جمع شد؛ causal_intelligence_dashboard.py را اجرا کن تا روی تصمیم‌ها اثر context بررسی شود.
→ manual_events.csv را فقط برای رویدادهای بسیار مهمی استفاده کن که collector از دست داده یا نیاز به curated override دارند.

Warnings:
⚠️ Automatic Event Collector فقط داده و tag تحقیقاتی تولید می‌کند؛ Paper/Live فعال نمی‌کند.
⚠️ Event direction با keyword/rule ساده ساخته می‌شود و باید به عنوان catalyst context دیده شود، نه سیگنال مستقل.
⚠️ 1 منبع رسمی fail شد؛ v7.0.0 چند fallback را امتحان می‌کند اما شکست source چرخه Forward را متوقف نمی‌کند.
==============================================================================================================