# Contextual Scoring

> **Not yet implemented.**

Contextual scoring will reason about conformity *across* a PR thread or repository rather than on a single comment in isolation. Example hypotheses: does reviewer language harden as a PR progresses? Does conformity pressure vary by repo culture? Can we detect the Masquerade (a social norm cloaked as a functional requirement) only when the full thread is visible?

The data infrastructure exists (`repo` and `pr_number` columns in `cleaned`). The method, prompt design, and runner do not. This is a candidate for a second study.

See [CONFORMITY.md](../../docs/notes/CONFORMITY.md#scoring) for the full rationale.
