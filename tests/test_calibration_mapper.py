from engine.calibration_mapper import _bucket


def test_score_bucket():
    assert _bucket(75) == "score_70_79"
