"""
Judge config: supported models (Llama, Gemma) and default model.
Ollama tag names are what the user has pulled (e.g. llama3.1:8b, gemma2:27b).
OpenAI uses API model ids (e.g. gpt-5.4-mini).
"""

from typing import Literal

# Two supported models for now. Map short name -> default Ollama tag.
SUPPORTED_MODELS = {
    # "llama": "llama3.1:8b",
    "llama": "llama3.1:8b-instruct-q8_0",
    "gemma": "gemma2:27b",
}

# Default model when --model is not given (Ollama backend).
DEFAULT_MODEL = "llama"

# Default OpenAI API model when --backend openai and no --model.
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"

Backend = Literal["ollama", "openai"]


def resolve_model(name: str) -> str:
    """
    Resolve --model argument to an Ollama tag.
    If name is a short key (llama, gemma), return the configured tag.
    Otherwise treat name as the literal Ollama tag.
    """
    key = name.strip().lower()
    if key in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[key]
    return name


def resolve_model_for_backend(backend: Backend, model_arg: str | None) -> str:
    """
    Resolve model string for storage / dedupe key.
    Ollama: short keys (llama, gemma) -> configured tags; else literal tag.
    OpenAI: use literal model id; default to DEFAULT_OPENAI_MODEL if model_arg is None/empty.
    """
    if backend == "openai":
        if model_arg is None or not str(model_arg).strip():
            return DEFAULT_OPENAI_MODEL
        return str(model_arg).strip()
    if model_arg is None or not str(model_arg).strip():
        return resolve_model(DEFAULT_MODEL)
    return resolve_model(str(model_arg).strip())
