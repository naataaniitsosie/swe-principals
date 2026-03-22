"""
LLM system prompt: full contents of docs/papers/CONFORMITY_SYSTEM_PROMPT.md.

The paper links to that file from CONFORMITY.md (LLM Coding Scheme section).
"""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYSTEM_PROMPT_PATH = _REPO_ROOT / "docs" / "papers" / "CONFORMITY_SYSTEM_PROMPT.md"


def _load_system_prompt() -> str:
    """Return the system prompt markdown exactly as in CONFORMITY_SYSTEM_PROMPT.md."""
    if not _SYSTEM_PROMPT_PATH.is_file():
        raise FileNotFoundError(f"System prompt file not found: {_SYSTEM_PROMPT_PATH}")
    text = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return text.strip() + "\n"


# Single source of truth: docs/papers/CONFORMITY_SYSTEM_PROMPT.md
SYSTEM_PROMPT = _load_system_prompt()

USER_MESSAGE_TEMPLATE = """Score this PR comment:

{cleaned_text}"""


def get_system_prompt() -> str:
    """Return the full LLM system prompt (rubric)."""
    return SYSTEM_PROMPT


def build_user_message(cleaned_text: str) -> str:
    """Build the user message for a single comment."""
    return USER_MESSAGE_TEMPLATE.format(cleaned_text=cleaned_text or "")
