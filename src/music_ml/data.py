"""Validated data contracts and explicitly synthetic, deterministic demo data."""

import csv
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

MOODS = {"happy": (0.8, 0.8), "calm": (0.25, 0.65), "sad": (0.3, 0.25), "energetic": (0.95, 0.6)}


class Track(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    track_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    artist: str = Field(min_length=1, max_length=200)
    energy: float = Field(ge=0, le=1)
    valence: float = Field(ge=0, le=1)
    danceability: float = Field(ge=0, le=1)
    popularity: float = Field(ge=0, le=1)


class Interaction(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    query_id: int = Field(ge=0)
    timestamp: int = Field(ge=0)
    mood: str
    energy: float = Field(ge=0, le=1)
    valence: float = Field(ge=0, le=1)
    track_id: str
    relevant: int = Field(ge=0, le=1)


def load_data(directory: Path) -> tuple[list[Track], list[Interaction]]:
    with (directory / "tracks.csv").open() as file:
        tracks = [Track.model_validate(row) for row in csv.DictReader(file)]
    with (directory / "interactions.csv").open() as file:
        rows = [Interaction.model_validate(row) for row in csv.DictReader(file)]
    ids = {track.track_id for track in tracks}
    if len(ids) != len(tracks) or len(tracks) < 10:
        raise ValueError("Catalog needs at least 10 unique tracks")
    seen = set()
    queries = {}
    for row in rows:
        key = (row.query_id, row.track_id)
        context = (row.timestamp, row.mood, row.energy, row.valence)
        if row.track_id not in ids or row.mood not in MOODS or key in seen:
            raise ValueError("Unknown track/mood or duplicate query-track interaction")
        if row.query_id in queries and queries[row.query_id] != context:
            raise ValueError("A query must have one timestamp and preference context")
        queries[row.query_id] = context
        seen.add(key)
    if len(queries) < 20 or len({r.relevant for r in rows}) != 2:
        raise ValueError("Need at least 20 queries and both relevance labels")
    return tracks, rows


def generate(directory: Path, seed: int = 42, queries: int = 240) -> None:
    """Generate fictional tracks and noisy preference labels, never real user observations."""
    directory.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    tracks = [
        Track(
            track_id=f"track-{i:03}",
            title=f"Demo Session {i + 1:02}",
            artist=f"Synthetic Artist {i % 12 + 1}",
            energy=float(rng.random()),
            valence=float(rng.random()),
            danceability=float(rng.random()),
            popularity=float(rng.random()),
        )
        for i in range(60)
    ]
    rows = []
    for query in range(queries):
        mood = list(MOODS)[query % len(MOODS)]
        energy, valence = np.clip(np.array(MOODS[mood]) + rng.normal(0, 0.13, 2), 0, 1)
        for track in tracks:
            utility = (
                2.8
                - 5 * abs(track.energy - energy)
                - 4 * abs(track.valence - valence)
                + 0.35 * track.danceability
                + rng.normal(0, 0.65)
            )
            rows.append(
                Interaction(
                    query_id=query,
                    timestamp=1700000000 + query * 3600,
                    mood=mood,
                    energy=float(energy),
                    valence=float(valence),
                    track_id=track.track_id,
                    relevant=int(utility > 1.1),
                )
            )
    for name, records in [("tracks.csv", tracks), ("interactions.csv", rows)]:
        with (directory / name).open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(records[0].model_dump()))
            writer.writeheader()
            writer.writerows(record.model_dump() for record in records)
