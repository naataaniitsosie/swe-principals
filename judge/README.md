# Judge — LLM scoring for NSI/ISI conformity

The judge scores cleaned PR comments using an Ollama model and the rubric in [`docs/papers/CONFORMITY_SYSTEM_PROMPT.md`](../docs/papers/CONFORMITY_SYSTEM_PROMPT.md) (see also [CONFORMITY.md](../docs/papers/CONFORMITY.md)). It reads from the **cleaned** table and writes **scores** (NSI/ISI 0–3 plus reasoning) to the same SQLite DB.

## Prerequisites

1. **Ollama** installed and running (e.g. [ollama.ai](https://ollama.ai)).
2. **Python dependency:** from the repo root:
   ```bash
   pip install ollama
   ```
   Or install all project deps: `pip install -r requirements.txt`.
3. **At least one judge model** pulled in Ollama. Supported models (two for now):
   - **Llama:** `ollama pull llama3.1:8b`
   - **Gemma:** `ollama pull gemma2:27b`
4. **Data:** The **cleaned** table must exist in the project DB (run `python preprocess.py` after extraction if needed). Default DB path: `data/raw/events.db` (see `project_config.py`).

## How to run

From the **repository root** (not inside `judge/`):

```bash
# Score with default model (gemma)
python judge.py

# Use Llama instead
python judge.py --model llama

# Limit to 10 comments (useful for testing)
python judge.py --limit 10

# Skip comments already scored for this model (resume / avoid re-runs)
python judge.py --skip-existing

# Use a specific DB file
python judge.py --db path/to/events.db
```

## CLI options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--model` | `-m` | `gemma` | Model: `llama`, `gemma`, or an Ollama tag (e.g. `llama3.1:8b`). |
| `--limit` | `-n` | none | Maximum number of comments to score. |
| `--skip-existing` | — | off | Skip comments that already have a score for this model. |
| `--db` | — | `project_config` | Path to the SQLite database. |

## Database schema

One SQLite file (default `data/raw/events.db`) holds three tables:

| Table     | Written by       | Shape |
|-----------|------------------|--------|
| **events**  | `dataset.py`     | `id` (TEXT PK), `event_data` (TEXT, JSON). Raw GHArchive events. |
| **cleaned** | `preprocess.py`  | Normalized: `id`, `cleaned_text`, `tokens` only. Join with **events** on `id` for repo, created_at, type, author_association. |
| **scores**  | `judge.py`       | See below. |

**scores** table (judge output):

| Column         | Type    | Description |
|----------------|---------|-------------|
| `comment_id`   | TEXT    | Same as `id` in **cleaned** (FK to comment). |
| `model_name`   | TEXT    | Ollama model tag that produced this score (e.g. `llama3.1:8b`, `gemma2:27b`). |
| `nsi_score`    | INTEGER | NSI score 0–3. |
| `isi_score`    | INTEGER | ISI score 0–3. |
| `nsi_reasoning`| TEXT    | Model’s NSI reasoning. |
| `isi_reasoning`| TEXT    | Model’s ISI reasoning. |
| `created_at`   | TEXT    | Optional; copied from cleaned record. |
| **Primary key**|         | `(comment_id, model_name)`. |

## Output

- **Table:** `scores` in the same SQLite DB as `cleaned`.
- **Deduplication:** One row per `(comment_id, model_name)`. Re-running overwrites existing rows for that pair.

Example query:

```bash
sqlite3 data/raw/events.db "SELECT comment_id, model_name, nsi_score, isi_score FROM scores LIMIT 5;"
```

## Deleting the scores table

**WARNING: Do not do this unless you REALLY want to reprocess.** Dropping the `scores` table removes all judge output. The next run of `python judge.py` will score every comment again (no `--skip-existing` state). Use only when you need a full reset (e.g. new rubric, new DB, or intentional reprocess).

Default DB path (see `project_config.py`): `data/raw/events.db`.

```bash
sqlite3 data/raw/events.db "DROP TABLE IF EXISTS scores;"
```

To recreate the table (empty), run the judge once; it will create the table on first write. Or run `python judge.py --limit 1` and then delete that row if you only wanted the schema.

## Rubric

The system prompt and scoring rules are defined in [`docs/papers/CONFORMITY_SYSTEM_PROMPT.md`](../docs/papers/CONFORMITY_SYSTEM_PROMPT.md). `judge/rubric.py` loads that file verbatim as the system prompt. The model is asked to respond with a JSON object (see the prompt for the full key schema); the judge currently persists NSI/ISI fields (`nsi_reasoning`, `nsi_score`, `isi_reasoning`, `isi_score`) to SQLite.
