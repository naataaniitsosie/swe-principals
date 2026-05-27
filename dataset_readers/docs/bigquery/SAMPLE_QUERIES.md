# BigQuery Sample Queries

Paste these directly into the [BigQuery console](https://console.cloud.google.com/bigquery). Each query targets the [`githubarchive.day`](https://www.gharchive.org) public dataset (no billing required to read it, but scan charges apply to your project).

> **Tip:** Click **Dry run** in the console before running to see estimated bytes scanned without spending quota.

---

## 1. Sanity check — single day, one repo

The cheapest starting point. Confirms the schema and that events exist for your target repo.

```sql
SELECT
  id,
  type,
  actor.login      AS actor_login,
  repo.name        AS repo_name,
  JSON_VALUE(payload, '$.action') AS action,
  created_at
FROM `githubarchive.day.20230601`
WHERE repo.name = 'torvalds/linux'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
LIMIT 50;
```

---

## 2. Count events by type — one month

Good for gauging event volume before pulling full payloads.

```sql
SELECT
  type,
  COUNT(*) AS event_count
FROM `githubarchive.day.*`
WHERE _TABLE_SUFFIX BETWEEN '20230101' AND '20230131'
  AND repo.name = 'torvalds/linux'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
GROUP BY type
ORDER BY event_count DESC;
```

---

## 3. Count events by type — full 2023–2025

Replace `'torvalds/linux'` with your target repo. Run a **dry run** first — this touches ~1 095 daily tables.

```sql
SELECT
  type,
  COUNT(*) AS event_count
FROM `githubarchive.day.*`
WHERE _TABLE_SUFFIX BETWEEN '20230101' AND '20251231'
  AND repo.name = 'torvalds/linux'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
GROUP BY type
ORDER BY event_count DESC;
```

---

## 4. Pull full payloads — multi-repo, date range

The production-style query. Swap in your actual repo list. Keep the column list minimal to limit scan volume.

```sql
SELECT
  id,
  type,
  actor.login                          AS actor_login,
  repo.name                            AS repo_name,
  JSON_VALUE(payload, '$.action')      AS action,
  JSON_VALUE(payload, '$.number')      AS pr_number,
  JSON_VALUE(payload, '$.review.body') AS review_body,
  JSON_VALUE(payload, '$.comment.body') AS comment_body,
  payload,
  created_at
FROM `githubarchive.day.*`
WHERE _TABLE_SUFFIX BETWEEN '20230101' AND '20231231'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
  AND repo.name IN (
    'torvalds/linux',
    'django/django',
    'rails/rails'
  )
ORDER BY created_at;
```

---

## 5. Inspect payload schema for one event type

Useful when you need to understand the nested JSON structure before writing extraction logic.

```sql
SELECT
  type,
  TO_JSON_STRING(payload) AS raw_payload
FROM `githubarchive.day.20230601`
WHERE repo.name = 'torvalds/linux'
  AND type = 'PullRequestReviewCommentEvent'
LIMIT 5;
```

---

## 6. Daily event counts over a month (activity heatmap)

Helpful for spotting repo activity patterns or dead periods in the dataset.

```sql
SELECT
  PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS event_date,
  type,
  COUNT(*) AS event_count
FROM `githubarchive.day.*`
WHERE _TABLE_SUFFIX BETWEEN '20230101' AND '20230131'
  AND repo.name = 'torvalds/linux'
  AND type IN (
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent'
  )
GROUP BY event_date, type
ORDER BY event_date, type;
```

---

## 7. Export to Cloud Storage (for large pulls)

For multi-year, multi-repo pulls that exceed what the console can display, write results to GCS and then download.

```sql
EXPORT DATA OPTIONS (
  uri = 'gs://your-bucket/github-events/*.json',
  format = 'JSON',
  overwrite = true
) AS
SELECT
  id,
  type,
  actor.login                     AS actor_login,
  repo.name                       AS repo_name,
  JSON_VALUE(payload, '$.action') AS action,
  payload,
  created_at
FROM `githubarchive.day.*`
WHERE _TABLE_SUFFIX BETWEEN '20230101' AND '20251231'
  AND type IN (
    'PullRequestEvent',
    'PullRequestReviewEvent',
    'PullRequestReviewCommentEvent',
    'IssueCommentEvent'
  )
  AND repo.name IN (
    'torvalds/linux',
    'django/django'
  );
```
