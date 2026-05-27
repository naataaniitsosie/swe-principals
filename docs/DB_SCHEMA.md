# Database schema

Single SQLite database: **`data/raw/events.db`** by default (see `project_config.py`).

---

## Overview

| Table     | Written by       | Purpose |
|-----------|------------------|---------|
| **events**  | `dataset.py`     | Raw GitHub events from GHArchive. |
| **cleaned** | `preprocess.py`  | Preprocessed comment text only (slim records). |
| **samples** | `sample.py`      | Stratified sample: selected `id` values (FK → cleaned) plus repo, event_type, stratum_key. Judge operates over this table. See [`sampling/README.md`](../sampling/README.md). |
| **scores**  | `judge.py`       | LLM judge output: FUN/NSI/INSI/ISI scores and reasoning per comment and model ([CONFORMITY_SYSTEM_PROMPT.md](../papers/publication1/CONFORMITY_SYSTEM_PROMPT.md)). |

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
| `type`        | string | Webhook / timeline event name. This project’s four main values are [described below](#meaning-of-top-level-type). |
| `actor`       | object | User who triggered the event. `id`, `login`, `display_login`. |
| `repo`        | object | Repository. `name` is `owner/repo` (e.g. `django/django`). |
| `created_at`  | string | ISO 8601 timestamp. |
| `payload`     | object | Event-specific data (see below). |

### Meaning of top-level type

Values are GitHub **timeline / webhook** event names ([event payloads overview](https://docs.github.com/en/webhooks/webhook-events-and-payloads)). This project’s extractor commonly keeps four kinds of PR-related activity; **`json_extract(event_data, '$.type')`** returns exactly these strings.

| `type` | Meaning |
|--------|---------|
| **`PullRequestEvent`** | Activity on a pull request record itself—opened, edited, closed, labeled, synchronized, assigned, etc. Payload centers on **`pull_request`**. |
| **`PullRequestReviewEvent`** | A **pull request review** was submitted (approve, request changes, or comment **as a review**). Payload centers on **`review`**. |
| **`PullRequestReviewCommentEvent`** | A **inline** comment on a **specific line** of the PR diff (review comment). Payload centers on **`comment`**. |
| **`IssueCommentEvent`** | A **comment** on an issue or pull request **thread** (in GitHub’s model, PRs are issues). Payload centers on **`comment`**. |

You may see other `type` strings if you ingest a broader GHArchive slice.

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

LLM judge output. One row per **(comment_id, model_name)**. Schema matches the JSON in [`CONFORMITY_SYSTEM_PROMPT.md`](../papers/publication1/CONFORMITY_SYSTEM_PROMPT.md): four independent dimensions (FUN, NSI, INSI, ISI), each with reasoning text and a 0–3 score. If the model response cannot be parsed as JSON, all four scores are stored as `-1` and parse metadata is retained for retry/inspection.

| Column           | Type    | Description |
|------------------|---------|-------------|
| `comment_id`     | TEXT    | Same as `id` in `cleaned`. Part of primary key. |
| `model_name`     | TEXT    | Model id (Ollama tag or OpenAI model name). Part of primary key. |
| `fun_score`      | INTEGER | FUN (functional) score 0–3, or `-1` if parsing failed. |
| `fun_reasoning`  | TEXT    | FUN reasoning. |
| `nsi_score`      | INTEGER | NSI (explicit normative social) score 0–3, or `-1` if parsing failed. |
| `nsi_reasoning`  | TEXT    | NSI reasoning. |
| `insi_score`     | INTEGER | INSI (implicit normative social) score 0–3, or `-1` if parsing failed. |
| `insi_reasoning` | TEXT    | INSI reasoning. |
| `isi_score`      | INTEGER | ISI (informational / expert) score 0–3, or `-1` if parsing failed. |
| `isi_reasoning`  | TEXT    | ISI reasoning. |
| `created_at`     | TEXT    | Optional; copied from cleaned record. |
| `parse_ok`       | INTEGER | `1` when model output parsed successfully; `0` for malformed/unparseable output. |
| `error_type`     | TEXT    | Error category for failed parses, e.g. `json_parse_error`. Empty when `parse_ok=1`. |
| `error_message`  | TEXT    | Parser exception message for failed parses. Empty when `parse_ok=1`. |
| `raw_response`   | TEXT    | Raw model output. Stored mainly so `parse_ok=0` rows can be inspected and retried. |

**Primary key:** `(comment_id, model_name)`.

The judge creates missing parse metadata columns automatically for older `scores` tables. If your DB still has a much older incompatible `scores` table (e.g. NSI/ISI only), drop it once so the judge can recreate the table with the full schema: `DROP TABLE IF EXISTS scores;` (you will lose prior judge rows).

---

## Example queries

Default DB path: `data/raw/events.db` (adjust if you use another file). Replace `model_name` values with your stored judge id (Ollama tag, e.g. `gemma4:e4b`, or OpenAI model name, e.g. `gpt-5.4-mini`).

```sql
-- Count by table
SELECT COUNT(*) FROM events;
SELECT COUNT(*) FROM cleaned;
SELECT COUNT(*) FROM scores;

-- Cleaned + events: comments per repo (repo lives in events)
SELECT json_extract(e.event_data, '$.repo.name') AS repo, COUNT(*)
FROM cleaned c INNER JOIN events e ON e.id = c.id
GROUP BY 1 ORDER BY 1;

-- Scores: row counts and mean scores per model (valid rows only; scores are 0–3)
SELECT
  model_name,
  COUNT(*) AS n,
  ROUND(AVG(fun_score), 3)  AS avg_fun,
  ROUND(AVG(nsi_score), 3)  AS avg_nsi,
  ROUND(AVG(insi_score), 3) AS avg_insi,
  ROUND(AVG(isi_score), 3)  AS avg_isi
FROM scores
WHERE parse_ok = 1
GROUP BY model_name
ORDER BY model_name;

-- Parse failures by model (scores are stored as -1 when parsing failed)
SELECT model_name, COUNT(*) AS n_parse_failures
FROM scores
WHERE parse_ok = 0
GROUP BY model_name
ORDER BY n_parse_failures DESC;

-- Inspect failed model outputs for retry/debugging
SELECT
  comment_id,
  model_name,
  error_type,
  error_message,
  substr(raw_response, 1, 500) AS raw_response_preview
FROM scores
WHERE parse_ok = 0
ORDER BY comment_id
LIMIT 20;

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
WHERE s.model_name = 'gemma4:e4b'  -- your model_name here
  AND s.parse_ok = 1
LIMIT 10;

-- Example: comments with strong implicit norm signal (INSI), for one model
SELECT
  s.comment_id,
  s.insi_score,
  substr(s.insi_reasoning, 1, 200) AS insi_reasoning_preview
FROM scores s
WHERE s.model_name = 'gpt-5.4-mini'  -- your model_name here
  AND s.parse_ok = 1
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
