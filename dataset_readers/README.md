# Dataset Readers

Pluggable readers for extracting GitHub PR/event data from different sources.

## Structure

```
dataset_readers/
├── config.py     # RepositoryConfig (shared)
├── base.py       # DatasetReaderBase (abstract)
├── registry.py   # @register_reader, get_reader, list_readers
├── gharchive/    # GHArchive (static hourly files)
│   ├── config.py
│   ├── client.py
│   ├── models.py
│   ├── filters.py
│   ├── storage.py
│   ├── extractor.py
│   └── reader.py
└── bigquery/     # BigQuery (githubarchive public dataset)
    └── reader.py
```

## Adding a Reader

1. Create `dataset_readers/<name>/reader.py`
2. Implement `DatasetReaderBase` and decorate with `@register_reader("name")`
3. Import the module in `dataset_readers/__init__.py`

## BigQuery Reader

Queries `bigquery-public-data.github_archive.*` — preferred for 2023–2025 data because it scales to multi-year pulls without local downloads and is idempotent on re-runs.

- [Overview & setup](docs/bigquery/OVERVIEW.md)
- [Cost analysis](docs/bigquery/COST.md)
- [Sample queries](docs/bigquery/SAMPLE_QUERIES.md)
