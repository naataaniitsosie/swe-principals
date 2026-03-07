"""
Ollama-backed LLM judge: sends rubric as system prompt, comment as user message, parses JSON result.
"""
import json
import logging
from dataclasses import dataclass
from typing import Optional

from judge.rubric import get_system_prompt, build_user_message

logger = logging.getLogger(__name__)


@dataclass
class JudgeResult:
    """Result of scoring one comment: NSI/ISI scores and reasoning."""
    nsi_score: int
    isi_score: int
    nsi_reasoning: str
    isi_reasoning: str
    raw_response: Optional[str] = None

    def to_row(self, comment_id: str, model_name: str, created_at: Optional[str] = None):
        """Return tuple for storage: (comment_id, model_name, nsi_score, isi_score, nsi_reasoning, isi_reasoning, created_at)."""
        return (
            comment_id,
            model_name,
            self.nsi_score,
            self.isi_score,
            self.nsi_reasoning or "",
            self.isi_reasoning or "",
            created_at,
        )


def _clamp_score(value: int) -> int:
    """Clamp score to 0-3."""
    if value < 0:
        return 0
    if value > 3:
        return 3
    return value


def _extract_json(text: str) -> dict:
    """Try to extract a JSON object from model output (may be wrapped in markdown or extra text)."""
    text = text.strip()
    # Try to find {...}
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


class OllamaJudge:
    """
    Judge that uses Ollama with the CONFORMITY rubric.
    Call score(cleaned_text) to get JudgeResult.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._system_prompt = get_system_prompt()

    def score(self, cleaned_text: str) -> JudgeResult:
        """
        Send the comment to Ollama with the rubric as system prompt.
        Parse JSON response into nsi_score, isi_score, nsi_reasoning, isi_reasoning.
        """
        try:
            import ollama
        except ImportError:
            raise ImportError(
                "ollama package is required. Install with: pip install ollama"
            ) from None

        user_message = build_user_message(cleaned_text)
        response = ollama.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        content = response.get("message", {}).get("content", "") or ""
        raw = content.strip()

        try:
            data = _extract_json(raw)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse judge JSON: %s. Raw: %s", e, raw[:200])
            return JudgeResult(
                nsi_score=0,
                isi_score=0,
                nsi_reasoning="",
                isi_reasoning="",
                raw_response=raw,
            )

        nsi_score = _clamp_score(int(data.get("nsi_score", 0)))
        isi_score = _clamp_score(int(data.get("isi_score", 0)))
        nsi_reasoning = str(data.get("nsi_reasoning", "") or "").strip()
        isi_reasoning = str(data.get("isi_reasoning", "") or "").strip()

        return JudgeResult(
            nsi_score=nsi_score,
            isi_score=isi_score,
            nsi_reasoning=nsi_reasoning,
            isi_reasoning=isi_reasoning,
            raw_response=raw,
        )
