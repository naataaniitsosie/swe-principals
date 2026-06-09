"""
Detection storage: reads stratified sample rows (samples JOIN cleaned).
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Set

_SAMPLES_JOIN_SQL = """
SELECT
    s.id,
    s.repo,
    s.event_type,
    s.stratum_key,
    c.cleaned_text,
    c.tokens,
    c.author_association,
    c.created_at
FROM samples s
INNER JOIN cleaned c ON c.id = s.id
"""

_FILTER_MAP = {
    "repo":       "s.repo = ?",
    "event_type": "s.event_type = ?",
}


def _build_query(filters: dict) -> tuple[str, list]:
    where_parts = []
    params: list = []
    for key, value in filters.items():
        fragment = _FILTER_MAP.get(key)
        if not fragment:
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        where_parts.append(fragment)
        params.append(value.strip() if isinstance(value, str) else value)
    sql = _SAMPLES_JOIN_SQL.strip()
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)
    return sql, params


class SamplesReader:
    """
    Reads records from the stratified sample (samples JOIN cleaned).
    Optional filters: {"repo": "owner/name", "event_type": "PullRequestReviewCommentEvent"}.
    """

    def __init__(
        self,
        db_path: Path,
        skip_comment_ids: Optional[Set[str]] = None,
        filters: Optional[dict] = None,
    ):
        self._db_path = Path(db_path)
        self._skip_ids = skip_comment_ids or set()
        self._filters = filters or {}

    def list_records(self) -> List[dict]:
        if not self._db_path.exists():
            return []
        conn = sqlite3.connect(str(self._db_path))
        try:
            sql, params = _build_query(self._filters)
            cursor = conn.execute(sql, params)
            records = []
            for row in cursor:
                comment_id, repo, event_type, stratum_key, cleaned_text, tokens_str, author_association, created_at = row
                if comment_id in self._skip_ids:
                    continue
                if not (cleaned_text or "").strip():
                    continue
                try:
                    tokens = json.loads(tokens_str) if tokens_str else []
                except (json.JSONDecodeError, TypeError):
                    tokens = []
                records.append({
                    "id": comment_id,
                    "repo": repo or "",
                    "event_type": event_type or "",
                    "stratum_key": stratum_key or "",
                    "cleaned_text": cleaned_text,
                    "tokens": tokens,
                    "author_association": author_association or "",
                    "created_at": created_at or "",
                })
            return records
        finally:
            conn.close()
