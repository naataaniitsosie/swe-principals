## Config

All data lives in one directory and one SQLite DB. Edit **`project_config.py`** at the repo root to change paths:

- **`DATA_DIR`** — directory for raw and cleaned data (default `data/raw`).
- **`DB_FILENAME`** — SQLite file name (default `events.db`).

Full DB path is `DATA_DIR / DB_FILENAME`. There is no CLI option to choose an output directory; everything uses this single DB.

---

## Runnable scripts (pipeline)

Run in order: **1. Extract** → **2. Preprocess** → **3. Analyze** (e.g. sentiment).

| Step | Script | Input | Output |
|------|--------|--------|--------|
| 1. Extract | `python dataset.py` | GHArchive (network) | `data/raw/events.db` |
| 2. Preprocess | `python preprocess.py` | config `DATA_DIR` | same DB (`cleaned` table) |
| 3. Analyze | `python sentiment.py` | `data/raw` or `data/cleaned` | `./data/sentiment` |

**Chaining:**
```bash
python dataset.py --start-date 2024-01-01 --end-date 2024-01-02
python preprocess.py
python sentiment.py ./data/raw --output-dir ./data/sentiment
```

---

### 1. Data extraction (`dataset.py`)

Extract PR events from GHArchive for all repositories under investigation (see CONFORMITY.md). Default: all 10 repos; optional date range. Writes to the single DB in config `DATA_DIR`.

```bash
python dataset.py
python dataset.py --start-date 2024-01-01 --end-date 2024-01-02
```

| Flag | Default | Description |
|------|---------|-------------|
| `--dataset-reader`, `-r` | `gharchive` | Reader to use |
| `--start-date` | `2024-02-01` | Start date (YYYY-MM-DD) |
| `--end-date` | `2024-02-02` | End date (YYYY-MM-DD) |

Output is a single SQLite file `events.db` with an `events` table (columns: `id`, `event_data` JSON blob).

**Stats with sqlite3** (default path `data/raw/events.db`):

```bash
# Total rows
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM events;"

# Rows per repo (raw: repo in event_data.repo.name)
sqlite3 data/raw/events.db "SELECT json_extract(event_data, '$.repo.name'), COUNT(*) FROM events GROUP BY 1 ORDER BY 1;"

# Total and unique by id
sqlite3 data/raw/events.db "SELECT COUNT(*) AS total, COUNT(DISTINCT id) AS unique_ids FROM events;"

# Cleaned table (if present): total and per-repo (cleaned has top-level repo)
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM cleaned;"
sqlite3 data/raw/events.db "SELECT json_extract(event_data, '$.repo'), COUNT(*) FROM cleaned GROUP BY 1 ORDER BY 1;"
```

---

### 2. Preprocess data (`preprocess.py`)

Preprocess the single SQLite DB produced by `dataset.py` (CONFORMITY.md Preprocessing): **dedupe by event id** (keep first), remove bot and CI comments, strip code blocks and diff snippets, drop trivial comments (e.g. “LGTM”, “Thanks!”), lowercase and tokenize. Reads `events` from and writes the `cleaned` table to the DB at **project_config** `DATA_DIR` / `DB_FILENAME`. No CLI options. Each output record adds `cleaned_text` and `tokens`. Events with no semantic value are dropped.

```bash
python preprocess.py
```

***Stats with sqlite3***:
```bash
# Cleaned: total rows
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM cleaned;"

# Cleaned: by event type
sqlite3 data/raw/events.db "SELECT json_extract(event_data, '$.type'), COUNT(*) FROM cleaned GROUP BY 1 ORDER BY 2 DESC;"

# Cleaned: by date
sqlite3 data/raw/events.db "SELECT date(json_extract(event_data, '$.created_at')), COUNT(*) FROM cleaned GROUP BY 1 ORDER BY 1;"
```

---

#### (Optional) Browse comments (Markdown per repo) (`browse_comments.py`)

Convert preprocessed `events.db` to one Markdown file per repo, **organized by date**, for scrolling through comments with full metadata (id, repo, created_at, type, author_association, tokens, cleaned_text). Writes one `.md` per repo into the directory you pass (default: config `DATA_DIR`).

```bash
python browse_comments.py
python browse_comments.py ./data/raw
```

Uses the `cleaned` table if present, else `events`.

