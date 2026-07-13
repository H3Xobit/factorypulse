"""Diagnosis graph nodes."""

from __future__ import annotations

import json
from uuid import uuid4

from factorypulse.graph.prompts import (
    DIAGNOSE_SYSTEM,
    DIAGNOSE_USER,
    TRANSLATE_SYSTEM,
    VERIFY_SYSTEM,
)
from factorypulse.graph.state import GraphState
from factorypulse.llm.router import LLMRouter
from factorypulse.models import Diagnosis
from factorypulse.rag.retrieve import retrieve


def _fmt_hits(hits: list[dict]) -> str:
    lines = []
    for h in hits:
        lines.append(
            f"- section_id={h.get('section_id')} fault_code={h.get('fault_code')} "
            f"title={h.get('title')} body={h.get('body')[:240]}"
        )
    return "\n".join(lines) if lines else "(none)"


def triage_router(state: GraphState) -> GraphState:
    symptom = state.get("symptom") or ""
    fault = state.get("fault_code")
    query = f"{fault or ''} {symptom} {state.get('machine','')}".strip()
    return {**state, "symptom": symptom, "fault_code": fault, "_query": query}  # type: ignore[typeddict-item]


def retrieve_manuals(state: GraphState) -> GraphState:
    query = f"{state.get('fault_code') or ''} {state.get('symptom') or ''}"
    hits = retrieve(query, source_type="manual", top_k=5)
    return {**state, "manual_hits": hits}


def retrieve_incidents(state: GraphState) -> GraphState:
    query = f"{state.get('fault_code') or ''} {state.get('symptom') or ''}"
    hits = retrieve(query, source_type="incident", top_k=5)
    return {**state, "incident_hits": hits}


def diagnose(state: GraphState) -> GraphState:
    router = LLMRouter()
    user = DIAGNOSE_USER.format(
        machine=state.get("machine"),
        fault_code=state.get("fault_code"),
        symptom=state.get("symptom"),
        manuals=_fmt_hits(state.get("manual_hits") or []),
        incidents=_fmt_hits(state.get("incident_hits") or []),
    )
    if state.get("correction_pass"):
        user += (
            "\nCorrection: previous diagnosis had unsupported claims. "
            "Stick strictly to evidence."
        )
    raw = router.complete_json(role="diagnose", system=DIAGNOSE_SYSTEM, user=user)
    try:
        diagnosis = Diagnosis.model_validate(raw)
    except Exception:
        raw = router.complete_json(
            role="diagnose", system=DIAGNOSE_SYSTEM, user=user + "\nReturn valid JSON."
        )
        diagnosis = Diagnosis.model_validate(raw)
    return {**state, "diagnosis": diagnosis.model_dump()}


def verify(state: GraphState) -> GraphState:
    router = LLMRouter()
    user = json.dumps(
        {
            "diagnosis": state.get("diagnosis"),
            "manual_hits": state.get("manual_hits"),
            "incident_hits": state.get("incident_hits"),
        }
    )
    raw = router.complete_json(role="verify", system=VERIFY_SYSTEM, user=user)
    unsupported = int(raw.get("unsupported_claims", 0))
    out = {**state, "unsupported_claims": unsupported}
    if unsupported > 1 and not state.get("correction_pass"):
        out["correction_pass"] = True
    return out


def report_writer(state: GraphState) -> GraphState:
    d = state.get("diagnosis") or {}
    evidence_lines = []
    for e in d.get("evidence") or []:
        evidence_lines.append(f"- [{e.get('source_type')}] {e.get('section_id')}: {e.get('quote')}")
    report_en = (
        f"FactoryPulse Triage Report\n"
        f"Machine: {state.get('machine')}\n"
        f"Fault code: {state.get('fault_code')}\n"
        f"Root cause: {d.get('root_cause')}\n"
        f"Confidence: {d.get('confidence')}\n"
        f"Recommended action: {d.get('recommended_action')}\n"
        f"Downtime risk: {d.get('estimated_downtime_risk')}\n"
        f"Evidence:\n" + "\n".join(evidence_lines)
    )
    return {**state, "report_en": report_en}


def translator(state: GraphState) -> GraphState:
    router = LLMRouter()
    report_ja = router.complete_text(
        role="translate", system=TRANSLATE_SYSTEM, user=state.get("report_en") or ""
    )
    return {**state, "report_ja": report_ja, "report_id": str(uuid4())}
