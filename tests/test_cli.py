import json
import sys

import pytest

from music_ml.cli import main


def test_cli_pipeline_and_drift_exit_codes(tmp_path, monkeypatch, capsys):
    data = tmp_path / "data"
    output = tmp_path / "model"

    def invoke(*args):
        monkeypatch.setattr(sys, "argv", ["music-ml", *map(str, args)])
        main()
        return capsys.readouterr().out

    invoke("generate", "--data-dir", data)
    validated = json.loads(invoke("validate", "--data-dir", data))
    assert validated == {"tracks": 60, "interactions": 14400}
    report = json.loads(invoke("train", "--data-dir", data, "--output-dir", output))
    assert report["gate_passed"]
    observations = tmp_path / "observations.jsonl"
    observations.write_text("\n".join('{"mood":"sad"}' for _ in range(100)))
    with pytest.raises(SystemExit) as error:
        invoke("drift", "--model", output / "model.json", "--observations", observations)
    assert error.value.code == 2
