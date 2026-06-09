# prompt/detection — Detection scoring prompts

Versioned system prompts for detection scoring (per-comment, no thread context).

## Files

| File | Description |
|------|-------------|
| `latest.md` | **Active prompt** — this is what `judge/rubric.py` loads |
| `v1.md` | Baseline — all five calibration examples including the Masquerade shot |
| `v2.md` | Masquerade shot removed (see rationale below) |

## Promoting a version

`latest.md` is a plain file copy — not a symlink. To make a new version active:

```bash
cp prompt/detection/vN.md prompt/detection/latest.md
```

Commit both the new `vN.md` and the updated `latest.md` together. The `EXPERIMENT_VERSION` constant in `judge/storage.py` should be bumped at the same time so that scores produced with the new prompt live in a separate namespace from prior runs.

## Version history

### V2 (current) — Masquerade shot removed

The Masquerade example was dropped because it is an **analysis-time abstraction**, not an **inference-time target**. Detecting a "Masquerade" means noticing that a reviewer cloaks a social norm as a functional requirement — a pattern that only becomes visible when comparing NSI and FUN scores in aggregate across comments or a thread. Presenting it as a calibration shot asks the model to detect a co-occurrence and name it, which risks coupling the FUN, NSI, and ISI dimensions during scoring — exactly the kind of joint-weighting the independent-dimensions rubric is designed to prevent. In V2, the model scores each dimension in isolation; the Masquerade label is applied in post-hoc analysis, not at inference time.

### V1 — Baseline

Direct copy of `papers/publication1/CONFORMITY_SYSTEM_PROMPT.md` as originally written. Retained for reproducibility and comparison.
