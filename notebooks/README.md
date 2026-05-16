# Notebooks

Interactive analysis of the conformity dataset. All notebooks import from `notebooks.lib/` for clean, reusable helper functions.

## Notebooks

### [data_explorer.ipynb](data_explorer.ipynb)
**Exploratory data analysis** — Understand dataset coverage, distribution of scores across metadata dimensions, and patterns in comments.

- Loads raw `events`, `cleaned`, `scores` tables
- Shows preprocessing coverage (raw events → cleaned → scored)
- Groups scores by repo, event type, author association, actor, and week
- Two-way breakdowns (repo × event_type, repo × author_association) as heatmaps
- Top-N bucketing for high-cardinality dimensions (actors)

**Start here** to get a sense of what's in the data.

### [score_analysis.ipynb](score_analysis.ipynb)
**Quantitative analysis of judge outputs** — Compute statistics on FUN/NSI/INSI/ISI scores across all breakdowns, visualize distributions, and identify patterns.

- Loads scores with full metadata context (repo, author_association, user_login, event_type)
- Computes per-group quantiles (count, mean, median, p25, p50, p75, p99)
- Marginal histograms (ordinal 0–3 counts) — full cohort vs all-zero-filtered
- Stacked bar charts by repo and event type
- Analyzes all-zero score rows (judge assigned no signal) with samples

**Use this** for statistical summaries and publication-ready visualizations.

## Quick Start

1. **Navigate to notebook directory:**
   ```bash
   cd notebooks/
   ```

2. **Launch Jupyter:**
   ```bash
   jupyter notebook data_explorer.ipynb
   ```
   The first code cell will add the repo root to `sys.path`, so imports work from either the repo root or `notebooks/` folder.

3. **Check available models:**
   Run the "Available judge models" cell to see which `model_name` values exist in `scores.model_name`.

4. **Pick a model and run:**
   Set `MODEL_NAME` in **data_explorer** (e.g., `"gpt-5.4-mini"`), then run all cells. Same approach in **score_analysis**.

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

**Semantic separation:**
- **data_explorer** — What's in the data? Coverage, distributions, patterns.
- **score_analysis** — What do the scores show? Statistics, quantiles, trends.

**Reusability:** The library is self-contained and can be imported from other scripts or notebooks without running Jupyter cells.

## Notes

- All notebooks assume you've run `dataset.py` and `preprocess.py` and `judge.py` to populate the SQLite DB (`data/raw/events.db`).
- Working directory can be either the repo root or `notebooks/` folder — path resolution is built-in.
- `author_association` (GitHub's label for repo relationship: OWNER, MEMBER, CONTRIBUTOR, etc.) is available on payload objects; see [docs/DB_SCHEMA.md](../docs/DB_SCHEMA.md).
- Event types are top-level `$.type` strings (`IssueCommentEvent`, `PullRequestEvent`, etc.); see [docs/DB_SCHEMA.md](../docs/DB_SCHEMA.md).
