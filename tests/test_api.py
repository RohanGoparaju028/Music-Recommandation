from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from music_ml.api import create_app


def test_serving_contract(trained):
    directory, _ = trained
    with TestClient(create_app(directory / "artifacts/model.json")) as client:
        assert client.get("/ready").status_code == 200
        response = client.post("/v1/recommendations", json={"mood": "calm", "k": 5})
        assert response.status_code == 200
        data = response.json()
        tracks = data["recommendations"]
        assert len(tracks) == 5
        assert [t["score"] for t in tracks] == sorted([t["score"] for t in tracks], reverse=True)
        assert data["model_version"] == client.get("/v1/model").json()["model_version"]
        excluded = client.post(
            "/v1/recommendations",
            json={"mood": "calm", "exclude_track_ids": [tracks[0]["track_id"]]},
        ).json()
        assert tracks[0]["track_id"] not in [t["track_id"] for t in excluded["recommendations"]]
        assert 'music_recommendations_total{mood="calm"}' in client.get("/metrics").text
        for body in [{"mood": "unknown"}, {"k": 0}, {"energy": 2}, {"extra": 1}]:
            assert client.post("/v1/recommendations", json=body).status_code == 422
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(
                pool.map(
                    lambda _: client.post(
                        "/v1/recommendations", json={"mood": "calm", "k": 5}
                    ).json(),
                    range(12),
                )
            )
        assert all(result == data for result in results)


def test_missing_and_corrupt_models_are_not_ready(tmp_path):
    path = tmp_path / "model.json"
    for contents in [None, '{"bad": true}']:
        if contents:
            path.write_text(contents)
        with TestClient(create_app(path)) as client:
            assert client.get("/health").status_code == 200
            assert client.get("/ready").status_code == 503
            assert client.post("/v1/recommendations", json={}).status_code == 503
