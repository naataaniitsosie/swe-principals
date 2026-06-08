# SQLite Reference Queries

Common queries against `data/raw/events.db`. Replace the path if you set a custom `DATA_DIR` in `project_config.py`.

---

## Events table

```bash
# Total rows
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM events;"

# Rows per repo
sqlite3 data/raw/events.db "SELECT json_extract(event_data, '$.repo.name'), COUNT(*) FROM events GROUP BY 1 ORDER BY 1;"

# Total vs unique IDs
sqlite3 data/raw/events.db "SELECT COUNT(*) AS total, COUNT(DISTINCT id) AS unique_ids FROM events;"
```

---

## Cleaned table

```bash
# Total rows
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM cleaned;"

# Per repo
sqlite3 data/raw/events.db "SELECT repo, COUNT(*) FROM cleaned GROUP BY repo ORDER BY repo;"

# Per event type
sqlite3 data/raw/events.db "SELECT event_type, COUNT(*) FROM cleaned GROUP BY event_type ORDER BY 2 DESC;"

# Per date
sqlite3 data/raw/events.db "SELECT date(created_at), COUNT(*) FROM cleaned GROUP BY 1 ORDER BY 1;"

# NULL pr_number audit (plain IssueCommentEvents or malformed events)
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM cleaned WHERE pr_number IS NULL AND repo != '';"
```

---

## Scores table

**How many comments have and have not been scored?**

"Scored" means at least one row in `scores` (any model).

```bash
sqlite3 -header data/raw/events.db "SELECT
  (SELECT COUNT(*) FROM cleaned) AS cleaned_total,
  (SELECT COUNT(DISTINCT comment_id) FROM scores) AS cleaned_with_any_score,
  (SELECT COUNT(*) FROM cleaned c WHERE NOT EXISTS (
    SELECT 1 FROM scores s WHERE s.comment_id = c.id
  )) AS cleaned_never_scored;"
```

**How many scores has each model produced?**

```bash
sqlite3 data/raw/events.db "SELECT model_name, COUNT(*) AS n_scores FROM scores GROUP BY model_name ORDER BY model_name;"
```

**Score distribution per dimension (0–3)**

```bash
sqlite3 -header -column data/raw/events.db "
SELECT 'FUN' AS rubric, fun_score AS score, COUNT(*) AS n
FROM scores GROUP BY fun_score
UNION ALL
SELECT 'NSI', nsi_score, COUNT(*) FROM scores GROUP BY nsi_score
UNION ALL
SELECT 'INSI', insi_score, COUNT(*) FROM scores GROUP BY insi_score
UNION ALL
SELECT 'ISI', isi_score, COUNT(*) FROM scores GROUP BY isi_score
ORDER BY rubric, score;"
```

**Most common single score (pooling all four dimensions)**

```bash
sqlite3 -header data/raw/events.db "
SELECT score, COUNT(*) AS n FROM (
  SELECT fun_score AS score FROM scores
  UNION ALL SELECT nsi_score FROM scores
  UNION ALL SELECT insi_score FROM scores
  UNION ALL SELECT isi_score FROM scores
)
GROUP BY score
ORDER BY n DESC, score DESC
LIMIT 1;"
```

**Non-zero score count per dimension**

```bash
sqlite3 -header data/raw/events.db "
SELECT 'FUN' AS rubric, COUNT(*) AS n FROM scores WHERE fun_score > 0
UNION ALL SELECT 'NSI', COUNT(*) FROM scores WHERE nsi_score > 0
UNION ALL SELECT 'INSI', COUNT(*) FROM scores WHERE insi_score > 0
UNION ALL SELECT 'ISI', COUNT(*) FROM scores WHERE isi_score > 0
ORDER BY rubric;"
```

**All-zero scored comments (with text, sorted by date)**

```bash
sqlite3 -header data/raw/events.db "
SELECT comment_id, created_at, model_name, fun_score, nsi_score, insi_score, isi_score, cleaned_text
FROM scores
INNER JOIN cleaned ON cleaned.id = scores.comment_id
WHERE fun_score + nsi_score + insi_score + isi_score = 0
ORDER BY created_at;"
```

Count only:

```bash
sqlite3 -header data/raw/events.db "SELECT COUNT(*) AS n
FROM scores
INNER JOIN cleaned ON cleaned.id = scores.comment_id
WHERE fun_score + nsi_score + insi_score + isi_score = 0;"
```

**Non-zero scored comments (with text)**

```bash
sqlite3 -header data/raw/events.db "
SELECT comment_id, created_at, model_name, fun_score, nsi_score, insi_score, isi_score, cleaned_text
FROM scores
INNER JOIN cleaned ON cleaned.id = scores.comment_id
WHERE fun_score + nsi_score + insi_score + isi_score > 0
ORDER BY created_at;"
```
