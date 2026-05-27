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

## Usage

```bash
python dataset.py --dataset-reader gharchive --start-date 2024-01-01 --end-date 2024-02-01
```

See [docs/CLI.md](docs/CLI.md) for all options.

## Adding a Reader

1. Create `dataset_readers/<name>/reader.py`
2. Implement `DatasetReaderBase` and decorate with `@register_reader("name")`
3. Import the module in `dataset_readers/__init__.py`

## BigQuery Reader

- [Overview & setup](docs/bigquery/OVERVIEW.md)
- [Schema reference](docs/bigquery/SCHEMA.md)
- [Cost analysis](docs/bigquery/COST.md)
- [Sample queries](docs/bigquery/SAMPLE_QUERIES.md)

## Decision Log

### 2025-05-27 — BigQuery not adopted; continuing with GHArchive API

After exploring Google BigQuery as a mechanism for pulling 2023–2025 GitHub event data at scale, we decided **not to use it**.

**Reason:** The required query (all four event types + `payload` column for 10 repos, 2023–2025) scans **~13–14 TB**. BigQuery's free tier covers 1 TB/month. At the on-demand rate of **$6.25/TB**, the full pull would cost approximately **$81–$87**. Spreading the query across the free tier over multiple calendar months is possible but impractical for a research timeline.

**Decision:** Continue using the GHArchive HTTP reader (`dataset_readers/gharchive/`), which is already implemented and costs nothing beyond disk and time.

**To revisit:** This decision should be reconsidered if the project secures funding. At ~$81 for a one-time complete historical pull, BigQuery remains the most operationally robust option (idempotent, no partial-download state, covers any date range in seconds).
