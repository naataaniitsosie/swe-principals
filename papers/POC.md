# Goal
The goal of the Proof of Concept (POC) is see if any particular sentatiments exist in the pull requests of long standing open source API projects.

## Scope
The scope of the POC is limited to a single open source API project with a significant number of pull requests and contributors. ExpressJS has been selected for this purpose and I have a deep experience with this project.

## Dataset
(GHArchive)[https://www.gharchive.org/] - A dataset that records the public GitHub timeline, including pull requests, issues, commits, and other events. (Event types)[https://docs.github.com/en/rest/using-the-rest-api/github-event-types?apiVersion=2022-11-28] exist in GitHub's own documentation.

### GHArchive Event Types
The POC extracts the following event types for PR sentiment analysis:

| Code | GHArchive type | Description |
|------|----------------|-------------|
| `PULL_REQUEST` | `PullRequestEvent` | PR opened, closed, merged |
| `PR_REVIEW` | `PullRequestReviewEvent` | PR reviews (approve, request changes, comment) |
| `PR_REVIEW_COMMENT` | `PullRequestReviewCommentEvent` | Inline comments on PR diff |
| `ISSUE_COMMENT` | `IssueCommentEvent` | Comments on PRs (PRs are issues) |

**Configuration:** Event types are defined in [`dataset_readers/gharchive/config.py`](dataset_readers/gharchive/config.py) (`DEFAULT_EVENT_TYPES`) and the `EventType` enum in [`dataset_readers/gharchive/models.py`](dataset_readers/gharchive/models.py).

### Why not Kaggle GitHub Repos?
The (Kaggle GitHub Repos)[https://www.kaggle.com/datasets/github/github-repos] dataset is a static snapshot of GitHub repositories, which focuses on the codebase and repository metadata rather than the dynamic interactions and contributions made through pull requests. For analyzing sentiments in pull requests, a dataset that captures the temporal and interactive nature of contributions is essential. GHArchive provides a more comprehensive view of the ongoing development activities, making it more suitable for this analysis.

## Sentiment Analysis Tools/Models
### cardiffnlp/twitter-roberta-base-sentiment-latest
Type: Transformer-based sentiment analysis (negative / neutral / positive)
Framework: Hugging Face Transformers
https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest

This model is trained on short, informal text and performs well on concise, pragmatic language. Pull-request comments often resemble this style (brief critiques, approvals, hedged feedback). It serves as the primary sentiment baseline for the study.

### distilbert-base-uncased-finetuned-sst-2-english
Type: Transformer-based sentiment analysis (positive / negative)
Framework: Hugging Face Transformers
https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english


## RQs
1. Given that ExpressJS is a long standing open source API project with a significant number of pull requests and contributors, are there any particular sentiments that can be identified in the pull requests?
2. Are there any practices or norms in the pull requests that may contribute to the identified sentiments?

## Future Work
- Expand the analysis to include multiple open source API projects to identify common sentiment trends across different communities. Fastify, Koa, Django, Flask, Spring Boot, Ruby on Rails, NestJS, etc.
- Investigate the impact of norms and practices on society at large, particularly in relation to bias and discrimination.

## Local Developent
### Configuration
(Optional) Create environment using Conda/Miniconda:
```
conda create -n swe-principals python=3.10
```

Activate Conda Environment:
```
conda activate swe-principals
```

Install dependancies:
```
pip install -r requirements.txt
```

### Execute

**1. Data extraction** (writes JSONL to `./data/raw` by default)

Run extraction (default: GHArchive):
```bash
python dataset.py
```

Switch dataset readers:
```bash
python dataset.py --dataset-reader gharchive
python dataset.py --dataset-reader bigquery
```

Flags for `dataset.py`:
- `--dataset-reader`, `-r` – Reader to use (default: `gharchive`)
- `--start-date` – Start date YYYY-MM-DD (default: 2024-02-01)
- `--end-date` – End date YYYY-MM-DD (default: 2024-02-02)
- `--output-dir` – Output directory (default: `./data/raw`)

**2. Sentiment analysis** (run on existing extracted data)

Run on all `.jsonl` files in the default raw directory:
```bash
python sentiment.py
```

Run on a specific file or directory:
```bash
python sentiment.py ./data/raw/expressjs_express_20260203_134451.jsonl
python sentiment.py ./data/raw
```

Write results to a custom directory:
```bash
python sentiment.py ./data/raw --output-dir ./data/sentiment
python sentiment.py -o ./out/sentiment
```

Flags for `sentiment.py`:
- `input` – Path to a `.jsonl` file or directory of `.jsonl` files (default: `./data/raw`)
- `--output-dir`, `-o` – Output directory for sentiment results (default: `./data/sentiment`)