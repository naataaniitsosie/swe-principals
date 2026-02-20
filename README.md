## Config

All data lives in one directory and one SQLite DB. Edit **`project_config.py`** at the repo root to change paths:

- **`DATA_DIR`** — directory for raw and cleaned data (default `data/raw`).
- **`DB_FILENAME`** — SQLite file name (default `events.db`).

Full DB path is `DATA_DIR / DB_FILENAME`. There is no CLI option to choose an output directory; everything uses this single DB.

---

## Database and table schema

The DB is a single SQLite file (see **`dataset_readers/gharchive/storage.py`**). It has two tables; both use the same column layout: `id` (TEXT PRIMARY KEY), `event_data` (TEXT, JSON).

| Table    | Written by        | Purpose |
|----------|-------------------|--------|
| **events**  | `dataset.py`      | Raw GitHub events from GHArchive. `event_data` is the full event (e.g. `repo`, `type`, `created_at`, `payload` with comment/review/PR data). |
| **cleaned** | `preprocess.py`   | Preprocessed comments only. `event_data` is a slim JSON object with: `id`, `cleaned_text`, `repo`, `created_at`, `type`, `author_association`, `tokens`. |

- **events** schema and extraction: **`dataset_readers/gharchive/storage.py`**, **`dataset.py`**.
- **cleaned** schema (slim fields): **`preprocessing/workflow.py`** (`slim_output`).
- Reading **cleaned** and writing Markdown per repo: **`browse_comments.py`**. Output files: `DATA_DIR/<owner>_<repo>.md` (e.g. `data/raw/django_django.md`).

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

Output is a single SQLite file `events.db` with an **events** table (see [Database and table schema](#database-and-table-schema)).

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

Preprocess the single SQLite DB produced by `dataset.py`. Reads **events**, dedupes by event `id` (keep first), then per event: drop bot/CI and trivial comments, extract text, strip code blocks and images and diff snippets, lowercase and tokenize, drop if fewer than 2 tokens; writes slim records to **cleaned** (see [Database and table schema](#database-and-table-schema)). No CLI options. Details: [CONFORMITY.md § Preprocessing](papers/CONFORMITY.md) and `preprocessing/workflow.py` (`default_workflow`).

```bash
python preprocess.py
```

***Stats with sqlite3***:
```bash
# Cleaned: total rows
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM cleaned;"

# Cleaned: by event type
sqlite3 data/raw/events.db "SELECT json_extract(event_data, '$.type'), COUNT(*) FROM cleaned GROUP BY 1 ORDER BY 2 DESC;"

# Rows per repo (cleaned: repo is inside event_data JSON)
sqlite3 data/raw/events.db "SELECT json_extract(event_data, '$.repo') AS repo, COUNT(*) FROM cleaned GROUP BY 1 ORDER BY 1;"

# Cleaned: by date
sqlite3 data/raw/events.db "SELECT date(json_extract(event_data, '$.created_at')), COUNT(*) FROM cleaned GROUP BY 1 ORDER BY 1;"
```

---

#### (Optional) Browse comments (Markdown per repo) (`browse_comments.py`)

Reads the **cleaned** table and writes one Markdown file per repo under `DATA_DIR`, organized by date (e.g. `data/raw/django_django.md`). No CLI options. See [Database and table schema](#database-and-table-schema).

```bash
python browse_comments.py
```

