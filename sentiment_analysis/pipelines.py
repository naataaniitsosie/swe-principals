"""
Sentiment analysis pipelines per POC.
- cardiffnlp/twitter-roberta-base-sentiment-latest (negative / neutral / positive)
- distilbert-base-uncased-finetuned-sst-2-english (positive / negative)
"""
import logging
from typing import Any, Dict, List

from transformers import pipeline

logger = logging.getLogger(__name__)

# POC models (see POC.md)
CARDIFF_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
DISTILBERT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

# Short names for output keys
MODEL_KEYS = {
    CARDIFF_MODEL: "cardiffnlp",
    DISTILBERT_MODEL: "distilbert",
}

MAX_LENGTH = 512


def _get_pipeline(model_id: str, **kwargs: Any):
    return pipeline(
        "sentiment-analysis",
        model=model_id,
        truncation=True,
        max_length=MAX_LENGTH,
        **kwargs,
    )


def run_sentiment(
    texts: List[str],
    models: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Run sentiment analysis on a list of texts with POC models.
    If models is None, uses both CARDIFF_MODEL and DISTILBERT_MODEL.
    Returns list of dicts: [{ "text": ..., "cardiffnlp": { "label", "score" }, "distilbert": { ... } }, ...]
    """
    if models is None:
        models = [CARDIFF_MODEL, DISTILBERT_MODEL]

    results = []
    pipelines = {m: _get_pipeline(m) for m in models}

    for text in texts:
        row = {"text": text[:500]}
        for model_id, pipe in pipelines.items():
            key = MODEL_KEYS.get(model_id, model_id)
            try:
                out = pipe(text[: MAX_LENGTH * 4])
                if out:
                    row[key] = {"label": out[0]["label"], "score": out[0]["score"]}
                else:
                    row[key] = {"label": None, "score": None}
            except Exception as e:
                logger.warning("Sentiment failed for %s: %s", key, e)
                row[key] = {"label": None, "score": None}
        results.append(row)

    return results


def run_sentiment_single(
    text: str,
    models: List[str] | None = None,
) -> Dict[str, Any]:
    """Run sentiment on a single text. Returns one dict with model keys."""
    out = run_sentiment([text], models=models)
    return out[0] if out else {}
