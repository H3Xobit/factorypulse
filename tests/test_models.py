from factorypulse.models import AnomalyEvent, DetectorSource, Severity


def test_anomaly_event_defaults():
    event = AnomalyEvent(
        machine="fan_unit",
        source=DetectorSource.rules,
        severity=Severity.fault,
        score=0.9,
        summary="test",
    )
    assert event.status == "open"
    assert event.event_id is not None
