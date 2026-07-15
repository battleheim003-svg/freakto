import pandas as pd
from engine.cost_gate_diagnostics import apply_thresholds, derive_train_thresholds, funnel_table, rejection_reason


def sample():
    return pd.DataFrame({
        'has_event':[True]*4,
        'entry_valid':[True,True,False,True],
        'stop_valid':[True,True,False,True],
        'target_valid':[True,True,False,True],
        'geometry_valid':[True,True,False,True],
        'event_execution_cost_pct':[.5,.5,.5,2.0],
        'gross_target_to_cost':[3.0,1.0,float('nan'),3.0],
        'net_reward_risk':[1.0,.2,float('nan'),1.0],
        'risk_penalty':[5,5,5,5],
    })


def test_rejection_reason_is_first_failure():
    df=sample()
    r=rejection_reason(df, maximum_cost_pct=1.25, minimum_target_to_cost=2, minimum_net_reward_risk=.5, maximum_risk_penalty=25)
    assert list(r)==['PASS','TARGET_TO_COST_TOO_LOW','INVALID_ENTRY','COST_TOO_HIGH']


def test_train_thresholds_and_application_are_return_free():
    df=sample()
    t=derive_train_thresholds(df)
    out=apply_thresholds(df,t)
    assert t.source_rows==3
    assert 'train_derived_cost_gate_pass' in out


def test_funnel_is_monotone_enough_and_reports_final():
    df=sample(); df['cost_gate_pass']=[True,False,False,False]
    f=funnel_table(df)
    assert f.iloc[-1]['stage']=='FINAL_COST_GATE'
    assert int(f.iloc[-1]['rows'])==1
