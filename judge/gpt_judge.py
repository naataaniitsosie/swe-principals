"""
OpenAI Chat Completions judge: same rubric and JSON parsing as OllamaJudge (judge.judge_result).

Uses OPENAI_API_TOKEN for authentication (set in the environment or in a `.env` file at the
repository root; see `project_config`).
"""
import os
from typing import Optional

import project_config  # noqa: F401 — loads `.env` from repo root before OPENAI_API_TOKEN is read
from openai import OpenAI

from judge.judge_result import JudgeResult, judge_result_from_raw_model_output
from judge.rubric import build_user_message, get_system_prompt

# Default model id (OpenAI API); override via GPTJudge(model=...).
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"

# Request timeout in seconds (large comments + reasoning JSON).
_DEFAULT_TIMEOUT_S = 120.0

_ENV_API_TOKEN = "OPENAI_API_TOKEN"


class GPTJudge:
    """
    Judge that uses the OpenAI API with the CONFORMITY system prompt.
    Call score(cleaned_text) -> JudgeResult (full CONFORMITY dimensions).
    """

    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        *,
        api_key: Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT_S,
    ):
        self.model = model
        self._timeout = timeout
        self._api_key = api_key or os.environ.get(_ENV_API_TOKEN)
        if not self._api_key or not str(self._api_key).strip():
            raise ValueError(
                f"OpenAI API key missing: set {_ENV_API_TOKEN} in the environment, "
                f"or add it to `.env` at the repo root ({project_config.repo_root()}), "
                "or pass api_key= to GPTJudge."
            )
        self._system_prompt = get_system_prompt()

    def score(self, cleaned_text: str) -> JudgeResult:
        """
        Send the comment to OpenAI with the rubric as system prompt.
        Parse JSON per CONFORMITY_SYSTEM_PROMPT (FUN, NSI, INSI, ISI).
        """
        client = OpenAI(api_key=self._api_key, timeout=self._timeout)
        user_message = build_user_message(cleaned_text)

        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        choice = completion.choices[0]
        content = (choice.message.content or "").strip()
        return judge_result_from_raw_model_output(content)
