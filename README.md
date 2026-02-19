## Config

All data lives in one directory and one SQLite DB. Edit **`project_config.py`** at the repo root to change paths:

- **`DATA_DIR`** — directory for raw and cleaned data (default `data/raw`).
- **`DB_FILENAME`** — SQLite file name (default `events.db`).

Full DB path is `DATA_DIR / DB_FILENAME`. There is no CLI option to choose an output directory; everything uses this single DB.

---

## Runnable scripts (pipeline)

Run in order: **1. Extract** → **1.5 Dataset stats** (optional) → **2. Preprocess** → **3. Analyze** (e.g. sentiment). Each script reads from the previous step’s output.

| Step | Script | Input | Output |
|------|--------|--------|--------|
| 1. Extract | `python dataset.py` | GHArchive (network) | `data/raw/events.db` (single SQLite DB; `repo` column for querying) |
| 1.5 Stats | `python dataset_stats.py` | config `DATA_DIR` | stdout (total / unique / duplicates per repo) |
| 2. Preprocess | `python preprocess.py` | config `DATA_DIR` | same DB (`cleaned` table) |
| 3. Analyze | `python sentiment.py` | `data/raw` or `data/cleaned` | `./data/sentiment` |

**Chaining (one db at config DATA_DIR):**
```bash
python dataset.py --start-date 2024-01-01 --end-date 2024-01-02
python dataset_stats.py
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

Output is a single SQLite file `events.db` with an `events` table. Indexed columns for querying:

| Attribute | Description |
|-----------|-------------|
| `repo` | Repository (e.g. `django/django`) |
| `created_at` | ISO timestamp for time range and ordering |
| `type` | Event type (IssueCommentEvent, PullRequestEvent, etc.) |
| `author_association` | MEMBER, CONTRIBUTOR, NONE, etc. |
| `actor_login` | GitHub login of the actor |

---

### 1.5 (Optional) Dataset stats (`dataset_stats.py`)

Report stats about the data from the dataset: **total**, **unique** (by event id), and **duplicate** counts per repo (from the single `events.db`). Chainable after `dataset.py`; pass directory containing `events.db` (default: config `DATA_DIR`).

```bash
python dataset_stats.py
python dataset_stats.py ./data/raw
```

| Argument | Default | Description |
|----------|---------|-------------|
| `dir` | config `DATA_DIR` | Directory containing `events.db` |
| `--db` DIR | — | Use this directory for `events.db` instead of dir |
| `--no-header` | — | Omit header row (e.g. for piping) |

---

### 2. Preprocess data (`preprocess.py`)

Preprocess the single SQLite DB produced by `dataset.py` (CONFORMITY.md Preprocessing): **dedupe by event id** (keep first), remove bot and CI comments, strip code blocks and diff snippets, drop trivial comments (e.g. “LGTM”, “Thanks!”), lowercase and tokenize. Reads `events` from the DB in config `DATA_DIR` and writes the `cleaned` table into the same DB. Each output record adds `cleaned_text` and `tokens`. Events with no semantic value are dropped.

```bash
python preprocess.py
```

```bash
python preprocess.py -i ./data/raw
```

| Flag | Default | Description |
|------|---------|-------------|
| `--input-dir`, `-i` | config `DATA_DIR` | Directory containing `events.db` (input and output are the same DB) |

---

#### (Optional) Browse comments (Markdown per repo) (`browse_comments.py`)

Convert preprocessed `events.db` to one Markdown file per repo, **organized by date**, for scrolling through comments with full metadata (id, repo, created_at, type, author_association, tokens, cleaned_text). Writes one `.md` per repo into the directory you pass (default: config `DATA_DIR`).

```bash
python browse_comments.py
python browse_comments.py ./data/raw
```

Uses the `cleaned` table if present, else `events`. You can run `dataset_stats.py` with the same dir to see per-repo stats.

