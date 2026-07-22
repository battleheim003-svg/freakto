"""Gate combination research."""
VERSION="v10.1.0"

DEFAULT_GATES=[
    "VOLUME_SCORE_GE_10",
    "STRUCTURE_SCORE_GE_10",
    "RISK_MEDIUM",
    "REGIME_FILTER",
]

def combinations():
    result=[]
    for i,g in enumerate(DEFAULT_GATES):
        result.append([g])
    return result
