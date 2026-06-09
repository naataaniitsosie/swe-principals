"""
OpenRouter judge: OpenAI-compatible API at https://openrouter.ai/api/v1.

Requires OPENROUTER_API_TOKEN in the environment or in a `.env` file at the
repository root (loaded automatically via project_config).
"""

import os
from typing import Optional

import project_config  # noqa: F401 — loads .env from repo root
from openai import OpenAI

from judge.judge_result import JudgeResult, judge_result_from_raw_model_output
from judge.rubric import build_user_message, get_system_prompt

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_ENV_API_TOKEN = "OPENROUTER_API_TOKEN"
_DEFAULT_TIMEOUT_S = 120.0


class OpenRouterJudge:
    """
    Judge that uses OpenRouter's OpenAI-compatible API with the CONFORMITY rubric.
    Set OPENROUTER_API_TOKEN in .env or the environment.
    """

    def __init__(
        self,
        model: str,
        *,
        api_key: Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT_S,
    ):
        self.model = model
        self._timeout = timeout
        self._api_key = api_key or os.environ.get(_ENV_API_TOKEN)
        if not self._api_key or not str(self._api_key).strip():
            raise ValueError(
                f"OpenRouter API key missing: set {_ENV_API_TOKEN} in the environment "
                f"or add it to `.env` at the repo root ({project_config.repo_root()})."
            )
        self._system_prompt = get_system_prompt()

    def score(self, cleaned_text: str) -> JudgeResult:
        client = OpenAI(
            api_key=self._api_key,
            base_url=_OPENROUTER_BASE_URL,
            timeout=self._timeout,
        )
        user_message = build_user_message(cleaned_text)
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        content = (completion.choices[0].message.content or "").strip()
        return judge_result_from_raw_model_output(content)
