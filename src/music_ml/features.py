"""One feature implementation shared by training and inference."""

import numpy as np

from music_ml.data import Track

FEATURE_NAMES = ["energy_distance", "valence_distance", "danceability", "popularity"]


def features(tracks: list[Track], energy: float, valence: float) -> np.ndarray:
    return np.array(
        [
            [
                abs(track.energy - energy),
                abs(track.valence - valence),
                track.danceability,
                track.popularity,
            ]
            for track in tracks
        ],
        dtype=float,
    )
