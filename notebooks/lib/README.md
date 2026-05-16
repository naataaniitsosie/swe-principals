# Notebook Helpers Library

Organized helper functions for analysis notebooks. Import from `notebooks.lib` when working in Jupyter.

## Modules

- **`db.py`** — Database connection and path constants
- **`sql.py`** — SQL helper functions for extracting JSON fields, building breakdowns
- **`stats.py`** — Statistical analysis: grouping, score aggregation, totals
- **`plots.py`** — Matplotlib visualization helpers (histograms, heatmaps, stacked bars)
- **`display.py`** — IPython display utilities (scrollable tables, sample panels)

## Quick Start

```python
import sys
from pathlib import Path

# Add repo root to path (notebooks/ or repository root both work)
here = Path.cwd().resolve()
for p in [here, *here.parents]:
    if (p / "project_config.py").is_file():
        sys.path.insert(0, str(p))
        break

from notebooks.lib import (
    summarize_by,
    plot_group_means,
    load_scores_with_metadata,
    score_stats_by_repo,
)

# Load scores with metadata
df = load_scores_with_metadata()

# Group by event type
by_type = summarize_by(df, "event_type")
plot_group_means(by_type, "event_type", "Scores by event type")

# Get stats by repo
stats = score_stats_by_repo()
```

## Module Contents

### db
- `DB_PATH` — path to SQLite database
- `connect()` — returns sqlite3.Connection

### sql
- `author_association_sql(alias)` — JSON path for author association
- `repo_name_sql(alias)` — JSON path for repo name
- `event_type_sql(alias)` — JSON path for event type
- `comment_author_login_sql(alias)` — JSON path for user login
- `breakdown_df(scope, select_exprs, group_by_positions, order_by)` — generic breakdown query
- `breakdown_repo_author_association(scope)` — repo × author_association counts
- `breakdown_event_type(scope)` — event type marginal counts
- `breakdown_repo_event_type(scope)` — repo × event type counts

### stats
- `SCORE_COLUMNS` — tuple of score column names
- `summarize_by(data, by, min_n, score_cols)` — group and average scores
- `bucket_top_n_series(s, top_n, other_label)` — collapse high-cardinality series
- `all_zero_scores_mask(df)` — boolean mask for rows with all-zero scores
- `load_scores_with_metadata(include_cleaned_text)` — load scores with event context
- `score_stats_grouped(df, group_cols)` — compute per-group quantiles
- `score_stats_by_repo(df, exclude_all_zero)` — stats grouped by repo
- `score_stats_by_repo_author_association(df, exclude_all_zero)` — repo × author_association stats
- `score_stats_by_repo_event_type(df, exclude_all_zero)` — repo × event type stats
- `score_stats_by_repo_aa_user(df, exclude_all_zero)` — repo × aa × user stats
- `score_stats_by_repo_aa_user_event_type(df, exclude_all_zero)` — 4-way stats
- `total_score_per_row(df)` — sum of four score dimensions per row
- `total_score_by_repo_table(df)` — repo totals (sum, mean, median, std)

### plots
- `plot_group_means(summary, label_col, title, max_labels)` — grouped bar chart
- `plot_heatmap(data, row, col, value, title)` — pivot table heatmap
- `plot_global_score_histograms_all_vs_non_full_zero(df, compare_full_population, single_figure_title)` — marginal histograms (0–3)
- `plot_score_summaries_by_category(df, category_col, title, max_categories, include_s0, one_figure_per_panel, use_event_type_abbrev, horizontal_event_bars, show_event_type_label_table)` — stacked bar breakdown
- `plot_total_score_by_repo(df, title_prefix)` — mean total score by repo
- `abbreviate_github_event_type(name, max_len)` — shorten event type strings

### display
- `display_dataframe_scrollable(df, max_height)` — IPython HTML table in scrollable panel
- `display_all_zero_score_comment_samples(df, limit, preview_chars)` — show samples of all-zero rows
