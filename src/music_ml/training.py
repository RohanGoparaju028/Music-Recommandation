"""Temporal query splits, validation-only selection, and held-out ranking evaluation."""

import hashlib
import json
import platform
from collections import defaultdict
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from music_ml.data import MOODS, Interaction, load_data
from music_ml.features import FEATURE_NAMES, features
from music_ml.model import Artifact, Ranker, version_for


def split_queries(rows):
    timestamps = {r.query_id: r.timestamp for r in rows}
    times = sorted(set(timestamps.values()))
    if len(times) < 10:
        raise ValueError("Need at least 10 distinct timestamps for temporal evaluation")
    first, second = times[int(len(times) * 0.6)], times[int(len(times) * 0.8)]
    return (
        [r for r in rows if r.timestamp < first],
        [r for r in rows if first <= r.timestamp < second],
        [r for r in rows if r.timestamp >= second],
    )


def evaluate(rows: list[Interaction], tracks, score_fn, k=10):
    catalog = {t.track_id: t for t in tracks}
    groups = defaultdict(list)
    for row in rows:
        groups[row.query_id].append(row)
    values = []
    for group in groups.values():
        candidates = [catalog[r.track_id] for r in group]
        labels = np.array([r.relevant for r in group])
        if labels.sum() == 0:
            continue
        scores = score_fn(candidates, group[0].energy, group[0].valence)
        order = np.argsort(-scores, kind="stable")[:k]
        discounts = 1 / np.log2(np.arange(len(order)) + 2)
        ideal = np.sort(labels)[::-1][:k] @ discounts
        values.append(
            (float(labels[order] @ discounts / ideal), float(labels[order].sum() / labels.sum()))
        )
    if not values:
        raise ValueError("Evaluation needs queries with relevant items")
    return {
        "ndcg_at_10": float(np.mean([v[0] for v in values])),
        "recall_at_10": float(np.mean([v[1] for v in values])),
        "evaluated_queries": len(values),
        "skipped_queries": len(groups) - len(values),
    }


def train(directory: Path, output: Path, seed: int = 42) -> dict:
    tracks, rows = load_data(directory)
    training, validation, test = split_queries(rows)
    catalog = {t.track_id: t for t in tracks}
    x = np.vstack([features([catalog[r.track_id]], r.energy, r.valence) for r in training])
    y = np.array([r.relevant for r in training])
    if len(set(y)) != 2:
        raise ValueError("Training split must contain both relevance classes")
    candidates = []
    for c in [0.1, 1.0, 10.0]:
        pipeline = make_pipeline(StandardScaler(), LogisticRegression(C=c, random_state=seed))
        pipeline.fit(x, y)
        metrics = evaluate(
            validation,
            tracks,
            lambda ts, e, v, model=pipeline: model.predict_proba(features(ts, e, v))[:, 1],
        )
        candidates.append((metrics["ndcg_at_10"], c, pipeline))
    _, selected_c, pipeline = max(candidates, key=lambda item: item[0])
    scaler, estimator = pipeline.steps[0][1], pipeline.steps[1][1]
    digest = hashlib.sha256()
    for name in ["tracks.csv", "interactions.csv"]:
        digest.update((directory / name).read_bytes())
    payload = dict(
        schema_version=1,
        feature_names=FEATURE_NAMES,
        mean=scaler.mean_.tolist(),
        scale=scaler.scale_.tolist(),
        coefficients=estimator.coef_[0].tolist(),
        intercept=float(estimator.intercept_[0]),
        tracks=[t.model_dump() for t in tracks],
        metadata={
            "seed": seed,
            "selected_c": selected_c,
            "data_sha256": digest.hexdigest(),
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "training_rows": len(training),
            "reference_moods": {
                m: sum(r.mood == m for r in training) / len(training) for m in MOODS
            },
        },
    )
    payload["model_version"] = version_for(payload)
    ranker = Ranker(Artifact.model_validate(payload))
    metrics = evaluate(test, tracks, ranker.scores)
    baseline = evaluate(test, tracks, lambda ts, e, v: np.array([t.popularity for t in ts]))
    # All thresholds are fixed before looking at the test split. Never tune on test results.
    passed = (
        metrics["ndcg_at_10"] >= 0.65 and metrics["ndcg_at_10"] >= baseline["ndcg_at_10"] + 0.02
    )
    report = {
        "model_version": payload["model_version"],
        "test": metrics,
        "baseline": baseline,
        "gate_passed": passed,
        "thresholds": {"min_ndcg": 0.65, "min_baseline_lift": 0.02},
        "validation_trials": [{"c": c, "ndcg_at_10": score} for score, c, _ in candidates],
        "split_queries": [
            len({r.query_id for r in split}) for split in (training, validation, test)
        ],
        "test_by_mood": {
            m: evaluate([r for r in test if r.mood == m], tracks, ranker.scores)
            for m in MOODS
            if any(r.mood == m for r in test)
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    if not passed:
        raise ValueError("Quality gate failed; metrics written, model not published")
    # A failed candidate never overwrites an existing serving model.
    temporary = output / "model.json.tmp"
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(output / "model.json")
    return report
