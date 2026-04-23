"""
Shared judge output: CONFORMITY LLM JSON → structured result and DB row.

Schema (see docs/papers/CONFORMITY_SYSTEM_PROMPT.md): FUN, NSI, INSI, and ISI are
independent dimensions; each has _reasoning (str) and _score (0–3).
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class JudgeResult:
    """Full LLM coding result per CONFORMITY_SYSTEM_PROMPT (all four dimensions)."""

    fun_reasoning: str
    fun_score: int
    nsi_reasoning: str
    nsi_score: int
    insi_reasoning: str
    insi_score: int
    isi_reasoning: str
    isi_score: int
    raw_response: Optional[str] = None

    def to_row(self, comment_id: str, model_name: str, created_at: Optional[str] = None):
        """Tuple for SQLite scores row (see judge/storage.py SCORES_SCHEMA)."""
        return (
            comment_id,
            model_name,
            self.fun_score,
            self.fun_reasoning or "",
            self.nsi_score,
            self.nsi_reasoning or "",
            self.insi_score,
            self.insi_reasoning or "",
            self.isi_score,
            self.isi_reasoning or "",
            created_at,
        )


def clamp_score(value: int) -> int:
    """Clamp score to 0-3."""
    if value < 0:
        return 0
    if value > 3:
        return 3
    return value


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from model output (may be wrapped in markdown or extra text)."""
    text = text.strip()
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        raise ValueError("Unbalanced braces in response")
    return json.loads(text[start:end])


def _to_score_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _reasoning(data: dict[str, Any], key: str) -> str:
    return str(data.get(key, "") or "").strip()


def judge_result_from_parsed(data: dict[str, Any], raw: str) -> JudgeResult:
    """Map parsed JSON dict to JudgeResult (CONFORMITY 8-key schema)."""
    return JudgeResult(
        fun_reasoning=_reasoning(data, "fun_reasoning"),
        fun_score=clamp_score(_to_score_int(data.get("fun_score", 0))),
        nsi_reasoning=_reasoning(data, "nsi_reasoning"),
        nsi_score=clamp_score(_to_score_int(data.get("nsi_score", 0))),
        insi_reasoning=_reasoning(data, "insi_reasoning"),
        insi_score=clamp_score(_to_score_int(data.get("insi_score", 0))),
        isi_reasoning=_reasoning(data, "isi_reasoning"),
        isi_score=clamp_score(_to_score_int(data.get("isi_score", 0))),
        raw_response=raw,
    )


def empty_judge_result(raw: Optional[str] = None) -> JudgeResult:
    """Fallback when JSON parse fails (all scores 0, empty reasoning)."""
    return JudgeResult(
        fun_reasoning="",
        fun_score=0,
        nsi_reasoning="",
        nsi_score=0,
        insi_reasoning="",
        insi_score=0,
        isi_reasoning="",
        isi_score=0,
        raw_response=raw,
    )


def judge_result_from_raw_model_output(raw: str) -> JudgeResult:
    """
    Parse model output string to JudgeResult, or return empty fallback on failure.
    """
    try:
        data = extract_json_object(raw)
        return judge_result_from_parsed(data, raw)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning("Failed to parse judge JSON: %s. Raw: %s", e, raw[:200])
        return empty_judge_result(raw)
