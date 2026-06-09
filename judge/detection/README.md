# Detection Scoring

Score each PR comment **in isolation** — no surrounding thread, no repo history, no author context. The LLM reads one comment and returns independent FUN / NSI / INSI / ISI scores.

This is what [`judge.py`](../../judge.py) runs. It reads from the stratified `samples` table (1,903 rows) and writes to `scores`.

## Modules

| File | Purpose |
|------|---------|
| `storage.py` | `SamplesReader` — reads `samples JOIN cleaned` with optional `repo` / `event_type` filters |
| `runner.py` | Orchestration: resolve model → build judge → score → batch-write to `scores` |

## What "detection" means

Each comment is treated as a standalone unit. The model has no access to:
- Earlier or later comments in the same PR thread
- The diff or code being reviewed
- The reviewer's history or author association

This produces per-comment FUN / NSI / INSI / ISI scores that are fully comparable across repos and models.

## Contrast with contextual scoring

Contextual scoring (see [`judge/contextual/`](../contextual/)) would group comments by PR thread or repository and reason about conformity dynamics over time. It is **not yet implemented**.
