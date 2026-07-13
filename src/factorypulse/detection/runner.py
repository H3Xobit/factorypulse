"""Poll DB + audio chunks and emit AnomalyEvents."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from factorypulse.db import (
    connect,
    insert_anomaly_event,
    recent_audio_chunks,
    recent_metric_series,
)
from factorypulse.detection.audio_detector import AudioAnomalyDetector
from factorypulse.detection.rules import evaluate_sample, load_thresholds
from factorypulse.detection.ts_detector import score_series_to_event
from factorypulse.settings import get_settings

logger = logging.getLogger(__name__)

SERIES_TARGETS = [
    ("vffs_packager", "seal_jaw_temp_c", "E-102"),
    ("centrifugal_pump", "vibration_rms", "E-220"),
    ("fan_unit", "accel_peak_g", "E-310"),
]


def run_once() -> int:
    settings = get_settings()
    rules = load_thresholds(Path(settings.config_dir) / "thresholds.yaml")
    audio_det = AudioAnomalyDetector(seed=settings.fp_seed)
    created = 0
    with connect() as conn:
        for machine, metric, fault_code in SERIES_TARGETS:
            series = recent_metric_series(conn, machine=machine, metric=metric, limit=128)
            if not series:
                continue
            _last_t, last_v = series[-1]
            rule_event = evaluate_sample(
                machine=machine, metric=metric, value=last_v, rules=rules
            )
            if rule_event is not None:
                insert_anomaly_event(conn, rule_event)
                created += 1
            values = [v for _, v in series]
            ts_event = score_series_to_event(
                machine=machine, metric=metric, values=values, fault_code=fault_code
            )
            if ts_event is not None:
                insert_anomaly_event(conn, ts_event)
                created += 1

        for chunk in recent_audio_chunks(conn, limit=10):
            path = Path(chunk["path"])
            if not path.exists():
                continue
            event = audio_det.predict_path(path, machine=str(chunk["machine"]))
            if event is not None:
                insert_anomaly_event(conn, event)
                created += 1
        conn.commit()
    logger.info("detection pass created=%s", created)
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="FactoryPulse detection runner")
    parser.add_argument("--once", action="store_true", help="run a single detection pass")
    args = parser.parse_args()
    settings = get_settings()
    logging.basicConfig(level=settings.fp_log_level)
    if args.once:
        run_once()
    else:
        run_once()


if __name__ == "__main__":
    main()
