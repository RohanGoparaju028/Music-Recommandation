# Local validation record

Run on 2026-09-28 with Python 3.12.13, seed 42, and the committed dependency locks.

| Check | Result |
| --- | --- |
| Python tests | 17 passed; 96.90% statement coverage |
| Ruff lint and formatting | Passed |
| Data validation | 60 tracks; 14,400 interactions |
| Held-out model NDCG@10 | 0.907143 |
| Held-out popularity NDCG@10 | 0.316781 |
| Held-out model Recall@10 | 0.555851 |
| Train / validation / test queries | 144 / 48 / 48 |
| Quality gate | Passed |
| Live Uvicorn readiness + recommendation smoke test | Passed |
| Frontend ESLint + TypeScript / Vite build | Passed in a temporary copy without `#` in its path |
| GitHub workflow syntax (actionlint 1.7.7) | Passed |
| Python runtime vulnerability audit | No known vulnerabilities reported |
| npm dependency audit | No vulnerabilities reported |

Metrics are synthetic fixture results, not real listener outcomes. The tests also verify export
parity with scikit-learn, deterministic retraining within the environment, temporal query separation,
artifact corruption rejection, failed-quality-gate preservation, concurrent inference, missing model
readiness, request validation, and drift detection.

Python 3.11/3.13, Docker image startup and CodeQL are configured in CI but were not executed locally.
Docker's client was present but its daemon was stopped. GitHub workflows run on pushes; see the repository Actions tab for current results.
The installed Starlette release emits a non-failing deprecation warning for its HTTPX-based test client.
