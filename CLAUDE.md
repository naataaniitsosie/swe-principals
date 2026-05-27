# CLAUDE.md — Project Guidelines

## North Star

**[`docs/notes/CONFORMITY.md`](docs/notes/CONFORMITY.md) is the guiding document for this project.**

All code, scoring prompts, methodology decisions, and paper content must align with the definitions, research questions, and methodology described there. When in doubt about scope, terminology, or design, consult CONFORMITY.md first before proposing changes.

## Project Overview

This repository studies **conformity in software engineering** by analyzing GitHub Pull Request discourse. It detects and scores social and functional conformity signals in PR review comments using LLM-as-judge scoring.

## Key Scripts (run in order)

1. `dataset.py` — Extract PR events from GHArchive into SQLite (`data/raw/events.db`)
2. `preprocess.py` — Clean and normalize events into the `cleaned` table
3. `sample.py` — Draw a deterministic stratified sample into the `samples` table (see `sampling/README.md`)
4. `judge.py` — Score sampled comments with an LLM (Ollama or OpenAI); reads from `samples`, not `cleaned`
5. `browse_comments.py` / `browse_scores.py` — Inspect data and scores

## Two Scoring Tracks

| Track | Event types | Prompt | Dimensions |
|-------|------------|--------|------------|
| Track 1 — Reviewer | `PullRequestReviewEvent`, `PullRequestReviewCommentEvent`, `IssueCommentEvent` | `papers/publication1/CONFORMITY_SYSTEM_PROMPT.md` | FUN / NSI / INSI / ISI |
| Track 2 — Contributor | `PullRequestEvent` | `papers/publication1/CONTRIBUTOR_CONFORMITY_SYSTEM_PROMPT.md` | A-NSI / A-ISI |

## Database

Single SQLite file: `data/raw/events.db`. Tables: `events`, `cleaned`, `scores`. Schema: [`docs/DB_SCHEMA.md`](docs/DB_SCHEMA.md).

## Environment

- Python 3.10+ via conda environment `swe-principals`
- Secrets in `.env` at repo root (not committed)
- Long Ollama runs: wrap with `caffeinate` to prevent macOS sleep

## Navigation Rule

Before exploring or modifying any directory, check whether it contains a `README.md`. If one exists, read it first — it is the authoritative description of that directory's purpose, structure, and conventions.
