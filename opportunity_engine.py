"""
opportunity_engine.py

این فایل فقط برای سازگاری با monitor.py نگه داشته شده است.

از این مرحله به بعد منطق اصلی تصمیم‌گیری داخل این کلاس است:

    engine/decision.py -> DecisionEngine
"""

from engine import DecisionEngine, OpportunityV2, format_opportunity_v2_message


def analyze_opportunity(df, symbol: str, timeframe: str) -> OpportunityV2:
    engine = DecisionEngine(min_side_score=50)
    return engine.analyze(df, symbol=symbol, timeframe=timeframe)


def format_opportunity_message(opportunity: OpportunityV2) -> str:
    return format_opportunity_v2_message(opportunity)