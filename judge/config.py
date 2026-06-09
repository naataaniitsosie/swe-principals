"""
Model registry for judge.py.

Each entry maps a CLI name to backend, the tag/id sent to that backend,
and a human-readable location string logged at run start.

Passing an unregistered name raises ValueError. To add a new model, add an
entry to MODEL_REGISTRY below.
"""

from typing import Literal, NamedTuple


Backend = Literal["ollama", "openai", "openrouter"]


class ModelInfo(NamedTuple):
    backend: Backend
    tag: str       # identifier sent to the backend API
    location: str  # logged at run start so the user knows where inference runs


# ---------------------------------------------------------------------------
# Frontier judges — score all four dimensions (FUN, NSI, INSI, ISI).
# Inter-rater agreement across these models is the primary reliability signal.
# See judge/README.md for the rationale behind dropping the social/technical split.
# ---------------------------------------------------------------------------

MODEL_REGISTRY: dict[str, ModelInfo] = {
    "claude-sonnet": ModelInfo("openrouter", "anthropic/claude-sonnet-4-6",       "OpenRouter — Anthropic Claude Sonnet 4.6"),
    "gemma4-27b":    ModelInfo("ollama",     "gemma4:27b",                         "local Ollama — Gemma 4 27B"),
    "gpt-5.4-mini":  ModelInfo("openai",     "gpt-5.4-mini",                       "OpenAI API — GPT-5.4 mini"),
    "deepseek-v3":   ModelInfo("openrouter", "deepseek/deepseek-chat-v3-0324",     "OpenRouter — DeepSeek V3.2"),

    # -------------------------------------------------------------------------
    # Smoke test models — pipeline verification only, not production scoring
    # -------------------------------------------------------------------------
    "gemma4-e4b":    ModelInfo("ollama",     "gemma4:e4b",                         "local Ollama — Gemma 4 E4B [smoke test]"),
    "starcoder2-3b": ModelInfo("ollama",     "starcoder2:3b",                      "local Ollama — StarCoder2 3B [smoke test]"),

    # -------------------------------------------------------------------------
    # Deprecated — retained so existing scores.model_name values remain
    # resolvable, but not recommended for new runs.
    # -------------------------------------------------------------------------
    "mistral-large":  ModelInfo("openrouter", "mistralai/mistral-large",            "OpenRouter — Mistral Large 3 [deprecated]"),
    "phi4":           ModelInfo("ollama",     "phi4-reasoning",                     "local Ollama — Phi-4 Reasoning [deprecated]"),
    "qwen3-coder":    ModelInfo("openrouter", "qwen/qwen3-coder-next",              "OpenRouter — Qwen3 Coder Next [deprecated]"),
    "o4-mini":        ModelInfo("openai",     "o4-mini",                            "OpenAI API — o4-mini [deprecated]"),
    "starcoder2":     ModelInfo("ollama",     "starcoder2:instruct",                "local Ollama — StarCoder2 15B Instruct [deprecated]"),
    "granite-code":   ModelInfo("ollama",     "granite-code:34b",                   "local Ollama — Granite Code 34B [deprecated]"),
}

DEFAULT_MODEL = "gemma4-27b"


def resolve_model(name: str) -> ModelInfo:
    """Return ModelInfo for a registered CLI model name. Raises ValueError if not found."""
    key = name.strip().lower()
    if key in MODEL_REGISTRY:
        return MODEL_REGISTRY[key]
    known = ", ".join(k for k in MODEL_REGISTRY if "deprecated" not in MODEL_REGISTRY[k].location)
    raise ValueError(f"Unknown model {name!r}. Active models: {known}")
