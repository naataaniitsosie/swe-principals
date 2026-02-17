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

### Detect Conformity in PR Review Comments
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

**Configuration:** Event types are defined in [`dataset_readers/gharchive/config.py`](dataset_readers/gharchive/config.py) (`EXPRESSJS_CONFIG.event_types`) and the `EventType` enum in [`dataset_readers/gharchive/models.py`](dataset_readers/gharchive/models.py).

#### Why not Kaggle GitHub Repos?
The (Kaggle GitHub Repos)[https://www.kaggle.com/datasets/github/github-repos] dataset is a static snapshot of GitHub repositories, which focuses on the codebase and repository metadata rather than the dynamic interactions and contributions made through pull requests. For analyzing sentiments in pull requests, a dataset that captures the temporal and interactive nature of contributions is essential. GHArchive provides a more comprehensive view of the ongoing development activities, making it more suitable for this analysis.

## Phase 1 — Surface-Level Conformity Detection (No LLM)

### Objective
Establish an existence proof that linguistic markers of norm enforcement are present in PR review discourse using interpretable lexical features.

We operationalize conformity narrowly as:

> The presence of linguistic markers indicating norm enforcement, deviation discouragement, or authority invocation in PR review comments.

### Preprocessing
- Remove bot and CI comments  
- Strip code blocks and diff snippets  
- Lowercase and tokenize text  
- Remove trivial comments (e.g., “LGTM”, “Thanks!”)  

### Linguistic Marker Categories

#### 1️⃣ Normative Modal Lexicon
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

#### 2️⃣ Norm Reference Lexicon
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

#### 3️⃣ Authority Anchors
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

### Surface Conformity Score

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

## Phase 2 — LLM-Based Semantic Conformity Detection

### Objective
Capture implicit and contextual conformity signals not detectable via lexical methods.

### Operationalization

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

### LLM Conformity Score
```
LLMConformityScore = sum(binary_labels)
```

Range: 0–4

### Combined Conformity Score

```
ConformityScore =
    α * SurfaceConformityScore +
    β * LLMConformityScore
```

Weights (α, β) will be determined empirically.

---

## Phase 3 — Model Comparison & Conformity Amplification (If phase 2 is successful)

### Objective
Test whether code-refined or alignment-tuned LLMs amplify conformity signals relative to baseline models.

### Procedure

1. Generate PR-style review comments using:
   - Base LLM (e.g., GPT-2 small)
   - Code-refined model
   - Instruction-tuned model

2. Score generated comments using:
   - SurfaceConformityScore
   - LLMConformityScore

3. Compare distributions across model families.

### Hypothesis

If code-refined models exhibit:
- Higher norm invocation frequency
- Stronger deviation policing
- Greater authority appeal

Then refinement may increase social conformity in code review discourse.

---

#### Models
| Model | HF ID | Notes |
| ----- | ----- | ----- |
| GPT2 Small | `openai-community/gpt2` | baseline model |
| <Model Name> | <HF ID> | <Notes> |

### Existing Code Artifacts
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