# Design: Materializing repo and pr_number in the cleaned Table

## 1. Motivation

Every analytical query that groups by repository or filters by PR number currently requires `json_extract(event_data, '$.repo.name')` against the raw `events` blob and a JOIN back to `events` from `cleaned`. This is verbose, error-prone (different event types expose `pr_number` at different JSON paths), and forces every downstream consumer — including `judge.py`, `browse_scores.py`, and any ad-hoc SQL — to re-implement the same extraction logic. Materializing `repo` and `pr_number` directly into `cleaned` eliminates the JOIN for the most common query patterns, centralizes the path-resolution logic in one place (`preprocess.py`), and makes the `samples` table design simpler because stratification by repo is already a first-class column.

---

## 2. Field Extraction Plan

### 2a. Per-event-type fields

| event_type | repo path | pr_number path | author_association path | notes |
|---|---|---|---|---|
| `PullRequestEvent` | `$.repo.name` | `$.payload.pull_request.number` | `$.payload.pull_request.author_association` | `$.payload.number` is an identical alias for pr_number; use `pull_request.number` for consistency. |
| `PullRequestReviewEvent` | `$.repo.name` | `$.payload.pull_request.number` | `$.payload.review.author_association` | |
| `PullRequestReviewCommentEvent` | `$.repo.name` | `$.payload.pull_request.number` | `$.payload.comment.author_association` | |
| `IssueCommentEvent` | `$.repo.name` | `$.payload.issue.number` | `$.payload.comment.author_association` | pr_number is NULL when `$.payload.issue.pull_request` is absent (plain issue, not a PR). |

### 2b. Top-level fields (uniform across all event types)

| column | source path | type | notes |
|---|---|---|---|
| `repo` | `$.repo.name` | `TEXT` | Full `owner/name` string. |
| `pr_number` | see 2a above | `INTEGER` | NULL for plain IssueCommentEvents. |
| `event_type` | `$.type` | `TEXT` | Top-level field; uniform. Avoids reserved word — use `event_type`, not `type`. |
| `created_at` | `$.created_at` | `TEXT` | ISO-8601 timestamp; top-level; uniform. |
| `author_association` | see 2a above | `TEXT` | Per-type path but same Python logic as `_get_author_association()` in `preprocessing/workflow.py:149`. |

### 2c. Payoff: eliminating the events JOIN in the judge

`judge/storage.py:CleanedReader` currently does `cleaned JOIN events` on every run solely to call `metadata_from_raw_event()`, which extracts `repo`, `created_at`, `type`, and `author_association` from the raw JSON blob. Once all five columns are materialized, the JOIN can be dropped entirely — `SELECT * FROM cleaned` suffices, and `CLEANED_JOIN_FILTERS` can reference columns directly instead of `json_extract(e.event_data, ...)` expressions.

---

## 3. Implementation Strategy

`preprocess.py` drops and recreates the `cleaned` table on every run, so no `ALTER TABLE` or backfill is needed.

- **Add all five columns** to the `CREATE TABLE cleaned` statement:
  `repo TEXT`, `pr_number INTEGER`, `event_type TEXT`, `created_at TEXT`, `author_association TEXT`.

- **Populate at INSERT time** in the row-processing loop:

  ```python
  event_type = event.get("type", "")
  repo = (event.get("repo") or {}).get("name", "")
  created_at = event.get("created_at", "")
  payload = event.get("payload") or {}

  if event_type == "IssueCommentEvent":
      pr_number = payload["issue"]["number"] if payload.get("issue", {}).get("pull_request") else None
  else:
      pr_number = (payload.get("pull_request") or {}).get("number")

  author_association = (
      (payload.get("comment") or {}).get("author_association")
      or (payload.get("review") or {}).get("author_association")
      or (payload.get("pull_request") or {}).get("author_association")
      or (payload.get("issue") or {}).get("author_association")
      or ""
  )
  ```

  This mirrors the existing `_get_author_association()` logic in `preprocessing/workflow.py:149`.

- **Update `judge/storage.py`** once the columns exist:
  - Drop the `INNER JOIN events` from `CLEANED_JOIN_SQL`.
  - Replace `json_extract(e.event_data, '$.repo.name')` in `CLEANED_JOIN_FILTERS` with `c.repo`.
  - Replace the 4-way `author_association` OR filter with `c.author_association = ?`.
  - Remove the `metadata_from_raw_event` call in `list_records()`; read columns directly from the row.

- **Verify correctness** after a full run with a spot-check query comparing materialized values against fresh `json_extract` from `events`:

  ```sql
  SELECT
    c.id,
    c.event_type,
    c.repo,         json_extract(e.event_data, '$.repo.name')      AS repo_check,
    c.created_at,   json_extract(e.event_data, '$.created_at')     AS created_at_check,
    c.pr_number,
    CASE c.event_type
      WHEN 'IssueCommentEvent'
        THEN json_extract(e.event_data, '$.payload.issue.number')
      ELSE json_extract(e.event_data, '$.payload.pull_request.number')
    END                                                              AS pr_number_check,
    c.author_association
  FROM cleaned c
  JOIN events e ON e.id = c.id
  WHERE c.repo        IS NOT json_extract(e.event_data, '$.repo.name')
     OR c.created_at  IS NOT json_extract(e.event_data, '$.created_at')
     OR c.event_type  IS NOT json_extract(e.event_data, '$.type')
  LIMIT 20;
  ```

  Zero rows returned means all materialized values match the source JSON.

---

## 4. Backward Compatibility

Adding columns to `cleaned` is additive. No other table is affected:

- **`scores`** joins `cleaned` on `scores.comment_id = cleaned.id` — unchanged.
- **`samples`** joins `cleaned` on `cleaned.id` — unchanged; it can now also reference `cleaned.repo` and `cleaned.pr_number` directly for stratification.
- **`events`** is read-only after ingestion; this change does not touch it.

---

## 5. Open Questions

1. **`IssueCommentEvent` on plain issues (not PRs).** Where `$.payload.issue.pull_request` is absent, `pr_number` is written as `NULL`. If the research question requires every `cleaned` row to belong to a PR, these rows should be filtered out at INSERT time in `preprocess.py` rather than retained with a null.

2. **NULL `pr_number` for review event types.** No null cases were observed in sampled payloads, but malformed events could produce one. The pipeline should tolerate this silently (write `NULL`). Post-run audit: `SELECT COUNT(*) FROM cleaned WHERE pr_number IS NULL AND repo IS NOT NULL;`.

3. **`author_association` empty string vs NULL.** The existing `_get_author_association()` returns `""` (empty string) as the fallback, not `NULL`. The materialized column should follow the same convention so downstream filter logic doesn't need to handle both.

4. **`docs/DB_SCHEMA.md` update.** Once the migration is applied, `DB_SCHEMA.md` should document all five new columns and note that they are materialized denormalizations from `events`, not a change in general policy.
