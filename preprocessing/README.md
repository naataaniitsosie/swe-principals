# Preprocessing

Cleans raw GitHub events from the `events` table and writes scoreable records to the `cleaned` table in the same SQLite database.

---

## Pipeline Position

```
dataset.py → preprocess.py → sample.py → judge.py
```

`preprocess.py` (repo root) is the entry point. It delegates to `preprocessing/pipeline.py`, which reads from `events`, runs the cleaning workflow on each event, and writes slim records to `cleaned` — all within `data/raw/events.db`.

**Why here and not earlier:** Cleaning must happen after extraction because it requires the full event payload (actor login, comment body, PR title + body) that the dataset reader writes verbatim into `events`. There is no intermediate format: the GHArchive reader writes raw JSON blobs, and preprocessing interprets them.

---

## Module Structure

```
preprocessing/
├── __init__.py
├── README.md         ← you are here; read before modifying
├── filters.py        ← drop rules: bot/CI logins, trivial comment phrases
├── text_cleaner.py   ← regex-based strippers (code blocks, images, diff lines), lowercase, tokenize
├── workflow.py       ← Step type, Context dataclass, Workflow class, default_workflow()
└── pipeline.py       ← CleanerPipeline: find DB, iterate events, call workflow, write cleaned
```

`preprocess.py` at the repo root is the thin entry point (mirrors `sample.py`).

---

## How to Run

```bash
python preprocess.py
```

No CLI flags. The DB path is derived from `project_config.DATA_DIR` (default: `data/raw/events.db`). Running `preprocess.py` **drops and recreates** the `cleaned` table. This is intentional: preprocessing is a deterministic function of `events`, so re-running is always safe. If you need the previous `cleaned` table, back up the DB first.

For long runs (large `events` table), wrap with `caffeinate` to prevent macOS sleep:

```bash
caffeinate python preprocess.py
```

---

## Cleaning Steps

Steps are applied in order by `default_workflow()` in `workflow.py`. An event is **dropped** (not written to `cleaned`) if any step returns `None`.

| # | Step | Drop condition |
|---|------|----------------|
| 1 | `filter_bot` | Actor login matches a bot/CI pattern (see [Bot/CI Patterns](#botci-patterns)) |
| 2 | `extract_text` | Event has no extractable text (comment body, review body, or PR title+body is missing or empty) |
| 3 | `strip_code` | _(no drop)_ — removes markdown fenced code blocks (`` ``` … ``` ``) |
| 4 | `strip_images` | _(no drop)_ — replaces `![alt](url)` and `[image](url)` with `<REDACTED IMAGE>` |
| 5 | `strip_diff` | _(no drop)_ — removes lines starting with `+` or `-` (diff snippet lines) |
| 6 | `normalize_lowercase` | _(no drop)_ — lowercases text and collapses whitespace |
| 7 | `tokenize_text` | _(no drop)_ — splits into words via `\w+` regex |
| 8 | `filter_min_tokens` | Fewer than **1 token** after cleaning (i.e., text is empty after stripping) |
| 9 | `finalize` | _(no drop)_ — writes `cleaned_text` and `tokens` back into the event context |
| 10 | `slim_output` | _(no drop)_ — retains only the fields written to `cleaned` (see [Output Schema](#output-schema)) |


---

## Bot/CI Patterns

Defined as `BOT_CI_PATTERNS` in `filters.py`. An event is dropped if the actor's login (lowercased) **contains** any of:

```
[bot]           # GitHub Apps (e.g. renovate[bot])
bot             # any login containing "bot"
github-actions
dependabot
dependabot[bot]
actions-user
greenkeeper
renovate
renovate[bot]
stale
stale[bot]
ci
travis
circleci
codecov
```

A missing or empty login is also treated as a bot (dropped).

---

## Output Schema

Written to the `cleaned` table in `events.db`. Defined by `slim_output` in `workflow.py` and `_create_cleaned_table` in `dataset_readers/gharchive/storage.py`.

| Column | Source | Description |
|--------|--------|-------------|
| `id` | `event.id` | GitHub event ID (primary key; FK → `events.id`) |
| `cleaned_text` | workflow output | Stripped, lowercased comment/PR text |
| `repo` | `event.repo.name` | e.g. `django/django` |
| `created_at` | `event.created_at` | ISO 8601 timestamp |
| `type` | `event.type` | e.g. `IssueCommentEvent` |
| `author_association` | payload field | e.g. `MEMBER`, `CONTRIBUTOR`, `NONE` |
| `tokens` | workflow output | JSON array of word tokens |

`author_association` is extracted from the first non-null of: `payload.comment`, `payload.review`, `payload.pull_request`, `payload.issue`.

---

## Workflow Internals

`workflow.py` exposes three primitives:

**`Context`** — mutable dataclass passed through the step chain:
```python
@dataclass
class Context:
    event: Dict[str, Any]   # raw event dict (mutated by finalize/slim_output)
    text: Optional[str]     # raw extracted text (set by extract_text)
    cleaned_text: Optional[str]  # text after stripping steps
    tokens: List[str]       # set by tokenize_text
```

**`Step`** — any callable `(Context) -> Optional[Context]`. Returning `None` drops the event.

**`Workflow`** — ordered list of steps. `.run(event)` returns the final `event` dict or `None`.

To add a custom step without modifying `default_workflow()`:
```python
from preprocessing.workflow import default_workflow

def my_step(ctx):
    if "forbidden_word" in (ctx.cleaned_text or ""):
        return None  # drop
    return ctx

workflow = default_workflow().chain(my_step)
```

Pass the custom workflow to `CleanerPipeline`:
```python
from preprocessing.pipeline import CleanerPipeline
pipeline = CleanerPipeline("data/raw", workflow=workflow)
pipeline.run()
```

---

## Making Changes: Rules

1. **Adding a bot/CI pattern:** Add to `BOT_CI_PATTERNS` in `filters.py`. Re-run `preprocess.py` to regenerate `cleaned`. There is no migration path — the table is always rebuilt from `events`.
2. **Changing the minimum token threshold:** Update the `min_tokens=1` argument in `default_workflow()` and note the change here. Re-run `preprocess.py`.
3. **Re-enabling `filter_trivial`:** Uncomment the line in `default_workflow()`. Understand that this will meaningfully reduce the `cleaned` row count (LGTM/thanks comments are common). Re-run `preprocess.py` and `sample.py` to keep `samples` in sync.
4. **Changing the `cleaned` schema:** Update `_create_cleaned_table` in `dataset_readers/gharchive/storage.py` and the Output Schema table above. `sampling/storage.py` and `judge.py` query `cleaned` — check them for breakage.
5. **Do not add raw event fields to `cleaned`:** The full payload is always available via `events.event_data`; duplicating it in `cleaned` wastes disk and creates silent staleness.

---

## Decision Log

### 2026-06-01 — `filter_trivial` removed; all human text retained

Any comment with extractable text is a potential conformity signal. A terse "ok", "lgtm", or "approved" can be a meaningful social response — its weight depends on context and is best judged by the LLM scorer, not a lexical pre-filter. Removing the trivial-phrase filter eliminates a source of silent data loss and keeps the pipeline's drop decisions auditable: events are only discarded for being bot/CI traffic or having no extractable text at all.
