import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from .stats import all_zero_scores_mask, SCORE_COLUMNS

_EVENT_TYPE_ABBREV: dict[str, str] = {
    "IssueCommentEvent": "IssueComment",
    "PullRequestReviewCommentEvent": "PRRevComment",
    "PullRequestReviewEvent": "PRReview",
    "PullRequestEvent": "PullRequest",
    "IssuesEvent": "Issues",
    "CommitCommentEvent": "CommitComment",
    "ReleaseEvent": "Release",
    "CreateEvent": "Create",
    "ForkEvent": "Fork",
    "WatchEvent": "Watch",
}


def abbreviate_github_event_type(name: str, *, max_len: int = 26) -> str:
    """Short label for long $.type strings (axis ticks / downloads)."""
    s = str(name).strip()
    if s in _EVENT_TYPE_ABBREV:
        return _EVENT_TYPE_ABBREV[s]
    if s.endswith("Event"):
        s = s[: -len("Event")]
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def plot_group_means(
    summary: pd.DataFrame,
    label_col: str,
    title: str,
    max_labels: int = 25,
) -> None:
    plot_df = summary.head(max_labels).copy()
    if plot_df.empty:
        print("Nothing to plot.")
        return
    x = range(len(plot_df))
    width = 0.2
    fig, ax = plt.subplots(figsize=(max(8, len(plot_df) * 0.35), 5))
    for i, col in enumerate(SCORE_COLUMNS):
        ax.bar([xi + (i - 1.5) * width for xi in x], plot_df[col], width=width, label=col)
    ax.set_xticks(list(x))
    ax.set_xticklabels(plot_df[label_col], rotation=45, ha="right")
    ax.set_ylabel("Mean score (0–3)")
    ax.set_title(title)
    ax.legend()
    ax.set_ylim(0, 3.2)
    plt.tight_layout()
    plt.show()


def plot_heatmap(
    data: pd.DataFrame,
    row: str,
    col: str,
    value: str,
    title: str,
) -> None:
    if data.empty:
        print("Nothing to plot.")
        return
    pt = data.pivot_table(index=row, columns=col, values=value, aggfunc="mean")
    if pt.empty:
        print("Pivot empty.")
        return
    fig, ax = plt.subplots(figsize=(max(6, pt.shape[1] * 0.6), max(4, pt.shape[0] * 0.45)))
    im = ax.imshow(pt.values, aspect="auto", vmin=0, vmax=3, cmap="viridis")
    ax.set_xticks(range(pt.shape[1]))
    ax.set_xticklabels(pt.columns, rotation=45, ha="right")
    ax.set_yticks(range(pt.shape[0]))
    ax.set_yticklabels(pt.index)
    ax.set_title(title)
    plt.colorbar(im, ax=ax, label="Mean")
    plt.tight_layout()
    plt.show()


def plot_global_score_histograms_all_vs_non_full_zero(
    df: pd.DataFrame,
    *,
    compare_full_population: bool = True,
    single_figure_title: str | None = None,
) -> None:
    """Marginal histograms (bar counts at 0,1,2,3) per FUN/NSI/INSI/ISI.

    If compare_full_population is True, draws two figures: full loaded cohort vs rows
    after dropping FUN=NSI=INSI=ISI=0. If False, draws one figure for the dataframe passed in.
    """

    def _one_grid(data: pd.DataFrame, supt: str, bar_color: str) -> None:
        xpos = np.arange(4)
        fig, axes = plt.subplots(2, 2, figsize=(11, 9))
        fig.suptitle(supt)
        for ax, col in zip(axes.flat, SCORE_COLUMNS):
            vc = data[col].value_counts().reindex([0, 1, 2, 3], fill_value=0)
            ax.bar(
                xpos,
                vc.values.astype(int),
                width=0.62,
                color=bar_color,
                edgecolor="white",
            )
            ax.set_xticks(xpos)
            ax.set_xticklabels(["0", "1", "2", "3"])
            ax.set_title(col)
            ax.set_xlabel("ordinal score")
            ax.set_ylabel("count")
            for xi, yi in zip(xpos, vc.values):
                ax.text(xi, yi, str(int(yi)), ha="center", va="bottom", fontsize=8)
        plt.tight_layout()
        plt.show()

    d = df.drop(columns=["cleaned_text"], errors="ignore").copy()
    if d.empty:
        return
    for c in SCORE_COLUMNS:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)

    if not compare_full_population:
        d_plot = d.loc[~all_zero_scores_mask(d)].copy()
        if d_plot.empty:
            print("No rows left after excluding full-zero blocks.")
            return
        title = single_figure_title or (
            "Marginal histograms — rows below exclude FUN=NSI=INSI=ISI all zero"
        )
        _one_grid(d_plot, title, "#55a868")
        return

    mask_zero = all_zero_scores_mask(d)
    d_non = d.loc[~mask_zero].copy()
    datasets = [
        (
            d,
            "Marginal histograms — full cohort (every loaded judge row; includes blanket all-zero)",
            "#4c72b0",
        ),
        (
            d_non,
            "Marginal histograms — after removing blanket all-zero rows (FUN=NSI=INSI=ISI=0)",
            "#55a868",
        ),
    ]
    for data, supt, bar_color in datasets:
        if data.empty:
            print("No rows left after removing full-zero blocks; skipping second histogram grid.")
            continue
        _one_grid(data, supt, bar_color)


def plot_score_summaries_by_category(
    df: pd.DataFrame,
    *,
    category_col: str,
    title: str,
    max_categories: int = 48,
    include_s0: bool = True,
    one_figure_per_panel: bool = False,
    use_event_type_abbrev: bool = False,
    horizontal_event_bars: bool | None = None,
    show_event_type_label_table: bool = True,
) -> None:
    """Stacked histogram-style counts per category_col, using only rows where not all four
    dimensions are 0. If include_s0 is False, bars stack s=1,2,3 only."""

    d = df.drop(columns=["cleaned_text"], errors="ignore").copy()
    if d.empty or category_col not in d.columns:
        return
    for c in SCORE_COLUMNS:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)
    d = d.loc[~all_zero_scores_mask(d)].copy()
    if d.empty:
        print(f"No rows with any non-zero score — skip {category_col} breakdown plot.")
        return
    cats_full = sorted(d[category_col].astype(str).unique())
    if len(cats_full) > max_categories:
        print(f"Skipping plots: {category_col} has {len(cats_full)} values (max {max_categories}).")
        return
    plot_col = category_col
    if use_event_type_abbrev and category_col == "event_type":
        d = d.copy()
        d["_plot_cat"] = d[category_col].astype(str).map(abbreviate_github_event_type)
        plot_col = "_plot_cat"
        if show_event_type_label_table:
            mapping = (
                pd.DataFrame(
                    {
                        "short_label": [abbreviate_github_event_type(x) for x in cats_full],
                        "full_event_type": cats_full,
                    }
                )
                .drop_duplicates(subset=["short_label", "full_event_type"])
                .sort_values("full_event_type")
                .reset_index(drop=True)
            )
            print("Event-type axis labels mapping displayed.")

    if horizontal_event_bars is None:
        horizontal_event_bars = bool(
            category_col == "event_type" and one_figure_per_panel
        )
    colors_full = ["#4c72b0", "#55a868", "#c44e52", "#8172b3"]
    levels = (0, 1, 2, 3) if include_s0 else (1, 2, 3)
    colors = colors_full if include_s0 else colors_full[1:]

    def plot_one_ax(ax, dim_col: str, *, show_panel_title: bool = True) -> None:
        ct = pd.crosstab(d[plot_col], d[dim_col])
        for v in (0, 1, 2, 3):
            if v not in ct.columns:
                ct[v] = 0
        ct = ct[[*levels]]
        ct = ct.reindex(sorted(ct.index.astype(str))).fillna(0).astype(int)
        if include_s0:
            ct.columns = ["s=0", "s=1", "s=2", "s=3"]
        else:
            ct.columns = ["s=1", "s=2", "s=3"]
        if horizontal_event_bars and category_col == "event_type":
            ct = ct.copy()
            ct.index.name = None
        kind = "barh" if horizontal_event_bars else "bar"
        ct.plot(
            kind=kind,
            stacked=True,
            ax=ax,
            color=colors,
            width=0.82,
            legend=True,
        )
        if show_panel_title:
            ax.set_title(dim_col)
        if horizontal_event_bars:
            if category_col != "event_type":
                ax.set_ylabel(category_col)
            else:
                ax.set_ylabel("")
            ax.set_xlabel("count")
        else:
            ax.set_xlabel(category_col)
            plt.setp(ax.get_xticklabels(), rotation=52, ha="right")
        _leg_fs = 11 if horizontal_event_bars else 8
        ax.legend(
            title="ordinal",
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=_leg_fs,
            title_fontsize=_leg_fs,
        )

    if one_figure_per_panel:
        nbin = int(d[plot_col].astype(str).nunique())
        maxlen = (
            max(len(str(x)) for x in cats_full)
            if category_col == "event_type"
            else 24
        )
        left_margin = float(min(0.58, max(0.22, 0.0088 * maxlen + 0.14)))
        for dim_col in SCORE_COLUMNS:
            if horizontal_event_bars:
                h = max(4.2, min(26.0, 0.34 * nbin + 2.8))
                w = max(8.2, min(11.5, 7.8 + 0.018 * maxlen))
            else:
                h = max(4.2, min(16.0, 0.22 * nbin + 3.5))
                w = 9.5
            fig, ax = plt.subplots(figsize=(w, h))
            plot_one_ax(ax, dim_col, show_panel_title=False)
            if horizontal_event_bars:
                ax.tick_params(axis="y", labelsize=7)
                plt.setp(ax.get_yticklabels(), fontsize=7)
            fig.subplots_adjust(
                left=left_margin,
                right=0.78,
                bottom=0.07,
                top=0.97,
            )
            plt.show()
        return

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    stack_label = "0/1/2/3" if include_s0 else "1/2/3 (s=0 omitted from stacks)"
    suffix = (
        "(full-zero judge rows excluded)"
        if include_s0
        else "(full-zero judge rows excluded; s=0 counts not stacked)"
    )
    fig.suptitle(f"{title} — stacked counts at {stack_label} per {category_col} {suffix}")
    for ax, dim_col in zip(axes.flat, SCORE_COLUMNS):
        plot_one_ax(ax, dim_col, show_panel_title=True)
    plt.tight_layout()
    plt.show()


def plot_total_score_by_repo(df: pd.DataFrame, *, title_prefix: str = "") -> None:
    """Bar chart: mean per-row total score (FUN+NSI+INSI+ISI) by repo."""
    from .stats import total_score_by_repo_table

    tbl = total_score_by_repo_table(df)
    if tbl.empty:
        return
    w = max(9.0, min(28.0, 0.42 * len(tbl) + 6.0))
    fig, ax = plt.subplots(figsize=(w, 5.2))
    repos = tbl["repo"].astype(str)
    x = range(len(tbl))
    mean_y = tbl["mean_total_score"].to_numpy(dtype=float, copy=False)
    ax.bar(x, mean_y, color="#4c72b0", edgecolor="white")
    ax.set_xticks(list(x))
    ax.set_xticklabels(repos)
    ax.set_ylabel("mean total score")
    ax.set_ylim(0, 12)
    ax.set_xlabel("repo")
    pref = (title_prefix + " — ") if title_prefix else ""
    ax.set_title(f"{pref}Mean total score per judge row (max 12)")
    plt.setp(ax.get_xticklabels(), rotation=52, ha="right")
    fig.tight_layout()
    plt.show()
