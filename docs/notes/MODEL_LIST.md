# Judge Models

Complete list of Ollama and API-based models for LLM scoring. See [`judge/README.md`](../judge/README.md) for full implementation details.

**Note:** Models are grouped by training data and general capabilities. Empirical performance on specific conformity dimensions (FUN, NSI, INSI, ISI) is measured in [`META_EVALUATION.md`](META_EVALUATION.md).

---

## Social-Focused Models

*Trained on human interactions, reasoning about nuance, and understanding social context.*

| Model | Size | Background | Access |
|-------|------|-----------|--------|
| Claude Sonnet 4.6 | — | General assistant with strong reasoning capability. | OpenRouter |
| Gemma 4 | 31B | General instruction-tuned model. | Ollama |
| Mistral Large 3 | 41B active (675B MoE) | General instruction-tuned, multilingual. | OpenRouter |
| Phi-4-Reasoning-Vision-15B | 15B | Reasoning-specialized, chain-of-thought capable. | Ollama |
| GPT-5.4 mini | — | General instruction-tuned baseline. | OpenAI API |

---

## Code-Focused Models

*Trained on source code and programming tasks.*

| Model | Size | Background | Access |
|-------|------|-----------|--------|
| DeepSeek-V3.2 | 37B active (671B MoE) | Code-specialized, deep reasoning. | OpenRouter |
| Qwen3-Coder-Next | 3B active (80B MoE) | Code-specialized, lightweight. | Ollama |
| o4-mini | — | Reasoning-focused code model. | OpenAI API |
| StarCoder 2 15B Instruct | 15B | Code-specialized, instruction-tuned. | Ollama |
| Granite Code 34B | 34B | Code-specialized, enterprise-focused. | Ollama |

---

## Running Models

### Ollama Setup

Pull any Ollama model:

```bash
ollama pull phi4                    # Phi-4-Reasoning
ollama pull starcoder2:15b          # StarCoder 2 15B
ollama pull gemma:31b               # Gemma 4 31B
```

Score with Ollama backend:

```bash
python judge.py --backend ollama --model phi4
python judge.py --backend ollama --model starcoder2:15b
```

### OpenAI Setup

Set `OPENAI_API_TOKEN` in `.env` (repo root), then:

```bash
python judge.py --backend openai --model gpt-5.4-mini
```

---

## Model Selection Guide

**For meta-evaluation (preferred for compute cost):**
- **Social judge:** `Phi-4-Reasoning-Vision-15B` (Ollama) — good reasoning, local
- **Technical judge:** `StarCoder 2 15B` (Ollama) — strong code understanding, socially blind

**For validation with API models:**
- **Social judge:** `Claude Sonnet 4.6` (OpenRouter) — state-of-the-art social reasoning
- **Technical judge:** `DeepSeek-V3.2` (OpenRouter) — best code intelligence

---

## References

- Full implementation: [`judge/README.md`](../judge/README.md)
- Scoring rubric: [`docs/papers/CONFORMITY_SYSTEM_PROMPT.md`](../papers/CONFORMITY_SYSTEM_PROMPT.md)
- Database schema: [`docs/DB_SCHEMA.md`](../DB_SCHEMA.md)
