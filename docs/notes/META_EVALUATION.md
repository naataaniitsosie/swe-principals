# Meta-Evaluation: Preference-Based Judge Validation

**Purpose:** Measure agreement between LLM judge scores and human preference rankings across FUN, NSI, INSI, and ISI dimensions.

**Methodology:** For each dimension, collect human preferences on comment pairs, then measure how consistently each model's scores align with those preferences.

---

## Overview

1. Run two judge models on 2K cleaned `django/django` comments
2. Create stratified preference pairs for each dimension
3. Collect human preference rankings (which comment exhibits more of the dimension?)
4. Measure model agreement with human preference
5. Report raw agreement scores by model × dimension

**Output:** Agreement scores showing where each model aligns with human judgment. Interpretation of patterns belongs in CONFORMITY.md.

---

## Models

See [`docs/notes/MODEL_LIST.md`](MODEL_LIST.md) for full specifications. For this evaluation, we use:

| Role | Model | Access |
|------|-------|--------|
| **Model 1** | Gemma 4 E4B | Ollama (`gemma4-e4b` -> `gemma4:e4b`; 4B effective, faster local social/general judge) |
| **Model 2** | StarCoder 2 3B | Ollama (`starcoder2-3b` -> `starcoder2:3b`; closest StarCoder2 size class to Gemma 4 E4B) |

Both models score all four dimensions (FUN, NSI, INSI, ISI).

---

## Preference Pair Selection

### Scope
- **Total pairs:** ~160–200 (40–50 pairs per dimension)
- **Stratification:** Balanced across event types within `django/django`
- **Source:** 2K cleaned `django/django` PR comments

### Pair Criteria

Each pair (Comment A, Comment B) should show **clear difference** on one target dimension. Comments should be selected so that one plausibly exhibits more of the construct than the other.

**Examples (for reference, not exhaustive):**

| Dimension | Comment A (Low) | Comment B (High) |
|-----------|-----------------|-----------------|
| **FUN** | "Consider error handling" | "This will crash if x is null" |
| **NSI** | "This could be clearer" | "We use camelCase. Please update." |
| **INSI** | "This seems off" | "Are we really doing it this way?" |
| **ISI** | "This is inefficient" | "The docs recommend using X for this" |

### Selection Process

1. Manually curate pairs by reading comments
2. OR: Use cluster analysis to find high-variance comments per dimension
3. Record pair ID, Comment A, Comment B, target dimension
4. Save to: `data/meta_eval/preference_pairs.jsonl`

---

## Human Preference Collection

### Format

For each pair:

```
Pair ID: [dim]_[number]
Target dimension: NSI
Comment A: [text]
Comment B: [text]

Question: Which comment exhibits MORE [dimension name]?
Options:
  - Comment A
  - Comment B
  - Both equally
  - Neither
```

### Scale

If using a confidence scale, record 1–5 (1=uncertain, 5=very confident).

### Raters

Minimum 1 rater per pair; 2–3 recommended for reliability checks.

### Output Format

```jsonl
{
  "pair_id": "nsi_001",
  "dimension": "nsi",
  "comment_a": "...",
  "comment_b": "...",
  "human_preference": "B",
  "rater_id": "rater_1",
  "confidence": 5
}
```

Save to: `data/meta_eval/human_preferences.jsonl`

---

## Model Scoring

### Run Models on Django Comments

```bash
# Score 2K django/django comments with both models
python judge.py --backend ollama --model gemma4-e4b --repo django/django --limit 2000
python judge.py --backend ollama --model starcoder2-3b --repo django/django --limit 2000
```

Output: Both models score 2K `django/django` comments on all four dimensions. Scores stored in SQLite `scores` table.

#### macOS: Preventing Sleep During Long Runs

Scoring 2K `django/django` comments takes hours. On macOS, the system will sleep and pause Ollama unless prevented. Use `caffeinate` to keep the system awake:

```bash
# Prevent idle and system sleep during model scoring
caffeinate -i -s python judge.py --backend ollama --model gemma4-e4b --repo django/django --limit 2000
caffeinate -i -s python judge.py --backend ollama --model starcoder2-3b --repo django/django --limit 2000
```

**`caffeinate` flags:**
- `-i` — Prevent idle sleep (keeps CPU active)
- `-s` — Prevent system sleep (only works when plugged in to power)
- `-d` — Also prevent display sleep (optional; not needed for CLI runs)

`caffeinate` only stays active while its child process (here, `python judge.py`) is running. When the script exits, normal sleep behavior resumes.

**Recommended setup:**
1. Plug your Mac into power before starting
2. Close unnecessary applications
3. Use `caffeinate -i -s` (allows display to sleep but keeps system running)
4. Consider running overnight

### Extract Pair Scores

For each pair and each model:

```
Pair ID: nsi_001

Model: gemma4:e4b
  Comment A: fun=1, nsi=1, insi=1, isi=1
  Comment B: fun=1, nsi=3, insi=1, isi=1

Model: starcoder2:3b
  Comment A: fun=1, nsi=1, insi=1, isi=1
  Comment B: fun=1, nsi=2, insi=1, isi=1
```

For evaluation, extract only the target dimension score.

---

## Agreement Measurement

### Definition

For each pair and model, determine if the model's ranking matches human preference:

```
Human preference: B > A
Model scores on dimension:
  - A_score vs B_score

Model agrees: B_score > A_score (or A_score > B_score if human pref is A, etc.)
Model disagrees: otherwise
```

### Metrics

**Agreement rate (per model, per dimension):**

```
agreement_rate = (# pairs where model agrees with human) / (total pairs)
```

**Example output:**

```
Dimension | Gemma4 E4B (%) | StarCoder2 3B (%)
----------|----------------|---------------
FUN       | 92%            | 88%
NSI       | 78%            | 62%
INSI      | 81%            | 71%
ISI       | 89%            | 85%
```

### Tie-Breaking

If human preference is "both equally" or "neither," mark as "no preference" and exclude from agreement calculation (or handle separately).

---

## Success Criteria

Minimum thresholds for each model × dimension combination:

| Threshold | Applies To |
|-----------|-----------|
| ≥ 85% | Any model on any dimension |
| ≥ 75% | Minimum acceptable (below this requires investigation) |
| < 60% | Failure (dimension likely needs prompt revision) |

**Overall pass:** All model × dimension combos ≥ 75%, with no more than 1 combo in the 75–84% band.

---

## Implementation

### Commands

```bash
# 1. Pull models
ollama pull gemma4:e4b
ollama pull starcoder2:3b

# 2. Score 2K django/django comments (use caffeinate on macOS to prevent sleep)
caffeinate -i -s python judge.py --backend ollama --model gemma4-e4b --repo django/django --limit 2000
caffeinate -i -s python judge.py --backend ollama --model starcoder2-3b --repo django/django --limit 2000

# 3. Create preference pairs
# Manual curation: read comments, select pairs
# Output: data/meta_eval/preference_pairs.jsonl

# 4. Collect human preferences
# Use annotation tool (Label Studio, etc.) or web form
# Output: data/meta_eval/human_preferences.jsonl

# 5. Compute agreement scores (script TBD)
python scripts/eval_preference_agreement.py \
  --pairs data/meta_eval/preference_pairs.jsonl \
  --human_prefs data/meta_eval/human_preferences.jsonl \
  --db data/raw/events.db \
  --output meta_eval_results.json
```

### Output Files

- `meta_eval_results.json` — Raw agreement scores (structured for analysis)
  ```json
  {
    "summary": {
      "gemma4:e4b": {"fun": 0.92, "nsi": 0.78, "insi": 0.81, "isi": 0.89},
      "starcoder2:3b": {"fun": 0.88, "nsi": 0.62, "insi": 0.71, "isi": 0.85}
    },
    "pairs": [
      {
        "pair_id": "nsi_001",
        "dimension": "nsi",
        "human_pref": "B",
        "gemma4_agrees": true,
        "starcoder2_3b_agrees": true
      },
      ...
    ]
  }
  ```

- `meta_eval_report.md` — Summary tables and per-pair results
- `meta_eval_failures.jsonl` — Pairs where one/both models disagreed (for analysis)

---

## Interpretation

**Important:** This evaluation measures model agreement with human preference. It does **not** measure construct validity, model quality, or confirm theoretical claims about social vs. technical signals.

**Interpretation of results belongs in [`CONFORMITY.md`](CONFORMITY.md).**

This document specifies only the measurement methodology.

---

## References

- **Judge implementation:** [`judge/README.md`](../judge/README.md)
- **Model specifications:** [`docs/notes/MODEL_LIST.md`](MODEL_LIST.md)
- **Rubric:** [`papers/publication1/CONFORMITY_SYSTEM_PROMPT.md`](../../papers/publication1/CONFORMITY_SYSTEM_PROMPT.md)
- **Dataset:** CONFORMITY.md (2K-comment `django/django` subset from the 40K cleaned comments in `data/raw/events.db`)
- **Interpretation & theory:** CONFORMITY.md
