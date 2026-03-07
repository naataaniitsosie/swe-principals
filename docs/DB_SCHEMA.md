# Database schema

Single SQLite database: **`data/raw/events.db`** by default (see `project_config.py`).

---

## Overview

| Table     | Written by       | Purpose |
|-----------|------------------|---------|
| **events**  | `dataset.py`     | Raw GitHub events from GHArchive. |
| **cleaned** | `preprocess.py`  | Preprocessed comment text only (slim records). |
| **scores**  | `judge.py`       | LLM judge output: NSI/ISI scores per comment and model. |

---

## Table: `events`

Raw events. One row per GitHub event.

| Column       | Type | Description |
|--------------|------|-------------|
| `id`         | TEXT | Primary key. GitHub event id. |
| `event_data` | TEXT | Full event as JSON. |

### `event_data` JSON (raw GitHub event)

Top-level fields (GHArchive / GitHub API shape):

| Field         | Type   | Description |
|---------------|--------|-------------|
| `id`          | string | Event id (same as table `id`). |
| `type`        | string | One of: `PullRequestEvent`, `PullRequestReviewEvent`, `PullRequestReviewCommentEvent`, `IssueCommentEvent`. |
| `actor`       | object | User who triggered the event. `id`, `login`, `display_login`. |
| `repo`        | object | Repository. `name` is `owner/repo` (e.g. `django/django`). |
| `created_at`  | string | ISO 8601 timestamp. |
| `payload`     | object | Event-specific data (see below). |

**Payload by event type:**

- **PullRequestEvent:** `payload.pull_request` — PR metadata (title, body, state, etc.).
- **PullRequestReviewEvent:** `payload.review` — review body, state; may have `author_association`.
- **PullRequestReviewCommentEvent:** `payload.comment` — comment body, timestamps, `author_association`.
- **IssueCommentEvent:** `payload.comment` — same shape; PRs are issues.

Use `json_extract(event_data, '$.field')` in SQL to read fields.

---

## Table: `cleaned`

Normalized preprocessed data. One row per event that passed preprocessing. **Only derived data** is stored here; fields that exist in raw (`events`) are not duplicated. Join with `events` on `id` to get `repo`, `created_at`, `type`, `author_association`.

| Column         | Type | Description |
|----------------|------|-------------|
| `id`           | TEXT | Primary key; same as `events.id` (FK to events). |
| `cleaned_text` | TEXT | Normalized comment text (lowercased, code/images/diff stripped). |
| `tokens`       | TEXT | JSON array of word tokens (list of strings). |

**To get a full record:** `SELECT c.id, c.cleaned_text, c.tokens, e.event_data FROM cleaned c INNER JOIN events e ON e.id = c.id`. Then derive `repo`, `created_at`, `type`, `author_association` from `e.event_data` (e.g. via `preprocessing.workflow.metadata_from_raw_event`).

---

## Table: `scores`

LLM judge output. One row per **(comment_id, model_name)**.

| Column          | Type    | Description |
|-----------------|---------|-------------|
| `comment_id`    | TEXT    | Same as `id` in `cleaned`. Part of primary key. |
| `model_name`    | TEXT    | Ollama model tag (e.g. `llama3.1:8b-instruct-q8_0`, `gemma2:27b`). Part of primary key. |
| `nsi_score`     | INTEGER | NSI score 0–3 (CONFORMITY rubric). |
| `isi_score`     | INTEGER | ISI score 0–3 (CONFORMITY rubric). |
| `nsi_reasoning` | TEXT    | Model’s NSI reasoning. |
| `isi_reasoning` | TEXT    | Model’s ISI reasoning. |
| `created_at`    | TEXT    | Optional; copied from cleaned record. |

**Primary key:** `(comment_id, model_name)`.

---

## Example queries

```sql
-- Count by table
SELECT COUNT(*) FROM events;
SELECT COUNT(*) FROM cleaned;
SELECT COUNT(*) FROM scores;

-- Cleaned + events: comments per repo (repo lives in events)
SELECT json_extract(e.event_data, '$.repo.name') AS repo, COUNT(*)
FROM cleaned c INNER JOIN events e ON e.id = c.id
GROUP BY 1 ORDER BY 1;

-- Scores: per model
SELECT model_name, COUNT(*), AVG(nsi_score), AVG(isi_score) FROM scores GROUP BY model_name;

-- Join cleaned text with scores for one model (cleaned has columns, no json_extract needed)
SELECT c.id, c.cleaned_text AS text, s.nsi_score, s.isi_score
FROM cleaned c
JOIN scores s ON s.comment_id = c.id
WHERE s.model_name = 'gemma2:27b'
LIMIT 10;
```

---

## Where schemas are defined in code

- **events / cleaned table layout:** `dataset_readers/gharchive/storage.py`
- **cleaned table (normalized):** `dataset_readers/gharchive/storage.py` (`CLEANED_TABLE_SCHEMA`). Written by `preprocessing/pipeline.py`; readers JOIN with `events` for metadata.
- **scores table:** `judge/storage.py` (`SCORES_SCHEMA`)
