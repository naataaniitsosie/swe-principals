"""
Ollama-backed LLM judge: sends rubric as system prompt, comment as user message, parses JSON result.

Parsing and JudgeResult shape are shared with GPTJudge via judge.judge_result (CONFORMITY 8-key JSON).
"""

from judge.judge_result import JudgeResult, judge_result_from_raw_model_output
from judge.rubric import get_system_prompt, build_user_message


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
        Parse JSON per CONFORMITY_SYSTEM_PROMPT (FUN, NSI, INSI, ISI).
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

        return judge_result_from_raw_model_output(raw)
