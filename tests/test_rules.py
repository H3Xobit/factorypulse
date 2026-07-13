from factorypulse.detection.rules import evaluate_sample, score_against_rule

RULE = {
    "machine": "vffs_packager",
    "metric": "seal_jaw_temp_c",
    "warn_above": 185.0,
    "fault_above": 195.0,
    "fault_code": "E-102",
    "description": "Seal jaw temperature deviation",
}


def test_score_against_rule_normal():
    assert score_against_rule(170.0, RULE) is None


def test_score_against_rule_warn():
    hit = score_against_rule(190.0, RULE)
    assert hit is not None
    severity, score = hit
    assert severity.value == "warn"
    assert 0.65 <= score < 0.80


def test_score_against_rule_fault():
    hit = score_against_rule(205.0, RULE)
    assert hit is not None
    severity, score = hit
    assert severity.value == "fault"
    assert score >= 0.80


def test_evaluate_sample_match():
    event = evaluate_sample(
        machine="vffs_packager",
        metric="seal_jaw_temp_c",
        value=200.0,
        rules={"seal_temp_c": RULE},
    )
    assert event is not None
    assert event.fault_code == "E-102"
    assert event.source.value == "rules"
