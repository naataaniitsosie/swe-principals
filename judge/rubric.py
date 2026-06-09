"""
LLM system prompt for detection scoring.

The active prompt is prompt/detection/latest.md.
To promote a new version: cp prompt/detection/vN.md prompt/detection/latest.md
See prompt/detection/README.md for the versioning convention.
"""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYSTEM_PROMPT_PATH = _REPO_ROOT / "prompt" / "detection" / "latest.md"


def _load_system_prompt() -> str:
    if not _SYSTEM_PROMPT_PATH.is_file():
        raise FileNotFoundError(f"System prompt not found: {_SYSTEM_PROMPT_PATH}")
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip() + "\n"


SYSTEM_PROMPT = _load_system_prompt()

USER_MESSAGE_TEMPLATE = """Score this PR comment:

{cleaned_text}"""


def get_system_prompt() -> str:
    """Return the full LLM system prompt (rubric)."""
    return SYSTEM_PROMPT


def build_user_message(cleaned_text: str) -> str:
    """Build the user message for a single comment."""
    return USER_MESSAGE_TEMPLATE.format(cleaned_text=cleaned_text or "")
