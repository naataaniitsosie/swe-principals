# Goal
The goal of the Proof of Concept (POC) is see if any particular sentatiments exist in the pull requests of long standing open source API projects.

## Scope
The scope of the POC is limited to a single open source API project with a significant number of pull requests and contributors. ExpressJS has been selected for this purpose and I have a deep experience with this project.

## Dataset
(GHArchive)[https://www.gharchive.org/] - A dataset that records the public GitHub timeline, including pull requests, issues, commits, and other events. (Event types)[https://docs.github.com/en/rest/using-the-rest-api/github-event-types?apiVersion=2022-11-28] exist in GitHub's own documentation.

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
Run data extraction:
```
python main.py
```