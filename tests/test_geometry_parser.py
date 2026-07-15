import math
from engine.geometry_parser import extract_numeric_values, parse_trade_geometry


def test_extracts_json_python_list_and_range():
    assert extract_numeric_values('[100, 110, 120]') == [100.0, 110.0, 120.0]
    assert extract_numeric_values("['100', '110']") == [100.0, 110.0]
    assert extract_numeric_values('100 - 110') == [100.0, 110.0]


def test_long_geometry_selects_nearest_favorable_levels():
    g = parse_trade_geometry('100 - 102', '[95, 96]', '[105, 110, 120]', 'LONG')
    assert g.geometry_valid
    assert g.entry == 101.0
    assert g.stop == 96.0
    assert g.target == 105.0


def test_short_geometry_selects_nearest_favorable_levels():
    g = parse_trade_geometry(100, '{"stop": [104, 108]}', '{"targets": [95, 90]}', 'SHORT')
    assert g.geometry_valid
    assert g.stop == 104.0
    assert g.target == 95.0


def test_invalid_directional_geometry_fails_closed():
    g = parse_trade_geometry(100, 105, 110, 'LONG')
    assert not g.geometry_valid
    assert 'INVALID_STOP' in g.parse_reason
