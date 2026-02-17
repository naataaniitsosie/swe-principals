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

### LLM Classifier/Quantifier
At the time of writing, there are not automated metrics similar to BLEU, ROUGE, METEOR, etc. for quantifying the conformity in a body of text. Therefore, we will use an LLM to classify and quantify the conformity in a body of text.

#### Models
| Model | HF ID | Notes |
| ----- | ----- | ----- |
| GPT2 Small | `openai-community/gpt2` | a small baseline model |
| <Model Name> | <HF ID> | <Notes> |

### Conformity Scoring
A measurable proxy for conformity are linguistic markers of norm enforcement and deviation discouragement.
```
Conformity ≈ f_LLM(output, norm_definition)
```

#### Languistic Markers of Conformity
1. Explicitly reference norms
  - "Per the docs…"
  - "This is not idiomatic."
  - "We typically…"
  - "Standard practice is…"
2. Correct deviations
  - "Please use the project’s lint config."
  - "This should follow our established pattern."
  - "This breaks consistency."
3. Frame change as expectation
  - "We should keep this consistent."
  - "This deviates from convention."

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
1. Harvest conformity norms from data maintainers to supplement the dataset. For example, explore the [expressjs](https://github.com/expressjs/express) repository and extract the conformity norms from the repository.

## Conclusion