# Judge — LLM scoring (FUN / NSI / INSI / ISI)

The judge scores PR comments from the stratified sample using the rubric in [`papers/publication1/CONFORMITY_SYSTEM_PROMPT.md`](../papers/publication1/CONFORMITY_SYSTEM_PROMPT.md). It reads from the **`samples`** table and writes **`scores`**: for each dimension **FUN, NSI, INSI, ISI** — a 0–3 score plus reasoning text.

## Two scoring modes (module layout)

| Sub-package | Status | What it does |
|-------------|--------|--------------|
| [`detection/`](detection/) | **Implemented** — this is what `judge.py` runs | Score each comment in isolation; no thread context |
| [`contextual/`](contextual/) | **Not implemented** | Score comments in the context of their PR thread or repo |

---

## Models

The `--model` flag selects the model **and** determines the backend automatically. The resolved backend and location are logged at run start.

### Why frontier-only, no social/technical split

An earlier design split models into "social judges" (NSI/INSI) and "technical judges" (FUN/ISI) based on training focus. That split was retired for three reasons:

1. **The capability asymmetry no longer exists at the frontier.** Models like Claude Sonnet and Gemma 4 27B score all four dimensions reliably — specialized code models no longer have a meaningful edge on FUN/ISI.
2. **It adds unjustifiable methodological complexity.** The social/technical split would need to be defended in the paper, and the justification is weaker now than it was two years ago.
3. **Disagreements become uninterpretable.** If a social judge and a technical judge disagree on FUN/ISI scores, there is no clean way to determine whether the disagreement is a real signal or model-specific calibration noise.

The replacement strategy: run all frontier judges on all four dimensions, then measure inter-rater agreement across models as the reliability signal.

### Frontier judges

Each model scores all four dimensions (FUN, NSI, INSI, ISI). Inter-rater agreement across models is the primary reliability measure.

| CLI name | Size | Tag / ID | Hosted at | Role |
|----------|------|----------|-----------|------|
| `claude-sonnet` | — | `anthropic/claude-sonnet-4-6` | OpenRouter | Primary judge. Strong instruction following and social reasoning. |
| `gemma4-27b` | 27B | `gemma4:27b` | local Ollama | Local workhorse. ~14 GB Q4, fits comfortably on 34 GB Mac. `ollama pull gemma4:27b` |
| `gpt-5.4-mini` | — | `gpt-5.4-mini` | OpenAI API | Standardised baseline. Fast and cheap for full-sample runs. |
| `deepseek-v3` | 37B active (671B MoE) | `deepseek/deepseek-chat-v3-0324` | OpenRouter | Fourth perspective. Strong general reasoning. [HF](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) |

### Smoke test models

Fast, low-quality models for verifying the pipeline end-to-end before committing to a full run. **Do not use for production scoring.**

| CLI name | Size | Tag / ID | Hosted at | Notes |
|----------|------|----------|-----------|-------|
| `gemma4-e4b` | 4B effective | `gemma4:e4b` | local Ollama | Smoke test proxy for `gemma4-27b`. `ollama pull gemma4:e4b` |
| `starcoder2-3b` | 3B | `starcoder2:3b` | local Ollama | Lightweight smoke test. `ollama pull starcoder2:3b` |

---

### Running the full judge suite

The intended workflow is to run all four frontier models on the full sample, then compare agreement:

```bash
# 1. Smoke test: verify pipeline and JSON output before committing
python judge.py -m gemma4-e4b -n 20 -r expressjs/express
python browse_scores.py --model gemma4:e4b --sample-n 15

# 2. Full runs — one per frontier model
python judge.py -m gemma4-27b  --skip-existing
python judge.py -m claude-sonnet --skip-existing
python judge.py -m gpt-5.4-mini --skip-existing
python judge.py -m deepseek-v3  --skip-existing
```

Inter-rater agreement (e.g. Krippendorff's α or ICC) is then computed across all four models per dimension. Dimensions where models agree are reliable; dimensions where they diverge need human adjudication (Objective 2).

---

## Prerequisites

- **Ollama models:** Ollama installed and running. Pull the model first (see `ollama pull` commands in the tables above).
- **OpenAI models:** `OPENAI_API_TOKEN` in `.env` at the repo root (or exported).
- **OpenRouter models:** `OPENROUTER_API_TOKEN` in `.env` at the repo root (or exported).
- **Data:** `samples` table must exist (run `python sample.py` if not).

## How to run

```bash
# Local Ollama
python judge.py -m gemma4-27b --skip-existing

# OpenAI
python judge.py -m gpt-5.4-mini --skip-existing

# OpenRouter
python judge.py -m claude-sonnet --skip-existing

# Smoke test: 10 comments from one repo
python judge.py -m gemma4-e4b -n 10 -r expressjs/express

# Dry run: see what would be scored without calling the model
python judge.py -m gemma4-27b --dry-run

# Score only inline diff comments across all repos
python judge.py -m gemma4-27b -e PullRequestReviewCommentEvent --skip-existing
```

## CLI options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--model` | `-m` | **required** | Model name from the registry above. |
| `--limit` | `-n` | none | Max comments to score (smoke tests). |
| `--skip-existing` | — | off | Skip `(comment_id, model)` pairs already in `scores`. |
| `--repo` | `-r` | all repos | Filter to one repo (`owner/name`). |
| `--event-type` | `-e` | all types | Filter to one event type (e.g. `PullRequestReviewCommentEvent`). |
| `--dry-run` | — | off | Print per-stratum counts; do not call the model. |

---

## Experiment versioning

`EXPERIMENT_VERSION` in `judge/storage.py` is an integer constant baked into every `scores` row. It is part of the primary key — `(comment_id, model_name, experiment_version)` — so the same comment scored by the same model across multiple experiments produces separate rows, all kept in the table. Think of it as a multi-tenant table: each version is its own namespace. Five full experiments across ten models could accumulate 10k+ rows without any conflicts.

**To start a new experiment run:** bump `EXPERIMENT_VERSION` in `judge/storage.py` and re-run `judge.py`. No existing rows are touched.

**Do not drop the scores table.** It is the permanent record of all scoring work. `--skip-existing` already scopes to the current version, so re-running is safe.

**Always filter by version in analysis queries:**
```sql
SELECT * FROM scores WHERE experiment_version = 1 AND parse_ok = 1;
```

---

## Output

- **Table:** `scores` in `data/raw/events.db`.
- **Primary key:** `(comment_id, model_name)` — re-runs overwrite existing rows for that pair.
- **Schema:** see [`docs/DB_SCHEMA.md`](../docs/DB_SCHEMA.md#table-scores).

Quick check:
```bash
sqlite3 data/raw/events.db "SELECT model_name, COUNT(*), AVG(nsi_score) FROM scores WHERE parse_ok=1 GROUP BY model_name;"
```

Browse scored comments in a readable layout:
```bash
python browse_scores.py --model gemma4:27b --sample-n 15
```

---

## Implementation

| Module | Role |
|--------|------|
| `config.py` | `MODEL_REGISTRY` — name → `(backend, tag, location)` |
| `detection/runner.py` | Orchestration: resolve model → judge → batch-write scores |
| `detection/storage.py` | `SamplesReader` — `samples JOIN cleaned` with filters |
| `storage.py` | `ScoresWriter`, `get_scored_comment_ids`, `EXPERIMENT_VERSION` |
| `judge_result.py` | `JudgeResult` dataclass; JSON parsing shared across all backends |
| `rubric.py` | Loads `CONFORMITY_SYSTEM_PROMPT.md` as the system prompt |
| `gpt_judge.py` | OpenAI backend |
| `openrouter_judge.py` | OpenRouter backend (OpenAI-compatible) |
| `ollama_judge.py` | Ollama backend |
