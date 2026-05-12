# Judge — LLM scoring (FUN / NSI / INSI / ISI)

The judge scores cleaned PR comments using **Ollama** (local) or the **OpenAI API**, with the rubric in [`docs/papers/CONFORMITY_SYSTEM_PROMPT.md`](../docs/papers/CONFORMITY_SYSTEM_PROMPT.md) (see also [CONFORMITY.md](../docs/papers/CONFORMITY.md)). It reads from the **cleaned** table and writes **scores**: for each dimension **FUN, NSI, INSI, ISI** — reasoning text plus a 0–3 score (same JSON schema as the prompt).

**Quick note:** Judges are chosen for size consistency so comparisons are not confounded by models that are too powerful or too weak for the rubric.

## Social Judges (NSI/INSI Detection)

*These models focus on human nuance, social psychology, and stylistic gatekeeping.*

*Size: dense models list total parameters; Mixture of Experts (MoE) models list active parameters with total MoE parameters in parentheses; em dash when the vendor does not publish counts (API-only judges).*

| Model | Size | Role | Access |
|-------|------|------|--------|
| Claude Sonnet 4.6 | — | Primary Social Judge. Expert at detecting passive-aggression and social cues. | OpenRouter |
| Gemma 4 31B | 31B | Logical Consistency. Identifies contradictory rules and "principled" social errors. | Ollama |
| Mistral Large 3 | 41B active (675B MoE) | Cultural Baseline. Provides a non-US centric perspective on social interactions. | OpenRouter |
| Phi-4-Reasoning-Vision-15B | 15B | CoT Specialist. Ideal for generating long Chain-of-Thought reasoning for "vibes." | Ollama |
| GPT-5.4 mini | — | The Control Group. Standardized baseline for intent and instruction following. | OpenAI API |

## Technical Judges (FUN/ISI Detection)

*These models focus on rigid syntax, functional correctness, and performance logic.*

| Model | Size | Role | Access |
|-------|------|------|--------|
| DeepSeek-V3.2 | 37B active (671B MoE) | SOTA Code Intelligence. Best for distinguishing logic flaws from stylistic choices. | OpenRouter |
| Qwen3-Coder-Next | 3B active (80B MoE) | Local Powerhouse. Specialized in deep syntax and repository-wide standards. | Ollama |
| o4-mini | — | Logical Verifier. Uses internal reasoning to verify if technical claims are factually true. | OpenAI API |
| StarCoder 2 15B Instruct | 15B | Socially Blind. Trained on raw code data; treats social pressure as irrelevant noise. | Ollama |
| Granite Code 34B | 34B | Enterprise Rigor. Detects "hardened" standards vs. subjective developer preferences. | Ollama |

## Prerequisites

1. **Backend (pick one or both):**
   - **Ollama:** installed and running ([ollama.ai](https://ollama.ai)). Pull a model, e.g. `ollama pull llama3.1:8b`.
   - **OpenAI:** `pip install openai` (included in `requirements.txt`). Set **`OPENAI_API_TOKEN`** for the OpenAI API. **Default:** put it in a **`.env`** file at the **repository root** (same folder as `project_config.py`); it is loaded automatically when you run the judge—no need to `export` unless you prefer. Do not commit `.env` (it is gitignored). Default API model: `gpt-5.4-mini` (override with `--model`).
2. **Python deps:** from the repo root: `pip install -r requirements.txt`.
3. **Data:** The **cleaned** table must exist in the project DB (run `python preprocess.py` after extraction if needed). Default DB path: `data/raw/events.db` (see `project_config.py`).

## How to run

From the **repository root** (not inside `judge/`):

```bash
# Ollama (default backend), default short model from judge/config.py
python judge.py

python judge.py --model llama

# OpenAI Chat Completions (OPENAI_API_TOKEN in .env at repo root, or export)
python judge.py --backend openai

python judge.py --backend openai --model gpt-5.4-mini

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
| `--backend` | `-b` | `ollama` | `ollama` (local) or `openai` (API; needs `OPENAI_API_TOKEN`). |
| `--model` | `-m` | see help | Ollama: short name (`llama`, `gemma`) or full tag. OpenAI: API model id. Defaults differ per backend. |
| `--limit` | `-n` | none | Maximum number of comments to score. |
| `--skip-existing` | — | off | Skip comments that already have a score for this model. |
| `--db` | — | `project_config` | Path to the SQLite database. |
| `--repo` | `-r` | see `project_config` | Restrict to one repo (`owner/name`), or empty for all. |

## Database schema

One SQLite file (default `data/raw/events.db`) holds three tables:

| Table     | Written by       | Shape |
|-----------|------------------|--------|
| **events**  | `dataset.py`     | `id` (TEXT PK), `event_data` (TEXT, JSON). Raw GHArchive events. |
| **cleaned** | `preprocess.py`  | Normalized: `id`, `cleaned_text`, `tokens` only. Join with **events** on `id` for repo, created_at, type, author_association. |
| **scores**  | `judge.py`       | See below. |

**scores** table (judge output): see [`docs/DB_SCHEMA.md`](../docs/DB_SCHEMA.md) for the full column list. In short: `fun_*`, `nsi_*`, `insi_*`, `isi_*` (score + reasoning each), plus `created_at`.

| Column | Description |
|--------|-------------|
| `comment_id`, `model_name` | Primary key. |
| `fun_score`, `fun_reasoning` | Functional / hard-constraint dimension. |
| `nsi_score`, `nsi_reasoning` | Explicit normative social influence. |
| `insi_score`, `insi_reasoning` | Implicit normative social influence. |
| `isi_score`, `isi_reasoning` | Informational / expert influence. |
| `created_at` | Optional; from cleaned record. |

## Output

- **Table:** `scores` in the same SQLite DB as `cleaned`.
- **Deduplication:** One row per `(comment_id, model_name)`. Re-running overwrites existing rows for that pair.

Example query:

```bash
sqlite3 data/raw/events.db "SELECT comment_id, model_name, nsi_score, isi_score FROM scores LIMIT 5;"
```

To **print** scored comments in a readable Markdown layout (same rubric as the prompt), use **`browse_scores.py`** at the repo root. **`--model`** must match `scores.model_name` exactly (Ollama tag or OpenAI id). Example for the default OpenAI mini model:

```bash
python browse_scores.py --model gpt-5.4-mini --sample-n 15
```

## Clear all scores — **dangerous**

> **Warning — destructive:** This **drops the entire `scores` table** and removes **all** LLM judge rows for **every** model. You **cannot** recover them. **Does not** delete `events` or `cleaned`. Only run when you deliberately want a full reset (re-rubric, bad run, outdated schema, or re-score from scratch).

Default DB path is `project_config.DATA_DIR / DB_FILENAME` (usually `data/raw/events.db`). Use your `--db` path if you override it.

```bash
sqlite3 data/raw/events.db "DROP TABLE IF EXISTS scores;"
```

The next `python judge.py` will recreate `scores` on first write. If you had an old table without FUN/INSI columns, dropping once also lets the judge create the [current schema](../docs/DB_SCHEMA.md#table-scores).

## Rubric

The system prompt and scoring rules are defined in [`docs/papers/CONFORMITY_SYSTEM_PROMPT.md`](../docs/papers/CONFORMITY_SYSTEM_PROMPT.md). `judge/rubric.py` loads that file verbatim as the system prompt. The model must return a single JSON object with all eight keys (`fun_*`, `nsi_*`, `insi_*`, `isi_*`); the judge parses and persists every field to SQLite.

Implementation: [`judge/ollama_judge.py`](ollama_judge.py) (Ollama), [`judge/gpt_judge.py`](gpt_judge.py) (OpenAI), shared parsing in [`judge/judge_result.py`](judge_result.py).
