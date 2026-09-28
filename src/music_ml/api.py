"""FastAPI model serving with readiness and bounded-label Prometheus metrics."""

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, ConfigDict, Field

from music_ml.data import MOODS
from music_ml.model import Ranker

logger = logging.getLogger(__name__)


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    mood: Literal["happy", "calm", "sad", "energetic"] = "happy"
    energy: float | None = Field(default=None, ge=0, le=1)
    valence: float | None = Field(default=None, ge=0, le=1)
    k: int = Field(default=10, ge=1, le=50)
    exclude_track_ids: list[str] = Field(default_factory=list, max_length=100)


def create_app(model_path: Path | None = None) -> FastAPI:
    path = model_path or Path(os.getenv("MODEL_PATH", "artifacts/model.json"))
    registry = CollectorRegistry()
    requests = Counter(
        "music_http_requests_total", "HTTP responses", ["route", "status"], registry=registry
    )
    latency = Histogram("music_http_duration_seconds", "HTTP latency", ["route"], registry=registry)
    moods = Counter(
        "music_recommendations_total",
        "Recommendation requests by mood",
        ["mood"],
        registry=registry,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.ranker = None
        try:
            app.state.ranker = Ranker.load(path)
        except (OSError, ValueError):
            logger.exception("Model unavailable; readiness will return 503")
        yield

    app = FastAPI(title="Music ML Ranking API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def observe(request: Request, call_next):
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = getattr(request.scope.get("route"), "path", "unmatched")
            requests.labels(route, str(status)).inc()
            latency.labels(route).observe(time.perf_counter() - start)

    def get_ranker() -> Ranker:
        ranker = app.state.ranker
        if ranker is None:
            raise HTTPException(503, "Model unavailable. Train a model and restart the service.")
        return ranker

    @app.get("/health")
    def health():
        return {"status": "alive"}

    @app.get("/ready")
    def ready():
        return {"status": "ready", "model_version": get_ranker().artifact.model_version}

    @app.get("/v1/model")
    def model():
        artifact = get_ranker().artifact
        return {
            "model_version": artifact.model_version,
            "features": artifact.feature_names,
            "catalog_size": len(artifact.tracks),
            "metadata": artifact.metadata,
        }

    @app.post("/v1/recommendations")
    def recommend(body: RecommendationRequest):
        ranker = get_ranker()
        default_energy, default_valence = MOODS[body.mood]
        energy = body.energy if body.energy is not None else default_energy
        valence = body.valence if body.valence is not None else default_valence
        recommendations = ranker.recommend(energy, valence, body.k, body.exclude_track_ids)
        moods.labels(body.mood).inc()
        return {
            "model_version": ranker.artifact.model_version,
            "mood": body.mood,
            "preferences": {"energy": energy, "valence": valence},
            "recommendations": recommendations,
        }

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})

    return app


app = create_app()
