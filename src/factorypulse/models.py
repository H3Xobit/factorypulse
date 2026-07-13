"""Pydantic models at every I/O boundary."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Severity(StrEnum):
    info = "info"
    warn = "warn"
    fault = "fault"


class DetectorSource(StrEnum):
    audio = "audio"
    timeseries = "timeseries"
    rules = "rules"
    injected = "injected"


class FaultType(StrEnum):
    bearing_degradation = "bearing_degradation"
    abnormal_pump_audio = "abnormal_pump_audio"
    seal_temp_drift = "seal_temp_drift"


class SensorSample(BaseModel):
    time: datetime
    machine: str
    metric: str
    value: float
    fault_tag: str | None = None


class AudioChunkMeta(BaseModel):
    machine: str
    path: str
    label: str | None = None
    fault_tag: str | None = None
    created_at: datetime | None = None


class AnomalyEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    machine: str
    source: DetectorSource
    severity: Severity
    fault_code: str | None = None
    score: float = Field(ge=0.0, le=1.0)
    summary: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: str = "open"
    created_at: datetime | None = None

    @field_validator("summary")
    @classmethod
    def summary_nonempty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("summary must be non-empty")
        return cleaned


class AnomalyEventOut(AnomalyEvent):
    id: int | None = None


class HealthResponse(BaseModel):
    status: str
    service: str = "factorypulse-api"
    version: str


class InjectFaultResponse(BaseModel):
    accepted: bool
    fault_type: FaultType
    event: AnomalyEvent


class EvidenceCitation(BaseModel):
    source_type: str
    section_id: str
    quote: str


class Diagnosis(BaseModel):
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[EvidenceCitation] = Field(default_factory=list)
    recommended_action: str
    estimated_downtime_risk: str


class TriageReport(BaseModel):
    report_id: UUID = Field(default_factory=uuid4)
    event_id: UUID | None = None
    machine: str
    diagnosis: Diagnosis
    report_en: str
    report_ja: str
    unsupported_claims: int = 0
