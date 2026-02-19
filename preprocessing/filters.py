"""
Filters to drop events with no semantic value (CONFORMITY.md: remove bot/CI, trivial comments).
Uses pattern matching on actor login and normalized comment text.
"""
import re
from typing import Dict, Any

# Bot/CI logins: GitHub app bots end with [bot]; common CI and automation logins
BOT_CI_PATTERNS = (
    "[bot]",           # GitHub Apps
    "bot",             # *bot*
    "github-actions",
    "dependabot",
    "dependabot[bot]",
    "actions-user",
    "greenkeeper",
    "renovate",
    "renovate[bot]",
    "stale",
    "stale[bot]",
    "ci",
    "travis",
    "circleci",
    "codecov",
)

# Trivial comments: no semantic value for conformity/sentiment (CONFORMITY.md examples + common)
TRIVIAL_PHRASES = frozenset({
    "lgtm", "lgtm!", "lgtm.",
    "thanks", "thanks!", "thanks.",
    "thank you", "thank you!",
    "approved", "approve",
    "ok", "ok.", "ok!",
    "nice", "nice!", "nice.",
    "👍", ":+1:", ":thumbsup:",
    "gtg", "sgtm", "sgtm.",
    "same", "same here",
    "done", "done.",
    "fixed", "fixed.",
    "re", "re.",
})


def is_bot_or_ci(actor: Dict[str, Any]) -> bool:
    """True if actor appears to be a bot or CI (pattern match on login)."""
    login = (actor.get("login") or "").lower()
    if not login:
        return True
    for pattern in BOT_CI_PATTERNS:
        if pattern in login:
            return True
    return False


def is_trivial_comment(text: str) -> bool:
    """True if text is a trivial comment with no semantic value (pattern match)."""
    if not text or not text.strip():
        return True
    normalized = text.strip().lower()
    # Exact match to trivial phrase
    if normalized in TRIVIAL_PHRASES:
        return True
    # Only punctuation/whitespace difference
    cleaned = re.sub(r"[^\w\s]", "", normalized).strip()
    if cleaned in TRIVIAL_PHRASES:
        return True
    # Single token that matches
    tokens = set(re.findall(r"\w+", normalized))
    if len(tokens) <= 2 and tokens.issubset(TRIVIAL_PHRASES):
        return True
    return False
