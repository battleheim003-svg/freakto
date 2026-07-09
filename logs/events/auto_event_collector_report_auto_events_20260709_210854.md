==============================================================================================================
🗞️ Freakto Automatic Event Collector v7.0.0
==============================================================================================================
Status                 : AUTO_EVENTS_COLLECTED_HIGH_IMPACT
Run ID                 : auto_events_20260709_210854
Fetch Live / Apply     : True / True
Lookback Hours         : 168
Sources OK/Failed      : 5 / 2
Fetched Items          : 110
Significant Events     : 11
New Events Written     : 1
Total Auto Events      : 12
High Impact Events     : 11
Official Tier Events   : 11

Top Events:
- HIGH | BULLISH | regulatory | sec_press_releases | q=SIGNIFICANT_EVENT | SEC to Host Virtual Roundtable on Modernizing IPOs and Expanding Access to Public Markets
- HIGH | BEARISH | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Forms New Retail Fraud Working Group
- HIGH | BEARISH | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve Board issues enforcement action with TS Banking Group, Inc. and TS Contrarian Bancshares, Inc.
- HIGH | BEARISH | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve Board requests comment on a proposal to amend its requirements for banks to maintain anti-money laundering programs
- HIGH | BEARISH | macro | federal_reserve_speeches | q=SIGNIFICANT_EVENT | Waller, Two Thoughts on the Transmission of Monetary Policy
- HIGH | NEUTRAL | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Small Business Advisory Committee to Explore Modernizing Market Access
- HIGH | NEUTRAL | regulatory | sec_press_releases | q=ACTIONABLE_EVENT_CONTEXT | SEC Names Paul Knight as Chief Operating Officer
- HIGH | NEUTRAL | macro | federal_reserve_press | q=ACTIONABLE_EVENT_CONTEXT | Federal Reserve announces the leadership and objectives of its task forces to advance the conduct of monetary policy

Source Health:
- sec_press_releases: OK | items=25 | events=4 | TIER_1_OFFICIAL_REGULATOR
- sec_litigation_releases: OK | items=25 | events=0 | TIER_1_OFFICIAL_REGULATOR
- federal_reserve_press: OK | items=20 | events=4 | TIER_1_OFFICIAL_MACRO
- federal_reserve_speeches: OK | items=15 | events=2 | TIER_1_OFFICIAL_MACRO
- ethereum_foundation_blog: OK | items=25 | events=1 | TIER_1_OFFICIAL_PROTOCOL
- coinbase_blog: FAILED | items=0 | events=0 | TIER_2_OFFICIAL_COMPANY_BLOG | err=https://www.coinbase.com/blog/feed.xml -> URLError: <urlopen error timed out> | https://www.coinbase.com/blog/feed -> URLError: <urlopen error timed out> | https://www.coinbase.com/blog -> URLError: <urlopen error timed out>
- binance_announcements: FAILED | items=0 | events=0 | TIER_1_OFFICIAL_EXCHANGE_NEWS | err=https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&catalogId=48&pageNo=1&pageSize=30 -> URLError: <urlopen error [Errno 11001] getaddrinfo failed> | https://www.binance.com/en/support/announcement/list/48 -> URLError: <urlopen error [Errno 11001] getaddrinfo failed> | https://www.binance.com/en/support/announcement -> URLError: <urlopen error [Errno 11001] getaddrinfo failed>

Recommendations:
→ رویدادهای high-impact جمع شد؛ causal_intelligence_dashboard.py را اجرا کن تا روی تصمیم‌ها اثر context بررسی شود.
→ manual_events.csv را فقط برای رویدادهای بسیار مهمی استفاده کن که collector از دست داده یا نیاز به curated override دارند.

Warnings:
⚠️ Automatic Event Collector فقط داده و tag تحقیقاتی تولید می‌کند؛ Paper/Live فعال نمی‌کند.
⚠️ Event direction با keyword/rule ساده ساخته می‌شود و باید به عنوان catalyst context دیده شود، نه سیگنال مستقل.
⚠️ 1 منبع رسمی fail شد؛ v7.0.0 چند fallback را امتحان می‌کند اما شکست source چرخه Forward را متوقف نمی‌کند.
==============================================================================================================