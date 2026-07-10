"""Exit research module. Research only, never changes live logic."""
from __future__ import annotations

VERSION="v10.1.0"

HOLDING_PERIODS=[1,3,6,12,18]
STOP_TARGET_MATRIX=[
    {"stop":0.5,"target":1},
    {"stop":1,"target":2},
    {"stop":2,"target":3},
]

def candidates():
    return {
        "holding_periods":HOLDING_PERIODS,
        "stop_target_matrix":STOP_TARGET_MATRIX
    }
