"""Replay packaging-line telemetry over MQTT with optional fault injection."""

from __future__ import annotations

import argparse
import json
import logging
import math
import time
import wave
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import paho.mqtt.client as mqtt

from factorypulse.settings import get_settings

logger = logging.getLogger(__name__)

TOPIC_SENSORS = "factorypulse/sensors"
TOPIC_AUDIO = "factorypulse/audio"


@dataclass
class ActiveFault:
    fault_type: str
    started_at: float
    duration_s: float = 45.0

    def active(self) -> bool:
        return (time.time() - self.started_at) < self.duration_s


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _synth_wav(
    path: Path,
    *,
    anomalous: bool,
    seed: int,
    seconds: float = 1.0,
    sr: int = 16000,
) -> None:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    base = 0.15 * np.sin(2 * np.pi * 120 * t)
    noise = 0.05 * rng.standard_normal(t.shape[0])
    if anomalous:
        base += 0.25 * np.sin(2 * np.pi * 780 * t)
        noise *= 3.0
    audio = np.clip(base + noise, -1.0, 1.0)
    pcm = (audio * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def build_sensor_payload(tick: int, fault: ActiveFault | None, seed: int) -> list[dict]:
    rng = np.random.default_rng(seed + tick)
    t = _now().isoformat()
    seal = 175.0 + 2.0 * math.sin(tick / 8.0) + float(rng.normal(0, 0.4))
    vib = 0.18 + 0.02 * math.sin(tick / 5.0) + float(abs(rng.normal(0, 0.01)))
    accel = 1.2 + 0.1 * math.sin(tick / 7.0) + float(abs(rng.normal(0, 0.05)))
    tag = None
    if fault and fault.active():
        tag = fault.fault_type
        if fault.fault_type == "seal_temp_drift":
            seal += 25.0 + tick % 5
        elif fault.fault_type == "bearing_degradation":
            accel += 3.5 + 0.2 * (tick % 7)
            vib += 0.4
        elif fault.fault_type == "abnormal_pump_audio":
            vib += 0.5
    return [
        {
            "time": t,
            "machine": "vffs_packager",
            "metric": "seal_jaw_temp_c",
            "value": seal,
            "fault_tag": tag,
        },
        {
            "time": t,
            "machine": "centrifugal_pump",
            "metric": "vibration_rms",
            "value": vib,
            "fault_tag": tag,
        },
        {
            "time": t,
            "machine": "fan_unit",
            "metric": "accel_peak_g",
            "value": accel,
            "fault_tag": tag,
        },
    ]


def run_replay(*, duration_s: int, interval_s: float, seed: int, fault: str | None) -> None:
    settings = get_settings()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"fp-sim-{seed}")
    client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=30)
    client.loop_start()
    active = ActiveFault(fault, time.time()) if fault else None
    tmp_audio = Path(settings.audio_chunk_dir) / "_sim"
    started = time.time()
    tick = 0
    logger.info("simulator started broker=%s:%s", settings.mqtt_broker, settings.mqtt_port)
    try:
        while (time.time() - started) < duration_s:
            if active and not active.active():
                active = None
            for sample in build_sensor_payload(tick, active, seed):
                client.publish(TOPIC_SENSORS, json.dumps(sample), qos=0)
            anomalous = bool(active and active.fault_type == "abnormal_pump_audio")
            wav_path = tmp_audio / f"tick_{tick:05d}.wav"
            _synth_wav(wav_path, anomalous=anomalous, seed=seed + tick)
            audio_msg = {
                "time": _now().isoformat(),
                "machine": "centrifugal_pump",
                "path": str(wav_path),
                "label": "abnormal" if anomalous else "normal",
                "fault_tag": active.fault_type if active else None,
            }
            client.publish(TOPIC_AUDIO, json.dumps(audio_msg), qos=0)
            tick += 1
            time.sleep(interval_s)
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("simulator stopped after %s ticks", tick)


def main() -> None:
    parser = argparse.ArgumentParser(description="FactoryPulse MQTT replay simulator")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument(
        "--fault",
        choices=["bearing_degradation", "abnormal_pump_audio", "seal_temp_drift"],
        default=None,
    )
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    settings = get_settings()
    logging.basicConfig(level=settings.fp_log_level)
    seed = settings.fp_seed if args.seed is None else args.seed
    run_replay(duration_s=args.duration, interval_s=args.interval, seed=seed, fault=args.fault)


if __name__ == "__main__":
    main()
