"""
Judge config: supported models (Llama, Gemma) and default model.
Ollama tag names are what the user has pulled (e.g. llama3.1:8b, gemma2:27b).
"""

# Two supported models for now. Map short name -> default Ollama tag.
SUPPORTED_MODELS = {
    # "llama": "llama3.1:8b",
    "llama": "llama3.1:8b-instruct-q8_0",
    "gemma": "gemma2:27b",
}

# Default model when --model is not given (primary judge per CONFORMITY).
DEFAULT_MODEL = "llama"


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
