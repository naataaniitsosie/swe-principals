"""
Preprocessing for PR comment data: chainable workflow over events.
Steps: filter bot/CI, extract text, filter trivial, strip code blocks and images and diff snippets, lowercase and tokenize, filter min tokens, output slim record. See workflow.default_workflow() and papers/CONFORMITY.md.
"""
from preprocessing.pipeline import CleanerPipeline
from preprocessing.workflow import (
    Workflow,
    Context,
    Step,
    default_workflow,
    extract_text,
    filter_bot,
    filter_trivial,
    strip_code,
    strip_images,
    strip_diff,
    normalize_lowercase,
    tokenize_text,
    filter_min_tokens,
    finalize,
    slim_output,
)

__all__ = [
    "CleanerPipeline",
    "Workflow",
    "Context",
    "Step",
    "default_workflow",
    "extract_text",
    "filter_bot",
    "filter_trivial",
    "strip_code",
    "strip_images",
    "strip_diff",
    "normalize_lowercase",
    "tokenize_text",
    "filter_min_tokens",
    "finalize",
    "slim_output",
]
