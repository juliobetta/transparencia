import pytest

from analysis.comparison import PeriodSpec, _delta


def test_period_spec_fields():
    spec = PeriodSpec(year=2024, month_start=1, month_end=6)
    assert spec.year == 2024
    assert spec.month_start == 1
    assert spec.month_end == 6


def test_delta_normal():
    d = _delta(100.0, 150.0)
    assert d["a"] == 100.0
    assert d["b"] == 150.0
    assert d["abs"] == pytest.approx(50.0)
    assert d["pct"] == pytest.approx(50.0)


def test_delta_decrease():
    d = _delta(200.0, 100.0)
    assert d["abs"] == pytest.approx(-100.0)
    assert d["pct"] == pytest.approx(-50.0)


def test_delta_zero_base():
    d = _delta(0.0, 50.0)
    assert d["abs"] == pytest.approx(50.0)
    assert d["pct"] is None


def test_delta_both_zero():
    d = _delta(0.0, 0.0)
    assert d["abs"] == pytest.approx(0.0)
    assert d["pct"] is None
