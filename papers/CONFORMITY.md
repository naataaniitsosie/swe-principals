# Conformity

## Introduction
Software Engineering (SE) is an expression of human thought and creativity. Naturally, biases and cultural norms are reflected in code artifacts, documentation, changelogs, reviews, comments, feedback, and other SE artifacts. The goals of this project is to explore and quanitfy "conformity" in SE pull request comments. The limited scope of this project is to explore the conformity of pull request comments, and not the conformity of code artifacts themselves.

## Background
Alignment with dominant group norms due to social pressure [citation needed]. In PR reviews, that could manifest as:
  - Enforcement of established conventions
  - Policing deviation
  - Framing norms as "how things are done"
  - Suppressing novelty in favor of standardization

### RQs
1. Does conformity exist as a detectable social phenomenon in software engineering discourse?
2. Do PR review comments exhibit ideological norm-enforcement patterns, and do code-refined LLMs amplify them?

## Methodology

### Goal
Detect the following in PR review comments:
1. References shared norms
2. Frames deviation as undesirable
3. Appeals to authority (docs, style guide, precedent)
4. Privileges consistency over experimentation

### Dataset
(GHArchive)[https://www.gharchive.org/] - A dataset that records the public GitHub timeline, including pull requests, issues, commits, and other events. (Event types)[https://docs.github.com/en/rest/using-the-rest-api/github-event-types?apiVersion=2022-11-28] exist in GitHub's own documentation.

#### GHArchive Event Types
The POC extracts the following event types for PR sentiment analysis:

| Code | GHArchive type | Description |
|------|----------------|-------------|
| `PULL_REQUEST` | `PullRequestEvent` | PR opened, closed, merged |
| `PR_REVIEW` | `PullRequestReviewEvent` | PR reviews (approve, request changes, comment) |
| `PR_REVIEW_COMMENT` | `PullRequestReviewCommentEvent` | Inline comments on PR diff |
| `ISSUE_COMMENT` | `IssueCommentEvent` | Comments on PRs (PRs are issues) |

**Configuration:** Event types are defined in [`dataset_readers/gharchive/config.py`](dataset_readers/gharchive/config.py) (`DEFAULT_EVENT_TYPES`) and the `EventType` enum in [`dataset_readers/gharchive/models.py`](dataset_readers/gharchive/models.py).

#### Why not Kaggle GitHub Repos?
The (Kaggle GitHub Repos)[https://www.kaggle.com/datasets/github/github-repos] dataset is a static snapshot of GitHub repositories, which focuses on the codebase and repository metadata rather than the dynamic interactions and contributions made through pull requests. For analyzing sentiments in pull requests, a dataset that captures the temporal and interactive nature of contributions is essential. GHArchive provides a more comprehensive view of the ongoing development activities, making it more suitable for this analysis.

#### Preprocessing
Applied per event in order; events that fail a step are dropped. Reads from **events**, writes to **cleaned** in the same DB.

1. **Deduplicate** by event `id` (keep first occurrence).
2. **Filter:** drop if actor is bot or CI (login matches e.g. `[bot]`, `github-actions`, `dependabot`).
3. **Extract text** from event (comment body, review body, or PR title+body); drop if missing or empty.
4. **Strip** markdown code blocks, markdown images (e.g. `![alt](url)`), and diff snippet lines (lines starting with `+` or `-`).
5. **Normalize:** lowercase and collapse whitespace.
6. **Tokenize** (word-boundary split); **filter:** drop if fewer than 2 tokens.
7. **Output** slim record to **cleaned**: `id`, `cleaned_text`, `repo`, `created_at`, `type`, `author_association`, `tokens`.

#### Repositories Under Investigation
API frameworks have a long history of standardized conventions and best practices. In addition, they are strictly governed by their maintainers and community [citation needed], which makes them a natural fit for this study.

**Note:** Use the exact `owner/repo` value when filtering in GHArchive (e.g. `RepositoriesFilter`).

| Repository (GHArchive filter) | Description | Language | Is Open Source? | Date Created (verified) |
|------------------------------|-------------|----------|-----------------|-------------------------|
| [expressjs/express](https://github.com/expressjs/express) | Web framework for Node.js | JavaScript | Yes | 2009-06-26 |
| [nestjs/nest](https://github.com/nestjs/nest) | Web framework for Node.js | TypeScript | Yes | 2016-10-26 |
| [koajs/koa](https://github.com/koajs/koa) | Web framework for Node.js | JavaScript | Yes | 2013-09-06 |
| [fastify/fastify](https://github.com/fastify/fastify) | Web framework for Node.js | JavaScript | Yes | 2016-06-01 |
| [hapijs/hapi](https://github.com/hapijs/hapi) | Web framework for Node.js | JavaScript | Yes | 2011-04-12 |
| [spring-projects/spring-boot](https://github.com/spring-projects/spring-boot) | Web framework for Java | Java | Yes | 2013-12-12 |
| [tiangolo/fastapi](https://github.com/tiangolo/fastapi) | Web framework for Python | Python | Yes | 2018-07-24 |
| [django/django](https://github.com/django/django) | Web framework for Python | Python | Yes | 2003-07-15 |
| [pallets/flask](https://github.com/pallets/flask) | Web framework for Python | Python | Yes | 2010-04-06 |
| [gin-gonic/gin](https://github.com/gin-gonic/gin) | Web framework for Go | Go | Yes | 2014-07-25 |

#### Approximate data volume (all 10 repos, 2024 + 2025)

With the default config (4 event types: `PullRequestEvent`, `PullRequestReviewEvent`, `PullRequestReviewCommentEvent`, `IssueCommentEvent`), for **2024-01-01 through 2025-12-31** and all 10 repositories, the extractor fetches each hour once and partitions events by repo (one output file per repo):

| Metric | Approximate |
|--------|-------------|
| **Time range** | 731 days → 17,544 hourly files |
| **Download** | Each hour is fetched **once** (for all repos). Raw hourly `.json.gz` files are ~100–150 MB each → **~1.7–2.6 TB** downloaded. |
| **Output (saved)** | Only events that match one of the 10 repos and one of the 4 event types. Roughly **tens of thousands to low hundreds of thousands** of events total (e.g. 50k–300k), **~100 MB–1.5 GB** on disk (JSONL, one file per repo). |

To get real numbers, run a short test and scale up:

```bash
python dataset.py --start-date 2024-06-01 --end-date 2024-06-02 --output-dir ./data/raw
```
Once tested, use the full date range and output directory.
```bash
python dataset.py --start-date 2024-01-01 --end-date 2025-12-31 --output-dir ./data/2024-2025-raw
```

Check event counts in the logs and output file sizes; multiply by (731 / 2) for a rough full 2024+2025 extrapolation.

### Phase 1 — Surface-Level Conformity Detection (No LLM)

#### Objective
Establish an existence proof that linguistic markers of norm enforcement are present in PR review discourse using interpretable lexical features.

We operationalize conformity narrowly as:

> The presence of linguistic markers indicating norm enforcement, deviation discouragement, or authority invocation in PR review comments.

#### Linguistic Marker Categories

##### 1️⃣ Normative Modal Lexicon
Examples:
```
should
must
need to
have to
ought to
please use
stick to
follow
avoid
prefer
recommend
```

Metrics:
- `modal_count`
- `contains_modal` (binary)

##### 2️⃣ Norm Reference Lexicon
Examples:
```
idiomatic
convention
standard practice
best practice
consistent
consistency
as per
per docs
documentation
style guide
lint
pattern
project standard
typical
usually
expected
```

Metrics:
- `norm_ref_count`
- `contains_norm_reference` (binary)

##### 3️⃣ Authority Anchors
Detect:
- URLs  
- “according to”  
- “per the”  
- “see docs”  
- “README”  
- “RFC”  

Metrics:
- `authority_count`
- `contains_authority_anchor` (binary)

#### Surface Conformity Score

```
SurfaceConformityScore =
    1*(contains_modal) +
    1*(contains_norm_reference) +
    1*(contains_authority_anchor)
```

Range: 0–3

Interpretation:
- 0 = No observable norm enforcement  
- 1 = Weak signal  
- 2 = Moderate signal  
- 3 = Strong surface-level norm enforcement  

---

### Phase 2 — LLM-Based Semantic Conformity Detection

#### Objective
Capture implicit and contextual conformity signals not detectable via lexical methods.

#### Operationalization

For each PR review comment, the LLM evaluates:
1. References shared norms (Yes/No)
2. Frames deviation as undesirable (Yes/No)
3. Appeals to authority (Yes/No)
4. Privileges consistency over experimentation (Yes/No)

The LLM must:
- Ignore correctness
- Ignore politeness
- Ignore helpfulness
- Focus only on norm invocation and enforcement

#### LLM Conformity Score
```
LLMConformityScore = sum(binary_labels)
```

Range: 0–4

#### Combined Conformity Score

```
ConformityScore =
    α * SurfaceConformityScore +
    β * LLMConformityScore
```

Weights (α, β) will be determined empirically.

---

### Phase 3 — Model Comparison & Conformity Amplification (If phase 2 is successful)

#### Objective
Test whether code-refined or alignment-tuned LLMs amplify conformity signals relative to baseline models.

#### Procedure

1. Generate PR-style review comments using:
   - Base LLM (e.g., GPT-2 small)
   - Code-refined model
   - Instruction-tuned model

2. Score generated comments using:
   - SurfaceConformityScore
   - LLMConformityScore

3. Compare distributions across model families.

#### Hypothesis

If code-refined models exhibit:
- Higher norm invocation frequency
- Stronger deviation policing
- Greater authority appeal

Then refinement may increase social conformity in code review discourse.

---

##### Models
| Model | HF ID | Notes |
| ----- | ----- | ----- |
| GPT2 Small | `openai-community/gpt2` | baseline model |
| <Model Name> | <HF ID> | <Notes> |

#### Existing Code Artifacts
In this repository, use the `dataset_readers` folder to read the dataset and extract PR comments.

```bash
python dataset.py
```

Switch dataset readers:
```bash
python dataset.py --dataset-reader gharchive
python dataset.py --dataset-reader bigquery # Not supported yet
```

Flags for `dataset.py`:
- `--dataset-reader`, `-r` – Reader to use (default: `gharchive`)
- `--start-date` – Start date YYYY-MM-DD (default: 2024-02-01)
- `--end-date` – End date YYYY-MM-DD (default: 2024-02-02)
- `--output-dir` – Output directory (default: `./data/raw`)

## Results

## Discussion

## Future Work
1. Harvest repository-specific conformity norms from data maintainers to supplement the dataset. For example, explore the [expressjs](https://github.com/expressjs/express) repository and extract the conformity norms from the repository.

## Conclusion

## Appendix

### Appendix A: Data Collection

Data are obtained from the public GitHub event stream via GHArchive (https://www.gharchive.org/), which provides hourly archives of the GitHub public API timeline. The collection pipeline requests one hourly file per time slot over the chosen date range. Each archive is a gzipped JSON file containing one JSON object per line; the client filters events *in stream* by repository (owner/name) and by event type, so that only events belonging to the repositories under investigation and to the selected types (e.g., `PullRequestEvent`, `PullRequestReviewEvent`, `PullRequestReviewCommentEvent`, `IssueCommentEvent`) are retained. This reduces memory and disk use while preserving the full payload of each retained event.

All retained events are written to a **single SQLite database** (one file per project, e.g. `events.db`). Deduplication is handled at write time: each event has a unique `id` (GitHub event id). The schema uses two tables, both with columns `id` (primary key) and `event_data` (a JSON blob containing the full event). The **events** table holds the raw, unfiltered (by content) event set. During preprocessing, a second table, **cleaned**, is populated in the same database. The preprocessing step reads from **events**, deduplicates by `id` (keeping the first occurrence), then for each event: drops bot/CI and trivial comments, extracts text, strips code blocks and images and diff snippets, lowercases and tokenizes, drops events with fewer than 2 tokens, and writes slim records (id, cleaned_text, repo, created_at, type, author_association, tokens) to **cleaned**. Thus, SQLite is used both to (1) deduplicate across runs and within the raw stream via `INSERT OR REPLACE` on `id` when appending to **events**, and (2) to separate raw versus cleaned data via the two tables, while keeping a single database file for the entire dataset.

---

### Appendix B: Visualizing Sample Data Using Markdown

To support qualitative inspection and sharing of sample data, the pipeline exports the **cleaned** event set to **one Markdown file per repository**. Each file shows a total count, then is organized by calendar date; under each date, comments are listed in chronological order and numbered. Each record is rendered as a metadata block (id, repo, created_at, type, author_association, tokens) followed by **cleaned_text:** and the cleaned text. This format is intended for scrolling, searching, and copy-pasting into analysis or annotation tools.

The export is produced by the script `browse_comments.py`, which reads from the **cleaned** table, groups records by repository, and writes one `.md` file per repo into the project data directory. No manual directory selection is required; paths are taken from the project configuration.

**Example (abbreviated).** The following illustrates the structure of a generated Markdown file. A researcher can copy and paste such snippets into a manuscript or appendix.

```markdown
# Repo: django/django

## 2024-01-01

### 1.

- **id:** 34499227501
- **repo:** django/django
- **created_at:** 2024-01-01T08:50:24Z
- **type:** IssueCommentEvent
- **author_association:** MEMBER
- **tokens:** ['thanks', 'can', 'you', 'allow', 'edits', 'from', 'maintainers', ...]

**cleaned_text:**
thanks can you allow edits from maintainers i want to push small final edits

---

### 2.

- **id:** 34499811339
- **repo:** django/django
- **created_at:** 2024-01-01T10:00:37Z
- **type:** PullRequestReviewEvent
- **author_association:** MEMBER
- **tokens:** ['thanks', 'approved']

**cleaned_text:**
thanks

---
```

To regenerate the Markdown files from the current database, run from the project root: `python browse_comments.py`.
