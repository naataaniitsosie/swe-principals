## Runnable scripts (pipeline)

Run in order: **1. Extract** → **2. Preprocess** → **3. Analyze** (e.g. sentiment). Each script reads from the previous step’s output.

| Step | Script | Input | Output |
|------|--------|--------|--------|
| 1. Extract | `python dataset.py` | GHArchive (network) | `./data/raw` (JSONL per repo) |
| 2. Preprocess | `python preprocess.py` | `./data/raw` | `./data/cleaned` (JSONL with `cleaned_text`, `tokens`) |
| 3. Analyze | `python sentiment.py` | `./data/cleaned` or `./data/raw` | `./data/sentiment` |

**Chaining (default paths):**
```bash
python dataset.py --start-date 2024-01-01 --end-date 2024-01-02 --output-dir ./data/raw
python preprocess.py --input-dir ./data/raw --output-dir ./data/cleaned
python sentiment.py ./data/cleaned --output-dir ./data/sentiment
```

---

### 1. Data extraction (`dataset.py`)

Extract PR events from GHArchive for all repositories under investigation (see CONFORMITY.md). Default: all 10 repos; optional date range and output dir.

```bash
python dataset.py
```

With a custom date range and output directory:

```bash
python dataset.py --start-date 2024-01-01 --end-date 2024-01-31 --output-dir ./data/raw
```

| Flag | Default | Description |
|------|---------|-------------|
| `--dataset-reader`, `-r` | `gharchive` | Reader to use |
| `--start-date` | `2024-02-01` | Start date (YYYY-MM-DD) |
| `--end-date` | `2024-02-02` | End date (YYYY-MM-DD) |
| `--output-dir` | `./data/raw` | Output directory |

---

### 2. Preprocess data (`preprocess.py`)

Preprocess the JSONL produced by `dataset.py` (CONFORMITY.md Preprocessing): remove bot and CI comments, strip code blocks and diff snippets, drop trivial comments (e.g. “LGTM”, “Thanks!”), lowercase and tokenize. Writes one JSONL per input file; each output record adds `cleaned_text` and `tokens`. Events with no semantic value are dropped.

```bash
python preprocess.py
```

Custom input/output:

```bash
python preprocess.py --input-dir ./data/raw --output-dir ./data/cleaned
```

| Flag | Default | Description |
|------|---------|-------------|
| `--input-dir`, `-i` | `./data/raw` | Directory of raw .jsonl from dataset.py |
| `--output-dir`, `-o` | `./data/cleaned` | Directory to write preprocessed .jsonl |

