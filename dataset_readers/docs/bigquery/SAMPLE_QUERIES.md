# BigQuery Sample Queries

Paste these directly into the [BigQuery console](https://console.cloud.google.com/bigquery). All queries target the [`githubarchive`](https://www.gharchive.org) public dataset.

> **Tip:** Click **Dry run** before running to see estimated bytes scanned without spending quota.

---

## Dataset Granularity

The archive is split across three datasets — choose the coarsest granularity that fits your date range to minimise bytes scanned:

| Dataset | Table pattern | Best for |
|---|---|---|
| `githubarchive.year` | `YYYY` — e.g. `2023` | Full-year or multi-year pulls (2011–2015 only as pre-aggregated tables) |
| `githubarchive.month` | `YYYYMM` — e.g. `202306` | Monthly pulls or ranges spanning several months |
| `githubarchive.day` | `YYYYMMDD` — e.g. `20230601` | Single-day lookups or ranges of a few days |

> **Note:** Pre-aggregated `year` tables exist for 2011–2015. For 2016 onward, use `month.*` or `day.*` with a `_TABLE_SUFFIX` range.

---

## Day Queries (`githubarchive.day`)

### 1. Sanity check — single day, one repo

Cheapest starting point. Confirms the schema and that events exist for your target repo.

```sql
SELECT
  id,
  type,
  actor.login      AS actor_login,
  repo.name        AS repo_name,
  JSON_VALUE(payload, '$.action') AS action,
  created_at
FROM `githubarchive.day.20230601`
WHERE repo.name = 'django/django'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
LIMIT 50;
```

### 2. Count events by type — one week

```sql
SELECT
  type,
  COUNT(*) AS event_count
FROM `githubarchive.day.*`
WHERE _TABLE_SUFFIX BETWEEN '20230601' AND '20230607'
  AND repo.name = 'django/django'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
GROUP BY type
ORDER BY event_count DESC;
```

### 3. Inspect payload for one event type

```sql
SELECT
  type,
  JSON_VALUE(payload, '$.action')       AS action,
  JSON_VALUE(payload, '$.review.state') AS review_state,
  JSON_VALUE(payload, '$.review.body')  AS review_body,
  actor.login                           AS reviewer,
  created_at
FROM `githubarchive.day.20230601`
WHERE repo.name = 'django/django'
  AND type = 'PullRequestReviewEvent'
LIMIT 10;
```

---

## Month Queries (`githubarchive.month`)

### 4. Count events by type — one month

```sql
SELECT
  type,
  COUNT(*) AS event_count
FROM `githubarchive.month.202306`
WHERE repo.name = 'django/django'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
GROUP BY type
ORDER BY event_count DESC;
```

### 5. Full payload pull — multi-repo, one month

The production-style query for a monthly slice. Keep the column list minimal to limit scan volume.

```sql
SELECT
  id,
  type,
  actor.login                               AS actor_login,
  repo.name                                 AS repo_name,
  JSON_VALUE(payload, '$.action')           AS action,
  JSON_VALUE(payload, '$.number')           AS pr_number,
  JSON_VALUE(payload, '$.pull_request.title') AS pr_title,
  JSON_VALUE(payload, '$.review.body')      AS review_body,
  JSON_VALUE(payload, '$.review.state')     AS review_state,
  JSON_VALUE(payload, '$.comment.body')     AS comment_body,
  created_at
FROM `githubarchive.month.202306`
WHERE type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
  AND repo.name IN (
    'django/django',
    'rails/rails',
    'torvalds/linux'
  )
ORDER BY created_at;
```

### 6. Monthly event counts over a year (activity trend)

```sql
SELECT
  _TABLE_SUFFIX                   AS month,
  type,
  COUNT(*)                        AS event_count
FROM `githubarchive.month.*`
WHERE _TABLE_SUFFIX BETWEEN '202301' AND '202312'
  AND repo.name = 'django/django'
  AND type IN (
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent'
  )
GROUP BY month, type
ORDER BY month, type;
```

---

## Year Queries (`githubarchive.year`)

> Pre-aggregated year tables cover **2011–2015 only**. For 2016 onward use `month.*`.

### 7. Count events by type — single year

```sql
SELECT
  type,
  COUNT(*) AS event_count
FROM `githubarchive.year.2015`
WHERE repo.name = 'django/django'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
GROUP BY type
ORDER BY event_count DESC;
```

### 8. Multi-year count — 2011 through 2015

```sql
SELECT
  _TABLE_SUFFIX AS year,
  type,
  COUNT(*)      AS event_count
FROM `githubarchive.year.*`
WHERE _TABLE_SUFFIX BETWEEN '2011' AND '2015'
  AND repo.name = 'django/django'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
GROUP BY year, type
ORDER BY year, type;
```

---

## Cross-Range Queries (2023–2025)

For the primary research window, use `githubarchive.month.*`. Run a dry run first — this spans 36 monthly tables.

### 9. Full 2023–2025 event count by type

```sql
SELECT
  type,
  COUNT(*) AS event_count
FROM `githubarchive.month.*`
WHERE _TABLE_SUFFIX BETWEEN '202301' AND '202512'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
  AND repo.name = 'django/django'
GROUP BY type
ORDER BY event_count DESC;
```

### 10. Export 2023–2025 to Cloud Storage (large pulls)

For multi-repo pulls too large to display in the console.

```sql
EXPORT DATA OPTIONS (
  uri = 'gs://your-bucket/github-events/*.json',
  format = 'JSON',
  overwrite = true
) AS
SELECT
  id,
  type,
  actor.login                           AS actor_login,
  repo.name                             AS repo_name,
  JSON_VALUE(payload, '$.action')       AS action,
  JSON_VALUE(payload, '$.number')       AS pr_number,
  JSON_VALUE(payload, '$.review.body')  AS review_body,
  JSON_VALUE(payload, '$.review.state') AS review_state,
  JSON_VALUE(payload, '$.comment.body') AS comment_body,
  payload,
  created_at
FROM `githubarchive.month.*`
WHERE _TABLE_SUFFIX BETWEEN '202301' AND '202512'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
  AND repo.name IN (
    'django/django',
    'rails/rails'
  );
```
