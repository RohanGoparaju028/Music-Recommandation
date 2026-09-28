import json

import pytest

from music_ml.data import MOODS
from music_ml.drift import report_drift


def test_drift_and_small_sample_guard(trained, tmp_path):
    directory, _ = trained
    observations = tmp_path / "requests.jsonl"
    model = directory / "artifacts/model.json"
    observations.write_text("\n".join(json.dumps({"mood": m}) for m in list(MOODS) * 25))
    assert not report_drift(model, observations)["drift_detected"]
    observations.write_text("\n".join(json.dumps({"mood": "sad"}) for _ in range(100)))
    assert report_drift(model, observations)["drift_detected"]
    observations.write_text('{"mood": "sad"}')
    with pytest.raises(ValueError, match="at least"):
        report_drift(model, observations)
