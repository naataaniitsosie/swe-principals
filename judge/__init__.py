"""
LLM judge for conformity scoring on PR comments (FUN, NSI, INSI, ISI).

Sub-packages:
  detection/  — score each comment in isolation (implemented; see judge.py)
  contextual/ — score comments in PR-thread context (not yet implemented)

Shared modules (used by both sub-packages):
  config.py           MODEL_REGISTRY: model name → backend + tag + location
  judge_result.py     JudgeResult dataclass and JSON parsing
  rubric.py           CONFORMITY system prompt loader
  storage.py          ScoresWriter, get_scored_comment_ids, EXPERIMENT_VERSION
  gpt_judge.py        OpenAI Chat Completions backend
  openrouter_judge.py OpenRouter backend (OpenAI-compatible)
  ollama_judge.py     Ollama local backend
"""
