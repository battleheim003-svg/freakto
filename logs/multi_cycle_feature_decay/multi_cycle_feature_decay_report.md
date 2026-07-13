# Freakto Multi-Cycle Feature Decay & Regime Drift

- Status: **COMPLETE_NO_PROMOTION**
- Mode: `MULTI_CYCLE_DEVELOPMENT_DIAGNOSTIC_ONLY`
- Selected replay: **FULL**
- Development cutoff: `2026-07-09T12:00:00Z`
- Rows loaded/usable: **16150 / 16150**
- Components: **7**
- Fixed benchmark: `score >= 70`
- Promotion applied: **False**
- Paper/Live enabled: **False**

## Non-overlapping era counts

- LEGACY: **4843**
- TRANSITION: **4056**
- RECENT: **7251**

## Key findings

- Components whose legacy association weakened materially in the recent era: Volume, Trend, Regime.
- 2 regime/side cells changed portfolio share by at least 10% between legacy and recent eras.
- Directional expectancy changed from -0.466002% in LEGACY to -0.461087% in RECENT.
- The frozen score>=70 benchmark had recent n=1390, expectancy=-0.259619% and PF=0.8188129113983381.

## Component classifications — ALL scope

- **Volume**: `DECAYED` | legacy rho=0.0132, recent rho=0.0097, recent spread=-0.040558%
- **Trend**: `DECAYED` | legacy rho=0.0017, recent rho=0.0115, recent spread=-0.098526%
- **Regime**: `DECAYED` | legacy rho=-0.0473, recent rho=0.0224, recent spread=-0.048519%
- **Momentum**: `WEAK_OR_MIXED` | legacy rho=-0.0240, recent rho=-0.0186, recent spread=-0.030481%
- **Adaptive Adjustment**: `WEAK_OR_MIXED` | legacy rho=-0.0322, recent rho=0.0072, recent spread=-0.013267%
- **Structure**: `WEAK_OR_MIXED` | legacy rho=-0.0194, recent rho=0.0291, recent spread=0.230228%
- **Risk Penalty**: `WEAK_OR_MIXED` | legacy rho=-0.0642, recent rho=-0.0058, recent spread=-0.045674%

## Regime/side diagnostics — ALL scope

- **UNKNOWN/SHORT**: `INELIGIBLE_UNKNOWN` | legacy=-0.920288% | recent=-0.654950% | recent n=3362
- **UNKNOWN/LONG**: `INELIGIBLE_UNKNOWN` | legacy=-0.143689% | recent=-0.293495% | recent n=3889

## Warnings

- 3Y, 5Y and FULL windows overlap; non-overlapping eras from the longest replay are the primary evidence.
- All positive findings are diagnostic only and require untouched Fresh OOS and Forward confirmation.

## Safety

This analysis is development diagnostic only. It does not tune or promote weights, thresholds, regimes, Paper trading, or Live trading.