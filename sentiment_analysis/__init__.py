"""
Sentiment analysis on extracted PR event data.
Reads JSONL from dataset extraction and runs POC models (cardiffnlp, distilbert).
"""
from sentiment_analysis.reader import load_events_with_text
from sentiment_analysis.pipelines import run_sentiment
from sentiment_analysis.runner import run_analysis

__all__ = ["load_events_with_text", "run_sentiment", "run_analysis"]
