import numpy as np

from factorypulse.detection.ts_detector import residual_zscore, score_series_to_event


def test_residual_zscore_stable_series():
    values = [1.0 + 0.01 * i for i in range(40)]
    z, last = residual_zscore(values)
    assert abs(z) < 3.0
    assert last == values[-1]


def test_score_series_detects_spike():
    values = list(np.linspace(1.0, 1.2, 40)) + [5.0]
    event = score_series_to_event(
        machine="fan_unit",
        metric="accel_peak_g",
        values=values,
        fault_code="E-310",
    )
    assert event is not None
    assert event.source.value == "timeseries"
    assert event.fault_code == "E-310"
    assert event.score >= 0.7
