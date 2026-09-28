# Model card: synthetic preference ranker

**Purpose:** demonstrate reproducible training, offline evaluation, export, serving, and monitoring.
**Model:** StandardScaler + L2 logistic regression, C selected from 0.1 / 1 / 10 using validation
NDCG@10. At inference, sigmoid scores rank tracks by predicted binary relevance.
**Features:** absolute energy distance, absolute valence distance, danceability, popularity.
**Data:** 60 fictional tracks and 240 synthetic query contexts with complete candidate labels.
No human behavioral, facial, biometric, or Spotify data is included.

Training, validation and test use a 60/20/20 time split by distinct query timestamps. The training
partition alone fits scaler and coefficients. The selected model is not refitted on test data.
Held-out NDCG@10 / Recall@10 and mood slices are written to `artifacts/metrics.json` alongside the
popularity baseline. The API reports the artifact version; it does not load metrics from another run.

The demo's label-generating function is aligned with model features; high scores show the pipeline
learns the designed relationship, not that listeners will prefer the recommendations. Popularity is
random in the fixture and is intentionally a weak comparison. A real experiment needs stronger
baselines (content similarity, collaborative filtering), calibrated labels, confidence intervals,
coverage/diversity measures, popularity bias analysis, and an online experiment before product claims.

No persistent user history or collaborative signal is modeled. Mood is a user-selected preference,
not a diagnosis or a claim about internal emotional state. The UI is a catalog-ranking demo, not a
music player. Synthetic tracks should never be presented as licensed playable audio.

Serving performs a full catalog scan, appropriate for the demo's 60 tracks. Large-scale retrieval,
feature freshness, authentication, rate limits, multi-worker metric aggregation, durable experiment
tracking and deployment automation are not implemented. The artifact bundles metadata and catalog
for consistency; an external experiment tracker/registry is a natural next step once real runs exist.

Content hashes detect accidental changes; they are not signatures or evidence that an artifact came
from an authorized producer. Load artifacts from trusted controlled storage. The server validates
artifact structure and rejects hash mismatches.
