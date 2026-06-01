## Pipeline Overview

```
  ╔══════════════════════════════════════════════════════════════════╗
  ║                     GHArchive  (network)                        ║
  ║          hourly .gz archives · public GitHub event stream       ║
  ╚══════════════════════════════╦═════════════════════════════════╝
                                 ║
                        ┌────────▼────────┐
                        │   dataset.py    │  ← filter by repo + event type
                        └────────┬────────┘
                                 │ writes
                         ┌───────▼───────┐
                         │    events     │  raw JSON blobs
                         └───────┬───────┘
                                 │
                        ┌────────▼────────┐
                        │  preprocess.py  │  ← dedupe · drop bots · clean text
                        └────────┬────────┘
                                 │ writes
                         ┌───────▼───────┐◀────────────────────────────────────┐
                         │    cleaned    │  id · cleaned_text · tokens          │
                         └───────┬───────┘                                      │
                                 │                              browse_comments.py
                        ┌────────▼────────┐                    Markdown per repo
                        │   sample.py     │  ← stratified sample               │
                        │                 │    repo × event_type strata         │
                        │                 │    floor 25 / cap 50 / per-stratum  │
                        │                 │    seeded · deterministic           │
                        └────────┬────────┘                                     │
                                 │ writes                                        │
                         ┌───────▼───────┐                                      │
                         │    samples    │  id · repo · event_type              │
                         └───────┬───────┘                           data_explorer.ipynb
                                 │                                   events + cleaned
                        ┌────────▼────────┐                          pre-score EDA
                        │    judge.py     │  ← LLM scoring (Ollama / OpenAI)
                        └────────┬────────┘
                                 │ writes
                         ┌───────▼───────┐◀────────────────────────────────────┐
                         │    scores     │  FUN · NSI · INSI · ISI  (0–3)      │
                         └───────────────┘                                      │
                                                               browse_scores.py │
                                                               stdout inspection │
                                                                                 │
                                                           score_analysis.ipynb │
                                                           score stats · charts  │
                                                                                 │
                                                           ──────────────────────┘
```

**Two scoring tracks** (derived from `event_type` at query time):

```
  Track 1 — Reviewer pressure              Track 2 — Contributor signaling
  ──────────────────────────────           ───────────────────────────────────
  PullRequestReviewEvent                   PullRequestEvent
  PullRequestReviewCommentEvent
  IssueCommentEvent

  Prompt: CONFORMITY_SYSTEM_PROMPT         Prompt: CONTRIBUTOR_CONFORMITY_SYSTEM_PROMPT
  Scores: FUN / NSI / INSI / ISI           Scores: A-NSI / A-ISI
```

---

## Installation

### Prerequisites
- **Python 3.10+** (recommend using `miniconda` or `conda`)
- **SQLite 3** (included with Python)

### Step 1: Create and activate the conda environment

```bash
conda create -n swe-principals python=3.10
conda activate swe-principals
```

### Step 2: Install core dependencies

```bash
pip install -r requirements.txt
```

This installs: `requests`, `transformers`, `torch`, `ollama`, `openai`, `python-dotenv`.

### Step 3 (Optional): Install notebook dependencies

```bash
pip install -r requirements-notebooks.txt
```

This adds: `pandas`, `matplotlib`, `jupyter`, `ipykernel`.

### Step 4 (Optional): Set up Jupyter kernel

```bash
python -m ipykernel install --user --name swe-principals --display-name "Python (swe-principals)"
```

Then select **"Python (swe-principals)"** from the kernel dropdown in VSCode.

### Environment Variables

Create a `.env` file in the repository root for secrets (e.g., OpenAI API token):

```bash
echo "OPENAI_API_TOKEN=sk-..." > .env
```

`.env` is listed in `.gitignore` — do not commit it.

---

## Config

All data lives in one directory and one SQLite DB. Edit **`project_config.py`** at the repo root to change paths:

- **`DATA_DIR`** — directory for raw and cleaned data (default `data/raw`).
- **`DB_FILENAME`** — SQLite file name (default `events.db`).

Full DB path is `DATA_DIR / DB_FILENAME`. On import, `project_config` loads a `.env` file from the repository root (if present) via `python-dotenv`. Use this for secrets such as `OPENAI_API_TOKEN` — no need to `export` manually.

---

## Scripts

Run in order: **1. Extract** → **2. Preprocess** → **3. Sample** → **4. Judge**.

| Step | Script | Input | Output | Docs |
|------|--------|-------|--------|------|
| 1. Extract | `python dataset.py` | GHArchive (network) | `events` table | [dataset_readers/README.md](dataset_readers/README.md) |
| 2. Preprocess | `python preprocess.py` | `events` table | `cleaned` table | [preprocessing/README.md](preprocessing/README.md) |
| 3. Sample | `python sample.py` | `cleaned` table | `samples` table | [sampling/README.md](sampling/README.md) |
| 4. Judge | `python judge.py` | `samples` table | `scores` table | [judge/README.md](judge/README.md) |
| — | `python browse_comments.py` | `cleaned` table | Markdown per repo | — |
| — | `python browse_scores.py` | `scores` + `cleaned` | stdout inspection | — |
| — | `notebooks/data_explorer.ipynb` | `events` + `cleaned` | pre-score EDA | [notebooks/README.md](notebooks/README.md) |
| — | `notebooks/score_analysis.ipynb` | `scores` | score stats + charts | [notebooks/README.md](notebooks/README.md) |

**Quick chain:**
```bash
python dataset.py --start-date 2023-01-01 --end-date 2025-12-31
python preprocess.py
python sample.py
python judge.py
```

For long extraction runs, wrap with `caffeinate` to prevent macOS sleep:
```bash
caffeinate python dataset.py --start-date 2023-01-01 --end-date 2025-12-31
```

### 1. Extract (`dataset.py`)

Pulls GitHub events from GHArchive for all 10 repositories and writes raw JSON blobs to the `events` table. See [dataset_readers/README.md](dataset_readers/README.md) for flags, reader architecture, and the BigQuery decision log.

```bash
python dataset.py --start-date 2023-01-01 --end-date 2025-12-31
```

| Flag | Default | Description |
|------|---------|-------------|
| `--dataset-reader`, `-r` | `gharchive` | Reader to use |
| `--start-date` | `2024-02-01` | Start date (YYYY-MM-DD) |
| `--end-date` | `2024-02-02` | End date (YYYY-MM-DD, inclusive) |

### 2. Preprocess (`preprocess.py`)

Cleans `events` → `cleaned`: dedupes by ID, drops bot/CI actors, strips code blocks / images / diff lines, lowercases, tokenizes, retains any event with at least `--min-tokens` tokens (default: 1 — any non-empty text). See [preprocessing/README.md](preprocessing/README.md) for all cleaning steps, drop rules, and how to extend the workflow.

```bash
python preprocess.py                  # retain all non-empty text (default)
python preprocess.py --min-tokens 5  # require at least 5 tokens
```

### 3. Sample (`sample.py`)

Draws a deterministic stratified sample from `cleaned` into `samples`. Strata: `repo × event_type`; floor 25 / cap 50 per stratum; per-stratum seeding. Re-running drops and recreates `samples`. See [sampling/README.md](sampling/README.md) for full design rationale and determinism guarantees.

```bash
python sample.py
```

### 4. Judge (`judge.py`)

Scores sampled comments via Ollama (local) or OpenAI. Reads `samples`, writes `scores`. See [judge/README.md](judge/README.md) for the full flag reference, model list, and rubric details.

```bash
python judge.py --model gemma4-e4b --limit 10
python judge.py --backend openai --model gpt-5.4-mini --skip-existing
```

| Flag | Default | Description |
|------|---------|-------------|
| `--backend`, `-b` | `ollama` | `ollama` or `openai` |
| `--model`, `-m` | backend default | Model name or tag |
| `--limit`, `-n` | none | Max comments to score |
| `--skip-existing` | off | Skip already-scored comments for this model |
| `--db` | `project_config` | Path to SQLite DB |
| `--repo`, `-r` | all | Restrict to one repo (`owner/name`) |

### Browse (`browse_comments.py`, `browse_scores.py`)

```bash
# Write one Markdown file per repo to DATA_DIR (no flags)
python browse_comments.py

# Print scored comments to stdout (--model must match scores.model_name exactly)
python browse_scores.py --model gpt-5.4-mini --sample-n 15
python browse_scores.py --model gemma4:e4b --all > sample_scores.md
```

`browse_scores.py` flags: `--model` (required), `--sample-n` (default 20), `--all`, `--comment-id`, `--db`.

---

## Database

Single SQLite file at `DATA_DIR/DB_FILENAME` (default `data/raw/events.db`). Full schema: [docs/DB_SCHEMA.md](docs/DB_SCHEMA.md).

| Table | Written by | Contents |
|-------|-----------|---------|
| `events` | `dataset.py` | Raw GHArchive events: `id`, `event_data` (full JSON blob) |
| `cleaned` | `preprocess.py` | `id`, `cleaned_text`, `tokens` — join with `events` on `id` for repo/date/type metadata |
| `samples` | `sample.py` | Selected IDs: `id`, `repo`, `event_type`, `stratum_key` |
| `scores` | `judge.py` | One row per `(comment_id, model_name)`: FUN/NSI/INSI/ISI score + reasoning each |

For common queries (score distributions, coverage checks, per-repo breakdowns), see [docs/QUERIES.md](docs/QUERIES.md).
