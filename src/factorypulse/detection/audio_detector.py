"""Log-mel + gradient boosting audio anomaly detector (M1 baseline)."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from factorypulse.models import AnomalyEvent, DetectorSource, Severity


def _read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        frames = wf.readframes(n)
        width = wf.getsampwidth()
        channels = wf.getnchannels()
    if width != 2:
        raise ValueError(f"unsupported sample width: {width}")
    data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, sr


def logmel_features(audio: np.ndarray, sr: int, n_mels: int = 32) -> np.ndarray:
    if audio.size == 0:
        return np.zeros(n_mels * 4, dtype=np.float32)
    frame = 512
    hop = 256
    if audio.size < frame:
        audio = np.pad(audio, (0, frame - audio.size))
    n_frames = 1 + (audio.size - frame) // hop
    window = np.hanning(frame).astype(np.float32)
    specs = []
    for i in range(min(n_frames, 64)):
        start = i * hop
        chunk = audio[start : start + frame] * window
        spectrum = np.abs(np.fft.rfft(chunk)) ** 2
        specs.append(spectrum)
    spec = np.stack(specs, axis=0)
    freqs = np.linspace(0, sr / 2, spec.shape[1])
    edges = np.geomspace(max(freqs[1], 1.0), max(freqs[-1], 2.0), n_mels + 1)
    mel = np.zeros((spec.shape[0], n_mels), dtype=np.float32)
    for b in range(n_mels):
        mask = (freqs >= edges[b]) & (freqs < edges[b + 1])
        if not np.any(mask):
            continue
        mel[:, b] = spec[:, mask].mean(axis=1)
    logmel = np.log(mel + 1e-8)
    stats = np.concatenate(
        [
            logmel.mean(axis=0),
            logmel.std(axis=0),
            logmel.max(axis=0),
            np.percentile(logmel, 90, axis=0),
        ]
    ).astype(np.float32)
    return stats


def synthesize_training_set(seed: int = 42, n_per_class: int = 40) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    xs: list[np.ndarray] = []
    ys: list[int] = []
    sr = 16000
    for label in (0, 1):
        for _i in range(n_per_class):
            t = np.linspace(0, 1.0, sr, endpoint=False)
            base = 0.15 * np.sin(2 * np.pi * 120 * t)
            noise = 0.05 * rng.standard_normal(sr)
            if label == 1:
                base += 0.25 * np.sin(2 * np.pi * 780 * t)
                noise *= 3.0
            audio = (base + noise).astype(np.float32)
            xs.append(logmel_features(audio, sr))
            ys.append(label)
    return np.stack(xs), np.asarray(ys, dtype=np.int64)


class AudioAnomalyDetector:
    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.model = GradientBoostingClassifier(random_state=seed)
        self._fitted = False

    def fit_default(self) -> None:
        x, y = synthesize_training_set(seed=self.seed)
        self.model.fit(x, y)
        self._fitted = True

    def ensure_fitted(self) -> None:
        if not self._fitted:
            self.fit_default()

    def predict_path(self, path: Path, machine: str = "centrifugal_pump") -> AnomalyEvent | None:
        self.ensure_fitted()
        audio, sr = _read_wav_mono(path)
        feats = logmel_features(audio, sr).reshape(1, -1)
        proba = float(self.model.predict_proba(feats)[0, 1])
        if proba < 0.65:
            return None
        severity = Severity.fault if proba >= 0.80 else Severity.warn
        return AnomalyEvent(
            machine=machine,
            source=DetectorSource.audio,
            severity=severity,
            fault_code="E-AUDIO",
            score=proba,
            summary="Audio classifier flagged anomalous machine sound",
            evidence={"path": str(path), "proba": proba},
        )
