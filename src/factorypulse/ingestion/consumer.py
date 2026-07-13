"""MQTT ingestion consumer: sensors -> TimescaleDB, audio -> files + DB."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import signal
import time
from datetime import UTC, datetime
from pathlib import Path

import paho.mqtt.client as mqtt

from factorypulse.db import connect, insert_audio_chunk, insert_sensor_sample
from factorypulse.models import SensorSample
from factorypulse.settings import get_settings

logger = logging.getLogger(__name__)

TOPIC_SENSORS = "factorypulse/sensors"
TOPIC_AUDIO = "factorypulse/audio"


class IngestionConsumer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._stop = False
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="fp-ingest")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: object,
        flags: object,
        reason_code: object,
        properties: object = None,
    ) -> None:
        logger.info("connected to MQTT reason=%s", reason_code)
        client.subscribe([(TOPIC_SENSORS, 0), (TOPIC_AUDIO, 0)])

    def _on_message(self, client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if msg.topic == TOPIC_SENSORS:
                self._handle_sensor(payload)
            elif msg.topic == TOPIC_AUDIO:
                self._handle_audio(payload)
        except Exception:
            logger.exception("failed to handle message topic=%s", msg.topic)

    def _handle_sensor(self, payload: dict) -> None:
        sample = SensorSample.model_validate(payload)
        with connect() as conn:
            insert_sensor_sample(conn, sample)
            conn.commit()

    def _handle_audio(self, payload: dict) -> None:
        src = Path(str(payload["path"]))
        machine = str(payload["machine"])
        dest_dir = Path(self.settings.audio_chunk_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%f")
        dest = dest_dir / f"{machine}_{stamp}.wav"
        if src.exists():
            shutil.copy2(src, dest)
        else:
            logger.warning("audio path missing: %s", src)
            return
        with connect() as conn:
            insert_audio_chunk(
                conn,
                machine=machine,
                path=str(dest),
                label=payload.get("label"),
                fault_tag=payload.get("fault_tag"),
            )
            conn.commit()

    def request_stop(self, *_args: object) -> None:
        self._stop = True

    def run(self, duration_s: int | None = None) -> None:
        signal.signal(signal.SIGINT, self.request_stop)
        signal.signal(signal.SIGTERM, self.request_stop)
        self.client.connect(self.settings.mqtt_broker, self.settings.mqtt_port, keepalive=30)
        self.client.loop_start()
        started = time.time()
        logger.info("ingestion running")
        try:
            while not self._stop:
                if duration_s is not None and (time.time() - started) >= duration_s:
                    break
                time.sleep(0.2)
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("ingestion stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="FactoryPulse MQTT ingestion consumer")
    parser.add_argument("--duration", type=int, default=None, help="optional run limit in seconds")
    args = parser.parse_args()
    settings = get_settings()
    logging.basicConfig(level=settings.fp_log_level)
    IngestionConsumer().run(duration_s=args.duration)


if __name__ == "__main__":
    main()
