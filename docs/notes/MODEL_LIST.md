# Judge Models

Complete list of Ollama and API-based models for LLM scoring. See [`judge/README.md`](../judge/README.md) for full implementation details.

**Note:** Models are grouped by training data and general capabilities. Empirical performance on specific conformity dimensions (FUN, NSI, INSI, ISI) is measured in [`META_EVALUATION.md`](META_EVALUATION.md).

---

## Social-Focused Models

*Trained on human interactions, reasoning about nuance, and understanding social context.*

| Model | Size | Background | Hugging Face | Ollama Install | Access |
|-------|------|-----------|--------------|----------------|--------|
| Claude Sonnet 4.6 | — | General assistant with strong reasoning capability. | — (proprietary) | — | OpenRouter |
| Gemma 4 E4B | 4B effective | Smaller Gemma 4 variant; recommended first Gemma 4 pass for local scoring. | — | `ollama pull gemma4:e4b` | Ollama |
| Mistral Large 3 | 41B active (675B MoE) | General instruction-tuned, multilingual. | [mistralai/Mistral-Large-3-675B-Instruct-2512](https://huggingface.co/mistralai/Mistral-Large-3-675B-Instruct-2512) | — (not on Ollama) | OpenRouter |
| Phi-4-Reasoning-Vision-15B | 15B | Reasoning-specialized, chain-of-thought capable. | [microsoft/Phi-4-reasoning-vision-15B](https://huggingface.co/microsoft/Phi-4-reasoning-vision-15B) | `ollama pull phi4-reasoning` (text-only; no vision tag) | Ollama |
| GPT-5.4 mini | — | General instruction-tuned baseline. | — (proprietary) | — | OpenAI API |

---

## Code-Focused Models

*Trained on source code and programming tasks.*

| Model | Size | Background | Hugging Face | Ollama Install | Access |
|-------|------|-----------|--------------|----------------|--------|
| DeepSeek-V3.2 | 37B active (671B MoE) | Code-specialized, deep reasoning. | [deepseek-ai/DeepSeek-V3.2](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) | — (not on Ollama) | OpenRouter |
| Qwen3-Coder-Next | 3B active (80B MoE) | Code-specialized, lightweight. | [Qwen/Qwen3-Coder-Next](https://huggingface.co/Qwen/Qwen3-Coder-Next) | `ollama pull qwen3-coder-next` | Ollama |
| o4-mini | — | Reasoning-focused code model. | — (proprietary) | — | OpenAI API |
| StarCoder 2 3B | 3B | Code-specialized, lightweight comparison model closest to Gemma 4 E4B's effective size class. | [bigcode/starcoder2-3b](https://huggingface.co/bigcode/starcoder2-3b) | `ollama pull starcoder2:3b` | Ollama |
| StarCoder 2 15B Instruct | 15B | Larger code-specialized instruction-tuned reference. | [bigcode/starcoder2-15b-instruct-v0.1](https://huggingface.co/bigcode/starcoder2-15b-instruct-v0.1) | `ollama pull starcoder2:instruct` | Ollama |
| Granite Code 34B | 34B | Code-specialized, enterprise-focused. | [ibm-granite/granite-34b-code-instruct-8k](https://huggingface.co/ibm-granite/granite-34b-code-instruct-8k) | `ollama pull granite-code:34b` | Ollama |

---

## Running Models

### Ollama Setup

Pull any Ollama model:

```bash
ollama pull gemma4:e4b              # Gemma 4 E4B, faster local option
ollama pull phi4-reasoning          # Phi-4 reasoning, text-only Ollama tag
ollama pull qwen3-coder-next        # Qwen3-Coder-Next (80B MoE, 3B active)
ollama pull starcoder2:3b           # StarCoder 2 3B
ollama pull granite-code:34b        # Granite Code 34B
```

Supported model names in `judge.py`:

| Model name | Ollama tag |
|------------|------------|
| `gemma4-e4b` | `gemma4:e4b` |
| `phi4` | `phi4-reasoning` |
| `qwen3-coder` | `qwen3-coder-next` |
| `starcoder2-3b` | `starcoder2:3b` |
| `starcoder2` | `starcoder2:instruct` |
| `granite-code` | `granite-code:34b` |

Score with Ollama backend:

```bash
python judge.py --backend ollama --model gemma4-e4b
python judge.py --backend ollama --model phi4
python judge.py --backend ollama --model qwen3-coder
python judge.py --backend ollama --model starcoder2-3b
python judge.py --backend ollama --model granite-code
```

### OpenAI Setup

Set `OPENAI_API_TOKEN` in `.env` (repo root), then:

```bash
python judge.py --backend openai --model gpt-5.4-mini
```

---

## Model Selection Guide

**For meta-evaluation (preferred for compute cost):**
- **Social judge:** `Gemma 4 E4B` (`gemma4-e4b`, Ollama) — practical local Gemma 4 pass on a 34 GB MacBook Pro
- **Technical judge:** `StarCoder 2 3B` (`starcoder2-3b`, Ollama) — code-focused contrast near Gemma 4 E4B's effective size class

**For validation with API models:**
- **Social judge:** `Claude Sonnet 4.6` (OpenRouter) — state-of-the-art social reasoning
- **Technical judge:** `DeepSeek-V3.2` (OpenRouter) — best code intelligence

### Local Feasibility and Re-Selection

The full meta-evaluation requires scoring tens of thousands of comments, so local throughput matters as much as model size. On a 34 GB MacBook Pro, prefer a model that can produce steady per-comment latency rather than the largest model that technically fits in memory.

| Model | Ollama tag | Local size | Comparison role | Practical note |
|-------|------------|------------|-----------------|----------------|
| Gemma 4 E4B | `gemma4:e4b` | 9.6 GB | Current social/general judge | Recommended first Gemma 4 choice; much more practical than 31B for full scoring. |
| StarCoder 2 3B | `starcoder2:3b` | 1.7 GB | Current technical/code-focused contrast | StarCoder2 has no 4B tag; 3B is the closest smaller size-class match to Gemma 4 E4B. |
| StarCoder 2 15B Instruct | `starcoder2:instruct` | 9.1 GB | Heavier technical/code reference | Similar local file size to Gemma 4 E4B, but a much larger parameter class; reserve for validation if 3B is too weak. |
| Phi-4 Reasoning | `phi4-reasoning` | 15B class | Alternate social/reasoning judge | Try if Gemma 4 E4B underperforms on NSI/INSI agreement. |
| Granite Code 34B | `granite-code:34b` | 34B class | Heavier technical/code judge | Likely memory- and latency-constrained locally; use only for sampled validation. |

Rechoose models if a 20-comment benchmark suggests the full run will take more than a few days, if the model frequently emits invalid JSON, or if the paired models are too mismatched in capability to interpret agreement differences. A practical workflow is to benchmark with `--limit 20`, inspect a sample with `browse_scores.py`, then run the full pass with `--skip-existing`.

---

## References

- Full implementation: [`judge/README.md`](../judge/README.md)
- Scoring rubric: [`papers/publication1/CONFORMITY_SYSTEM_PROMPT.md`](../../papers/publication1/CONFORMITY_SYSTEM_PROMPT.md)
- Database schema: [`docs/DB_SCHEMA.md`](../DB_SCHEMA.md)
