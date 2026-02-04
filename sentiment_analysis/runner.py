"""
Orchestrate sentiment analysis on extracted JSONL: read events, run POC models, write results.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from sentiment_analysis.reader import load_events_with_text_from_paths
from sentiment_analysis.pipelines import run_sentiment

logger = logging.getLogger(__name__)

def _write_samples_md(
    output_path: Path,
    raw_events: List[Dict[str, Any]],
    sentiments: List[Dict[str, Any]],
) -> None:
    """Write samples as Markdown sections (text + classifications) to output_path."""
    lines = ["# Sentiment analysis samples", ""]
    for i, (raw, sent) in enumerate(zip(raw_events, sentiments), 1):
        text = sent.get("text", "")
        event_type = raw.get("type", "")
        created = raw.get("created_at", "")
        actor = raw.get("actor", {}).get("login", "")
        cardiff = sent.get("cardiffnlp", {})
        distil = sent.get("distilbert", {})
        cardiff_str = f"{cardiff.get('label', '—')} ({cardiff.get('score', 0):.2f})"
        distil_str = f"{distil.get('label', '—')} ({distil.get('score', 0):.2f})"
        lines.extend([
            f"## Sample {i}",
            "",
            f"- **Event type:** {event_type}",
            f"- **Created:** {created}",
            f"- **Actor:** {actor}",
            f"- **cardiffnlp:** {cardiff_str}",
            f"- **distilbert:** {distil_str}",
            "",
            "**Text:**",
            "",
            text,
            "",
            "---",
            "",
        ])
    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote samples to %s", output_path)


def _collect_paths(path: str | Path) -> List[Path]:
    """Return list of JSONL file paths (single file or all .jsonl in directory)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    if p.is_file():
        return [p]
    return sorted(p.glob("*.jsonl"))


def run_analysis(
    input_path: str | Path,
    output_dir: str | Path = "./data/sentiment",
    models: List[str] | None = None,
) -> str:
    """
    Load events from input_path (file or directory of .jsonl), run sentiment,
    write one JSONL of results to output_dir. Returns path to output file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = _collect_paths(input_path)
    if not paths:
        raise FileNotFoundError(f"No .jsonl files under {input_path}")

    events_with_text = list(load_events_with_text_from_paths(paths))
    if not events_with_text:
        logger.warning("No events with text found in %s", paths)
        out_path = output_dir / "sentiment_results.jsonl"
        out_path.write_text("", encoding="utf-8")
        return str(out_path)

    texts = [t for _, t in events_with_text]
    raw_events = [e for e, _ in events_with_text]

    sentiments = run_sentiment(texts, models=models)

    out_path = output_dir / "sentiment_results.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for raw, sentiment_row in zip(raw_events, sentiments):
            record = {
                "event_id": raw.get("id"),
                "type": raw.get("type"),
                "created_at": raw.get("created_at"),
                "actor_login": raw.get("actor", {}).get("login"),
                "sentiment": sentiment_row,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    md_path = output_dir / "samples.md"
    _write_samples_md(md_path, raw_events, sentiments)

    logger.info("Wrote %d results to %s", len(sentiments), out_path)
    return str(out_path)
