"""Build and run the diagnosis LangGraph."""

from __future__ import annotations

from typing import Any

from factorypulse.graph.nodes import (
    diagnose,
    report_writer,
    retrieve_incidents,
    retrieve_manuals,
    translator,
    triage_router,
    verify,
)
from factorypulse.graph.state import GraphState


def run_diagnosis(payload: dict[str, Any]) -> GraphState:
    """Deterministic graph execution without requiring LangGraph runtime quirks.

    Flow: triage -> retrieve manuals/incidents -> diagnose -> verify
          (-> diagnose once if needed) -> report -> translate.
    """
    state: GraphState = {
        "event_id": str(payload.get("event_id") or ""),
        "machine": str(payload["machine"]),
        "symptom": str(payload.get("symptom") or payload.get("summary") or ""),
        "fault_code": payload.get("fault_code"),
        "correction_pass": False,
    }
    state = triage_router(state)
    manuals = retrieve_manuals(state)
    incidents = retrieve_incidents(state)
    state = {**state, **manuals, **incidents}
    state = diagnose(state)
    state = verify(state)
    if state.get("unsupported_claims", 0) > 1 and state.get("correction_pass"):
        state = diagnose(state)
        state = verify(state)
    state = report_writer(state)
    state = translator(state)
    return state
