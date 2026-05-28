# dataset.py CLI Reference

```
python dataset.py [--dataset-reader READER] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
```

## Options

| Flag | Short | Default | Description |
|---|---|---|---|
| `--dataset-reader` | `-r` | `gharchive` | Reader to use. Run `python dataset.py --help` to see registered readers. |
| `--start-date` | — | `2024-02-01` | Inclusive start date (YYYY-MM-DD). |
| `--end-date` | — | `2024-02-01` | Inclusive end date (YYYY-MM-DD). All 24 hours of this day are fetched. |

## Examples

Pull one month:
```bash
python dataset.py --start-date 2024-01-01 --end-date 2024-01-31
```

Pull a full year:
```bash
python dataset.py --start-date 2024-01-01 --end-date 2024-12-31
```

Long run on macOS (prevent sleep):
```bash
caffeinate python dataset.py --start-date 2023-01-01 --end-date 2025-12-31
```

## Repositories & event types

The repo list and event types are defined in `dataset_readers/gharchive/config.py` (`REPOSITORIES` and `DEFAULT_EVENT_TYPES`). They are not CLI-configurable — edit that file to change scope.

## Output

Writes to `data/raw/events.db` (SQLite). Table: `events`. See [`docs/DB_SCHEMA.md`](../../docs/DB_SCHEMA.md) for schema.
