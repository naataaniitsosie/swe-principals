## Models and Inference


## Config

All data lives in one directory and one SQLite DB. Edit **`project_config.py`** at the repo root to change paths:

- **`DATA_DIR`** — directory for raw and cleaned data (default `data/raw`).
- **`DB_FILENAME`** — SQLite file name (default `events.db`).

Full DB path is `DATA_DIR / DB_FILENAME`. There is no CLI option to choose an output directory; everything uses this single DB.

---

## Database and table schema

The DB is a single SQLite file (see **`dataset_readers/gharchive/storage.py`** and **`docs/DB_SCHEMA.md`**).

| Table    | Written by        | Purpose |
|----------|-------------------|--------|
| **events**  | `dataset.py`      | Raw GitHub events from GHArchive. `id`, `event_data` (full JSON). |
| **cleaned** | `preprocess.py`   | Normalized: `id`, `cleaned_text`, `tokens` only (no duplication of raw). Join with **events** on `id` for repo, created_at, type, author_association. |
| **scores**  | `judge.py`        | LLM judge output. One row per (comment_id, model_name): `nsi_score`, `isi_score`, `nsi_reasoning`, `isi_reasoning` (0–3 scale per CONFORMITY rubric). |

- **events** schema and extraction: **`dataset_readers/gharchive/storage.py`**, **`dataset.py`**.
- **cleaned** (normalized): **`dataset_readers/gharchive/storage.py`** (`CLEANED_TABLE_SCHEMA`). Written by **`preprocessing/pipeline.py`**; readers JOIN with events for metadata.
- Reading **cleaned** and writing Markdown per repo: **`browse_comments.py`**. Output files: `DATA_DIR/<owner>_<repo>.md` (e.g. `data/raw/django_django.md`).

---

## Runnable scripts (pipeline)

Run in order: **1. Extract** → **2. Preprocess**. Optional: **browse_comments**, **judge**.

| Step | Script | Input | Output |
|------|--------|--------|--------|
| 1. Extract | `python dataset.py` | GHArchive (network) | `data/raw/events.db` |
| 2. Preprocess | `python preprocess.py` | config `DATA_DIR` | same DB (`cleaned` table) |

**Chaining:**
```bash
python dataset.py --start-date 2024-01-01 --end-date 2024-01-02
python preprocess.py
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

# Cleaned table (normalized): total and per-repo (join events for repo)
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM cleaned;"
sqlite3 data/raw/events.db "SELECT json_extract(e.event_data, '$.repo.name'), COUNT(*) FROM cleaned c JOIN events e ON e.id = c.id GROUP BY 1 ORDER BY 1;"
```

---

### 2. Preprocess data (`preprocess.py`)

Preprocess the single SQLite DB produced by `dataset.py`. Reads **events**, dedupes by event `id` (keep first), then per event: drop bot/CI and trivial comments, extract text, strip code blocks and images and diff snippets, lowercase and tokenize, drop if fewer than 2 tokens; writes normalized rows to **cleaned** (id, cleaned_text, tokens only; see [Database and table schema](#database-and-table-schema) and [docs/DB_SCHEMA.md](docs/DB_SCHEMA.md)). No CLI options. Details: [CONFORMITY.md § Preprocessing](papers/CONFORMITY.md) and `preprocessing/workflow.py` (`default_workflow`).

```bash
python preprocess.py
```

***Stats with sqlite3***:
```bash
# Cleaned: total rows
sqlite3 data/raw/events.db "SELECT COUNT(*) FROM cleaned;"

# Cleaned + events: by event type and by repo (metadata in events)
sqlite3 data/raw/events.db "SELECT json_extract(e.event_data, '$.type'), COUNT(*) FROM cleaned c JOIN events e ON e.id = c.id GROUP BY 1 ORDER BY 2 DESC;"
sqlite3 data/raw/events.db "SELECT json_extract(e.event_data, '$.repo.name') AS repo, COUNT(*) FROM cleaned c JOIN events e ON e.id = c.id GROUP BY 1 ORDER BY 1;"
sqlite3 data/raw/events.db "SELECT date(json_extract(e.event_data, '$.created_at')), COUNT(*) FROM cleaned c JOIN events e ON e.id = c.id GROUP BY 1 ORDER BY 1;"
```

---

#### (Optional) Browse comments (Markdown per repo) (`browse_comments.py`)

Reads **cleaned** via JOIN with **events** (normalized schema) and writes one Markdown file per repo under `DATA_DIR`, organized by date (e.g. `data/raw/django_django.md`). Output is always fresh: overwrites existing files and removes any repo `.md` files not in the current run. No CLI options; uses `project_config` for DB and output path.

```bash
python browse_comments.py
```

See [Database and table schema](#database-and-table-schema) and [docs/DB_SCHEMA.md](docs/DB_SCHEMA.md).

---

### Judge (LLM scoring) (`judge.py`)

Scores cleaned PR comments for NSI/ISI conformity using an Ollama model and the rubric in [CONFORMITY.md](papers/CONFORMITY.md). Reads from the **cleaned** table, writes to the **scores** table in the same DB. Deduplication is by `(comment_id, model_name)`.

**Supported models (two for now):** Llama and Gemma. Use short names or Ollama tags (e.g. `llama3.1:8b`, `gemma2:27b`).

```bash
python judge.py
python judge.py --model gemma --limit 10
python judge.py --model llama --skip-existing
```

| Flag | Default | Description |
|------|---------|--------------|
| `--model`, `-m` | `gemma` | Model: `llama`, `gemma`, or an Ollama tag. |
| `--limit`, `-n` | none | Max comments to score (for testing). |
| `--skip-existing` | off | Skip comments already scored for this model. |
| `--db` | `project_config` | Path to SQLite DB (default: `data/raw/events.db`). |

