"""FastAPI service for FactoryPulse (M1 surface)."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager
from typing import Annotated, Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from factorypulse import __version__
from factorypulse.db import connect, get_anomaly_event, insert_anomaly_event, list_anomaly_events
from factorypulse.detection.runner import run_once
from factorypulse.models import (
    AnomalyEvent,
    DetectorSource,
    FaultType,
    HealthResponse,
    InjectFaultResponse,
    Severity,
)
from factorypulse.settings import get_settings
from factorypulse.simulator.replay import run_replay

logger = logging.getLogger(__name__)
_sim_lock = threading.Lock()


def _spawn_fault_simulation(fault_type: FaultType) -> None:
    settings = get_settings()

    def _job() -> None:
        with _sim_lock:
            run_replay(
                duration_s=20,
                interval_s=1.0,
                seed=settings.fp_seed,
                fault=fault_type.value,
            )
            try:
                run_once()
            except Exception:
                logger.exception("detection after inject failed")

    threading.Thread(target=_job, name=f"inject-{fault_type.value}", daemon=True).start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=get_settings().fp_log_level)
    logger.info("api starting version=%s", __version__)
    from factorypulse.ingestion.consumer import IngestionConsumer

    consumer = IngestionConsumer()
    ingest_thread = threading.Thread(
        target=consumer.run,
        kwargs={"duration_s": None},
        name="fp-ingest",
        daemon=True,
    )
    ingest_thread.start()
    app.state.ingest_consumer = consumer
    try:
        yield
    finally:
        consumer.request_stop()


app = FastAPI(title="FactoryPulse API", version=__version__, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@app.get("/events")
def events(limit: int = Query(default=50, ge=1, le=500)) -> list[dict[str, Any]]:
    try:
        with connect() as conn:
            rows = list_anomaly_events(conn, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["event_id"] = str(item["event_id"])
        if item.get("created_at") is not None:
            item["created_at"] = item["created_at"].isoformat()
        out.append(item)
    return out


@app.get("/events/{event_id}")
def event_detail(event_id: UUID) -> dict[str, Any]:
    try:
        with connect() as conn:
            row = get_anomaly_event(conn, event_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    item = dict(row)
    item["event_id"] = str(item["event_id"])
    if item.get("created_at") is not None:
        item["created_at"] = item["created_at"].isoformat()
    return item


@app.post("/simulate/inject-fault", response_model=InjectFaultResponse)
def inject_fault(
    type: Annotated[FaultType, Query(alias="type")],
) -> InjectFaultResponse:
    machine = {
        FaultType.bearing_degradation: "fan_unit",
        FaultType.abnormal_pump_audio: "centrifugal_pump",
        FaultType.seal_temp_drift: "vffs_packager",
    }[type]
    fault_code = {
        FaultType.bearing_degradation: "E-310",
        FaultType.abnormal_pump_audio: "E-AUDIO",
        FaultType.seal_temp_drift: "E-102",
    }[type]
    event = AnomalyEvent(
        machine=machine,
        source=DetectorSource.injected,
        severity=Severity.fault,
        fault_code=fault_code,
        score=0.95,
        summary=f"Injected fault: {type.value}",
        evidence={"fault_type": type.value, "via": "api"},
    )
    try:
        with connect() as conn:
            insert_anomaly_event(conn, event)
            conn.commit()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc

    _spawn_fault_simulation(type)
    return InjectFaultResponse(accepted=True, fault_type=type, event=event)


@app.get("/reports")
def list_reports(limit: int = Query(default=20, ge=1, le=200)) -> list[dict[str, Any]]:
    from factorypulse.db import list_triage_reports

    try:
        with connect() as conn:
            rows = list_triage_reports(conn, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    out = []
    for row in rows:
        item = dict(row)
        for key in ("report_id", "event_id"):
            if item.get(key) is not None:
                item[key] = str(item[key])
        if item.get("created_at") is not None:
            item["created_at"] = item["created_at"].isoformat()
        out.append(item)
    return out


@app.get("/reports/{report_id}")
def get_report(report_id: UUID) -> dict[str, Any]:
    from factorypulse.db import get_triage_report

    try:
        with connect() as conn:
            row = get_triage_report(conn, report_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="report not found")
    item = dict(row)
    for key in ("report_id", "event_id"):
        if item.get(key) is not None:
            item[key] = str(item[key])
    if item.get("created_at") is not None:
        item["created_at"] = item["created_at"].isoformat()
    return item


@app.post("/diagnose/{event_id}")
def diagnose_event(event_id: UUID) -> dict[str, Any]:
    from factorypulse.db import get_anomaly_event, insert_triage_report
    from factorypulse.graph.build import run_diagnosis

    try:
        with connect() as conn:
            event = get_anomaly_event(conn, event_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    if event is None:
        raise HTTPException(status_code=404, detail="event not found")

    result = run_diagnosis(
        {
            "event_id": str(event_id),
            "machine": event["machine"],
            "symptom": event["summary"],
            "fault_code": event.get("fault_code"),
            "summary": event["summary"],
        }
    )
    diagnosis = result.get("diagnosis") or {}
    report = {
        "report_id": result.get("report_id"),
        "event_id": str(event_id),
        "machine": event["machine"],
        "root_cause": diagnosis.get("root_cause"),
        "confidence": diagnosis.get("confidence"),
        "recommended_action": diagnosis.get("recommended_action"),
        "estimated_downtime_risk": diagnosis.get("estimated_downtime_risk"),
        "evidence": diagnosis.get("evidence") or [],
        "report_en": result.get("report_en"),
        "report_ja": result.get("report_ja"),
        "unsupported_claims": result.get("unsupported_claims") or 0,
        "metadata": {"offline": True},
    }
    try:
        with connect() as conn:
            insert_triage_report(conn, report)
            conn.commit()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    return report


@app.get("/events/stream")
async def events_stream():
    import asyncio
    import json as json_lib

    from sse_starlette.sse import EventSourceResponse

    async def gen():
        last_seen = None
        while True:
            try:
                with connect() as conn:
                    rows = list_anomaly_events(conn, limit=5)
                payload = []
                for row in rows:
                    item = dict(row)
                    item["event_id"] = str(item["event_id"])
                    if item.get("created_at") is not None:
                        item["created_at"] = item["created_at"].isoformat()
                    payload.append(item)
                stamp = payload[0]["event_id"] if payload else None
                if stamp != last_seen:
                    last_seen = stamp
                    yield {"event": "events", "data": json_lib.dumps(payload)}
            except Exception as exc:
                yield {"event": "error", "data": str(exc)}
            await asyncio.sleep(2)

    return EventSourceResponse(gen())
