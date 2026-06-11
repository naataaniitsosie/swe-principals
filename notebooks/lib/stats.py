import pandas as pd
from .db import connect

SCORE_COLUMNS = ("fun_score", "nsi_score", "insi_score", "isi_score")


def summarize_by(
    data: pd.DataFrame,
    by: list[str] | str,
    min_n: int = 1,
    score_cols: tuple[str, ...] = SCORE_COLUMNS,
) -> pd.DataFrame:
    cols = [by] if isinstance(by, str) else list(by)
    g = data.groupby(cols, dropna=False)
    out = g[list(score_cols)].mean()
    out["n"] = g.size()
    out = out.reset_index()
    return out[out["n"] >= min_n].sort_values("n", ascending=False)


def bucket_top_n_series(s: pd.Series, top_n: int, other_label: str = "Other") -> pd.Series:
    counts = s.value_counts()
    keep = set(counts.head(top_n).index)
    return s.where(s.isin(keep), other_label)


def all_zero_scores_mask(df: pd.DataFrame) -> pd.Series:
    """True where FUN, NSI, INSI, and ISI are all exactly 0."""
    return (
        (df["fun_score"] == 0)
        & (df["nsi_score"] == 0)
        & (df["insi_score"] == 0)
        & (df["isi_score"] == 0)
    )


def load_scores_with_metadata(
    *,
    include_cleaned_text: bool = False,
    experiment_version: int | None = None,
    model_allowlist: list[str] | None = None,
) -> pd.DataFrame:
    """Scores joined to cleaned. One row per (comment_id, model_name).

    Only includes successfully parsed rows (parse_ok = 1).
    Pass experiment_version to scope to a single experiment run; defaults to all versions.
    Pass model_allowlist to restrict to specific model names.
    Set include_cleaned_text=True when you need comment text (e.g. samples of all-zero rows).
    """
    text_col = ", c.cleaned_text AS cleaned_text" if include_cleaned_text else ""
    version_filter = (
        f"AND s.experiment_version = {int(experiment_version)}"
        if experiment_version is not None
        else ""
    )
    if model_allowlist:
        placeholders = ", ".join(f"'{m}'" for m in model_allowlist)
        model_filter = f"AND s.model_name IN ({placeholders})"
    else:
        model_filter = ""
    q = f"""
    SELECT
      s.comment_id,
      s.model_name,
      s.experiment_version,
      s.fun_score,
      s.nsi_score,
      s.insi_score,
      s.isi_score,
      COALESCE(NULLIF(TRIM(c.repo), ''), '(missing)') AS repo,
      COALESCE(NULLIF(TRIM(c.author_association), ''), '(empty)') AS author_association,
      COALESCE(NULLIF(TRIM(c.event_type), ''), '(missing)') AS event_type
      {text_col}
    FROM scores s
    INNER JOIN cleaned c ON c.id = s.comment_id
    WHERE s.parse_ok = 1
    {version_filter}
    {model_filter}
    """
    with connect() as conn:
        return pd.read_sql_query(q, conn)


def score_stats_grouped(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Per group: n_rows, per score column _n and _avg/_mean/_median/_p25 … _p99."""
    rows: list[dict[str, object]] = []
    for keys, g in df.groupby(group_cols, dropna=False):
        keys_t = keys if isinstance(keys, tuple) else (keys,)
        row = {group_cols[i]: keys_t[i] for i in range(len(group_cols))}
        row["n_rows"] = len(g)
        for c in SCORE_COLUMNS:
            s = g[c].dropna()
            row[f"{c}_n"] = int(s.shape[0])
            if s.empty:
                nan = float("nan")
                for suffix in (
                    "avg",
                    "mean",
                    "median",
                    "p25",
                    "p50",
                    "p75",
                    "p99",
                ):
                    row[f"{c}_{suffix}"] = nan
            else:
                mean = float(s.mean())
                row[f"{c}_avg"] = mean
                row[f"{c}_mean"] = mean
                row[f"{c}_median"] = float(s.median())
                row[f"{c}_p25"] = float(s.quantile(0.25))
                row[f"{c}_p50"] = float(s.quantile(0.50))
                row[f"{c}_p75"] = float(s.quantile(0.75))
                row[f"{c}_p99"] = float(s.quantile(0.99))
        rows.append(row)
    out = pd.DataFrame(rows)
    return out.sort_values(group_cols, kind="mergesort").reset_index(drop=True)


def score_stats_by_repo(
    df: pd.DataFrame | None = None, *, exclude_all_zero: bool = False
) -> pd.DataFrame:
    """FUN/NSI/INSI/ISI summaries grouped by repo only."""
    if df is None:
        df = load_scores_with_metadata()
        if exclude_all_zero:
            df = df.loc[~all_zero_scores_mask(df)].copy()
    return score_stats_grouped(df, ["repo"])


def score_stats_by_repo_author_association(
    df: pd.DataFrame | None = None, *, exclude_all_zero: bool = False
) -> pd.DataFrame:
    """Summaries grouped by repo × author_association."""
    if df is None:
        df = load_scores_with_metadata()
        if exclude_all_zero:
            df = df.loc[~all_zero_scores_mask(df)].copy()
    return score_stats_grouped(df, ["repo", "author_association"])


def score_stats_by_repo_event_type(
    df: pd.DataFrame | None = None, *, exclude_all_zero: bool = False
) -> pd.DataFrame:
    """Summaries grouped by repo × event_type (top-level $.type)."""
    if df is None:
        df = load_scores_with_metadata()
        if exclude_all_zero:
            df = df.loc[~all_zero_scores_mask(df)].copy()
    return score_stats_grouped(df, ["repo", "event_type"])


def score_stats_by_repo_aa_user(
    df: pd.DataFrame | None = None, *, exclude_all_zero: bool = False
) -> pd.DataFrame:
    """Summaries grouped by repo × author_association × user_login."""
    if df is None:
        df = load_scores_with_metadata()
        if exclude_all_zero:
            df = df.loc[~all_zero_scores_mask(df)].copy()
    return score_stats_grouped(df, ["repo", "author_association", "user_login"])


def score_stats_by_repo_aa_user_event_type(
    df: pd.DataFrame | None = None, *, exclude_all_zero: bool = False
) -> pd.DataFrame:
    """Summaries grouped by repo × author_association × user_login × $.type."""
    if df is None:
        df = load_scores_with_metadata()
        if exclude_all_zero:
            df = df.loc[~all_zero_scores_mask(df)].copy()
    return score_stats_grouped(
        df,
        ["repo", "author_association", "user_login", "event_type"],
    )


def total_score_per_row(df: pd.DataFrame) -> pd.Series:
    """Per judge row: fun_score + nsi_score + insi_score + isi_score (range 0–12)."""
    d = df.drop(columns=["cleaned_text"], errors="ignore").copy()
    total = pd.Series(0, index=d.index, dtype="int64")
    for c in SCORE_COLUMNS:
        col = (
            d[c]
            if c in d.columns
            else pd.Series(0, index=d.index, dtype="int64")
        )
        total = total + pd.to_numeric(col, errors="coerce").fillna(0).astype(int)
    return total


def total_score_by_repo_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per repo: counts, sum/mean/median/std of per-row total score."""
    d = df.drop(columns=["cleaned_text"], errors="ignore").copy()
    if d.empty or "repo" not in d.columns:
        return pd.DataFrame()
    ts = total_score_per_row(d)
    out = (
        pd.DataFrame({"repo": d["repo"].astype(str), "total_score": ts})
        .groupby("repo", dropna=False)
        .agg(
            n_rows=("total_score", "count"),
            sum_total_score=("total_score", "sum"),
            mean_total_score=("total_score", "mean"),
            median_total_score=("total_score", "median"),
            std_total_score=("total_score", "std"),
        )
        .reset_index()
        .sort_values("repo", kind="mergesort")
        .reset_index(drop=True)
    )
    return out
