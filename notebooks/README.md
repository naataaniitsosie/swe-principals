# Notebooks

Interactive analysis of the conformity dataset. All notebooks import from `notebooks.lib/` for clean, reusable helper functions.

## Notebooks

### [data_explorer.ipynb](data_explorer.ipynb)
**Dataset overview** — Understand what's in the data *before scoring*. Shows preprocessing pipeline and coverage.

- Loads raw `events` and preprocessed `cleaned` tables (no scores)
- Shows preprocessing coverage: events → cleaned (% that survived preprocessing)
- Breaks down cleaned comments by repo, event type, and author association
- Displays samples of cleaned comment text

**Start here** to understand the dataset structure and what preprocessing does.

### [score_analysis.ipynb](score_analysis.ipynb)
**Judge analysis** — Quantitative analysis of judge models and their outputs. Statistics on FUN/NSI/INSI/ISI scores.

- Shows which judge models scored comments and how many scores each produced
- Computes per-group quantiles (count, mean, median, p25, p50, p75, p99) across all dimensions
- Marginal histograms (ordinal 0–3 counts) — full cohort vs all-zero-filtered
- Stacked bar charts by repo and event type
- Analyzes all-zero score rows (judge assigned no signal) with samples

**Use this** for statistical summaries and publication-ready visualizations of judge output.

## Quick Start

1. **Start with dataset overview:**
   ```bash
   cd notebooks/
   jupyter notebook data_explorer.ipynb
   ```
   This shows preprocessing coverage and data distribution *before* any scoring happened.

2. **Then analyze judge output:**
   ```bash
   jupyter notebook score_analysis.ipynb
   ```
   This shows which models scored the data and detailed statistics on all scores.

**Note:** The first code cell in each notebook adds the repo root to `sys.path`, so imports work from either the repo root or `notebooks/` folder. Both notebooks load and display data automatically — just run cells top-to-bottom.

## Helper Library: `lib/`

All reusable functions live in `notebooks/lib/` — see [lib/README.md](lib/README.md) for full API reference.

### Import Examples

```python
from notebooks.lib import (
    # Database
    connect, DB_PATH,
    
    # SQL helpers
    breakdown_repo_author_association, breakdown_event_type,
    
    # Statistics
    load_scores_with_metadata, score_stats_by_repo,
    summarize_by, bucket_top_n_series,
    
    # Visualization
    plot_group_means, plot_heatmap, plot_total_score_by_repo,
    
    # Display
    display_dataframe_scrollable,
)
```

### Module Structure

- **`db.py`** — Database path and connection
- **`sql.py`** — SQL builders for JSON extraction and breakdowns
- **`stats.py`** — Statistical grouping and quantile computation
- **`plots.py`** — Matplotlib visualization helpers
- **`display.py`** — IPython display utilities (scrollable tables, panels)
- **`__init__.py`** — Clean public API

## Design

**Simplicity first:** Notebooks focus on analysis flow, not plumbing. Common patterns (database queries, grouping, plotting) are extracted into the library.

**Clear separation:**
- **data_explorer** — Pre-scoring analysis. What's in the dataset? Preprocessing coverage and distribution across metadata dimensions. **Contains no score data.**
- **score_analysis** — Post-scoring analysis. Which judge models scored the data? What do the scores show? Statistics, quantiles, distributions.

**Reusability:** The library is self-contained and can be imported from other scripts or notebooks without running Jupyter cells.

## Notes

- All notebooks assume you've run `dataset.py` and `preprocess.py` and `judge.py` to populate the SQLite DB (`data/raw/events.db`).
- Working directory can be either the repo root or `notebooks/` folder — path resolution is built-in.
- `author_association` (GitHub's label for repo relationship: OWNER, MEMBER, CONTRIBUTOR, etc.) is available on payload objects; see [docs/DB_SCHEMA.md](../docs/DB_SCHEMA.md).
- Event types are top-level `$.type` strings (`IssueCommentEvent`, `PullRequestEvent`, etc.); see [docs/DB_SCHEMA.md](../docs/DB_SCHEMA.md).
