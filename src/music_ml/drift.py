"""Offline categorical population stability index for observed request moods."""

import json
from collections import Counter
from pathlib import Path

import numpy as np

from music_ml.data import MOODS
from music_ml.model import Ranker


def report_drift(model: Path, observations: Path, min_samples: int = 100) -> dict:
    counts = Counter()
    for line in observations.read_text().splitlines():
        mood = json.loads(line)["mood"]
        if mood not in MOODS:
            raise ValueError(f"Unknown mood: {mood}")
        counts[mood] += 1
    n = sum(counts.values())
    if n < min_samples:
        raise ValueError(f"Need at least {min_samples} observations; got {n}")
    expected = Ranker.load(model).artifact.metadata["reference_moods"]
    # Additive smoothing avoids log(0); normalize both distributions.
    p = np.array([expected[m] for m in MOODS]) + 1e-6
    q = np.array([counts[m] / n for m in MOODS]) + 1e-6
    p, q = p / p.sum(), q / q.sum()
    psi = float(np.sum((q - p) * np.log(q / p)))
    return {
        "samples": n,
        "mood_psi": psi,
        "threshold": 0.2,
        "drift_detected": psi > 0.2,
        "observed_moods": {m: counts[m] / n for m in MOODS},
    }
