==============================================================================================================
🗞️ Freakto Automatic Event Collector v7.0.0
==============================================================================================================
Status                 : AUTO_EVENTS_COLLECTED_HIGH_IMPACT
Run ID                 : auto_events_20260730_171242
Fetch Live / Apply     : True / True
Lookback Hours         : 168
Sources OK/Failed      : 6 / 1
Fetched Items          : 135
Significant Events     : 6
New Events Written     : 0
Total Auto Events      : 18
High Impact Events     : 6
Official Tier Events   : 6

Top Events:
- HIGH | BEARISH | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve Board issues enforcement actions with former employee of Regions Bank and former employee of First Interstate Bank
- HIGH | BEARISH | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve Board issues enforcement action with Iuka Bancshares, Inc. and The Iuka State Bank
- HIGH | NEUTRAL | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Announces Continuation of Small Business Advisory Committee Meeting
- HIGH | NEUTRAL | regulatory | sec_press_releases | q=SIGNIFICANT_EVENT | Small Business Forum’s Report to Congress Highlights Recommendations to Improve Capital-Raising Policy
- HIGH | NEUTRAL | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve issues FOMC statement
- HIGH | NEUTRAL | protocol | ethereum_foundation_blog | q=SIGNIFICANT_EVENT | Ethereum Foundation Board Update

Source Health:
- sec_press_releases: OK | items=25 | events=2 | TIER_1_OFFICIAL_REGULATOR
- sec_litigation_releases: OK | items=25 | events=0 | TIER_1_OFFICIAL_REGULATOR
- federal_reserve_press: OK | items=20 | events=3 | TIER_1_OFFICIAL_MACRO
- federal_reserve_speeches: OK | items=15 | events=0 | TIER_1_OFFICIAL_MACRO
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