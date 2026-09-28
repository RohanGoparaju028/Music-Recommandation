import json

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from music_ml.data import Track, generate, load_data
from music_ml.features import features
from music_ml.model import Ranker
from music_ml.training import evaluate, split_queries, train


def test_temporal_splits_and_quality(trained):
    directory, report = trained
    _, rows = load_data(directory / "data")
    splits = split_queries(rows)
    for earlier, later in zip(splits, splits[1:], strict=False):
        assert max(r.timestamp for r in earlier) < min(r.timestamp for r in later)
        assert not {r.query_id for r in earlier} & {r.query_id for r in later}
    assert report["gate_passed"]
    assert report["test"]["ndcg_at_10"] > report["baseline"]["ndcg_at_10"] + 0.02
    assert set(report["test_by_mood"]) == {"happy", "sad", "calm", "energetic"}


def test_reproducible_training_and_export_parity(trained, tmp_path):
    directory, original = trained
    report = train(directory / "data", tmp_path)
    assert report == original
    ranker = Ranker.load(tmp_path / "model.json")
    tracks, rows = load_data(directory / "data")
    training, _, _ = split_queries(rows)
    catalog = {t.track_id: t for t in tracks}
    x = np.vstack([features([catalog[r.track_id]], r.energy, r.valence) for r in training])
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=ranker.artifact.metadata["selected_c"], random_state=42),
    )
    model.fit(x, [r.relevant for r in training])
    np.testing.assert_allclose(
        ranker.scores(tracks, 0.2, 0.8),
        model.predict_proba(features(tracks, 0.2, 0.8))[:, 1],
        atol=1e-12,
    )


def test_artifact_tampering_rejected(trained, tmp_path):
    directory, _ = trained
    payload = json.loads((directory / "artifacts/model.json").read_text())
    payload["intercept"] += 1
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="hash"):
        Ranker.load(path)


def test_invalid_data_rejected(tmp_path):
    generate(tmp_path, queries=24)
    path = tmp_path / "interactions.csv"
    lines = path.read_text().splitlines()
    path.write_text("\n".join([*lines, lines[1]]) + "\n")
    with pytest.raises(ValueError, match="duplicate"):
        load_data(tmp_path)
    with pytest.raises(ValueError):
        Track(
            track_id="a",
            title="a",
            artist="a",
            energy=float("nan"),
            valence=0.5,
            danceability=0.5,
            popularity=0.5,
        )


def test_evaluation_has_known_answer(trained):
    directory, _ = trained
    tracks, rows = load_data(directory / "data")
    query = [r for r in rows if r.query_id == 0]
    labels = {r.track_id: r.relevant for r in query}
    report = evaluate(query, tracks, lambda ts, e, v: np.array([labels[t.track_id] for t in ts]))
    assert report["ndcg_at_10"] == 1.0
    assert report["recall_at_10"] == min(10, sum(labels.values())) / sum(labels.values())


def test_gate_failure_preserves_existing_model(trained, tmp_path, monkeypatch):
    import music_ml.training as training

    directory, _ = trained
    existing = tmp_path / "model.json"
    existing.write_text("previous serving model")
    monkeypatch.setattr(training, "evaluate", lambda *a, **kw: {"ndcg_at_10": 0.1})
    with pytest.raises(ValueError, match="Quality gate"):
        train(directory / "data", tmp_path)
    assert existing.read_text() == "previous serving model"
    assert not json.loads((tmp_path / "metrics.json").read_text())["gate_passed"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("feature_names", ["unknown"]),
        ("scale", [0, 1, 1, 1]),
        ("coefficients", [1]),
        ("schema_version", 2),
    ],
)
def test_incompatible_artifact_schema_rejected(trained, field, value):
    from music_ml.model import Artifact

    directory, _ = trained
    payload = json.loads((directory / "artifacts/model.json").read_text())
    payload[field] = value
    with pytest.raises(ValueError):
        Artifact.model_validate(payload)


def test_excluding_whole_catalog_returns_empty(trained):
    directory, _ = trained
    ranker = Ranker.load(directory / "artifacts/model.json")
    assert ranker.recommend(0.5, 0.5, 10, [t.track_id for t in ranker.artifact.tracks]) == []
