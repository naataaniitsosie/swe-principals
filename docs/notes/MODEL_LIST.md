# Judge Models

Complete list of Ollama and API-based models for LLM scoring. See [`judge/README.md`](../judge/README.md) for full implementation details.

**Note:** Models are grouped by training data and general capabilities. Empirical performance on specific conformity dimensions (FUN, NSI, INSI, ISI) is measured in [`META_EVALUATION.md`](META_EVALUATION.md).

---

## Social-Focused Models

*Trained on human interactions, reasoning about nuance, and understanding social context.*

| Model | Size | Background | Hugging Face | Ollama Install | Access |
|-------|------|-----------|--------------|----------------|--------|
| Claude Sonnet 4.6 | — | General assistant with strong reasoning capability. | — (proprietary) | — | OpenRouter |
| Gemma 4 | 31B | General instruction-tuned model. | [google/gemma-4-31B-it](https://huggingface.co/google/gemma-4-31B-it) | `ollama pull gemma4:31b` | Ollama |
| Mistral Large 3 | 41B active (675B MoE) | General instruction-tuned, multilingual. | [mistralai/Mistral-Large-3-675B-Instruct-2512](https://huggingface.co/mistralai/Mistral-Large-3-675B-Instruct-2512) | — (not on Ollama) | OpenRouter |
| Phi-4-Reasoning-Vision-15B | 15B | Reasoning-specialized, chain-of-thought capable. | [microsoft/Phi-4-reasoning-vision-15B](https://huggingface.co/microsoft/Phi-4-reasoning-vision-15B) | — (text-only `phi4-reasoning` available; no vision tag) | Ollama |
| GPT-5.4 mini | — | General instruction-tuned baseline. | — (proprietary) | — | OpenAI API |

---

## Code-Focused Models

*Trained on source code and programming tasks.*

| Model | Size | Background | Hugging Face | Ollama Install | Access |
|-------|------|-----------|--------------|----------------|--------|
| DeepSeek-V3.2 | 37B active (671B MoE) | Code-specialized, deep reasoning. | [deepseek-ai/DeepSeek-V3.2](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) | — (not on Ollama) | OpenRouter |
| Qwen3-Coder-Next | 3B active (80B MoE) | Code-specialized, lightweight. | [Qwen/Qwen3-Coder-Next](https://huggingface.co/Qwen/Qwen3-Coder-Next) | `ollama pull qwen3-coder-next` | Ollama |
| o4-mini | — | Reasoning-focused code model. | — (proprietary) | — | OpenAI API |
| StarCoder 2 15B Instruct | 15B | Code-specialized, instruction-tuned. | [bigcode/starcoder2-15b-instruct-v0.1](https://huggingface.co/bigcode/starcoder2-15b-instruct-v0.1) | `ollama pull starcoder2:instruct` | Ollama |
| Granite Code 34B | 34B | Code-specialized, enterprise-focused. | [ibm-granite/granite-34b-code-instruct-8k](https://huggingface.co/ibm-granite/granite-34b-code-instruct-8k) | `ollama pull granite-code:34b` | Ollama |

---

## Running Models

### Ollama Setup

Pull any Ollama model:

```bash
ollama pull gemma4:31b              # Gemma 4 31B
ollama pull qwen3-coder-next        # Qwen3-Coder-Next (80B MoE, 3B active)
ollama pull starcoder2:instruct     # StarCoder 2 15B Instruct
ollama pull granite-code:34b        # Granite Code 34B
```

Score with Ollama backend:

```bash
python judge.py --backend ollama --model gemma4:31b
python judge.py --backend ollama --model starcoder2:instruct
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
