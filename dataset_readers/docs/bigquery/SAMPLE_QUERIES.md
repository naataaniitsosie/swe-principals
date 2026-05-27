# BigQuery Sample Queries

> **Tip:** Click **Dry run** in the console before running to see estimated bytes scanned without spending quota.

---

## One-and-Done: Full 2023–2025 Local Download

The BigQuery console caps direct downloads at ~16,000 rows, so the full pull goes through the **Python client** (streams row-by-row) or the **`bq` CLI** (buffers in memory). Pick one:

### Option A — Python client (recommended)

```python
# scripts/bq_pull.py
from google.cloud import bigquery
import json, os
from pathlib import Path

PROJECT = os.environ["GCP_PROJECT"]  # set in .env
OUTPUT  = Path("data/raw/github_events_2023_2025.jsonl")

SQL = """
SELECT
  id,
  type,
  actor.login                                  AS actor_login,
  repo.name                                    AS repo_name,
  JSON_VALUE(payload, '$.action')              AS action,
  JSON_VALUE(payload, '$.number')              AS pr_number,
  JSON_VALUE(payload, '$.pull_request.title')  AS pr_title,
  JSON_VALUE(payload, '$.review.body')         AS review_body,
  JSON_VALUE(payload, '$.review.state')        AS review_state,
  JSON_VALUE(payload, '$.comment.body')        AS comment_body,
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
    'expressjs/express',
    'nestjs/nest',
    'koajs/koa',
    'fastify/fastify',
    'hapijs/hapi',
    'spring-projects/spring-boot',
    'tiangolo/fastapi',
    'django/django',
    'pallets/flask',
    'gin-gonic/gin'
  )
ORDER BY created_at
"""

client = bigquery.Client(project=PROJECT)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w") as f:
    for row in client.query(SQL).result():
        f.write(json.dumps(dict(row)) + "\n")

print(f"Saved to {OUTPUT}")
```

```bash
caffeinate python scripts/bq_pull.py
```

### Option B — `bq` CLI (no Python)

```bash
bq query \
  --use_legacy_sql=false \
  --format=newline_delimited_json \
  --max_rows=10000000 \
  --project_id="$(grep GCP_PROJECT .env | cut -d= -f2)" \
'SELECT
   id, type,
   actor.login AS actor_login, repo.name AS repo_name,
   JSON_VALUE(payload, "$.action")              AS action,
   JSON_VALUE(payload, "$.number")              AS pr_number,
   JSON_VALUE(payload, "$.pull_request.title")  AS pr_title,
   JSON_VALUE(payload, "$.review.body")         AS review_body,
   JSON_VALUE(payload, "$.review.state")        AS review_state,
   JSON_VALUE(payload, "$.comment.body")        AS comment_body,
   payload, created_at
 FROM `githubarchive.month.*`
 WHERE _TABLE_SUFFIX BETWEEN "202301" AND "202512"
   AND type IN (
     "PullRequestEvent","PullRequestReviewEvent",
     "PullRequestReviewCommentEvent","IssueCommentEvent"
   )
   AND repo.name IN (
     "expressjs/express","nestjs/nest","koajs/koa","fastify/fastify",
     "hapijs/hapi","spring-projects/spring-boot","tiangolo/fastapi",
     "django/django","pallets/flask","gin-gonic/gin"
   )
 ORDER BY created_at' \
> data/raw/github_events_2023_2025.jsonl
```

> **Note:** `bq query` buffers the full result set before writing. For very large result sets, prefer Option A.

---

## Exploration & Learning Queries

The queries below are for understanding the dataset, checking schema, and validating before a full pull.

### Dataset granularity

| Dataset | Table pattern | Best for |
|---|---|---|
| `githubarchive.year` | `YYYY` — e.g. `2023` | Full-year pulls (pre-aggregated 2011–2015 only) |
| `githubarchive.month` | `YYYYMM` — e.g. `202306` | Multi-month ranges |
| `githubarchive.day` | `YYYYMMDD` — e.g. `20230601` | Single-day lookups |

> Pre-aggregated `year` tables exist for 2011–2015. For 2016 onward, use `month.*` or `day.*`.

### Sanity check — single day, one repo

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

### Count events by type — one month

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

### Inspect payload for one event type

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

### Monthly event counts over a year (activity trend)

```sql
SELECT
  _TABLE_SUFFIX   AS month,
  type,
  COUNT(*)        AS event_count
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
