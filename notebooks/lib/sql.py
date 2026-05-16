import pandas as pd
from .db import connect


def author_association_sql(alias: str = "e") -> str:
    """Same paths as `preprocessing.workflow._get_author_association` / `judge/storage.CLEANED_JOIN_FILTERS`."""
    return (
        f"COALESCE("
        f"json_extract({alias}.event_data, '$.payload.comment.author_association'), "
        f"json_extract({alias}.event_data, '$.payload.review.author_association'), "
        f"json_extract({alias}.event_data, '$.payload.pull_request.author_association'), "
        f"json_extract({alias}.event_data, '$.payload.issue.author_association')"
        f")"
    )


def repo_name_sql(alias: str = "e") -> str:
    return f"json_extract({alias}.event_data, '$.repo.name')"


def event_type_sql(alias: str = "e") -> str:
    """Top-level GitHub / GHArchive event type (e.g. ``IssueCommentEvent``)."""
    return f"json_extract({alias}.event_data, '$.type')"


def comment_author_login_sql(alias: str = "e") -> str:
    """GitHub login for comment/review author; falls back to ``actor.login``."""
    return (
        f"COALESCE("
        f"json_extract({alias}.event_data, '$.payload.comment.user.login'), "
        f"json_extract({alias}.event_data, '$.payload.review.user.login'), "
        f"json_extract({alias}.event_data, '$.actor.login')"
        f")"
    )


_BREAKDOWN_FROM = {
    "events": "FROM events e",
    "cleaned": "FROM cleaned c INNER JOIN events e ON e.id = c.id",
    "scores": (
        "FROM scores s "
        "INNER JOIN cleaned c ON c.id = s.comment_id "
        "INNER JOIN events e ON e.id = c.id"
    ),
}


def breakdown_df(
    scope: str,
    select_exprs: list[tuple[str, str]],
    group_by_positions: str,
    order_by: str = "n DESC",
) -> pd.DataFrame:
    """Run a grouped COUNT(*) query for scope in {'events','cleaned','scores'}.

    Use SQLite ``GROUP BY 1`` / ``GROUP BY 1, 2`` so grouping matches SELECT aliases.
    """
    if scope not in _BREAKDOWN_FROM:
        raise ValueError(f"scope must be one of {list(_BREAKDOWN_FROM)}")
    cols = ", ".join(f"{expr} AS {alias}" for expr, alias in select_exprs)
    q = f"""
    SELECT {cols}, COUNT(*) AS n
    {_BREAKDOWN_FROM[scope]}
    GROUP BY {group_by_positions}
    ORDER BY {order_by}
    """
    with connect() as conn:
        return pd.read_sql_query(q, conn)


def breakdown_repo_author_association(scope: str = "cleaned") -> pd.DataFrame:
    """Counts by full `owner/repo` (`$.repo.name`) × author_association."""
    rn = repo_name_sql("e")
    aa = author_association_sql("e")
    aa_label = f"COALESCE(NULLIF(TRIM({aa}), ''), '(empty)')"
    return breakdown_df(
        scope,
        [(rn, "repo"), (aa_label, "author_association")],
        "1, 2",
        order_by="repo ASC, author_association ASC, n DESC",
    )


def breakdown_event_type(scope: str = "cleaned") -> pd.DataFrame:
    """Counts by GH event ``type`` (``json_extract(..., '$.type')``)."""
    et = event_type_sql("e")
    type_label = f"COALESCE(NULLIF(TRIM({et}), ''), '(missing)')"
    return breakdown_df(
        scope,
        [(type_label, "event_type")],
        "1",
        order_by="n DESC, event_type ASC",
    )


def breakdown_repo_event_type(scope: str = "cleaned") -> pd.DataFrame:
    """Counts by full `owner/repo` (`$.repo.name`) × GH event `type` (`$.type`)."""
    rn = repo_name_sql("e")
    et = event_type_sql("e")
    repo_col = f"COALESCE(NULLIF(TRIM({rn}), ''), '(missing)')"
    type_label = f"COALESCE(NULLIF(TRIM({et}), ''), '(missing)')"
    return breakdown_df(
        scope,
        [(repo_col, "repo"), (type_label, "event_type")],
        "1, 2",
        order_by="repo ASC, event_type ASC, n DESC",
    )
