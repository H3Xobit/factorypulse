"""Database helpers for TimescaleDB / Postgres."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from factorypulse.models import AnomalyEvent, SensorSample
from factorypulse.settings import get_settings


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    settings = get_settings()
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn


def insert_sensor_sample(conn: psycopg.Connection, sample: SensorSample) -> None:
    conn.execute(
        """
        INSERT INTO sensor_samples (time, machine, metric, value, fault_tag)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (sample.time, sample.machine, sample.metric, sample.value, sample.fault_tag),
    )


def insert_audio_chunk(
    conn: psycopg.Connection,
    *,
    machine: str,
    path: str,
    label: str | None,
    fault_tag: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO audio_chunks (machine, path, label, fault_tag)
        VALUES (%s, %s, %s, %s)
        """,
        (machine, path, label, fault_tag),
    )


def insert_anomaly_event(conn: psycopg.Connection, event: AnomalyEvent) -> int:
    row = conn.execute(
        """
        INSERT INTO anomaly_events (
            event_id, machine, source, severity, fault_code, score, summary, evidence, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
        RETURNING id
        """,
        (
            str(event.event_id),
            event.machine,
            event.source.value,
            event.severity.value,
            event.fault_code,
            event.score,
            event.summary,
            json.dumps(event.evidence),
            event.status,
        ),
    ).fetchone()
    assert row is not None
    return int(row["id"])


def list_anomaly_events(conn: psycopg.Connection, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, event_id, machine, source, severity, fault_code, score, summary,
               evidence, status, created_at
        FROM anomaly_events
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    ).fetchall()
    return list(rows)


def get_anomaly_event(conn: psycopg.Connection, event_id: UUID) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, event_id, machine, source, severity, fault_code, score, summary,
               evidence, status, created_at
        FROM anomaly_events
        WHERE event_id = %s
        """,
        (str(event_id),),
    ).fetchone()
    return dict(row) if row else None


def recent_metric_series(
    conn: psycopg.Connection,
    *,
    machine: str,
    metric: str,
    limit: int = 256,
) -> list[tuple[datetime, float]]:
    rows = conn.execute(
        """
        SELECT time, value
        FROM sensor_samples
        WHERE machine = %s AND metric = %s
        ORDER BY time DESC
        LIMIT %s
        """,
        (machine, metric, limit),
    ).fetchall()
    series = [(r["time"], float(r["value"])) for r in rows]
    series.reverse()
    return series


def recent_audio_chunks(conn: psycopg.Connection, limit: int = 20) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, created_at, machine, path, label, fault_tag
        FROM audio_chunks
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    ).fetchall()
    return list(rows)



def insert_triage_report(conn: psycopg.Connection, report: dict[str, Any]) -> int:
    row = conn.execute(
        """
        INSERT INTO triage_reports (
            report_id, event_id, machine, root_cause, confidence, recommended_action,
            estimated_downtime_risk, evidence, report_en, report_ja, unsupported_claims, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb)
        RETURNING id
        """,
        (
            str(report["report_id"]),
            str(report["event_id"]) if report.get("event_id") else None,
            report["machine"],
            report["root_cause"],
            report["confidence"],
            report["recommended_action"],
            report["estimated_downtime_risk"],
            json.dumps(report.get("evidence") or []),
            report["report_en"],
            report["report_ja"],
            int(report.get("unsupported_claims") or 0),
            json.dumps(report.get("metadata") or {}),
        ),
    ).fetchone()
    assert row is not None
    return int(row["id"])


def get_triage_report(conn: psycopg.Connection, report_id: UUID) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM triage_reports WHERE report_id = %s",
        (str(report_id),),
    ).fetchone()
    return dict(row) if row else None


def list_triage_reports(conn: psycopg.Connection, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM triage_reports ORDER BY created_at DESC LIMIT %s",
        (limit,),
    ).fetchall()
    return list(rows)
