"""
Middleware/workflow for preprocessing: chainable steps that operate on a context.
Each step receives a Context and returns the (updated) context or None to drop the event.
Use default_workflow() or build Workflow([...]) from exported steps; pass to CleanerPipeline(..., workflow=w).
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable

from dataset_readers.gharchive.models import GitHubEvent

from preprocessing.filters import is_bot_or_ci, is_trivial_comment
from preprocessing.text_cleaner import (
    strip_code_blocks,
    strip_diff_snippets,
    strip_images as strip_images_text,
    lowercase,
    tokenize,
)


@dataclass
class Context:
    """Mutable context passed through the workflow. Steps read and update fields."""
    event: Dict[str, Any]
    text: Optional[str] = None
    cleaned_text: Optional[str] = None
    tokens: List[str] = field(default_factory=list)


# Step: (Context) -> Optional[Context]. Return None to drop the event.
Step = Callable[[Context], Optional[Context]]


def extract_text(ctx: Context) -> Optional[Context]:
    """Extract comment/PR text from event (same logic as dataset reader)."""
    try:
        gh = GitHubEvent.from_dict(ctx.event)
        ctx.text = gh.extract_text_content()
    except (ValueError, KeyError):
        ctx.text = None
    return ctx if ctx.text and ctx.text.strip() else None


def filter_bot(ctx: Context) -> Optional[Context]:
    """Drop events from bot/CI actors."""
    actor = (ctx.event.get("actor") or {})
    return None if is_bot_or_ci(actor) else ctx


def filter_trivial(ctx: Context) -> Optional[Context]:
    """Drop trivial comments (e.g. LGTM, Thanks!)."""
    return None if is_trivial_comment(ctx.text or "") else ctx


def strip_code(ctx: Context) -> Optional[Context]:
    """Strip markdown code blocks from text."""
    ctx.cleaned_text = strip_code_blocks(ctx.text or "")
    return ctx


def strip_images(ctx: Context) -> Optional[Context]:
    """Strip markdown images ![alt](url) and [image](url) from text."""
    ctx.cleaned_text = strip_images_text(ctx.cleaned_text or ctx.text or "")
    return ctx


def strip_diff(ctx: Context) -> Optional[Context]:
    """Strip diff snippet lines from cleaned text."""
    ctx.cleaned_text = strip_diff_snippets(ctx.cleaned_text or ctx.text or "")
    return ctx


def normalize_lowercase(ctx: Context) -> Optional[Context]:
    """Lowercase and collapse whitespace."""
    t = ctx.cleaned_text or ctx.text or ""
    ctx.cleaned_text = " ".join(lowercase(t).split()).strip()
    return ctx


def tokenize_text(ctx: Context) -> Optional[Context]:
    """Tokenize cleaned text."""
    ctx.tokens = tokenize(ctx.cleaned_text or "")
    return ctx


def filter_min_tokens(ctx: Context, min_tokens: int = 2) -> Optional[Context]:
    """Drop if too few tokens (no semantic value)."""
    return None if len(ctx.tokens) < min_tokens else ctx


def finalize(ctx: Context) -> Optional[Context]:
    """Add cleaned_text and tokens to event for output."""
    out = dict(ctx.event)
    out["cleaned_text"] = ctx.cleaned_text or ""
    out["tokens"] = ctx.tokens
    ctx.event = out
    return ctx


def slim_output(ctx: Context) -> Optional[Context]:
    """Keep only pertinent fields: id, cleaned_text, repo, created_at, type, author_association, tokens."""
    ev = ctx.event
    repo = ev.get("repo") or {}
    repo_name = repo.get("name", "") if isinstance(repo, dict) else ""
    ctx.event = {
        "id": ev.get("id"),
        "cleaned_text": ctx.cleaned_text or ev.get("cleaned_text", ""),
        "repo": repo_name,
        "created_at": ev.get("created_at"),
        "type": ev.get("type"),
        "author_association": _get_author_association(ev),
        "tokens": ctx.tokens or ev.get("tokens", []),
    }
    return ctx


class Workflow:
    """Run a chain of steps on each event. Steps are applied in order; None from any step drops the event."""

    def __init__(self, steps: List[Step]):
        self.steps = steps

    def run(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run the workflow on one event. Returns updated event or None if dropped."""
        ctx = Context(event=dict(event))
        for step in self.steps:
            ctx = step(ctx)
            if ctx is None:
                return None
        return ctx.event

    def chain(self, *steps: Step) -> "Workflow":
        """Return a new workflow with additional steps appended (immutable)."""
        return Workflow(self.steps + list(steps))


def default_workflow() -> Workflow:
    """Filter bot/CI, extract text, filter trivial, strip code/images/diff, lowercase, tokenize, drop if < 2 tokens, slim output."""
    return Workflow([
        filter_bot,
        extract_text,
        # filter_trivial,
        strip_code,
        strip_images,
        strip_diff,
        normalize_lowercase,
        tokenize_text,
        lambda ctx: filter_min_tokens(ctx, min_tokens=2),
        finalize,
        slim_output,
    ])

# --- Helpers (not workflow steps) ---

def _get_author_association(event: Dict[str, Any]) -> str:
    """Extract author_association from payload (comment, review, or pull_request). Used by slim_output."""
    payload = event.get("payload") or {}
    return (
        payload.get("comment", {}).get("author_association")
        or payload.get("review", {}).get("author_association")
        or payload.get("pull_request", {}).get("author_association")
        or payload.get("issue", {}).get("author_association")
        or ""
    )
