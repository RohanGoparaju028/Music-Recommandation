import io
import json
import runpy
from unittest.mock import patch

import pytest


def test_smoke_retries_container_startup_reset():
    responses = [
        ConnectionResetError("Container is starting"),
        io.BytesIO(b'{"status":"ready"}'),
        io.BytesIO(json.dumps({"recommendations": [{}] * 5, "model_version": "test"}).encode()),
    ]
    with patch("urllib.request.urlopen", side_effect=responses) as request:
        with patch("time.sleep") as sleep:
            runpy.run_path("scripts/smoke.py", run_name="__main__")
    assert request.call_count == 3
    sleep.assert_called_once_with(1)


def test_smoke_fails_when_service_never_becomes_ready():
    with patch("urllib.request.urlopen", side_effect=ConnectionResetError("Not ready")):
        with patch("time.sleep") as sleep:
            with pytest.raises(SystemExit, match="failed readiness"):
                runpy.run_path("scripts/smoke.py", run_name="__main__")
    assert sleep.call_count == 30
