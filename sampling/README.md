# Sampling

Stratified sample selection from the `cleaned` table. Produces a `samples` table of selected event IDs that `judge.py` scores instead of all of `cleaned`.

---

## Pipeline Position

```
dataset.py → preprocess.py → sample.py → judge.py
```

`sample.py` (repo root) is the entry point. It delegates to `sampling/pipeline.py`, which reads from `cleaned`, runs the stratified sampler, and writes to `samples` — all within the same `events.db`.

**Why here and not earlier:** Sampling must happen after preprocessing because the `cleaned` table is the source of truth for what is scoreable. Raw events in `events` may contain bots, empty text, or duplicate IDs that preprocessing removes. Drawing a sample from `cleaned` guarantees every selected row is ready for the judge.

---

## Module Structure

```
sampling/
├── __init__.py
├── README.md       ← you are here; read before modifying
├── sampler.py      ← stratified sampling logic and seed derivation
├── storage.py      ← samples table schema, CREATE TABLE, insert/query helpers
└── pipeline.py     ← orchestration: find DB, call sampler, write results
```

`sample.py` at the repo root is the thin CLI entry point (mirrors `preprocess.py`).

---

## Stratification Strategy

Strata are defined as **`repo × event_type`** cells. With 10 repos and 4 event types, there are up to 40 strata.

**Per-stratum floor and cap** (from [CONFORMITY.md](../docs/notes/CONFORMITY.md#stratified-sampling)):

| Parameter | Value |
|-----------|-------|
| Minimum per cell (floor) | 25 comments |
| Maximum per cell (cap) | 50 comments |
| If cell has fewer than 25 available | take all available |

**Rough totals:**
- 4 event types × 50 cap = 200 comments per repo (ceiling)
- 10 repos × 200 = 2,000 comments total (ceiling)
- Realized total will be lower because sparse strata (e.g. `PullRequestReviewEvent` in `gin-gonic/gin` or `pallets/flask`) cannot reach the cap.

---

## Determinism Design

**The sample is fully deterministic.** Given the same `cleaned` table contents, running `sample.py` twice produces the exact same set of selected IDs in the exact same order. No randomness is introduced at runtime. This is achieved through three interlocking guarantees:

1. **Fixed seed per stratum.** Each `repo × event_type` cell is shuffled with a `random.Random` instance seeded from a SHA-256 hash of `"{repo}|{event_type}|{BASE_SEED}"`. The same string always hashes to the same integer, so the same RNG state is reconstructed on every run.
2. **Sorted stratum iteration.** Strata are processed in sorted order, so the sequence of RNG calls is stable regardless of dict insertion order in the Python runtime.
3. **Stable input IDs.** `cleaned.id` values come from GitHub event IDs (integers assigned by GitHub), not insertion-order row numbers. Their sorted order is deterministic across runs.

The net result: **the corpus is reproducible by anyone who has the same `cleaned` table and knows `BASE_SEED`**.

### Storage: ID table, not a view, not a copy

The `samples` table stores only the **selected `id` values** (foreign keys into `cleaned`), plus stratification metadata. Full text is retrieved at query time via a JOIN.

This was chosen over two alternatives:

**Why not a SQLite view?**  
SQLite has no seeded `RANDOM()`. A view re-executes its query on every read, which means a `ORDER BY RANDOM() LIMIT 50` view would produce a different sample each time. The only way to make it deterministic is to embed hardcoded IDs in the view definition — which is functionally identical to an ID table but stored as opaque SQL text. The ID table is strictly clearer.

**Why not copying rows (materializing the full text)?**  
Duplicating `cleaned_text` and `tokens` wastes disk, creates a silent staleness problem when `preprocess.py` is re-run (the copy drifts from its source without warning), and provides no query performance benefit since judge.py already JOINs multiple tables. The ID table keeps `samples` as a pure, auditable selection manifest.

### Seeding: per-stratum, not global

Each stratum gets its own deterministic seed derived from the repo name and event type:

```python
import hashlib

BASE_SEED = 42  # change only intentionally; doing so invalidates all existing samples

def stratum_seed(repo: str, event_type: str) -> int:
    key = f"{repo}|{event_type}|{BASE_SEED}"
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**31)
```

Within each stratum: `rng = random.Random(stratum_seed(repo, event_type))`, then `rng.sample(ids, k)`.

**Why per-stratum and not a single global seed?**  
The methodology includes supplemental data for `hapijs/hapi`, `koajs/koa`, and `pallets/flask` (2022–2023 years added after 2024 data proved sparse). If sampling used a single global seed over all rows, adding data for one repo would shift the sample drawn from every other repo. Per-stratum seeding makes each stratum's sample independent: adding rows to the `hapi` × `IssueCommentEvent` stratum cannot change the `django/django` × `IssueCommentEvent` sample. This is the correct property for a reproducible corpus.

**`BASE_SEED` is a global constant in `sampler.py`.** If you change it, every existing `samples` table is invalidated and must be regenerated. Treat it as append-only: document the reason for any change in this README's Decision Log.

---

## `samples` Table Schema

Defined in `storage.py` and referenced here as the written source of truth.

```sql
CREATE TABLE IF NOT EXISTS samples (
    id          TEXT PRIMARY KEY,  -- FK → cleaned.id (and events.id)
    repo        TEXT NOT NULL,     -- e.g. "django/django"
    event_type  TEXT NOT NULL,     -- e.g. "IssueCommentEvent"
    stratum_key TEXT NOT NULL      -- "{repo}|{event_type}"; convenient for GROUP BY
);
```

**To get a full scoreable record** (what judge.py queries):

```sql
SELECT
    s.id,
    s.repo,
    s.event_type,
    c.cleaned_text,
    c.tokens,
    e.event_data
FROM samples s
INNER JOIN cleaned c ON c.id = s.id
INNER JOIN events  e ON e.id = s.id;
```

---

## How to Run

```bash
python sample.py
```

Running `sample.py` **drops and recreates** the `samples` table. This is intentional: the sample is a deterministic function of `cleaned` plus the fixed parameters above, so re-running is always safe and idempotent. If you need to inspect what was sampled previously, query `samples` before re-running.

---

## Making Changes: Rules

1. **Changing `BASE_SEED`:** Document the reason in the Decision Log below. Any existing `samples` table must be regenerated. Coordinate with anyone who has already scored rows from the old sample.
2. **Changing floor/cap numbers:** Update both `sampler.py` and the table in [CONFORMITY.md](../docs/notes/CONFORMITY.md#stratified-sampling) to stay in sync with the paper's methodology section.
3. **Changing the `samples` schema:** Update `storage.py` *and* the schema block above. The judge's query (in `judge/`) will need updating too.
4. **Adding a new event type:** Add it to `DEFAULT_EVENT_TYPES` in `dataset_readers/gharchive/config.py` and to the `EventType` enum in `dataset_readers/gharchive/models.py`. The judge handles prompt selection independently.
5. **Do not add `cleaned_text` or `tokens` to `samples`:** See the storage rationale above.

---

## Decision Log

### 2026-05-27 — ID table chosen over view and materialized copy; per-stratum seeding chosen over global

Initial design. Decisions recorded above in [Determinism Design](#determinism-design). `BASE_SEED = 42`.
