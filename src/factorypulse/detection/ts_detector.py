"""Time-series anomaly scoring with Chronos optional; residual z-score fallback."""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np

from factorypulse.models import AnomalyEvent, DetectorSource, Severity

logger = logging.getLogger(__name__)


def residual_zscore(values: Sequence[float], window: int = 32) -> tuple[float, float]:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size < max(8, window // 2):
        return 0.0, float(arr[-1]) if arr.size else 0.0
    w = min(window, arr.size - 1)
    hist = arr[-(w + 1) : -1]
    mu = float(hist.mean())
    sigma = float(hist.std()) + 1e-6
    last = float(arr[-1])
    z = (last - mu) / sigma
    return z, last


def chronos_residual_score(values: Sequence[float]) -> float | None:
    try:
        import torch
        from chronos import BaseChronosPipeline
    except Exception:
        return None
    arr = np.asarray(list(values), dtype=np.float32)
    if arr.size < 32:
        return None
    try:
        pipeline = BaseChronosPipeline.from_pretrained(
            "amazon/chronos-bolt-small",
            device_map="cpu",
        )
        context = torch.tensor(arr[:-1], dtype=torch.float32)
        forecast = pipeline.predict(context, prediction_length=1)
        pred = float(np.median(forecast.detach().cpu().numpy()))
        sigma = float(np.std(arr[:-1])) + 1e-6
        return abs(float(arr[-1]) - pred) / sigma
    except Exception:
        logger.exception("chronos scoring failed; using residual fallback")
        return None


def score_series_to_event(
    *,
    machine: str,
    metric: str,
    values: Sequence[float],
    fault_code: str | None = None,
) -> AnomalyEvent | None:
    chronos_z = chronos_residual_score(values)
    if chronos_z is None:
        z, last = residual_zscore(values)
        method = "residual_zscore"
        score_raw = abs(z)
    else:
        last = float(values[-1]) if values else 0.0
        method = "chronos_bolt_small"
        score_raw = float(chronos_z)
        z = chronos_z

    if score_raw < 3.0:
        return None
    score = min(1.0, 0.7 + (score_raw - 3.0) / 3.0 * 0.3)
    severity = Severity.fault if score_raw >= 4.5 else Severity.warn
    return AnomalyEvent(
        machine=machine,
        source=DetectorSource.timeseries,
        severity=severity,
        fault_code=fault_code,
        score=score,
        summary=f"Time-series residual anomaly on {metric}",
        evidence={
            "metric": metric,
            "method": method,
            "z": float(z),
            "last_value": last,
            "n": len(values),
        },
    )
