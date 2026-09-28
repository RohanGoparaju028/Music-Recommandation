"""Live HTTP smoke test for a locally running or containerized API."""

import json
import os
import time
import urllib.error
import urllib.request

base = os.getenv("API_URL", "http://localhost:8000")
for _attempt in range(30):
    try:
        with urllib.request.urlopen(f"{base}/ready", timeout=2) as response:
            assert json.load(response)["status"] == "ready"
        break
    except (urllib.error.URLError, TimeoutError):
        time.sleep(1)
else:
    raise SystemExit("API failed readiness smoke test")
request = urllib.request.Request(
    f"{base}/v1/recommendations",
    data=json.dumps({"mood": "calm", "k": 5}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=5) as response:
    result = json.load(response)
assert len(result["recommendations"]) == 5
assert result["model_version"]
print(f"Smoke test passed: model={result['model_version']}")
