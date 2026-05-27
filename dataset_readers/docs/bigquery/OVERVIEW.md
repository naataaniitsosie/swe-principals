# BigQuery Reader — Overview

## Why BigQuery

The GHArchive reader downloads raw `.json.gz` files (~35 MB/hour) and processes them locally — fine for narrow date ranges but slow and disk-heavy for multi-year pulls. BigQuery exposes the same data as the `bigquery-public-data.github_archive.*` public dataset, letting us issue SQL against it without downloading anything.

Two properties make it the preferred mechanism for 2023–2025 data:

1. **Scale** — a single query can cover years of data in seconds.
2. **Recovery** — re-running the same SQL is idempotent; there is no partial-download state to clean up.

## Dataset

Source: [gharchive.org](https://www.gharchive.org) — records every public GitHub event since 2011 and exposes them as a public BigQuery dataset.

```
githubarchive.day.<YYYYMMDD>
```

Tables live in the `githubarchive` GCP project under the `day` dataset, one table per calendar day. Use a wildcard with `_TABLE_SUFFIX` to span multiple days. Relevant event types for this project:

| Event type | `type` filter value |
|---|---|
| `PullRequestEvent` | `'PullRequestEvent'` |
| `PullRequestReviewEvent` | `'PullRequestReviewEvent'` |
| `PullRequestReviewCommentEvent` | `'PullRequestReviewCommentEvent'` |
| `IssueCommentEvent` | `'IssueCommentEvent'` |

## Setup

1. Create a GCP project (free) at [console.cloud.google.com](https://console.cloud.google.com).
2. Enable the BigQuery API.
3. Authenticate locally:
   ```bash
   gcloud auth application-default login
   ```
4. Set `GCP_PROJECT` in `.env` at the repo root:
   ```
   GCP_PROJECT=your-project-id
   ```
5. Install the Python client:
   ```bash
   pip install google-cloud-bigquery
   ```

## Query Pattern

Always project only the columns you need and filter on `repo.name` early. BigQuery charges by bytes scanned, and the `payload` column alone is the bulk of each row.

```sql
SELECT
  id,
  type,
  actor.login      AS actor_login,
  repo.name        AS repo_name,
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
  AND repo.name IN UNNEST(@repos)
```

See [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) for console-ready queries you can paste directly into BigQuery.
