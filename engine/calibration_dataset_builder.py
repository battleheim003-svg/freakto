"""Build a clean calibration dataset from Freakto evaluation logs."""
from pathlib import Path
import pandas as pd

DEFAULT_SOURCE = Path('logs/decision_evaluations.csv')
DEFAULT_OUTPUT = Path('logs/calibration_dataset/calibration_training.csv')


def build_calibration_dataset(source=DEFAULT_SOURCE, output=DEFAULT_OUTPUT):
    source = Path(source)
    output = Path(output)
    if not source.exists():
        raise FileNotFoundError(source)

    df = pd.read_csv(source, low_memory=False)
    if 'evaluation_status' in df.columns:
        df = df[df['evaluation_status'].astype(str).str.upper() == 'COMPLETE'].copy()

    keep = [
        'decision_id','timestamp','symbol','side','score','confidence_label',
        'actionability','evaluated_return','return_after_24h_pct',
        'target_1_hit','market_regime','risk_level'
    ]
    cols = [c for c in keep if c in df.columns]
    result = df[cols].copy()

    if 'evaluated_return' not in result.columns:
        for c in ['return_after_24h_pct','return_after_12h_pct','return_after_4h_pct']:
            if c in result.columns:
                result['evaluated_return'] = pd.to_numeric(result[c], errors='coerce')
                break

    if 'evaluated_return' in result.columns:
        result['win'] = pd.to_numeric(result['evaluated_return'], errors='coerce') > 0

    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False, encoding='utf-8-sig')
    return output, len(result)


if __name__ == '__main__':
    path, rows = build_calibration_dataset()
    print(f'Calibration dataset created: {path} rows={rows}')
