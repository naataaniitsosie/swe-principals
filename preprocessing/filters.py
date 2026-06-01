"""
Filters to drop events with no semantic value (CONFORMITY.md: remove bot/CI actors).
Uses pattern matching on actor login.
"""
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

def is_bot_or_ci(actor: Dict[str, Any]) -> bool:
    """True if actor appears to be a bot or CI (pattern match on login)."""
    login = (actor.get("login") or "").lower()
    if not login:
        return True
    for pattern in BOT_CI_PATTERNS:
        if pattern in login:
            return True
    return False
