# Data contract and real-data integration

The default generator writes 60 fictional tracks and 240 sessions (14,400 candidate observations)
to `data/generated/`. All candidates are labeled per synthetic session. Mood-conditioned preferences
are sampled with noise; relevance is generated from energy/valence distances, danceability, and noise.
This makes the task intentionally learnable. Seeds default to 42.

`tracks.csv`:

| Column | Contract |
| --- | --- |
| track_id | Unique non-empty string |
| title, artist | Non-empty display strings; fictional in demo |
| energy, valence, danceability, popularity | Finite numeric values in [0, 1] |

`interactions.csv`:

| Column | Contract |
| --- | --- |
| query_id | Nonnegative session/request integer |
| timestamp | Nonnegative Unix seconds; same for all candidates in a query |
| mood | happy, calm, sad, or energetic |
| energy, valence | Preference context in [0, 1]; same within a query |
| track_id | Must exist in catalog; at most once per query |
| relevant | Binary label, 0 or 1 |

At least 10 tracks, 20 queries, 10 distinct timestamps and both label classes are required. Both label
classes must occur in the training split. Extra columns, NaN, infinity, inconsistent contexts, unknown
tracks and duplicate observations are rejected. Run:

```sh
uv run python -m music_ml.cli validate --data-dir /path/to/data
uv run python -m music_ml.cli train --data-dir /path/to/data --output-dir artifacts/candidate
```

For real data, obtain a legally usable catalog and consented impression logs, define relevance (for
example a completed listen), and export this schema through a separate ingestion job. Log which items
were actually shown. An unseen item is not automatically a negative. Preserve candidate sets per query
so ranking evaluation reflects the retrieval stage. The evaluator ranks the supplied candidates, which
can differ from full-catalog serving for real data; report candidate coverage and sampling methodology.

The current catalog is a single static snapshot. With real data, use feature values as of the query
and train cutoff, especially popularity; future catalog aggregates can leak test behavior. The current
split separates queries in time, not listeners (there are no listener identifiers). For personalization,
add user-aware leakage controls and report both returning-user and unseen-user performance. Keep one
final test window untouched during iteration. Validate rights and provenance separately: the parser
checks structure, not consent or licensing. Store no direct listener identifiers in this demo format.
