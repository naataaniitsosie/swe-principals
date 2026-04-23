"""
Model resolution for `judge.py` / `judge.runner`.

Two backends behave differently:

- **Ollama** (`--backend ollama`, the CLI default): `--model` is an Ollama *tag*
  (e.g. `llama3.1:8b-instruct-q8_0`). We also allow *short aliases* (see
  `SUPPORTED_MODELS`) so you can pass `llama` instead of the full tag. Whatever
  string is resolved here is stored in SQLite as `scores.model_name`.

- **OpenAI** (`--backend openai`): `--model` is an OpenAI API model id
  (e.g. `gpt-5.4-mini`). There is no alias map; the id is used as-is (or the
  OpenAI default below if `--model` is omitted).
"""

from typing import Literal

# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

# CLI / runner backend selector; drives which branch of `resolve_model_for_backend` runs.
Backend = Literal["ollama", "openai"]


# ---------------------------------------------------------------------------
# OpenAI only (`--backend openai`)
# ---------------------------------------------------------------------------

# Used when `--backend openai` and `--model` is omitted or blank.
# Must match an id your API key can call; stored verbatim in `scores.model_name`.
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"


# ---------------------------------------------------------------------------
# Ollama only (`--backend ollama`, default)
# ---------------------------------------------------------------------------

# Short CLI aliases -> full Ollama model tags (what `ollama run` / the API expects).
# Only this backend uses this map. If `--model` is not a key here, it is treated as a
# literal tag (so you can pass any pulled model without adding it below).
SUPPORTED_MODELS = {
    "llama": "llama3.1:8b-instruct-q8_0",
    "gemma": "gemma2:27b",
}

# When `--backend ollama` and `--model` is omitted: resolve this *key* via `SUPPORTED_MODELS`.
DEFAULT_MODEL = "llama"


def resolve_model(name: str) -> str:
    """
    Ollama: map a `--model` string to the tag we store and send to Ollama.

    - If `name` matches a key in `SUPPORTED_MODELS` (case-insensitive), return the tag.
    - Otherwise return `name` unchanged (already a full Ollama tag).
    """
    key = name.strip().lower()
    if key in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[key]
    return name


# ---------------------------------------------------------------------------
# Both backends: single entry point for `scores.model_name` / dedupe key
# ---------------------------------------------------------------------------


def resolve_model_for_backend(backend: Backend, model_arg: str | None) -> str:
    """
    Return the model string used everywhere after CLI parsing: judging, DB writes,
    and `get_scored_comment_ids`.

    - **openai:** API model id; default `DEFAULT_OPENAI_MODEL` if `model_arg` empty.
    - **ollama:** resolved via `resolve_model` / `SUPPORTED_MODELS`; default
      `DEFAULT_MODEL` if `model_arg` empty.
    """
    if backend == "openai":
        if model_arg is None or not str(model_arg).strip():
            return DEFAULT_OPENAI_MODEL
        return str(model_arg).strip()
    if model_arg is None or not str(model_arg).strip():
        return resolve_model(DEFAULT_MODEL)
    return resolve_model(str(model_arg).strip())
