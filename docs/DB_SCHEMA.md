# Database schema

Single SQLite database: **`data/raw/events.db`** by default (see `project_config.py`).

---

## Overview

| Table     | Written by       | Purpose |
|-----------|------------------|---------|
| **events**  | `dataset.py`     | Raw GitHub events from GHArchive. |
| **cleaned** | `preprocess.py`  | Preprocessed comment text only (slim records). |
| **scores**  | `judge.py`       | LLM judge output: FUN/NSI/INSI/ISI scores and reasoning per comment and model ([CONFORMITY_SYSTEM_PROMPT.md](papers/CONFORMITY_SYSTEM_PROMPT.md)). |

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

LLM judge output. One row per **(comment_id, model_name)**. Schema matches the JSON in [`CONFORMITY_SYSTEM_PROMPT.md`](papers/CONFORMITY_SYSTEM_PROMPT.md): four independent dimensions (FUN, NSI, INSI, ISI), each with reasoning text and a 0–3 score.

| Column           | Type    | Description |
|------------------|---------|-------------|
| `comment_id`     | TEXT    | Same as `id` in `cleaned`. Part of primary key. |
| `model_name`     | TEXT    | Model id (Ollama tag or OpenAI model name). Part of primary key. |
| `fun_score`      | INTEGER | FUN (functional) score 0–3. |
| `fun_reasoning`  | TEXT    | FUN reasoning. |
| `nsi_score`      | INTEGER | NSI (explicit normative social) score 0–3. |
| `nsi_reasoning`  | TEXT    | NSI reasoning. |
| `insi_score`     | INTEGER | INSI (implicit normative social) score 0–3. |
| `insi_reasoning` | TEXT    | INSI reasoning. |
| `isi_score`      | INTEGER | ISI (informational / expert) score 0–3. |
| `isi_reasoning`  | TEXT    | ISI reasoning. |
| `created_at`     | TEXT    | Optional; copied from cleaned record. |

**Primary key:** `(comment_id, model_name)`.

If your DB still has an older `scores` table (e.g. NSI/ISI only), drop it once so the judge can recreate the table with the full schema: `DROP TABLE IF EXISTS scores;` (you will lose prior judge rows).

---

## Example queries

Default DB path: `data/raw/events.db` (adjust if you use another file). Replace `model_name` values with your stored judge id (Ollama tag, e.g. `llama3.1:8b-instruct-q8_0`, or OpenAI model name, e.g. `gpt-5.4-mini`).

```sql
-- Count by table
SELECT COUNT(*) FROM events;
SELECT COUNT(*) FROM cleaned;
SELECT COUNT(*) FROM scores;

-- Cleaned + events: comments per repo (repo lives in events)
SELECT json_extract(e.event_data, '$.repo.name') AS repo, COUNT(*)
FROM cleaned c INNER JOIN events e ON e.id = c.id
GROUP BY 1 ORDER BY 1;

-- Scores: row counts and mean scores per model (FUN / NSI / INSI / ISI are 0–3)
SELECT
  model_name,
  COUNT(*) AS n,
  ROUND(AVG(fun_score), 3)  AS avg_fun,
  ROUND(AVG(nsi_score), 3)  AS avg_nsi,
  ROUND(AVG(insi_score), 3) AS avg_insi,
  ROUND(AVG(isi_score), 3)  AS avg_isi
FROM scores
GROUP BY model_name
ORDER BY model_name;

-- Inspect raw judge rows (all columns from CONFORMITY-shaped output)
SELECT * FROM scores LIMIT 10;

-- Join cleaned comment text with full scores for one model
SELECT
  c.id,
  c.cleaned_text,
  s.fun_score,
  s.nsi_score,
  s.insi_score,
  s.isi_score,
  substr(s.fun_reasoning, 1, 80)   AS fun_reasoning_preview,
  substr(s.nsi_reasoning, 1, 80)  AS nsi_reasoning_preview
FROM cleaned c
JOIN scores s ON s.comment_id = c.id
WHERE s.model_name = 'llama3.1:8b-instruct-q8_0'  -- your model_name here
LIMIT 10;

-- Example: comments with strong implicit norm signal (INSI), for one model
SELECT
  s.comment_id,
  s.insi_score,
  substr(s.insi_reasoning, 1, 200) AS insi_reasoning_preview
FROM scores s
WHERE s.model_name = 'gpt-5.4-mini'  -- your model_name here
  AND s.insi_score >= 2
ORDER BY s.insi_score DESC, s.comment_id
LIMIT 20;
```

---

To **inspect** comments with scores in a human-readable layout (similar to the CONFORMITY prompt examples), use **`browse_scores.py`** at the repo root (`python browse_scores.py --help`).

---

## Where schemas are defined in code

- **events / cleaned table layout:** `dataset_readers/gharchive/storage.py`
- **cleaned table (normalized):** `dataset_readers/gharchive/storage.py` (`CLEANED_TABLE_SCHEMA`). Written by `preprocessing/pipeline.py`; readers JOIN with `events` for metadata.
- **scores table:** `judge/storage.py` (`SCORES_SCHEMA`)
