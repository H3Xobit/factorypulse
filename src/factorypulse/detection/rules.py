"""Static threshold rules from config/thresholds.yaml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from factorypulse.models import AnomalyEvent, DetectorSource, Severity


def load_thresholds(config_path: Path) -> dict[str, Any]:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "rules" not in data:
        raise ValueError(f"invalid thresholds file: {config_path}")
    return dict(data["rules"])


def score_against_rule(value: float, rule: dict[str, Any]) -> tuple[Severity, float] | None:
    fault_above = float(rule["fault_above"])
    warn_above = float(rule["warn_above"])
    if value >= fault_above:
        span = max(fault_above * 0.25, 1e-6)
        score = min(1.0, 0.8 + (value - fault_above) / span * 0.2)
        return Severity.fault, score
    if value >= warn_above:
        span = max(fault_above - warn_above, 1e-6)
        score = 0.65 + 0.14 * ((value - warn_above) / span)
        return Severity.warn, min(score, 0.79)
    return None


def evaluate_sample(
    *,
    machine: str,
    metric: str,
    value: float,
    rules: dict[str, Any],
) -> AnomalyEvent | None:
    for rule in rules.values():
        if rule.get("machine") not in {machine, "any"}:
            continue
        if rule.get("metric") != metric:
            continue
        hit = score_against_rule(value, rule)
        if hit is None:
            continue
        severity, score = hit
        return AnomalyEvent(
            machine=machine,
            source=DetectorSource.rules,
            severity=severity,
            fault_code=str(rule.get("fault_code")) if rule.get("fault_code") else None,
            score=score,
            summary=str(rule.get("description", f"{metric} threshold exceeded")),
            evidence={"metric": metric, "value": value, "rule": rule},
        )
    return None
