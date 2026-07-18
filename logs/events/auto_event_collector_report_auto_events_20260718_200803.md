==============================================================================================================
🗞️ Freakto Automatic Event Collector v7.0.0
==============================================================================================================
Status                 : AUTO_EVENTS_COLLECTED_HIGH_IMPACT
Run ID                 : auto_events_20260718_200803
Fetch Live / Apply     : True / True
Lookback Hours         : 168
Sources OK/Failed      : 6 / 1
Fetched Items          : 135
Significant Events     : 11
New Events Written     : 11
Total Auto Events      : 23
High Impact Events     : 11
Official Tier Events   : 11

Top Events:
- HIGH | BULLISH | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Proposes New E-Delivery Approach to Make Information More Readily Accessible and Useful for Investors
- HIGH | BEARISH | macro | federal_reserve_press | q=SIGNIFICANT_EVENT | Agencies issue joint statement on handling of highly sensitive information during bank examinations
- HIGH | BEARISH | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve Board issues enforcement action with former chief lending officer of Heritage State Bank
- HIGH | BEARISH | macro | federal_reserve_speeches | q=SIGNIFICANT_EVENT | Bowman, Modernizing Financial Regulation
- HIGH | NEUTRAL | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Minutes of the Board's discount rate meetings on June 8 and June 17, 2026
- HIGH | NEUTRAL | macro | federal_reserve_speeches | q=SIGNIFICANT_EVENT | Jefferson, Navigating Economic Shocks: A Monetary Policymaker’s Perspective
- HIGH | NEUTRAL | macro | federal_reserve_speeches | q=SIGNIFICANT_EVENT | Cook, Economic Outlook
- HIGH | NEUTRAL | macro | federal_reserve_speeches | q=SIGNIFICANT_EVENT | Bowman, Responsible Innovation and Financial Inclusion

Source Health:
- sec_press_releases: OK | items=25 | events=1 | TIER_1_OFFICIAL_REGULATOR
- sec_litigation_releases: OK | items=25 | events=0 | TIER_1_OFFICIAL_REGULATOR
- federal_reserve_press: OK | items=20 | events=3 | TIER_1_OFFICIAL_MACRO
- federal_reserve_speeches: OK | items=15 | events=6 | TIER_1_OFFICIAL_MACRO
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