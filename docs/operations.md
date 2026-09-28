# Operations

## Runtime

| Endpoint | Meaning |
| --- | --- |
| `GET /health` | Process is alive; does not imply a usable model |
| `GET /ready` | 200 with model version when loaded; 503 if missing/corrupt |
| `GET /v1/model` | Version, feature names, catalog size, training metadata |
| `POST /v1/recommendations` | Validated preference request and ranked tracks |
| `GET /metrics` | Prometheus HTTP counters/latency and request mood counts |
| `GET /docs` | OpenAPI interactive docs |

`MODEL_PATH` defaults to `artifacts/model.json`. `CORS_ORIGINS` is a comma-separated allowlist, default
`http://localhost:5173`. Environment variables must be exported by the shell or supplied by Compose;
the root `.env.example` is documentation, not an automatic dotenv loader. UI `VITE_API_URL` is a
build-time setting; Vite reads `.env.local` in its frontend directory.

The model loads once during application lifespan. Failed loading leaves liveness available but
readiness and inference return 503. Fix the artifact and restart; there is no hot reload. Inference
uses synchronous FastAPI handlers (thread pool), immutable model data, and the same features as
training. HTTP metric labels use route templates, not arbitrary request paths, to bound cardinality.
The intended runtime is one Uvicorn worker per instance. Multi-worker metrics need additional setup.

Prometheus examples:

```promql
histogram_quantile(0.95, sum by (le) (rate(music_http_duration_seconds_bucket{route="/v1/recommendations"}[5m])))
sum(rate(music_http_requests_total{status=~"5.."}[5m])) / sum(rate(music_http_requests_total[5m]))
```

These are suggested queries, not a deployed Prometheus service or established production SLOs.
Use `/ready` for routing traffic. Keep metadata/metrics endpoints on a trusted network before a public
deployment; the demo has no authentication. No raw request history is persisted by the API.

## Candidate promotion and rollback

1. Train into a new directory: `uv run python -m music_ml.cli train --output-dir artifacts/candidate`.
2. Review its `metrics.json`, data provenance, and `model.json` together. A failed candidate emits
   metrics and leaves any existing model untouched, so do not assume every file in a reused output
   directory belongs to the failed run. Compare report/model versions.
3. Copy the approved model to a versioned deployment path, set `MODEL_PATH`, restart, and smoke-test.
4. Roll back by selecting the previous trusted artifact path and restarting. No online updates occur.

The Docker image contains a generated demo model. To try a different artifact, mount a read-only model
file and set `MODEL_PATH` to its container path. GitHub training artifacts are candidates only; nothing
is uploaded to an external registry or automatically promoted to a live service.

## Offline drift check

Prepare one mood observation per request in JSONL, for example `{"mood":"calm"}`. Observations must
come from your own aggregation/export; the demo does not implement a traffic log collector. Then:

```sh
uv run python -m music_ml.cli drift --model artifacts/model.json --observations requests.jsonl
```

The command compares observed mood frequencies with the training reference using population stability
index (PSI), requiring at least 100 observations. It returns exit code 2 above the demo threshold 0.2,
0 otherwise, and fails on malformed/insufficient input. This detects only mood mix changes, not
energy/valence override drift, label drift, model degradation, or fairness issues. Investigate before
retraining; a PSI alert alone is not evidence that a new model improves recommendations.

## Automation references

Actions are pinned to verified upstream commit hashes, with Dependabot managing updates.
Workflows use read-only repository permissions except CodeQL's scoped security-event write permission,
avoid privileged pull-request triggers, and disable persisted checkout credentials. See
[GitHub's workflow security guidance](https://docs.github.com/en/actions/reference/security/secure-use).
The API uses [FastAPI lifespan loading](https://fastapi.tiangolo.com/advanced/events/).
The portable linear-model export avoids executable pickle artifacts; see
[scikit-learn model persistence considerations](https://scikit-learn.org/stable/model_persistence.html).
