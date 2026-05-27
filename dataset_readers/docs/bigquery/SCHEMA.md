# githubarchive BigQuery Schema

Source: [gharchive.org](https://www.gharchive.org) · [schema.js](https://github.com/igrigorik/gharchive.org/blob/master/bigquery/schema.js)

---

## Top-Level Columns

| Column | Type | Notes |
|---|---|---|
| `id` | STRING | GitHub event ID |
| `type` | STRING | Event type (see below) |
| `actor` | RECORD | User who triggered the event |
| `repo` | RECORD | Repository the event belongs to |
| `org` | RECORD | Organization (nullable — only present for org-owned repos) |
| `payload` | STRING | **Raw JSON string.** Use `JSON_VALUE()` / `JSON_QUERY()` to extract fields |
| `public` | BOOLEAN | Always `true` (archive only records public events) |
| `created_at` | TIMESTAMP | UTC timestamp of the event |

---

## Nested RECORDs

### `actor`

| Field | Type |
|---|---|
| `id` | INTEGER |
| `login` | STRING |
| `gravatar_id` | STRING |
| `avatar_url` | STRING |
| `url` | STRING |

### `repo`

| Field | Type |
|---|---|
| `id` | INTEGER |
| `name` | STRING — `owner/repo` format, e.g. `django/django` |
| `url` | STRING |

### `org`

| Field | Type |
|---|---|
| `id` | INTEGER |
| `login` | STRING |
| `gravatar_id` | STRING |
| `avatar_url` | STRING |
| `url` | STRING |

---

## Event Types (relevant to this project)

| `type` value | When it fires |
|---|---|
| `PullRequestEvent` | PR opened, closed, merged, edited, labeled, etc. |
| `PullRequestReviewEvent` | Reviewer submits an approval, request-for-changes, or comment review |
| `PullRequestReviewCommentEvent` | Inline comment on a PR diff |
| `IssueCommentEvent` | Comment posted on a PR's conversation thread |

---

## Payload JSON Paths

`payload` is a raw JSON string. Extract fields with `JSON_VALUE(payload, '$.path')` (returns scalar) or `JSON_QUERY(payload, '$.path')` (returns JSON object/array).

### PullRequestEvent

| Path | Description |
|---|---|
| `$.action` | `opened`, `closed`, `edited`, `reopened`, `labeled`, `synchronize`, … |
| `$.number` | PR number |
| `$.pull_request.title` | PR title |
| `$.pull_request.body` | PR description |
| `$.pull_request.state` | `open` or `closed` |
| `$.pull_request.merged` | `true` / `false` |
| `$.pull_request.user.login` | PR author login |
| `$.pull_request.additions` | Lines added |
| `$.pull_request.deletions` | Lines deleted |
| `$.pull_request.changed_files` | Files changed |
| `$.pull_request.base.repo.full_name` | Target repo (same as `repo.name`) |

### PullRequestReviewEvent

| Path | Description |
|---|---|
| `$.action` | Always `submitted` |
| `$.review.id` | Review ID |
| `$.review.body` | Review comment body (may be null for approval-only reviews) |
| `$.review.state` | `approved`, `changes_requested`, `commented` |
| `$.review.user.login` | Reviewer login |
| `$.pull_request.number` | PR number |
| `$.pull_request.title` | PR title |

### PullRequestReviewCommentEvent

| Path | Description |
|---|---|
| `$.action` | `created` |
| `$.comment.id` | Comment ID |
| `$.comment.body` | Comment text |
| `$.comment.user.login` | Comment author |
| `$.comment.path` | File path the comment is on |
| `$.comment.position` | Line position in the diff |
| `$.pull_request.number` | PR number |

### IssueCommentEvent

| Path | Description |
|---|---|
| `$.action` | `created`, `edited`, `deleted` |
| `$.comment.id` | Comment ID |
| `$.comment.body` | Comment text |
| `$.comment.user.login` | Comment author |
| `$.issue.number` | Issue/PR number |
| `$.issue.pull_request` | Present (non-null) when the issue is actually a PR |

---

## Schema Exploration Queries

### Inspect raw payload for a single event type

```sql
SELECT
  type,
  JSON_QUERY(payload, '$') AS raw_payload
FROM `githubarchive.day.20230601`
WHERE repo.name = 'django/django'
  AND type = 'PullRequestReviewEvent'
LIMIT 3;
```

### List all top-level payload keys for an event type

BigQuery doesn't have a native `keys()` function, but casting to JSON and eyeballing 5 rows is the quickest way to discover the structure.

```sql
SELECT
  JSON_VALUE(payload, '$.action')       AS action,
  JSON_VALUE(payload, '$.review.state') AS review_state,
  JSON_VALUE(payload, '$.review.body')  AS review_body,
  JSON_VALUE(payload, '$.pull_request.number') AS pr_number,
  JSON_VALUE(payload, '$.pull_request.title')  AS pr_title,
  actor.login                           AS reviewer,
  repo.name                             AS repo,
  created_at
FROM `githubarchive.day.20230601`
WHERE type = 'PullRequestReviewEvent'
  AND repo.name = 'django/django'
LIMIT 10;
```

### Confirm which payload fields are populated vs null

```sql
SELECT
  COUNTIF(JSON_VALUE(payload, '$.review.body') IS NOT NULL)  AS has_body,
  COUNTIF(JSON_VALUE(payload, '$.review.body') IS NULL)      AS no_body,
  COUNTIF(JSON_VALUE(payload, '$.review.state') = 'approved')           AS approved,
  COUNTIF(JSON_VALUE(payload, '$.review.state') = 'changes_requested')  AS changes_requested,
  COUNTIF(JSON_VALUE(payload, '$.review.state') = 'commented')          AS commented
FROM `githubarchive.day.20230601`
WHERE type = 'PullRequestReviewEvent';
```

### Full extraction — all four event types, flattened

Use this as a template when building the actual reader query. Columns are named so they land cleanly in the `events` table.

```sql
SELECT
  id                                              AS event_id,
  type                                            AS event_type,
  actor.login                                     AS actor_login,
  repo.name                                       AS repo_name,
  JSON_VALUE(payload, '$.action')                 AS action,
  JSON_VALUE(payload, '$.number')                 AS pr_number,
  -- PullRequestEvent
  JSON_VALUE(payload, '$.pull_request.title')     AS pr_title,
  JSON_VALUE(payload, '$.pull_request.body')      AS pr_body,
  JSON_VALUE(payload, '$.pull_request.merged')    AS pr_merged,
  -- PullRequestReviewEvent
  JSON_VALUE(payload, '$.review.body')            AS review_body,
  JSON_VALUE(payload, '$.review.state')           AS review_state,
  -- PullRequestReviewCommentEvent
  JSON_VALUE(payload, '$.comment.body')           AS comment_body,
  JSON_VALUE(payload, '$.comment.path')           AS comment_file_path,
  -- IssueCommentEvent (body reuses comment.body path)
  created_at
FROM `githubarchive.day.*`
WHERE _TABLE_SUFFIX BETWEEN '20230101' AND '20230131'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
  AND repo.name = 'django/django'
ORDER BY created_at;
```

---

## Gotchas

- **`payload` is always STRING.** There is no structured RECORD for the payload — always use `JSON_VALUE()` or `JSON_QUERY()`.
- **`review.body` can be null.** Approval-only reviews often have an empty or null body; filter with `JSON_VALUE(...) IS NOT NULL` when you only want substantive text.
- **`IssueCommentEvent` covers both issues and PRs.** Check `JSON_VALUE(payload, '$.issue.pull_request') IS NOT NULL` to confirm the comment belongs to a PR.
- **Schema drift across years.** Older tables (pre-2015) may have slightly different payload structures as the GitHub Events API evolved. Validate before running multi-year queries.
