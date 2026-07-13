from pathlib import Path

from factorypulse.detection.audio_detector import (
    AudioAnomalyDetector,
    synthesize_training_set,
)
from factorypulse.simulator.replay import _synth_wav


def test_logmel_feature_shape():
    x, y = synthesize_training_set(seed=0, n_per_class=2)
    assert x.shape[0] == 4
    assert x.shape[1] == 32 * 4
    assert set(y.tolist()) == {0, 1}


def test_audio_detector_flags_anomalous(tmp_path: Path):
    normal = tmp_path / "normal.wav"
    abnormal = tmp_path / "abnormal.wav"
    _synth_wav(normal, anomalous=False, seed=1)
    _synth_wav(abnormal, anomalous=True, seed=2)

    det = AudioAnomalyDetector(seed=42)
    det.fit_default()

    normal_event = det.predict_path(normal)
    abnormal_event = det.predict_path(abnormal)

    assert normal_event is None or normal_event.score < 0.85
    assert abnormal_event is not None
    assert abnormal_event.score >= 0.65
    assert abnormal_event.source.value == "audio"
