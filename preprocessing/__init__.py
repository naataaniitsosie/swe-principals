"""
Preprocessing for PR comment data (CONFORMITY.md).
Chainable workflow: remove bots/CI, trivial comments; strip code/diff; lowercase and tokenize.
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
