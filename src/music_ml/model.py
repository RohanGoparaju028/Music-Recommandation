"""Portable JSON model artifacts: no executable pickle deserialization."""

import hashlib
import json
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from music_ml.data import Track
from music_ml.features import FEATURE_NAMES, features


class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: int = 1
    model_version: str
    feature_names: list[str]
    mean: list[float]
    scale: list[float]
    coefficients: list[float]
    intercept: float
    tracks: list[Track] = Field(min_length=10)
    metadata: dict

    @model_validator(mode="after")
    def check_contract(self):
        if self.schema_version != 1 or self.feature_names != FEATURE_NAMES:
            raise ValueError("Unsupported artifact feature/schema version")
        if any(
            len(v) != len(FEATURE_NAMES) for v in [self.mean, self.scale, self.coefficients]
        ) or any(s <= 0 for s in self.scale):
            raise ValueError("Invalid model dimensions or scale")
        if len({t.track_id for t in self.tracks}) != len(self.tracks):
            raise ValueError("Duplicate tracks in artifact")
        return self


def version_for(payload: dict) -> str:
    content = {k: v for k, v in payload.items() if k != "model_version"}
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:16]


class Ranker:
    def __init__(self, artifact: Artifact):
        self.artifact = artifact

    @classmethod
    def load(cls, path: Path):
        artifact = Artifact.model_validate_json(path.read_text())
        if artifact.model_version != version_for(artifact.model_dump()):
            raise ValueError("Artifact content hash mismatch")
        return cls(artifact)

    def scores(self, tracks: list[Track], energy: float, valence: float) -> np.ndarray:
        a = self.artifact
        logits = ((features(tracks, energy, valence) - a.mean) / a.scale) @ np.array(
            a.coefficients
        ) + a.intercept
        return 1 / (1 + np.exp(-np.clip(logits, -40, 40)))

    def recommend(self, energy: float, valence: float, k: int, exclude: list[str]) -> list[dict]:
        tracks = [t for t in self.artifact.tracks if t.track_id not in set(exclude)]
        if not tracks:
            return []
        scores = self.scores(tracks, energy, valence)
        order = np.argsort(-scores, kind="stable")[:k]
        return [{**tracks[i].model_dump(), "score": round(float(scores[i]), 6)} for i in order]
