"""LangGraph state for diagnosis pipeline."""

from __future__ import annotations

from typing import Any, TypedDict


class GraphState(TypedDict, total=False):
    event_id: str
    machine: str
    symptom: str
    fault_code: str | None
    manual_hits: list[dict[str, Any]]
    incident_hits: list[dict[str, Any]]
    diagnosis: dict[str, Any]
    unsupported_claims: int
    report_en: str
    report_ja: str
    report_id: str
    correction_pass: bool
